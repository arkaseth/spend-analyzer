from app.classifier.rules import classify_transaction, add_rule


class ClassificationEngine:
    def classify(self, transaction: dict) -> dict:
        txn = dict(transaction)
        category, classification = classify_transaction(
            txn.get("description", ""),
            txn.get("merchant_category"),
            txn.get("amount", 0),
        )
        txn["category"] = category
        txn["classification"] = classification
        return txn

    def classify_batch(self, transactions: list[dict]) -> list[dict]:
        return [self.classify(t) for t in transactions]

    def recategorize(self, transaction: dict, category: str, classification: str) -> dict:
        txn = dict(transaction)
        txn["category"] = category
        txn["classification"] = classification
        return txn
