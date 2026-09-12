import re
from datetime import datetime
from app.parsers.base import BaseParser
from app.parsers.registry import register


@register
class ICICIAmazonParser(BaseParser):
    bank_name = "ICICI Amazon Pay"
    account_type = "credit_card"

    @classmethod
    def can_parse(cls, text: str) -> bool:
        return "ICICI" in text and "Amazon Pay" in text

    def parse(self, text: str) -> list[dict]:
        transactions = []
        lines = text.split('\n')
        date_pattern = re.compile(r'^(\d{2}/\d{2}/\d{4})\s+(\d+)\s+(.*)')
        in_spends = False

        for line in lines:
            line = line.strip()
            if "SPENDS OVERVIEW" in line:
                in_spends = True
                continue
            if not in_spends:
                continue
            if "EARNINGS" in line:
                break

            m = date_pattern.match(line)
            if m:
                date_str = m.group(1)
                detail_rest = m.group(3)
                cr_match = re.search(r'([\d,]+\.\d{2})\s*CR?$', detail_rest)
                dr_match = re.search(r'([\d,]+\.\d{2})\s*$', detail_rest)

                amount = None
                txn_type = "debit"
                desc = detail_rest

                if cr_match:
                    amount = float(cr_match.group(1).replace(",", ""))
                    txn_type = "credit"
                    desc = detail_rest[:cr_match.start()].strip()
                elif dr_match:
                    amount = float(dr_match.group(1).replace(",", ""))
                    desc = detail_rest[:dr_match.start()].strip()
                # Handle reward points between description and amount
                # Pattern: desc reward_pts amount
                alt_match = re.match(r'(.+?)\s+(\d+)\s+([\d,]+\.\d{2})\s*$', detail_rest)
                if alt_match and not cr_match and not dr_match:
                    desc = alt_match.group(1).strip()
                    amount = float(alt_match.group(3).replace(",", ""))

                if amount is None:
                    continue

                try:
                    dt = datetime.strptime(date_str, "%d/%m/%Y")
                except ValueError:
                    continue

                merchant_cat = None
                for keyword in ["E COMMERC", "GROCERY", "UTILITY", "RECHARGE", "APPAREL"]:
                    if keyword in desc.upper():
                        merchant_cat = keyword
                        break

                transactions.append({
                    "transaction_date": dt.strftime("%Y-%m-%d"),
                    "description": desc.strip().rstrip("IN").strip(),
                    "amount": amount,
                    "type": txn_type,
                    "merchant_category": merchant_cat,
                    "is_emi": False,
                })

        return transactions
