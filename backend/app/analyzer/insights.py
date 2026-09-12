from collections import defaultdict
from decimal import Decimal


def generate_insights(transactions: list[dict]) -> list[dict]:
    insights = []
    
    discretionary_txns = [t for t in transactions if t.get("classification") == "discretionary" and t.get("type") == "debit"]
    category_spend = defaultdict(lambda: {"total": Decimal("0"), "count": 0, "transactions": []})
    
    for txn in discretionary_txns:
        cat = txn.get("category", "Other")
        amount = Decimal(str(txn.get("amount", 0)))
        category_spend[cat]["total"] += amount
        category_spend[cat]["count"] += 1
        category_spend[cat]["transactions"].append(txn)
    
    sorted_cats = sorted(category_spend.items(), key=lambda x: x[1]["total"], reverse=True)
    
    if sorted_cats:
        top_cat = sorted_cats[0]
        insights.append({
            "title": "Top Discretionary Spend",
            "description": f"You spend ₹{float(top_cat[1]['total']):,.0f} on {top_cat[0]} — your highest discretionary category.",
            "savings_potential": round(float(top_cat[1]["total"] * Decimal("0.3")), 2),
            "category": top_cat[0],
        })
    
    top3_total = sum(c[1]["total"] for c in sorted_cats[:3])
    all_disc_total = sum(txn.get("amount", 0) for txn in discretionary_txns)
    all_disc_decimal = Decimal(str(all_disc_total)) if not isinstance(all_disc_total, Decimal) else all_disc_total
    
    if top3_total > 0:
        savings = round(float(top3_total * Decimal("0.5")), 2)
        insights.append({
            "title": "Cut Top 3 Categories by 50%",
            "description": f"Reducing your top 3 discretionary categories by half could save ₹{savings:,.0f}/month.",
            "savings_potential": savings,
            "category": ", ".join(c[0] for c in sorted_cats[:3]),
        })
    
    recurring_txns = find_recurring(transactions)
    if recurring_txns:
        recurring_total = sum(txn.get("amount", 0) for txn in recurring_txns)
        insights.append({
            "title": "Recurring Subscriptions",
            "description": f"You have {len(recurring_txns)} recurring subscriptions totaling ₹{recurring_total:,.0f}/month.",
            "savings_potential": round(recurring_total * 0.3, 2) if recurring_total else 0,
            "category": "Subscriptions",
        })
    
    total_spend = sum(Decimal(str(t.get("amount", 0))) for t in transactions if t.get("type") == "debit" and t.get("classification") != "transfer")
    if total_spend > 0:
        disc_total = sum(Decimal(str(t.get("amount", 0))) for t in discretionary_txns)
        disc_pct = round(float(disc_total / total_spend * 100), 1)
        insights.append({
            "title": "Discretionary Ratio",
            "description": f"{disc_pct}% of your spending is discretionary ({float(disc_total):,.0f} out of ₹{float(total_spend):,.0f}).",
            "savings_potential": round(float(disc_total * Decimal("0.2")), 2),
            "category": None,
        })
    
    return insights


def find_recurring(transactions: list[dict]) -> list[dict]:
    from collections import Counter
    
    desc_counter = Counter()
    for txn in transactions:
        if txn.get("type") == "debit" and txn.get("classification") != "transfer":
            desc = txn.get("description", "").strip()
            if desc:
                desc_counter[desc] += 1
    
    recurring_descs = {desc for desc, count in desc_counter.items() if count >= 2}
    return [t for t in transactions if t.get("description", "").strip() in recurring_descs and t.get("type") == "debit"]
