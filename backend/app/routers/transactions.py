import csv
import io
import json as json_lib
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date, datetime
from decimal import Decimal

from app.database import get_db
from app.models.transaction import Transaction
from app.classifier.engine import ClassificationEngine
from app.classifier.rules import classify_transaction
from app.schemas.transaction import TransactionUpdate
from app.services.auth import get_session_context, SessionContext

router = APIRouter(prefix="/transactions", tags=["transactions"])
classifier = ClassificationEngine()


@router.get("/")
async def list_transactions(
    bank_name: str | None = Query(None),
    category: str | None = Query(None),
    classification: str | None = Query(None),
    txn_type: str | None = Query(None, alias="type"),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    search: str | None = Query(None),
    min_amount: float | None = Query(None),
    max_amount: float | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    if bank_name:
        conditions.append(Transaction.bank_name == bank_name)
    if category:
        conditions.append(Transaction.category == category)
    if classification:
        conditions.append(Transaction.classification == classification)
    if txn_type:
        conditions.append(Transaction.type == txn_type)
    if start_date:
        try:
            d = date.fromisoformat(start_date)
            conditions.append(Transaction.transaction_date >= d)
        except ValueError:
            pass
    if end_date:
        try:
            d = date.fromisoformat(end_date)
            conditions.append(Transaction.transaction_date <= d)
        except ValueError:
            pass
    if search:
        conditions.append(Transaction.description.ilike(f"%{search}%"))
    if min_amount is not None:
        conditions.append(Transaction.amount >= min_amount)
    if max_amount is not None:
        conditions.append(Transaction.amount <= max_amount)

    if context.user_id:
        conditions.append(Transaction.user_id == context.user_id)
    elif context.session_id:
        conditions.append(Transaction.session_id == context.session_id)
    else:
        # Strict guest privacy: unsigned guest without active session sees 0 transactions
        return {
            "total": 0,
            "offset": offset,
            "limit": limit,
            "transactions": [],
        }

    query = select(Transaction).where(and_(*conditions) if conditions else True).order_by(Transaction.transaction_date.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    txns = result.scalars().all()

    count_query = select(func.count(Transaction.id)).where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "transactions": [{
            "id": t.id,
            "bank_name": t.bank_name,
            "account_type": t.account_type,
            "transaction_date": t.transaction_date.isoformat(),
            "description": t.description,
            "amount": float(t.amount),
            "type": t.type,
            "category": t.category,
            "classification": t.classification,
            "merchant_category": t.merchant_category,
            "is_emi": t.is_emi,
            "is_recurring": t.is_recurring,
        } for t in txns],
    }


@router.patch("/{txn_id}")
async def recategorize_transaction(
    txn_id: str,
    body: TransactionUpdate,
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction).where(Transaction.id == txn_id)
    if context.user_id:
        query = query.where(Transaction.user_id == context.user_id)
    elif context.session_id:
        query = query.where(Transaction.session_id == context.session_id)

    result = await db.execute(query)
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(404, "Transaction not found")

    data = body.model_dump(exclude_none=True)
    for field in ("category", "classification", "tags", "type", "description"):
        if field in data:
            setattr(txn, field, data[field])

    await db.commit()
    return {"message": "Transaction updated"}


@router.delete("/{txn_id}")
async def delete_transaction(
    txn_id: str,
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction).where(Transaction.id == txn_id)
    if context.user_id:
        query = query.where(Transaction.user_id == context.user_id)
    elif context.session_id:
        query = query.where(Transaction.session_id == context.session_id)

    result = await db.execute(query)
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(404, "Transaction not found")
    await db.delete(txn)
    await db.commit()
    return {"message": "Transaction deleted"}


@router.post("/reclassify")
async def reclassify_all(
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction)
    if context.user_id:
        query = query.where(Transaction.user_id == context.user_id)
    elif context.session_id:
        query = query.where(Transaction.session_id == context.session_id)
    else:
        query = query.where(Transaction.user_id.is_(None))

    result = await db.execute(query)
    txns = result.scalars().all()
    count = 0
    for txn in txns:
        cat, cls = classify_transaction(txn.description, txn.merchant_category, float(txn.amount))
        if cat != txn.category or cls != txn.classification:
            txn.category = cat
            txn.classification = cls
            count += 1
    await db.commit()
    return {"message": f"Reclassified {count} transactions"}


@router.get("/export/csv")
async def export_transactions_csv(
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction).order_by(Transaction.transaction_date)
    if context.user_id:
        query = query.where(Transaction.user_id == context.user_id)
    elif context.session_id:
        query = query.where(Transaction.session_id == context.session_id)
    else:
        # Strict guest privacy
        query = query.where(False)

    result = await db.execute(query)
    txns = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "date", "description", "amount", "type", "category", "classification",
                      "bank_name", "account_type", "source", "merchant_category", "is_emi", "is_recurring"])
    for t in txns:
        writer.writerow([
            t.id, t.transaction_date.isoformat(), t.description, float(t.amount), t.type,
            t.category, t.classification, t.bank_name, t.account_type, t.source,
            t.merchant_category or "", t.is_emi, t.is_recurring,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@router.get("/export/json")
async def export_transactions_json(
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction).order_by(Transaction.transaction_date)
    if context.user_id:
        query = query.where(Transaction.user_id == context.user_id)
    elif context.session_id:
        query = query.where(Transaction.session_id == context.session_id)
    else:
        # Strict guest privacy
        query = query.where(False)

    result = await db.execute(query)
    txns = result.scalars().all()

    data = [{
        "id": t.id,
        "date": t.transaction_date.isoformat(),
        "description": t.description,
        "amount": float(t.amount),
        "type": t.type,
        "category": t.category,
        "classification": t.classification,
        "bank_name": t.bank_name,
        "account_type": t.account_type,
        "source": t.source,
        "merchant_category": t.merchant_category,
        "is_emi": t.is_emi,
        "is_recurring": t.is_recurring,
    } for t in txns]

    return StreamingResponse(
        iter([json_lib.dumps(data, indent=2, default=str)]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=transactions.json"},
    )


@router.get("/descriptions")
async def autocomplete_descriptions(
    q: str = Query("", min_length=0, max_length=200),
    limit: int = Query(10, le=50),
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Transaction.description.isnot(None)]
    if q:
        conditions.append(Transaction.description.ilike(f"%{q}%"))
    if context.user_id:
        conditions.append(Transaction.user_id == context.user_id)
    elif context.session_id:
        conditions.append(Transaction.session_id == context.session_id)

    query = select(Transaction.description).distinct().where(and_(*conditions)).limit(limit)
    result = await db.execute(query)
    descriptions = [row[0] for row in result.all() if row[0]]
    return {"descriptions": descriptions}


@router.get("/categories")
async def list_categories():
    from app.classifier.rules import get_all_categories
    return {"categories": get_all_categories()}


@router.get("/banks")
async def list_banks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Transaction.bank_name).distinct())
    banks = [row[0] for row in result.all()]
    return {"banks": banks}
