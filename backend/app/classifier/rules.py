import re

CLASSIFICATION_RULES: dict[str, dict[str, list[str]]] = {
    "mandatory": {
        "Housing": ["RENT", "LEASE", "MAINTENANCE", "HDFC ERGO", "PROPERTY"],
        "Groceries": ["DMART", "GROCERY", "BIG BASKET", "MILANO", "SUPERMARKET", "FRESH", "INSTAMART", "ZEPTO", "BLINKIT", "GROFERS"],
        "Utilities": ["BBPS", "ELECTRICITY", "RECHARGE", "BROADBAND", "WATER", "GAS", "BILLPAY", "RELIANCE", "AIRTEL", "JIO", "BESCOM"],
        "Insurance": ["INSURANCE", "POLICY", "HDFC ERGO", "HDFCERGOGINS", "LIC", "HEALTH INSURANCE", "MAX LIFE", "STAR HEALTH"],
        "EMI/Loans": ["EMI", "FLEXIPAY", "ENCASH", "LOAN", "DEPOSITOR INV", "PZCRE", "BAJAJ FIN"],
        "Fuel": ["PETROL", "FUEL", "BP ", "AYUSHMAN FUELS", "INDIAN OIL", "SHELL", "HPCL", "IOCL"],
        "Medical": ["MEDICAL", "CLINIC", "MED WORLD", "DR SUHA", "PHARMACY", "APOLLO", "1MG", "NETMEDS", "HOSPITAL", "DIAGNOSTIC"],
        "Transport": ["METRO", "UBER", "OLA", "BUS", "TRAIN", "RAPIDO", "IRCTC", "FASTAG", "TOLL", "YANDEX", "FINNET", "ONAY", "TAXI", "CAB"],
        "Education": ["COACHING", "COURSE", "TRAINING", "RD COACHING", "UNIVERSITY", "SCHOOL", "UDEMY", "COURSERA"],
        "Investment": ["ZERODHA", "GROWW", "UPSTOX", "MUTUAL FUND", "NACH/EIH", "NACH/MAHINDRA", "NACH/TPOWER", "NACH/HINDUSTAN", "NACH/TATAMOTOR", "NACH/IHCL"],
        "Tax": ["ITDTAX", "INCOME TAX", "TIN-NSDL", "CHALLAN"],
    },
    "discretionary": {
        "Dining": ["ZOMATO", "SWIGGY", "RESTAURANT", "MILANO ICE CREAM", "CORNER HOUSE", "ICE CREA", "ICE CREAM", "DISTRICT DINING", "DINING", "DOMINOS", "PIZZA", "CAFE", "EAZYDINER", "HEDONNE", "MCDONALD", "KFC", "BURGER", "STARBUCKS", "CHAI"],
        "Gaming": ["STEAMGAMES", "STEAM PURCHASE", "STEAM", "PLAYSTATION", "XBOX", "NINTENDO", "EPIC GAMES", "RIOT GAMES"],
        "Lounge": ["DREAMFOLKS", "080 DOM", "080 LOUNGE", "ENCALM", "AIRPORT LOUNGE", "LOUNGE"],
        "Entertainment": ["SONYLIV", "NETFLIX", "HOTSTAR", "SPOTIFY", "PRIME VIDEO", "YOUTUBE", "OTT", "GOOGLE PLAY", "DISTRICT MOVIE", "BOOKMYSHOW", "PVR", "INOX", "CINEMA"],
        "Shopping": ["AMAZON", "MYNTRA", "URBANCLAP", "HEADPHONE", "FLIPKART", "SHOP", "E COMMERC", "AJIO", "TATA CLIQ", "NYKAA", "MEESHO"],
        "Travel": ["CLEARTRIP", "FLIGHT", "HOTEL", "MAKEMYTRIP", "AIR", "HOLIDAY", "TRAVEL", "GOIBIBO", "INDIGO", "AIR INDIA", "BUNGALOWS", "BUNGALOW", "BOOKING", "PELAGO", "GETYOURGUIDE", "AIRBNB", "AGODA"],
        "Fitness": ["MUSCLE NECTAR", "GYM", "FITNESS", "SUPPLEMENT", "CULT.FIT", "HEALTHKART"],
        "Personal Care": ["BEAUTY", "SALON", "OH WOW BEAUTY", "SPA", "GROOMING", "ENRICH"],
        "Subscriptions": ["SPOTIFY SI", "SONYLIV", "NETFLIX", "PRIME", "MEMBERSHIP"],
    },
}

