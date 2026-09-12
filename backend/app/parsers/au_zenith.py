import re
from datetime import datetime
from app.parsers.base import BaseParser
from app.parsers.registry import register


@register
class AUZenithParser(BaseParser):
    bank_name = "AU Zenith+"
    account_type = "credit_card"

    @classmethod
    def can_parse(cls, text: str) -> bool:
        return "AU" in text and "Zenith+" in text

    def parse(self, text: str) -> list[dict]:
        transactions = []
        lines = text.split('\n')
        date_pattern = re.compile(r'^(\d{2})\s*/\s*(\d{2})\s*/\s*(\d{4})\s+(.*)')
        in_txn_section = False
        merged = []
        current = None

        for line in lines:
            line = line.strip()
            if "Transaction Summary" in line:
                in_txn_section = True
                continue
            if "Reward Point Summary" in line:
                in_txn_section = False
                continue
            if "Page " in line and " of " in line:
                continue

            if not in_txn_section:
                continue

            m = date_pattern.match(line)
            if m:
                if current:
                    merged.append(current)
                day, mon, year, rest = m.group(1), m.group(2), m.group(3), m.group(4)
                current = {"date": f"{day}/{mon}/{year}", "detail": rest}
            else:
                if current:
                    current["detail"] += " " + line

        if current:
            merged.append(current)

        for entry in merged:
            detail = entry["detail"]
            amt_match = re.search(r'([\d,]+\.\d{2})(Dr\.|Cr\.)', detail)
            if amt_match:
                amount_str = amt_match.group(1)
                txn_code = amt_match.group(2)
                desc = detail[:amt_match.start()].strip().rstrip("`").strip()
                amount = float(amount_str.replace(",", ""))
                txn_type = "credit" if txn_code == "Cr." else "debit"
                is_emi = "Convert to EMI" in detail

                try:
                    dt = datetime.strptime(entry["date"], "%d/%m/%Y")
                except ValueError:
                    continue

                transactions.append({
                    "transaction_date": dt.strftime("%Y-%m-%d"),
                    "description": desc.strip(),
                    "amount": amount,
                    "type": txn_type,
                    "merchant_category": None,
                    "is_emi": is_emi,
                })

        return transactions
