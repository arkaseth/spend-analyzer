import pytest
from app.parsers.sbi_cashback import SBICashbackParser
from app.parsers.icici_amazon import ICICIAmazonParser
from app.parsers.idfc_first import IDFCFIRSTParser
from app.parsers.indusind import IndusIndParser
from app.parsers.yes_bank import YesBankParser
from app.parsers.au_zenith import AUZenithParser


def test_sbi_cashback_parser():
    parser = SBICashbackParser()
    sample_text = """
    GSTIN of SBI Card
    Cashback Card Details
    TRANSACTIONS FOR ARKA SETH
    04 Jun 24 DMART SUPERMARKET 1,933.50 D
    05 Jun 24 SPOTIFY INDIA (Pay in EMIs) 119.00 D
    06 Jun 24 CASHBACK EARNED 50.00 C
    Important Messages
    """
    assert parser.can_parse(sample_text) is True
    txns = parser.parse(sample_text)
    assert len(txns) == 3

    # Check first txn
    assert txns[0]["transaction_date"] == "2024-06-04"
    assert "DMART SUPERMARKET" in txns[0]["description"]
    assert txns[0]["amount"] == 1933.50
    assert txns[0]["type"] == "debit"
    assert txns[0]["is_emi"] is False

    # Check EMI txn
    assert txns[1]["amount"] == 119.00
    assert txns[1]["is_emi"] is True

    # Check credit txn
    assert txns[2]["amount"] == 50.00
    assert txns[2]["type"] == "credit"


def test_icici_amazon_parser():
    parser = ICICIAmazonParser()
    sample_text = """
    ICICI Bank Amazon Pay Credit Card
    SPENDS OVERVIEW
    19/05/2024 101 AMAZON INDIA E COMMERC 2,499.00
    20/05/2024 102 SWIGGY RECHARGE 350.00
    21/05/2024 103 REFUND REVERSAL 500.00 CR
    EARNINGS
    """
    assert parser.can_parse(sample_text) is True
    txns = parser.parse(sample_text)
    assert len(txns) == 3

    assert txns[0]["transaction_date"] == "2024-05-19"
    assert txns[0]["amount"] == 2499.00
    assert txns[0]["type"] == "debit"
    assert txns[0]["merchant_category"] == "E COMMERC"

    assert txns[2]["amount"] == 500.00
    assert txns[2]["type"] == "credit"


def test_idfc_first_parser():
    parser = IDFCFIRSTParser()
    sample_text = """
    IDFC FIRST BANK
    STATEMENT OF ACCOUNT
    01-Apr-2024 01-Apr-2024 UPI/MOB/12345/SWIGGY/PAY 250.00 15,250.00
    02-Apr-2024 02-Apr-2024 BY TRANSFER SALARY CREDIT 50,000.00 65,250.00
    STATEMENT SUMMARY
    TOTAL DEBIT 250.00
    TOTAL CREDIT 50000.00
    REGISTERED OFFICE MUMBAI
    """
    assert parser.can_parse(sample_text) is True
    txns = parser.parse(sample_text)
    assert len(txns) == 2

    # Debit check
    assert txns[0]["transaction_date"] == "2024-04-01"
    assert txns[0]["amount"] == 250.00
    assert txns[0]["type"] == "debit"

    # Credit check
    assert txns[1]["transaction_date"] == "2024-04-02"
    assert txns[1]["amount"] == 50000.00
    assert txns[1]["type"] == "credit"


def test_indusind_parser():
    parser = IndusIndParser()
    sample_text = """
    Indusind Bank
    Account Statement
    01 May 2024 POS 1234 GROCERY STORE 75.00 25,007.50
    02 May 2024 BY TRANSFER INTEREST 120.00 25,127.50
    STATEMENT SUMMARY
    """
    assert parser.can_parse(sample_text) is True
    txns = parser.parse(sample_text)
    assert len(txns) == 2

    assert txns[0]["transaction_date"] == "2024-05-01"
    assert txns[0]["amount"] == 75.00
    assert txns[0]["type"] == "debit"

    assert txns[1]["amount"] == 120.00
    assert txns[1]["type"] == "credit"


def test_yes_bank_parser():
    parser = YesBankParser()
    sample_text = """
    YES BANK
    Credit Card Statement
    Statement Details
    15/05/2024 DMART CARMELARAM Groceries 1,500.00 Dr
    16/05/2024 PAYMENT RECEIVED 1,500.00 Cr
    End of the Statement
    """
    assert parser.can_parse(sample_text) is True
    txns = parser.parse(sample_text)
    assert len(txns) == 2

    assert txns[0]["transaction_date"] == "2024-05-15"
    assert txns[0]["amount"] == 1500.00
    assert txns[0]["type"] == "debit"
    assert txns[0]["merchant_category"] == "Groceries"

    assert txns[1]["type"] == "credit"


def test_au_zenith_parser():
    parser = AUZenithParser()
    sample_text = """
    AU SMALL FINANCE BANK
    Zenith+ Credit Card
    Transaction Summary
    09 / 01 / 2025 ZOMATO RESTAURANT 450.00Dr. Convert to EMI
    10 / 01 / 2025 CASHBACK ADJUSTMENT 50.00Cr.
    Reward Point Summary
    """
    assert parser.can_parse(sample_text) is True
    txns = parser.parse(sample_text)
    assert len(txns) == 2

    assert txns[0]["transaction_date"] == "2025-01-09"
    assert txns[0]["amount"] == 450.00
    assert txns[0]["type"] == "debit"
    assert txns[0]["is_emi"] is True

    assert txns[1]["type"] == "credit"