TRANSFER_RULES: list[str] = [
    "PAYMENT RECEIVED", "CC PAYMENT", "CREDIT CARD PAYMENT",
    "BBPS PAYMENT", "AUTO DEBIT", "DEBIT-TRANSFER", "DEBIT TRANSFER",
    "TRANSFER-DEBIT", "TRANSFERTO", "TRANSFERFROM", "FUNDS TRANSFER",
    "FUND TRANSFER", "TELE TRANSFER", "NETBANKING TRANSFER",
    "BILLDESK", "SETTLEMENT",
]

INCOME_RULES: list[str] = [
    "CASHBACK", "CASH BACK", "REFUND", "REVERSAL", "WAIVER",
    "CREDITINTEREST", "INTEREST", "SALARY", "DIVIDEND",
]

FEE_RULES: list[str] = [
    "MEMBERSHIP FEE", "SURCHARGE", "GST", "IGST",
    "FOREIGN CURRENCY MARKUP", "LATE FEE",
    "FUEL SURCHARGE", "FUEL FEE",
    "CHARGE:AMB",
]


def normalize_description(desc: str) -> str:
    cleaned = desc
    # Strip UPI prefixes like UPI/MOB/123456789012/ or UPI/CR/123456789012/ or UPI- or UPI_
    cleaned = re.sub(r'(?i)\bUPI[/:_-]+(?:MOB|CR|DR)?[/:_-]*\d*[/:_-]*', ' ', cleaned)
    # Strip POS prefixes like POS-0123-
    cleaned = re.sub(r'(?i)\bPOS[/:_-]*\d*[/:_-]*', ' ', cleaned)
    # Strip IMPS/NEFT prefixes
    cleaned = re.sub(r'(?i)\b(?:IMPS|NEFT|RTGS)[/:_-]*[A-Z0-9]*[/:_-]*', ' ', cleaned)
    return " ".join(cleaned.split())


def classify_transaction(description: str, merchant_category: str | None = None, amount: float = 0) -> tuple[str, str]:
    desc_upper = description.upper()
    cleaned_upper = normalize_description(description).upper()
    combined_desc = f"{desc_upper} {cleaned_upper}"

    # 1. Check Transfers (e.g. Credit Card Payments, internal transfers)
    for keyword in TRANSFER_RULES:
        if keyword in desc_upper:
            return "Transfer", "transfer"

    # 2. Check true Income (salary, interest, cashback, refund)
    for keyword in INCOME_RULES:
        if keyword in desc_upper:
            return "Income", "income"

    # 3. Check explicit merchant category if provided by statement
    if merchant_category:
        for classification, categories in CLASSIFICATION_RULES.items():
            for category, keywords in categories.items():
                for keyword in keywords:
                    if keyword.upper() in merchant_category.upper():
                        return category, classification

    # 4. Check Fee rules (specific bank charges like MEMBERSHIP FEE, LATE FEE, etc.)
    for keyword in FEE_RULES:
        if keyword.upper() in desc_upper:
            return "Fees & Charges", "mandatory"

    # 5. Check classification rules against raw & normalized description
    for classification, categories in CLASSIFICATION_RULES.items():
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword.upper() in combined_desc:
                    return category, classification

    # 6. Fallback categorizations
    if "TRANSFERTO" in desc_upper or "IMPS/" in desc_upper or "IMPS-" in desc_upper or "NEFT/" in desc_upper:
        return "Transfer", "transfer"

    if "UPI/" in desc_upper or "UPI_" in desc_upper or "UPI-" in desc_upper:
        return "UPI", "uncategorized"

    if "POS-" in desc_upper or " POS " in desc_upper:
        return "POS", "uncategorized"

    if not description or not description.strip():
        return "Fees & Charges", "mandatory"

    return "Uncategorized", "uncategorized"


def get_all_categories() -> list[dict]:
    result = []
    for classification, categories in CLASSIFICATION_RULES.items():
        for category, keywords in categories.items():
            result.append({
                "category": category,
                "classification": classification,
                "keywords": keywords,
            })
    return result


def add_rule(keyword: str, category: str, classification: str):
    if classification not in CLASSIFICATION_RULES:
        CLASSIFICATION_RULES[classification] = {}
    if category not in CLASSIFICATION_RULES[classification]:
        CLASSIFICATION_RULES[classification][category] = []
    if keyword.upper() not in [k.upper() for k in CLASSIFICATION_RULES[classification][category]]:
        CLASSIFICATION_RULES[classification][category].append(keyword.upper())
