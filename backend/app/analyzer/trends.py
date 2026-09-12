from collections import defaultdict
from decimal import Decimal
from datetime import datetime


def compute_monthly_trends(transactions: list[dict]) -> list[dict]:
    monthly: dict[str, dict] = defaultdict(lambda: {"mandatory": Decimal("0"), "discretionary": Decimal("0")})
    
    for txn in transactions:
        date_str = txn.get("transaction_date", "")
        if not date_str:
            continue
        try:
            dt = datetime.fromisoformat(date_str) if "T" not in date_str else datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            continue
        month_key = dt.strftime("%Y-%m")
        amount = Decimal(str(txn.get("amount", 0)))
        classification = txn.get("classification", "uncategorized")
        
        if classification == "mandatory" and txn.get("type") == "debit":
            monthly[month_key]["mandatory"] += amount
        elif classification == "discretionary" and txn.get("type") == "debit":
            monthly[month_key]["discretionary"] += amount
    
    result = []
    for month_key in sorted(monthly.keys()):
        data = monthly[month_key]
        total = data["mandatory"] + data["discretionary"]
        dt = datetime.strptime(month_key + "-01", "%Y-%m-%d")
        result.append({
            "month": dt.strftime("%b %Y"),
            "mandatory": float(data["mandatory"]),
            "discretionary": float(data["discretionary"]),
            "total": float(total),
        })
    
    return result
