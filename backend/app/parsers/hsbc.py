import re
from datetime import datetime
from app.parsers.base import BaseParser
from app.parsers.registry import register


@register
class HSBCParser(BaseParser):
    bank_name = "HSBC"
    account_type = "credit_card"

    @classmethod
    def can_parse(cls, text: str) -> bool:
        return "HSBC" in text and "CREDIT CARD STATEMENT" in text

    def parse(self, text: str) -> list[dict]:
        transactions = []
        lines = text.split('\n')
        date_pattern = re.compile(
            r'^(\d{2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+(.*)'
        )
        in_txn = False

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "DATE TRANSACTION DETAILS AMOUNT" in line.upper():
                in_txn = True
                continue
            if "TOTAL" in line.upper() and "PURCHASE" in line.upper():
                in_txn = False
                continue
            if "ACCOUNT SUMMARY" in line.upper():
                in_txn = False
                continue
            if not in_txn:
                continue

            m = date_pattern.match(line)
            if not m:
                continue

            day_str, mon_str, rest = m.group(1), m.group(2), m.group(3)

            amount_match = re.search(r'([\d,]+\.\d{2})\s*(CR)?\s*$', rest)
            if not amount_match:
                continue

            amount_str = amount_match.group(1)
            is_credit = amount_match.group(2) is not None
            desc = rest[:amount_match.start()].strip()
            amount = float(amount_str.replace(",", ""))
            txn_type = "credit" if is_credit else "debit"

            try:
                dt = datetime.strptime(f"{day_str} {mon_str} 2026", "%d %b %Y")
                if dt > datetime.now():
                    dt = datetime.strptime(f"{day_str} {mon_str} 2025", "%d %b %Y")
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
