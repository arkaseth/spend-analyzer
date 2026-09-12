import re
from datetime import datetime
from app.parsers.base import BaseParser
from app.parsers.registry import register


DATE_PATTERNS = [
    (re.compile(r'^(\d{2}/\d{2}/\d{4})'), "%d/%m/%Y"),
    (re.compile(r'^(\d{2}/\d{2}/\d{2})\s'), "%d/%m/%y"),
    (re.compile(r'^(\d{2}-\d{2}-\d{4})'), "%d-%m-%Y"),
    (re.compile(r'^(\d{2}[A-Z]{3}\d{4})'), "%d%b%Y"),
    (re.compile(r'^(\d{4}-\d{2}-\d{2})'), "%Y-%m-%d"),
]

DOT_COMMA_RE = re.compile(r'(\d)\.(\d{3})\.(\d{2})\b')
AMOUNT_RE = re.compile(r'[\d,]+\.\d{2}')
DATE_INLINE_RE = re.compile(r'\d{2}/\d{2}/\d{2,4}')


def _fix_ocr_amounts(text: str) -> str:
    return DOT_COMMA_RE.sub(r'\1,\2.\3', text)


@register
class GenericParser(BaseParser):
    bank_name = "Unknown"
    account_type = "unknown"

    @classmethod
    def can_parse(cls, text: str) -> bool:
        lines = text.split('\n')
        date_hits = 0
        amount_hits = 0
        for line in lines:
            if any(p[0].match(line.strip()) for p in DATE_PATTERNS):
                date_hits += 1
                if AMOUNT_RE.search(line):
                    amount_hits += 1
        return date_hits >= 2 and amount_hits >= 2

    def parse(self, text: str) -> list[dict]:
        transactions = []
        text = _fix_ocr_amounts(text)
        lines = text.split('\n')
        merged = []
        current = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            date_found = False
            for pattern, fmt in DATE_PATTERNS:
                m = pattern.match(line)
                if m:
                    if current:
                        merged.append(current)
                    current = {"date": m.group(1), "fmt": fmt, "detail": line[m.end():].strip()}
                    date_found = True
                    break
            if not date_found and current:
                current["detail"] += " " + line

        if current:
            merged.append(current)

        for entry in merged:
            detail = entry["detail"]

            amounts = AMOUNT_RE.findall(detail)
            if len(amounts) < 1:
                continue

            if len(amounts) >= 2:
                txn_amount_str = amounts[-2].replace(",", "")
                # balance_str = amounts[-1].replace(",", "")
            else:
                txn_amount_str = amounts[-1].replace(",", "")

            txn_amount = float(txn_amount_str)
            if txn_amount <= 0 or txn_amount > 1_000_000_000:
                continue

            txn_type = "debit"
            stripped = detail.strip()
            if stripped.startswith("-"):
                txn_type = "credit"

            desc = detail
            for a in amounts:
                desc = desc.replace(a, "", 1)
            desc = re.sub(r'[|]\s*', ' ', desc)
            desc = DATE_INLINE_RE.sub('', desc)
            desc = re.sub(r'\s+', ' ', desc).strip()
            desc = desc.strip('|').strip()

            try:
                dt = datetime.strptime(entry["date"], entry["fmt"])
            except ValueError:
                continue

            transactions.append({
                "transaction_date": dt.strftime("%Y-%m-%d"),
                "description": desc if desc else f"Transaction {entry['date']}",
                "amount": txn_amount,
                "type": txn_type,
                "merchant_category": None,
            })

        return transactions
