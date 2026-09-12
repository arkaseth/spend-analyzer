import re
from datetime import datetime
from app.parsers.base import BaseParser
from app.parsers.registry import register


@register
class IndusIndParser(BaseParser):
    bank_name = "IndusInd"
    account_type = "savings"

    @classmethod
    def can_parse(cls, text: str) -> bool:
        return "Indusind Bank" in text and "Account Statement" in text

    def _is_amount(self, s: str) -> bool:
        s_clean = s.replace(",", "").strip()
        return bool(re.match(r'^\d+\.\d{2}$', s_clean))

    def _to_float(self, s: str) -> float:
        return float(s.replace(",", "").strip())

    def parse(self, text: str) -> list[dict]:
        transactions = []
        lines = text.split('\n')
        date_pattern = re.compile(
            r'^(\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\s+(.*)',
            re.IGNORECASE
        )
        merged = []
        current = None

        FOOTER_MARKERS = [
            "TRANSACTION HISTORY", "OPENING BALANCE", "CLOSING BALANCE",
            "TOTAL DEBIT", "TOTAL CREDIT", "STATEMENT SUMMARY", "PAGE "
        ]

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if any(m in line_str.upper() for m in FOOTER_MARKERS):
                if current:
                    merged.append(current)
                    current = None
                continue

            m = date_pattern.match(line_str)
            if m:
                if current:
                    merged.append(current)
                current = {"date": m.group(1), "detail": m.group(2)}
            else:
                if current:
                    current["detail"] += " " + line_str

        if current:
            merged.append(current)

        for entry in merged:
            detail = entry["detail"]
            tokens = detail.strip().split()
            if len(tokens) < 2:
                continue

            # Find all decimal amount tokens with their indices
            amt_indices = [i for i, t in enumerate(tokens) if self._is_amount(t)]
            if not amt_indices:
                continue

            # The last amount is the running balance
            bal_idx = amt_indices[-1]
            balance = self._to_float(tokens[bal_idx])

            # Amounts before balance are transaction amounts
            prior_amts = [i for i in amt_indices if i < bal_idx]
            if not prior_amts:
                continue

            amt = 0.0
            txn_type = "debit"
            first_amt_idx = prior_amts[0]

            if len(prior_amts) >= 2:
                # Both withdrawal and deposit present
                w_val = self._to_float(tokens[prior_amts[-2]])
                d_val = self._to_float(tokens[prior_amts[-1]])
                if w_val > 0:
                    amt = w_val
                    txn_type = "debit"
                else:
                    amt = d_val
                    txn_type = "credit"
            else:
                amt = self._to_float(tokens[first_amt_idx])
                desc_candidate = " ".join(tokens[:first_amt_idx]).upper()
                # Check credit indicators
                if "BY " in desc_candidate or "CREDIT" in desc_candidate or "REFUND" in desc_candidate or "INTEREST" in desc_candidate or "SALARY" in desc_candidate:
                    txn_type = "credit"
                else:
                    txn_type = "debit"

            if amt <= 0:
                continue

            description = " ".join(tokens[:first_amt_idx]).strip()

            try:
                dt = datetime.strptime(entry["date"], "%d %b %Y")
            except ValueError:
                continue

            transactions.append({
                "transaction_date": dt.strftime("%Y-%m-%d"),
                "description": description,
                "amount": amt,
                "type": txn_type,
                "merchant_category": None,
                "is_emi": False,
            })

        return transactions
