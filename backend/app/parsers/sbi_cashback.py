import re
from datetime import datetime
from app.parsers.base import BaseParser
from app.parsers.registry import register


@register
class SBICashbackParser(BaseParser):
    bank_name = "SBI Cashback"
    account_type = "credit_card"

    @classmethod
    def can_parse(cls, text: str) -> bool:
        return "GSTIN of SBI Card" in text and "Cashback" in text

    def parse(self, text: str) -> list[dict]:
        transactions = []
        lines = text.split('\n')
        date_pattern = re.compile(
            r'^(\d{2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{2})\s+(.*)'
        )
        in_txn_section = False

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "TRANSACTIONS FOR" in line:
                in_txn_section = True
                continue
            if "Important Messages" in line:
                break

            m = date_pattern.match(line)
            if not m:
                continue

            day, mon, year_short, rest = m.group(1), m.group(2), m.group(3), m.group(4)
            year = "20" + year_short

            amount_match = re.search(r'([\d,]+\.\d{2})\s+([DC])$', rest)
            if not amount_match:
                continue

            amount_str, txn_code = amount_match.group(1), amount_match.group(2)
            desc = rest[:amount_match.start()].strip()
            amount = float(amount_str.replace(",", ""))
            txn_type = "credit" if txn_code == "C" else "debit"
            is_emi = "(Pay in EMIs)" in desc

            try:
                dt = datetime.strptime(f"{day} {mon} {year}", "%d %b %Y")
            except ValueError:
                continue

            transactions.append({
                "transaction_date": dt.strftime("%Y-%m-%d"),
                "description": desc,
                "amount": amount,
                "type": txn_type,
                "merchant_category": None,
                "is_emi": is_emi,
            })

        return transactions
