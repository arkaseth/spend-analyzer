import re
from datetime import datetime
from app.parsers.base import BaseParser
from app.parsers.registry import register


@register
class HDFCSwiggyParser(BaseParser):
    bank_name = "HDFC Swiggy"
    account_type = "credit_card"

    @classmethod
    def can_parse(cls, text: str) -> bool:
        return "HDFC Bank" in text and "Swiggy" in text and "Credit Card" in text

    def parse(self, text: str) -> list[dict]:
        transactions = []
        lines = text.split('\n')
        date_pattern = re.compile(r'^(\d{2}/\d{2}/\d{4})\s+(.*)')
        in_domestic = False

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "Domestic Transactions" in line or "mestic Transactions" in line:
                in_domestic = True
                continue

            m = date_pattern.match(line)
            if not m:
                continue
            if not in_domestic:
                continue

            date_str, rest = m.group(1), m.group(2)

            amount_match = re.search(r'([\d,]+\.\d{2})\s*(Cr)?\s*$', rest)
            if not amount_match:
                continue

            amount_str = amount_match.group(1)
            is_credit = amount_match.group(2) is not None
            desc = rest[:amount_match.start()].strip()
            amount = float(amount_str.replace(",", ""))
            txn_type = "credit" if is_credit else "debit"

            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
            except ValueError:
                continue

            transactions.append({
                "transaction_date": dt.strftime("%Y-%m-%d"),
                "description": desc,
                "amount": amount,
                "type": txn_type,
                "merchant_category": None,
                "is_emi": False,
            })

        return transactions
