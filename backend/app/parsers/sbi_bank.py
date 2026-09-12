import re
from datetime import datetime
from app.parsers.base import BaseParser
from app.parsers.registry import register


@register
class SBIBankParser(BaseParser):
    bank_name = "SBI"
    account_type = "savings"

    @classmethod
    def can_parse(cls, text: str) -> bool:
        return "State Bank of India" in text and "Savings" in text

    def parse(self, text: str) -> list[dict]:
        transactions = []
        lines = text.split('\n')
        date_pattern = re.compile(r'^(\d{2}[A-Z]{3}\d{4})\s+(.*)')
        merged = []
        current = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            m = date_pattern.match(line)
            if m:
                if current:
                    merged.append(current)
                current = {"date": m.group(1), "detail": m.group(2)}
            else:
                if current:
                    current["detail"] += " " + line
        if current:
            merged.append(current)

        for entry in merged:
            detail = entry["detail"]

            transferto_match = re.match(
                r'(TRANSFERTO\S+)\s+([\d,]+\.\d{2})\s*-\s*([\d,]+\.\d{2})\b',
                detail
            )
            if transferto_match:
                desc = transferto_match.group(1).rstrip("-")
                amount = float(transferto_match.group(2).replace(",", ""))
                try:
                    dt = datetime.strptime(entry["date"], "%d%b%Y")
                except ValueError:
                    continue
                transactions.append({
                    "transaction_date": dt.strftime("%Y-%m-%d"),
                    "description": desc,
                    "amount": amount,
                    "type": "debit",
                    "merchant_category": None,
                })
                continue

            transferfrom_match = re.match(
                r'(TRANSFERFROM\S+)\s*-\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\b',
                detail
            )
            if transferfrom_match:
                desc = transferfrom_match.group(1).rstrip("-")
                amount = float(transferfrom_match.group(2).replace(",", ""))
                try:
                    dt = datetime.strptime(entry["date"], "%d%b%Y")
                except ValueError:
                    continue
                transactions.append({
                    "transaction_date": dt.strftime("%Y-%m-%d"),
                    "description": desc,
                    "amount": amount,
                    "type": "credit",
                    "merchant_category": None,
                })
                continue

            tokens = detail.split()
            desc_tokens = []
            debit_val = None
            credit_val = None
            i = 0
            while i < len(tokens):
                t = tokens[i]
                if t == "-" and i + 1 < len(tokens):
                    if self._is_amount(tokens[i + 1]):
                        credit_val = float(tokens[i + 1].replace(",", ""))
                        balance = float(tokens[i + 2].replace(",", "")) if i + 2 < len(tokens) and self._is_amount(tokens[i + 2]) else None
                        i += 3 if balance else 2
                    break
                elif t == "-" and i > 0 and self._is_amount(tokens[i - 1]):
                    debit_val = float(tokens[i - 1].replace(",", ""))
                    del desc_tokens[-1]
                    balance = float(tokens[i + 1].replace(",", "")) if i + 1 < len(tokens) and self._is_amount(tokens[i + 1]) else None
                    i += 2
                    break
                else:
                    desc_tokens.append(t)
                    i += 1

            if debit_val is None and credit_val is None:
                desc = " ".join(desc_tokens)
                for idx in range(len(tokens) - 1, 1, -1):
                    if self._is_amount(tokens[idx]) and self._is_amount(tokens[idx - 1]):
                        d_or_c = float(tokens[idx - 1].replace(",", ""))
                        balance = float(tokens[idx].replace(",", ""))
                        desc_tokens = tokens[:idx - 1]
                        if self._is_amount(tokens[idx - 2]) or tokens[idx - 2] == "-":
                            credit_val = d_or_c
                            if tokens[idx - 2] == "-":
                                desc_tokens = tokens[:idx - 2]
                        else:
                            debit_val = d_or_c
                            desc_tokens = tokens[:idx - 1]
                        break

            if debit_val is None and credit_val is None:
                continue

            txn_type = "credit" if credit_val else "debit"
            amount = credit_val if credit_val else debit_val
            try:
                dt = datetime.strptime(entry["date"], "%d%b%Y")
            except ValueError:
                continue

            transactions.append({
                "transaction_date": dt.strftime("%Y-%m-%d"),
                "description": " ".join(desc_tokens).strip(),
                "amount": float(amount) if amount else 0.0,
                "type": txn_type,
                "merchant_category": None,
            })
        return transactions

    @staticmethod
    def _is_amount(s: str) -> bool:
        try:
            float(s.replace(",", ""))
            return True
        except ValueError:
            return False
