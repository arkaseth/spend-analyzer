import uuid
import hashlib
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from app.models.transaction import Transaction
from app.classifier.rules import classify_transaction


def generate_demo_transactions(user_id: Optional[str] = None, session_id: Optional[str] = None, is_transient: bool = False) -> list[Transaction]:
    today = date.today()
    
    # 35 realistic transactions spanning past 3-4 months
    sample_records = [
        # Month 1 - Mandatory & Income
        (-90, "COMPANY PAYROLL SALARY CREDIT", 125000.00, "credit", "SBI Bank", "savings"),
        (-88, "HOUSE OWNER MONTHLY RENT", 28000.00, "debit", "SBI Bank", "savings"),
        (-86, "BESCOM ELECTRICITY BILL PAYMENT", 1950.00, "debit", "SBI Bank", "savings"),
        (-85, "JIO FIBER BROADBAND RECHARGE", 1178.00, "debit", "ICICI Amazon", "credit_card"),
        (-83, "DMART SUPERMARKET CARMELARAM", 3850.50, "debit", "ICICI Amazon", "credit_card"),
        (-82, "SHELL PETROL FUEL PUMP", 2200.00, "debit", "SBI Cashback", "credit_card"),
        (-80, "SWIGGY BANGALORE", 780.00, "debit", "SBI Cashback", "credit_card"),
        (-78, "STEAM PURCHASE COUNTER STRIKE 2", 1299.00, "debit", "ICICI Amazon", "credit_card"),
        (-76, "SPOTIFY SI MUMBAI", 119.00, "debit", "ICICI Amazon", "credit_card"),
        (-75, "PAYMENT RECEIVED CC PAYMENT", 15420.00, "credit", "SBI Cashback", "credit_card"),
        
        # Month 2
        (-60, "COMPANY PAYROLL SALARY CREDIT", 125000.00, "credit", "SBI Bank", "savings"),
        (-58, "HOUSE OWNER MONTHLY RENT", 28000.00, "debit", "SBI Bank", "savings"),
        (-56, "BIG BASKET GROCERY ORDER", 2450.00, "debit", "ICICI Amazon", "credit_card"),
        (-54, "STAR HEALTH INSURANCE PREMIUM", 8500.00, "debit", "SBI Bank", "savings"),
        (-52, "UBER TRIP BANGALORE", 450.00, "debit", "SBI Cashback", "credit_card"),
        (-50, "ZOMATO RESTAURANT DINING", 1450.00, "debit", "SBI Cashback", "credit_card"),
        (-48, "CORNER HOUSE ICE CREAM DESSERT", 420.00, "debit", "SBI Cashback", "credit_card"),
        (-46, "080 DOMESTIC AIRPORT LOUNGE", 2.00, "debit", "SBI Cashback", "credit_card"),
        (-45, "INDIGO FLIGHT TICKET BOOKING", 6850.00, "debit", "ICICI Amazon", "credit_card"),
        (-44, "AIRBNB VACATION STAY", 11500.00, "debit", "ICICI Amazon", "credit_card"),
        (-42, "NETFLIX SUBSCRIPTION", 649.00, "debit", "ICICI Amazon", "credit_card"),
        (-40, "CARD CASHBACK REWARD CREDIT", 1420.00, "credit", "SBI Cashback", "credit_card"),
        (-38, "DEBIT-TRANSFER TO SAVINGS", 20000.00, "debit", "SBI Bank", "savings"),
        
        # Month 3 - Recent
        (-30, "COMPANY PAYROLL SALARY CREDIT", 125000.00, "credit", "SBI Bank", "savings"),
        (-28, "HOUSE OWNER MONTHLY RENT", 28000.00, "debit", "SBI Bank", "savings"),
        (-25, "BESCOM ELECTRICITY BILLPAY", 1820.00, "debit", "SBI Bank", "savings"),
        (-24, "ZEPTO GROCERIES INSTANT", 650.00, "debit", "SBI Cashback", "credit_card"),
        (-22, "AYUSHMAN FUELS PETROL", 1800.00, "debit", "SBI Cashback", "credit_card"),
        (-20, "DISTRICT DINING CAFE", 980.00, "debit", "SBI Cashback", "credit_card"),
        (-18, "STEAMGAMES SUMMER SALE", 2499.00, "debit", "ICICI Amazon", "credit_card"),
        (-15, "YANDEX TAXI RIDE", 320.00, "debit", "SBI Cashback", "credit_card"),
        (-12, "APOLLO PHARMACY MEDICAL", 890.00, "debit", "ICICI Amazon", "credit_card"),
        (-10, "BOOKING.COM HOTEL GETAWAY", 5400.00, "debit", "ICICI Amazon", "credit_card"),
        (-7, "AMAZON ONLINE SHOPPING", 3250.00, "debit", "ICICI Amazon", "credit_card"),
        (-3, "MUTUAL FUND DIVIDEND EARNING", 1850.00, "credit", "SBI Bank", "savings"),
    ]

    transactions = []
    for days_ago, desc, amount, ttype, bank, acct in sample_records:
        txn_date = today + timedelta(days=days_ago)
        cat, cls = classify_transaction(desc)
        
        amt_dec = Decimal(str(amount))
        hash_input = f"{bank}|{txn_date.isoformat()}|{amount:.2f}|{desc.lower()}|{ttype}"
        txn_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        tx = Transaction(
            id=str(uuid.uuid4()),
            bank_name=bank,
            account_type=acct,
            source="demo_seed",
            transaction_date=txn_date,
            description=desc,
            amount=amt_dec,
            type=ttype,
            category=cat,
            classification=cls,
            merchant_category=None,
            is_emi=False,
            is_recurring=cat in ["Subscriptions", "Housing", "Utilities"],
            statement_file="demo_statement.pdf",
            txn_hash=txn_hash,
            user_id=user_id,
            is_transient=is_transient,
            session_id=session_id,
        )
        transactions.append(tx)

    return transactions
