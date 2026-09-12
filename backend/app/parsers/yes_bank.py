import re
from datetime import datetime
from app.parsers.base import BaseParser
from app.parsers.registry import register


@register
class YesBankParser(BaseParser):
    bank_name = "YES BANK"
    account_type = "credit_card"

    @classmethod
    def can_parse(cls, text: str) -> bool:
        return "YES BANK" in text and "Credit Card Statement" in text

    def parse(self, text: str) -> list[dict]:
        transactions = []
        lines = text.split('\n')
        date_pattern = re.compile(r'^(\d{2}/\d{2}/\d{4})\s+(.*)')
        in_statement = False

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "Statement Details" in line:
                in_statement = True
                continue
            if "End of the Statement" in line:
                in_statement = False
                continue
            if not in_statement:
                continue
            if "SMS" in line and '"Help"' in line:
                continue

            m = date_pattern.match(line)
            if not m:
                continue

            date_str, rest = m.group(1), m.group(2)

            amount_match = re.search(r'([\d,]+\.\d{2})\s*(Dr|Cr)$', rest)
            if not amount_match:
                continue

            amount_str, txn_code = amount_match.group(1), amount_match.group(2)
            desc_part = rest[:amount_match.start()].strip()
            txn_type = "credit" if txn_code == "Cr" else "debit"
            amount = float(amount_str.replace(",", ""))

            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
            except ValueError:
                continue

            merchant_cat = None
            for known_cat in [
                "Miscellaneous Stores", "Retail Outlet Services",
                "Service Stations", "Professional Service",
                "Groceries", "Dining", "Entertainment",
                "Travel", "Utilities",
            ]:
                if known_cat in desc_part:
                    merchant_cat = known_cat
                    desc_part = desc_part.replace(known_cat, "").strip()
                    break

            transactions.append({
                "transaction_date": dt.strftime("%Y-%m-%d"),
                "description": desc_part.strip(),
                "amount": amount,
                "type": txn_type,
                "merchant_category": merchant_cat,
                "is_emi": False,
            })

        return transactions
