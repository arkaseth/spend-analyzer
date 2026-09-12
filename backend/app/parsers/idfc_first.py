import re
from datetime import datetime
from app.parsers.base import BaseParser
from app.parsers.registry import register


@register
class IDFCFIRSTParser(BaseParser):
    bank_name = "IDFC FIRST"
    account_type = "savings"

    @classmethod
    def can_parse(cls, text: str) -> bool:
        return "IDFC FIRST" in text and "STATEMENT OF ACCOUNT" in text

    FOOTER_MARKERS = [
        "REGISTERED OFFICE", "ALWAYS YOU FIRST", "STATEMENT OF ACCOUNT",
        "STATEMENT SUMMARY", "TOTAL DEBIT", "TOTAL CREDIT", "OPENING BALANCE",
        "CLOSING BALANCE", "STATEMENT PERIOD", "CUSTOMER ID", "ACCOUNT NO",
        "BRANCH ADDRESS", "NOMINATION", "PAGE "
    ]

    def _find_last_amount(self, tokens: list[str]) -> tuple[float | None, int]:
        for i in range(len(tokens) - 1, -1, -1):
            t = tokens[i].replace(",", "").strip()
            # Handle possible trailing CR / DR
            t_clean = re.sub(r'(?i)(cr|dr)$', '', t)
            if re.match(r'^\d+\.\d{2}$', t_clean):
                return float(t_clean), i
        return None, -1

    def parse(self, text: str) -> list[dict]:
        transactions = []
        lines = text.split('\n')
        date_pattern = re.compile(
            r'^(\d{2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4})\s+'
            r'(\d{2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4})\s+(.*)',
            re.IGNORECASE
        )
        merged = []
        current = None

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Check for footer/header cutoff
            is_footer = any(marker in line_str.upper() for marker in self.FOOTER_MARKERS)
            if is_footer:
                if current:
                    merged.append(current)
                    current = None
                continue

            m = date_pattern.match(line_str)
            if m:
                if current:
                    merged.append(current)
                current = {
                    "date": m.group(1),
                    "value_date": m.group(2),
                    "detail": m.group(3),
                }
            else:
                if current:
                    current["detail"] += " " + line_str

        if current:
            merged.append(current)

        for entry in merged:
            detail = entry["detail"]
            # Cut off any footer string that might have gotten merged
            for marker in self.FOOTER_MARKERS:
                idx = detail.upper().find(marker)
                if idx != -1:
                    detail = detail[:idx]

            tokens = detail.strip().split()
            if len(tokens) < 2:
                continue

            balance, bal_idx = self._find_last_amount(tokens)
            if balance is None or bal_idx < 1:
                continue

            remaining = tokens[:bal_idx]
            amount, amt_idx = self._find_last_amount(remaining)
            if amount is None or amount <= 0:
                continue

            desc_tokens = remaining[:amt_idx]
            description = " ".join(desc_tokens).strip() if desc_tokens else " ".join(remaining)

            # Determine transaction type
            desc_upper = description.upper()
            detail_upper = detail.upper()
            is_credit = False
            if " CR" in detail_upper or "/CR/" in desc_upper or "TRANSFERFROM" in desc_upper or "INTEREST" in desc_upper or "REFUND" in desc_upper:
                is_credit = True
            elif "BY TRANSFER" in desc_upper or "CREDIT" in desc_upper or "SALARY" in desc_upper:
                is_credit = True

            txn_type = "credit" if is_credit else "debit"

            try:
                dt = datetime.strptime(entry["date"], "%d-%b-%Y")
            except ValueError:
                continue

            transactions.append({
                "transaction_date": dt.strftime("%Y-%m-%d"),
                "description": description,
                "amount": amount,
                "type": txn_type,
                "merchant_category": None,
                "is_emi": False,
            })

        return transactions
