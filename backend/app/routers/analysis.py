from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.transaction import Transaction
from app.analyzer.categories import compute_category_breakdown, compute_summary
from app.analyzer.trends import compute_monthly_trends
from app.analyzer.insights import generate_insights
from app.services.auth import get_session_context, SessionContext

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/overview")
async def get_overview(
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction)
    if context.user_id:
        query = query.where(Transaction.user_id == context.user_id)
    elif context.session_id:
        query = query.where(Transaction.session_id == context.session_id)
    else:
        # Strict guest privacy: unsigned visitors have no data unless they sign in, start an incognito session, or demo mode
        return {
            "total_spend": 0.0,
            "income": 0.0,
            "mandatory_spend": 0.0,
            "discretionary_spend": 0.0,
            "mandatory_percentage": 0.0,
            "discretionary_percentage": 0.0,
            "monthly_trends": [],
            "category_breakdown": [],
            "insights": [],
            "total_transactions": 0,
            "message": "Sign in or explore demo data to view spend analysis.",
        }

    result = await db.execute(query)
    txns = result.scalars().all()

    txn_dicts = [{
        "transaction_date": t.transaction_date.isoformat(),
        "description": t.description,
        "amount": float(t.amount),
        "type": t.type,
        "category": t.category,
        "classification": t.classification,
        "merchant_category": t.merchant_category,
        "is_emi": t.is_emi,
        "is_recurring": t.is_recurring,
        "bank_name": t.bank_name,
    } for t in txns]

    if not txn_dicts:
        return {
            "total_spend": 0.0,
            "income": 0.0,
            "mandatory_spend": 0.0,
            "discretionary_spend": 0.0,
            "mandatory_percentage": 0.0,
            "discretionary_percentage": 0.0,
            "monthly_trends": [],
            "category_breakdown": [],
            "insights": [],
            "total_transactions": 0,
            "message": "No transactions found. Upload a statement first.",
        }

    summary = compute_summary(txn_dicts)
    trends = compute_monthly_trends(txn_dicts)
    categories = compute_category_breakdown(txn_dicts)
    insights = generate_insights(txn_dicts)

    return {
        **summary,
        "monthly_trends": trends,
        "category_breakdown": categories,
        "insights": insights,
        "total_transactions": len(txns),
    }
