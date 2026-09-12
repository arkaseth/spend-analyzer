import os
import uuid
import hashlib
import tempfile
from pathlib import Path
from datetime import date
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_

from app.database import get_db
from app.models.transaction import Transaction
from app.parsers import detect_parser, all_parsers
from app.schemas.transaction import ManualTransactionCreate
import app.parsers

from app.classifier.engine import ClassificationEngine
from app.ocr.engine import OCREngine
from app.services.auth import get_session_context, SessionContext

router = APIRouter(prefix="/upload", tags=["upload"])
classifier = ClassificationEngine()
ocr_engine = OCREngine()

MAX_PDF_SIZE = 50 * 1024 * 1024


def extract_and_classify_pdf(tmp_path: str):
    import pdfplumber
    text = None

    with pdfplumber.open(tmp_path) as pdf:
        pages_text = []
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        text = "\n".join(pages_text)

    if not text or not text.strip():
        if not ocr_engine.available:
            raise ValueError("This is a scanned image PDF requiring OCR, but Tesseract OCR is not installed.")
        ocr_text = ocr_engine.extract_text(tmp_path)
        if ocr_text:
            text = ocr_text

    if not text or not text.strip():
        raise ValueError("Could not extract any text from this PDF (OCR produced no text)")

    parser_cls = detect_parser(text)
    if not parser_cls:
        raise ValueError("Could not detect bank format. Ensure this is a supported bank statement.")

    parser = parser_cls()
    raw_txns = parser.parse(text)
    if not raw_txns:
        raise ValueError("No transactions found in the statement")

    classified_txns = classifier.classify_batch(raw_txns)
    return parser, classified_txns


def build_and_save_txns(parser, classified_txns, filename, context, existing_hashes, db):
    saved_count = 0
    skipped_count = 0

    for txn_data in classified_txns:
        date_str = txn_data["transaction_date"]
        if isinstance(date_str, str):
            txn_date = date.fromisoformat(date_str)
        else:
            txn_date = date_str

        amt = round(float(txn_data.get("amount", 0)), 2)
        desc = str(txn_data.get("description", "")).strip()
        ttype = txn_data.get("type", "debit")

        # Deterministic hash to deduplicate across repeated uploads
        hash_input = f"{parser.bank_name}|{txn_date.isoformat()}|{amt:.2f}|{desc.lower()}|{ttype}"
        txn_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        if txn_hash in existing_hashes:
            skipped_count += 1
            continue

        existing_hashes.add(txn_hash)
        txn = Transaction(
            bank_name=parser.bank_name,
            account_type=parser.account_type,
            source="pdf_upload",
            transaction_date=txn_date,
            description=desc,
            amount=amt,
            type=ttype,
            category=txn_data.get("category", "Uncategorized"),
            classification=txn_data.get("classification", "uncategorized"),
            merchant_category=txn_data.get("merchant_category"),
            is_emi=bool(txn_data.get("is_emi", False)),
            statement_file=filename,
            txn_hash=txn_hash,
            user_id=context.user_id,
            is_transient=context.is_transient,
            session_id=context.session_id,
        )
        db.add(txn)
        saved_count += 1

    return saved_count, skipped_count


async def _get_existing_hashes(db: AsyncSession, context: SessionContext) -> set[str]:
    hash_query = select(Transaction.txn_hash).where(Transaction.txn_hash.is_not(None))
    if context.user_id:
        hash_query = hash_query.where(Transaction.user_id == context.user_id)
    elif context.session_id:
        hash_query = hash_query.where(Transaction.session_id == context.session_id)
    existing_res = await db.execute(hash_query)
    return set(existing_res.scalars().all())


