from collections import defaultdict
from decimal import Decimal


def compute_category_breakdown(transactions: list[dict]) -> list[dict]:
    category_totals: dict[str, dict] = defaultdict(lambda: {"total": Decimal("0"), "count": 0, "classification": ""})
    total_spend = Decimal("0")
    
    for txn in transactions:
        if txn.get("type") != "debit":
            continue
        if txn.get("classification") == "transfer":
            continue
        category = txn.get("category", "Uncategorized")
        amount = Decimal(str(txn.get("amount", 0)))
        classification = txn.get("classification", "uncategorized")
        
        category_totals[category]["total"] += amount
        category_totals[category]["count"] += 1
        category_totals[category]["classification"] = classification
        total_spend += amount
    
    if total_spend == 0:
        return []
    
    result = []
    for category, data in sorted(category_totals.items(), key=lambda x: x[1]["total"], reverse=True):
        result.append({
            "category": category,
            "classification": data["classification"],
            "total": float(data["total"]),
            "count": data["count"],
            "percentage": round(float(data["total"] / total_spend * 100), 1),
        })
    
    return result


def compute_summary(transactions: list[dict]) -> dict:
    mandatory = Decimal("0")
    discretionary = Decimal("0")
    total = Decimal("0")
    
    for txn in transactions:
        if txn.get("type") != "debit":
            continue
        if txn.get("classification") == "transfer":
            continue
        amount = Decimal(str(txn.get("amount", 0)))
        classification = txn.get("classification", "uncategorized")
        total += amount
        if classification == "mandatory":
            mandatory += amount
        elif classification == "discretionary":
            discretionary += amount
    
    return {
        "total_spend": float(total),
        "mandatory_spend": float(mandatory),
        "discretionary_spend": float(discretionary),
        "mandatory_percentage": round(float(mandatory / total * 100), 1) if total else 0,
        "discretionary_percentage": round(float(discretionary / total * 100), 1) if total else 0,
    }
