import re
from datetime import datetime
from app.parsers.base import BaseParser
from app.parsers.registry import register


@register
class AmexParser(BaseParser):
    bank_name = "AMEX"
    account_type = "credit_card"

    MONTH_MAP = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12,
    }

    @classmethod
    def can_parse(cls, text: str) -> bool:
        return "American Express" in text and "Statement of Account" in text

    def parse(self, text: str) -> list[dict]:
        transactions = []
        lines = text.split('\n')

        year_match = re.search(r'Statement Period.*(\d{4})', text)
        year = year_match.group(1) if year_match else "2025"

        month_names = "|".join(self.MONTH_MAP.keys())
        txn_pattern = re.compile(rf'^({month_names})\s+(\d+)\s+(.*)')
        in_foreign_section = False

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "Foreign Spending" in line and "Amount" in line:
                in_foreign_section = True
                continue
            if "Payment Advice" in line or "Please return" in line or "Payment Methods" in line:
                break
            if not in_foreign_section:
                continue

            m = txn_pattern.match(line)
            if not m:
                continue

            month_name, day_str, rest = m.group(1), m.group(2), m.group(3)

            amt_match = re.search(r'([\d,]+\.\d{2})\s*$', rest)
            if not amt_match:
                continue

            amount_str = amt_match.group(1)
            desc = rest[:amt_match.start()].strip()
            amount = float(amount_str.replace(",", ""))

            month_num = self.MONTH_MAP.get(month_name)
            if not month_num:
                continue

            try:
                dt = datetime(int(year), month_num, int(day_str))
            except (ValueError, TypeError):
                continue

            transactions.append({
                "transaction_date": dt.strftime("%Y-%m-%d"),
                "description": desc.strip(),
                "amount": amount,
                "type": "debit",
                "merchant_category": None,
                "is_emi": False,
            })

        return transactions