@router.post("/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")

    content = await file.read()
    if len(content) > MAX_PDF_SIZE:
        raise HTTPException(413, "File too large (max 50MB)")

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        parser, classified_txns = extract_and_classify_pdf(tmp_path)
        existing_hashes = await _get_existing_hashes(db, context)
        saved_count, skipped_count = build_and_save_txns(
            parser, classified_txns, file.filename, context, existing_hashes, db
        )
        await db.commit()
        return {
            "message": f"Processed {len(classified_txns)} transactions ({saved_count} new, {skipped_count} duplicates skipped) from {parser.bank_name}",
            "count": saved_count,
            "skipped": skipped_count,
            "total": len(classified_txns),
            "bank": parser.bank_name,
            "results": [
                {
                    "filename": file.filename,
                    "status": "success",
                    "count": saved_count,
                    "skipped": skipped_count,
                    "bank": parser.bank_name,
                }
            ],
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error processing PDF: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/batch")
async def upload_multiple_pdfs(
    files: list[UploadFile] = File(...),
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db)
):
    if not files:
        raise HTTPException(400, "No files provided")

    existing_hashes = await _get_existing_hashes(db, context)
    total_saved = 0
    total_skipped = 0
    successful_files = 0
    file_results = []

    for file in files:
        filename = file.filename or "unknown.pdf"
        if not filename.lower().endswith(".pdf"):
            file_results.append({
                "filename": filename,
                "status": "error",
                "error": "Only PDF files are supported"
            })
            continue

        content = await file.read()
        if len(content) > MAX_PDF_SIZE:
            file_results.append({
                "filename": filename,
                "status": "error",
                "error": "File too large (max 50MB)"
            })
            continue

        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            parser, classified_txns = extract_and_classify_pdf(tmp_path)
            saved_count, skipped_count = build_and_save_txns(
                parser, classified_txns, filename, context, existing_hashes, db
            )
            total_saved += saved_count
            total_skipped += skipped_count
            successful_files += 1
            file_results.append({
                "filename": filename,
                "status": "success",
                "bank": parser.bank_name,
                "count": saved_count,
                "skipped": skipped_count,
                "total": len(classified_txns),
            })
        except Exception as e:
            file_results.append({
                "filename": filename,
                "status": "error",
                "error": str(e)
            })
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    if successful_files > 0:
        await db.commit()

    return {
        "total_files": len(files),
        "successful_files": successful_files,
        "total_saved": total_saved,
        "total_skipped": total_skipped,
        "results": file_results,
        "message": f"Processed {successful_files}/{len(files)} file(s): {total_saved} new transactions saved ({total_skipped} duplicates skipped)",
    }


@router.post("/manual")
async def add_manual_transaction(
    txn_data: ManualTransactionCreate,
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db),
):
    raw = txn_data.model_dump()
    classified = classifier.classify(raw)

    amt = round(float(txn_data.amount), 2)
    desc = txn_data.description.strip()
    hash_input = f"{txn_data.bank_name}|{txn_data.transaction_date.isoformat()}|{amt:.2f}|{desc.lower()}|{txn_data.type}"
    txn_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    txn = Transaction(
        bank_name=txn_data.bank_name,
        account_type=txn_data.account_type,
        source="manual",
        transaction_date=txn_data.transaction_date,
        description=desc,
        amount=amt,
        type=txn_data.type,
        category=classified["category"],
        classification=classified["classification"],
        merchant_category=txn_data.merchant_category,
        is_emi=txn_data.is_emi,
        is_recurring=txn_data.is_recurring,
        txn_hash=txn_hash,
        user_id=context.user_id,
        is_transient=context.is_transient,
        session_id=context.session_id,
    )
    db.add(txn)
    await db.commit()
    return {"message": "Transaction added", "id": txn.id}


@router.post("/reset")
async def reset_all_data(
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    if context.user_id:
        conditions.append(Transaction.user_id == context.user_id)
    elif context.session_id:
        conditions.append(Transaction.session_id == context.session_id)
    else:
        conditions.append(Transaction.user_id.is_(None))

    await db.execute(delete(Transaction).where(and_(*conditions) if conditions else True))
    await db.commit()
    return {"message": "Transactions cleared successfully", "deleted": True}


@router.get("/banks")
async def list_supported_banks():
    return {"banks": list(all_parsers().keys())}
