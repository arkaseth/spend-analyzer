import pytest
from app.classifier.rules import (
    normalize_description,
    classify_transaction,
    get_all_categories,
    add_rule,
    CLASSIFICATION_RULES,
)


def test_normalize_description_strips_upi_prefixes():
    raw = "UPI/MOB/123456789012/SWIGGY/PAYMENT"
    normalized = normalize_description(raw)
    assert "SWIGGY" in normalized
    assert "UPI" not in normalized


def test_normalize_description_strips_pos_and_imps():
    pos_desc = "POS-98765-RETAIL STORE"
    assert "RETAIL STORE" in normalize_description(pos_desc)

    imps_desc = "IMPS/9876543210/TRANSFER"
    assert "TRANSFER" in normalize_description(imps_desc)


def test_classify_transfer_rules():
    transfers = [
        "PAYMENT RECEIVED - THANK YOU",
        "AUTO DEBIT CC PAYMENT",
        "BBPS PAYMENT FOR CREDIT CARD",
        "NETBANKING TRANSFER TO LOAN",
        "SETTLEMENT OF ACCOUNT",
    ]
    for desc in transfers:
        cat, cls = classify_transaction(desc)
        assert cls == "transfer", f"Failed for {desc}: got {cls}"
        assert cat == "Transfer"


def test_classify_income_rules():
    incomes = [
        "CARD CASHBACK CREDIT",
        "MERCHANT REFUND FOR ORDER",
        "CREDITINTEREST CAPITALIZED",
        "MONTHLY SALARY CREDIT",
    ]
    for desc in incomes:
        cat, cls = classify_transaction(desc)
        assert cls == "income", f"Failed for {desc}: got {cls}"
        assert cat == "Income"


def test_classify_normalized_upi_vendor_rules():
    # UPI Swiggy -> Dining (discretionary)
    cat, cls = classify_transaction("UPI/MOB/999888777/SWIGGY BANGALORE")
    assert cat == "Dining"
    assert cls == "discretionary"

    # UPI Dr Suha Clinic -> Medical (mandatory)
    cat, cls = classify_transaction("UPI/DR SUHA CLINIC/BANGALORE")
    assert cat == "Medical"
    assert cls == "mandatory"

    # DMART -> Groceries (mandatory)
    cat, cls = classify_transaction("DMART CARMELARAM")
    assert cat == "Groceries"
    assert cls == "mandatory"

    # Fuel petrol pump -> Fuel (mandatory)
    cat, cls = classify_transaction("AYUSHMAN FUELS PETROL")
    assert cat == "Fuel"
    assert cls == "mandatory"


def test_classify_fees_and_charges():
    cat, cls = classify_transaction("FUEL SURCHARGE WAIVER ADJUSTMENT LATE FEE")
    # LATE FEE is in fee rules
    cat_fee, cls_fee = classify_transaction("ANNUAL MEMBERSHIP FEE")
    assert cat_fee == "Fees & Charges"
    assert cls_fee == "mandatory"


def test_classify_uncategorized_fallbacks():
    # Unknown UPI vendor
    cat, cls = classify_transaction("UPI/UNKNOWN_PERSON/987654321")
    assert cat == "UPI"
    assert cls == "uncategorized"

    # Complete unknown
    cat, cls = classify_transaction("XYZ RANDOM NARATION 12345")
    assert cat == "Uncategorized"
    assert cls == "uncategorized"


def test_add_rule_dynamically():
    add_rule("TESTNEWVENDOR", "Shopping", "discretionary")
    cat, cls = classify_transaction("PAYMENT AT TESTNEWVENDOR ONLINE")
    assert cat == "Shopping"
    assert cls == "discretionary"


def test_user_requested_rules():
    # Dining
    cat, cls = classify_transaction("district dining")
    assert cat == "Dining" and cls == "discretionary"

    cat, cls = classify_transaction("corner house ICE CREA")
    assert cat == "Dining" and cls == "discretionary"

    # Gaming
    cat, cls = classify_transaction("Steamgames")
    assert cat == "Gaming" and cls == "discretionary"

    cat, cls = classify_transaction("steam purchase")
    assert cat == "Gaming" and cls == "discretionary"

    # Debit-Transfer
    cat, cls = classify_transaction("Debit-Transfer")
    assert cat == "Transfer" and cls == "transfer"

    # Lounge
    for desc in ["Dreamfolks", "080 Dom", "Encalm"]:
        cat, cls = classify_transaction(desc)
        assert cat == "Lounge" and cls == "discretionary"

    # Taxi / Transport
    for desc in ["Yandex", "finnet", "onay"]:
        cat, cls = classify_transaction(desc)
        assert cat == "Transport" and cls == "mandatory"

    # Travel
    for desc in ["bungalows", "booking", "pelago", "getyourguide"]:
        cat, cls = classify_transaction(desc)
        assert cat == "Travel" and cls == "discretionary"

    # Groceries
    cat, cls = classify_transaction("grofers")
    assert cat == "Groceries" and cls == "mandatory"

