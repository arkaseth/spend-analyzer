# Spend Analyzer — Complete Design Document

## 1. Overview

A cross-platform personal finance intelligence system that parses bank and credit card PDF statements, categorizes transactions into **mandatory** vs **discretionary** spending, detects EMIs and recurring subscriptions, provides automated savings recommendations, and supports multi-user persistent accounts, ephemeral incognito sessions, and demo data exploration.

| Property | Value |
|---|---|
| **Backend** | Python 3.12 + FastAPI + SQLAlchemy 2.0 (Async) + SQLite / PostgreSQL |
| **Frontend** | Flutter 3.x (Web, Android, iOS, Desktop) + Material 3 + Provider state management |
| **OCR Engine** | Tesseract OCR 5.3.4 + pypdfium2 (high-res rendering + fallback binarization) |
| **Parsers** | 11 bank parsers (10 bank-specific + 1 generic heuristic fallback) |
| **Authentication** | PBKDF2-HMAC-SHA256 (100,000 rounds) password hashing + HMAC-SHA256 JWT Tokens |
| **Privacy Modes** | Strict multi-tenant isolation, Transient/Incognito session mode, Sample Demo mode |
| **Uploads** | Single and multi-file batch PDF uploads with per-file status reports |
| **Deployment** | Docker on Render (`https://spend-analyzer-ghj9.onrender.com`) + Netlify (`https://spend-analyzer.arkaseth.com`) |

---

## 2. Project Structure

```
spendAnalyzer/
├── DESIGN.md                       # System design, architecture & runbook
├── README.md                       # Project overview & quickstart
├── render.yaml                     # Render cloud deployment blueprint
├── netlify.toml                    # Netlify Flutter build & SPA redirect pipeline
├── .github/workflows/
│   └── ci_cd.yml                   # Automated Pytest suite + Flutter Web compilation
├── backend/
│   ├── Dockerfile                  # Production container with Tesseract OCR pre-installed
│   ├── requirements.txt            # Python dependencies (FastAPI, SQLAlchemy, pdfplumber, httpx)
│   ├── pytest.ini                  # Pytest async configuration
│   ├── tests/                      # Automated test suite (22 tests)
│   │   ├── test_api.py             # Endpoint lifecycle & batch upload tests
│   │   ├── test_auth.py            # User registration, login, demo seeding, transient cleanup
│   │   ├── test_classifier.py      # Classification engine & rule ordering tests
│   │   └── test_parsers.py         # Bank-specific parser regex & extraction tests
│   └── app/
│       ├── main.py                 # FastAPI application, CORS middleware, router aggregation
│       ├── database.py             # Async database connection & non-destructive SQLite PRAGMA migrations
│       ├── config.py               # Environment configuration
│       ├── models/                 # SQLAlchemy ORM models
│       │   ├── user.py             # User account model (PBKDF2 hash, salt, email index)
│       │   ├── transaction.py      # Transaction model (user_id, session_id, is_transient, txn_hash)
│       │   └── category.py         # CategoryRule model
│       ├── schemas/                # Pydantic schemas (requests, responses, filters)
│       │   └── transaction.py
│       ├── services/               # Core business services
│       │   ├── auth.py             # Password hashing, JWT token lifecycle, SessionContext dependency
│       │   └── demo_data.py        # 35-transaction realistic sample generator across 3 months
│       ├── parsers/                # Statement parsers
│       │   ├── base.py             # BaseParser interface
│       │   ├── registry.py         # Detection and parser registry
│       │   ├── generic.py          # Universal heuristic fallback
│       │   ├── sbi_bank.py         # SBI Savings parser
│       │   ├── sbi_cashback.py     # SBI Cashback CC parser
│       │   ├── icici_amazon.py     # ICICI Amazon Pay CC parser
│       │   ├── yes_bank.py         # YES BANK KLICK CC parser
│       │   ├── au_zenith.py        # AU Zenith+ CC parser
│       │   ├── amex.py             # AMEX Platinum Travel CC parser
│       │   ├── hdfc_swiggy.py      # HDFC Swiggy CC parser (OCR-based)
│       │   ├── hsbc.py             # HSBC TravelOne CC parser (OCR-based)
│       │   ├── idfc_first.py       # IDFC FIRST Savings parser (OCR-based)
│       │   └── indusind.py         # IndusInd Savings parser (OCR-based)
│       ├── ocr/
│       │   ├── __init__.py
│       │   └── engine.py           # OCR pipeline (Tesseract + pypdfium2)
│       ├── classifier/
│       │   ├── __init__.py
│       │   ├── rules.py            # Ordered keyword matching rules
│       │   └── engine.py           # ClassificationEngine wrapper
│       ├── analyzer/
│       │   ├── __init__.py
│       │   ├── trends.py           # Monthly trend computation
│       │   ├── categories.py       # Category breakdown + summary
│       │   └── insights.py         # Spending insights generation
│       └── routers/
│           ├── __init__.py
│           ├── auth.py             # User accounts & session endpoints
│           ├── upload.py           # Multi-file batch + single PDF upload
│           ├── transactions.py     # CRUD + filter + CSV/JSON export
│           └── analysis.py         # Analysis overview endpoint
└── frontend/
    ├── pubspec.yaml                # Flutter dependencies
    ├── web/
    │   ├── index.html              # Web entry page
    │   └── _redirects              # SPA routing & Netlify API proxy rules
    ├── lib/
    │   ├── main.dart               # MultiProvider setup
    │   ├── app.dart                # MaterialApp shell & SessionBanner
    │   ├── services/
    │   │   └── api_service.dart    # HTTP client with JWT & session headers
    │   ├── providers/
    │   │   ├── auth_provider.dart  # User auth, incognito & demo state
    │   │   ├── transaction_provider.dart
    │   │   └── analysis_provider.dart
    │   ├── screens/
    │   │   ├── dashboard_screen.dart
    │   │   ├── upload_screen.dart
    │   │   ├── transactions_screen.dart
    │   │   └── insights_screen.dart
    │   └── widgets/
    │       ├── auth/               # LoginDialog, SessionBanner, UserAccountButton
    │       └── common/             # EmptyState, TransactionTile, CategoryBadge
    └── test/                       # Flutter unit & widget tests
```

---

## 3. Backend Architecture

### 3.1 Configuration (`app/config.py`)

```python
DATABASE_URL      = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./spend_analyzer.db")
UPLOAD_DIR        = os.getenv("UPLOAD_DIR", "./uploads")
OCR_ENABLED       = os.getenv("OCR_ENABLED", "false").lower() == "true"
TESSERACT_CMD     = os.getenv("TESSERACT_CMD", "tesseract")
```

All settings are environment-variable overridable.

### 3.2 Database (`app/database.py`)

- **Engine:** SQLAlchemy async engine with `aiosqlite`.
- **Session:** `async_sessionmaker` factory yielding `AsyncSession`.
- **Init:** `init_db()` creates all tables on startup (lifespan event).
- **Tables:**
  - `transactions` — Core transaction records
  - `category_rules` — User-defined classification rules

### 3.3 Models

#### User (`app/models/user.py`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Unique user ID |
| `email` | String(255) | Unique index, user login email |
| `username` | String(100) | Display name |
| `password_hash` | String(255) | PBKDF2-HMAC-SHA256 hash |
| `salt` | String(64) | Cryptographic per-user random salt |
| `is_active` | Boolean | Account status |
| `created_at` | DateTime | Account creation timestamp |

#### Transaction (`app/models/transaction.py`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated transaction ID |
| `user_id` | UUID (FK) | ForeignKey to `users.id` (nullable for guest/transient sessions) |
| `is_transient` | Boolean | `True` for ephemeral/incognito session records (purged on exit) |
| `session_id` | String(100) | Ephemeral session token for incognito and demo data scoping |
| `txn_hash` | String(64) | SHA-256 hash `(bank|date|amt|desc|type)` for duplicate detection |
| `bank_name` | String(100) | e.g., "SBI", "ICICI Amazon Pay", "HDFC Swiggy" |
| `account_type` | String(50) | "savings", "credit_card" |
| `source` | String(50) | "pdf_upload", "manual", "demo" |
| `transaction_date` | Date | ISO transaction date |
| `description` | Text | Raw merchant/narration text |
| `amount` | Decimal(12,2) | Always positive |
| `type` | String(10) | "debit" or "credit" |
| `category` | String(100) | "Groceries", "Dining", "Travel", "Gaming", etc. |
| `classification` | String(50) | "mandatory", "discretionary", "income", "uncategorized" |
| `merchant_category` | String(200) | Statement-provided category |
| `is_emi` | Boolean | Part of an EMI repayment plan |
| `is_recurring` | Boolean | Recurring subscription or bill |
| `statement_file` | String(500) | Source PDF filename |
| `created_at` | DateTime | Auto-set on creation |

#### CategoryRule (`app/models/category.py`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `keyword` | String(200) | Keyword to match |
| `category` | String(100) | Target category |
| `classification` | String(50) | Target classification |
| `is_regex` | Boolean | Whether keyword is regex |
| `priority` | Integer | Match priority (higher = first) |
| `created_at` | Text | ISO timestamp |

### 3.4 Pydantic Schemas (`app/schemas/transaction.py`)

| Schema | Purpose |
|--------|---------|
| `ManualTransactionCreate` | Validates manual entry input (date, description, amount, type, etc.) |
| `TransactionUpdate` | Validates PATCH body (category, classification, tags, type, description) |
| `TransactionCreate` | Full transaction creation (used internally) |
| `TransactionResponse` | Full response with id + created_at |
| `TransactionFilter` | Query parameter filtering |
| `CategorySummary` | Category breakdown item |
| `MonthlyTrend` | Monthly aggregation item |
| `Insight` | Savings insight item |
| `AnalysisResponse` | Full analysis overview response |

Validation rules for `ManualTransactionCreate`:
- `description`: 1-1000 chars
- `amount`: > 0, max 2 decimal places
- `type`: regex `^(debit|credit)$`
- `classification` (in TransactionUpdate): must be one of `mandatory`, `discretionary`, `income`, `uncategorized`

### 3.5 Parser System

#### Architecture

The parser system uses a **registry pattern**:

1. `BaseParser` (ABC): defines `can_parse(text) -> bool` and `parse(text) -> list[dict]`
2. `registry.py`: maintains `_parsers` dict, provides `register()` decorator, `detect_parser()` function
3. Each bank parser is decorated with `@register` and automatically registered on import
4. `detect_parser()` iterates through all parsers in insertion order, returns first match
5. The generic parser is imported last (so it's checked last)

#### All 11 Parsers

| # | Parser | Bank | Account Type | Detection Key | Transaction Count |
|---|--------|------|-------------|---------------|-------------------|
| 1 | `sbi_bank.py` | SBI | savings | `"State Bank of India"` + `"Savings"` | 6 |
| 2 | `sbi_cashback.py` | SBI Cashback | credit_card | `"GSTIN of SBI Card"` + `"Cashback"` | 17 |
| 3 | `icici_amazon.py` | ICICI Amazon Pay | credit_card | `"ICICI"` + `"Amazon Pay"` | 9 |
| 4 | `yes_bank.py` | YES BANK | credit_card | `"YES BANK"` + `"Credit Card Statement"` | 17 |
| 5 | `au_zenith.py` | AU Zenith+ | credit_card | `"AU"` + `"Zenith+"` | 4 (more after fix) |
| 6 | `amex.py` | AMEX | credit_card | `"American Express"` + `"Statement of Account"` | 6 |
| 7 | `hdfc_swiggy.py` | HDFC Swiggy | credit_card | `"HDFC Bank"` + `"Swiggy"` + `"Credit Card"` | 58 |
| 8 | `hsbc.py` | HSBC | credit_card | `"HSBC"` + `"CREDIT CARD STATEMENT"` | 8 |
| 9 | `idfc_first.py` | IDFC FIRST | savings | `"IDFC FIRST"` + `"STATEMENT OF ACCOUNT"` | 112 |
| 10 | `indusind.py` | IndusInd | savings | `"Indusind Bank"` + `"Account Statement"` | 45 |
| 11 | `generic.py` | Unknown | unknown | Heuristic: ≥2 date matches + ≥2 amount matches | 29 (HDFC Savings) |

#### Parser Output Format

Every parser's `parse()` returns a list of dicts with these fields:

```python
{
    "transaction_date": "2024-04-03",   # ISO format
    "description": "DMART CARMELARAM",   # Cleaned description
    "amount": 1933.50,                   # Float
    "type": "debit",                     # "debit" | "credit"
    "merchant_category": None,           # Optional merchant category
    "is_emi": False,                     # EMI flag
}
```

#### How Parser Detection Works

1. Text is extracted from the PDF (either via pdfplumber or OCR)
2. `detect_parser(text)` iterates parsers in order
3. Each parser's `can_parse(text)` class method checks for unique identifying strings
4. The first parser that returns `True` is used
5. If no parser matches, HTTP 400 is returned

#### Adding a New Parser

1. Create `backend/app/parsers/your_bank.py`
2. Subclass `BaseParser`, set `bank_name` and `account_type`
3. Implement `can_parse(cls, text)` — return True if text matches your bank
4. Implement `parse(self, text)` — return list of transaction dicts
5. Add `@register` decorator
6. Import in `app/parsers/__init__.py`

#### Generic Fallback Parser (`generic.py`)

- Uses heuristic date/amount detection for any unknown bank format
- Fixes OCR number formatting (`34.929.86` → `34,929.86`)
- Always last in detection order
- Requires ≥2 date pattern matches AND ≥2 amount pattern matches to trigger

### 3.6 OCR Pipeline (`app/ocr/engine.py`)

```
PDF → pypdfium2 (render page at 3x scale) → PIL Image → tesserocr (PyTessBaseAPI) → text
```

- Uses `pypdfium2` for PDF-to-image rendering
- Uses `tesserocr` (direct C++ API binding, not subprocess) for OCR
- Auto-discovers `eng.traineddata`:
  1. `$TESSDATA_PREFIX` env var
  2. Bundled `backend/local_tesseract/tessdata/`
  3. System paths (`/usr/share/tesseract-ocr/5/tessdata`, etc.)
- Falls back silently if Tesseract is not available
- `is_scanned()` checks if first page has zero chars and >0 images

### 3.7 Classification Engine

#### Rules (`app/classifier/rules.py`)

Classification rules are organized as a two-level dict:

```python
CLASSIFICATION_RULES = {
    "mandatory": {
        "Housing": ["RENT", "LEASE", "MAINTENANCE", ...],
        "Groceries": ["DMART", "GROCERY", "BIG BASKET", ...],
        "Utilities": ["BBPS", "ELECTRICITY", "RECHARGE", ...],
        "Insurance": ["INSURANCE", "POLICY", "HDFC ERGO", ...],
        "EMI/Loans": ["EMI", "FLEXIPAY", "ENCASH", ...],
        "Fuel": ["PETROL", "FUEL", "BP", ...],
        "Medical": ["MEDICAL", "CLINIC", "PHARMACY", ...],
        "Transport": ["METRO", "UBER", "OLA", ...],
        "Education": ["COACHING", "COURSE", "TRAINING", ...],
        "Investment": ["ZERODHA", "NACH/EIH", ...],
        "Tax": ["ITDTAX", "INCOME TAX"],
    },
    "discretionary": {
        "Dining": ["ZOMATO", "SWIGGY", "RESTAURANT", ...],
        "Entertainment": ["SONYLIV", "NETFLIX", "SPOTIFY", ...],
        "Shopping": ["AMAZON", "MYNTRA", "FLIPKART", ...],
        "Travel": ["CLEARTRIP", "FLIGHT", "HOTEL", ...],
        "Fitness": ["MUSCLE NECTAR", "GYM", ...],
        "Personal Care": ["BEAUTY", "SALON", ...],
        "Subscriptions": ["SPOTIFY SI", "SONYLIV", ...],
    },
}
```

#### Classification Priority Order

1. **Fee detection** — Check FEE_RULES keywords (e.g., `ANNUAL MEMBERSHIP FEE`, `LATE FEE`, `SURCHARGE`) first → `("Fees & Charges", "mandatory")`. Ensures fee items aren't misattributed to subscriptions.
2. **Income detection** — If any INCOME_RULES keyword matches → `("Income", "income")`
3. **Merchant category match** — If `merchant_category` field exists, check it first
4. **Keyword match** — Check description against CLASSIFICATION_RULES keywords (Housing, Groceries, Utilities, Dining, Gaming, Lounge, Transport, Travel, etc.)
5. **UPI catch-all** — If `UPI/`, `UPI_`, or `UPI-` in description → `("UPI", "uncategorized")`
6. **POS catch-all** — If `POS-` or ` POS ` in description → `("POS", "uncategorized")`
7. **Transfer catch-all** — If `TRANSFERTO`, `DEBIT-TRANSFER`, `IMPS/`, `NEFT/` → `("Transfer", "uncategorized")`
8. **Empty description** — `("Fees & Charges", "mandatory")`
9. **Fallback** — `("Uncategorized", "uncategorized")`

#### Engine (`app/classifier/engine.py`)

```python
class ClassificationEngine:
    def classify(self, transaction: dict) -> dict    # Adds category + classification
    def classify_batch(self, transactions: list[dict]) -> list[dict]
    def recategorize(self, transaction: dict, category: str, classification: str) -> dict
```

### 3.8 Analysis Engine

#### Category Breakdown (`app/analyzer/categories.py`)

- Filters only debit transactions
- Groups by `category` field
- Computes total, count, percentage per category
- Returns sorted by total descending

#### Monthly Trends (`app/analyzer/trends.py`)

- Groups debit transactions by `YYYY-MM`
- Separates mandatory vs discretionary totals
- Returns sorted by month ascending

#### Insights (`app/analyzer/insights.py`)

Generates 4 insight types:

| Insight | Logic |
|---------|-------|
| Top Discretionary Spend | Finds highest discretionary category, suggests 30% saving |
| Cut Top 3 Categories by 50% | Suggests 50% reduction on top-3 discretionary |
| Recurring Subscriptions | Detects descriptions appearing ≥2 times, suggests 30% saving |
| Discretionary Ratio | Shows discretionary % of total spend, suggests 20% reduction |

### 3.9 API Endpoints

| Method | Path | Description | Headers / Auth | Request | Response |
|---|---|---|---|---|---|
| `GET` | `/` | Health check & API docs link | — | — | `{"message": "Spend Analyzer API", "docs": "/docs"}` |
| `POST` | `/auth/register` | Create user account | — | JSON `{email, username, password}` | `{"token", "user"}` |
| `POST` | `/auth/login` | Login user | — | JSON `{email, password}` | `{"token", "user"}` |
| `GET` | `/auth/me` | Current authenticated user | `Bearer <token>` | — | `{"id", "email", "username"}` |
| `POST` | `/auth/seed-demo` | Seed 35 realistic demo txns | `X-Session-ID` / `Bearer` | — | `{"message", "count": 35}` |
| `POST` | `/auth/clear-demo` | Clear sample demo data | `X-Session-ID` / `Bearer` | — | `{"message": "Demo data cleared"}` |
| `POST` | `/auth/transient/clear`| Purge incognito session data | `X-Session-ID` | — | `{"message", "deleted": true}` |
| `POST` | `/upload/pdf` | Upload single statement | `Bearer` / `Session` | `multipart/form-data` with `file` | `{"message", "count", "bank", "results"}` |
| `POST` | `/upload/batch` | Upload multiple statements | `Bearer` / `Session` | `multipart/form-data` with `files` | `{"total_files", "successful_files", "results": [...]}` |
| `POST` | `/upload/manual` | Add manual transaction | `Bearer` / `Session` | JSON `ManualTransactionCreate` | `{"message", "id"}` |
| `POST` | `/upload/reset` | Clear user/session data | `Bearer` / `Session` | — | `{"message", "deleted": true}` |
| `GET` | `/upload/banks` | List supported banks | — | — | `{"banks": [...]}` |
| `GET` | `/transactions/` | List/filter transactions | `Bearer` / `Session` | Query filters (search, category, etc.) | `{"total", "transactions": [...]}` |
| `PATCH` | `/transactions/{id}` | Update transaction | `Bearer` / `Session` | JSON `TransactionUpdate` | `{"message": "Transaction updated"}` |
| `DELETE`| `/transactions/{id}` | Delete transaction | `Bearer` / `Session` | — | `{"message": "Transaction deleted"}` |
| `POST` | `/transactions/reclassify` | Re-run classification rules | `Bearer` / `Session` | — | `{"message": "Reclassified N transactions"}` |
| `GET` | `/transactions/descriptions` | Autocomplete descriptions | `Bearer` / `Session` | Query: `q`, `limit` | `{"descriptions": [...]}` |
| `GET` | `/transactions/export/csv` | Download CSV export | `Bearer` / `Session` | — | CSV file stream |
| `GET` | `/transactions/export/json` | Download JSON export | `Bearer` / `Session` | — | JSON file stream |
| `GET` | `/transactions/categories` | List all known categories | — | — | `{"categories": [...]}` |
| `GET` | `/transactions/banks` | List banks in DB | — | — | `{"banks": [...]}` |
| `GET` | `/analysis/overview` | Overview analysis | `Bearer` / `Session` | — | `AnalysisResponse` JSON |

---

## 4. Frontend Architecture

### 4.1 State Management (Provider)

```
MultiProvider
├── AuthProvider           # User profile, JWT token, Incognito mode, Demo mode state
├── TransactionProvider    # Transaction list, pagination, search, category filter state
└── AnalysisProvider       # Spend overview, charts, batch upload progress state
```

### 4.2 Navigation

Bottom navigation bar with 4 tabs:
1. **Dashboard** — Summary cards, monthly trend bar chart, category pie chart, top 3 insights
2. **Upload** — PDF upload button + manual entry dialog + supported banks list
3. **Transactions** — Searchable, filterable transaction list with swipe-to-delete
4. **Insights** — Full insight cards + category breakdown with progress bars

### 4.3 API Service (`lib/services/api_service.dart`)

- Web-safe: uses `kIsWeb` to determine backend URL
  - **Web:** `http://192.168.119.164:8000` (WSL2 IP)
  - **Android emulator:** `http://10.0.2.2:8000`
  - **Native:** `http://localhost:8000`
- Supports `setBaseUrl()` for custom override
- `http.Client`-based for all requests
- Handles PDF upload via `MultipartRequest` with `fromBytes`

### 4.4 Data Flow

```
Upload PDF → AnalysisProvider.uploadPdf()
  → ApiService.uploadPdf() → POST /upload/pdf
  → Backend: detect_parser → parse → classify → save to DB
  → Response: {count, bank}
  → AnalysisProvider: reloadAnalysis()
  → TransactionProvider: reloadTransactions()

Manual Entry → _ManualEntryForm._submit()
  → ApiService.addManualTransaction() → POST /upload/manual
  → Same flow without parsing

View Dashboard → AnalysisProvider.loadAnalysis()
  → ApiService.getAnalysis() → GET /analysis/overview
  → Renders cards, charts, insights

View Transactions → TransactionProvider.loadTransactions()
  → ApiService.getTransactions() → GET /transactions/
  → Infinite scroll via loadMore
```

### 4.5 Screen Details

#### Dashboard Screen
- **Summary Row:** Total Spend (₹) + Mandatory %
- **Monthly Trends:** Stacked bar chart (green=mandatory, orange=discretionary) via `fl_chart`
- **Category Breakdown:** Donut pie chart with legend; categories <2% grouped as "Others"
- **Quick Insights:** Top 3 insight cards with savings icons

#### Upload Screen
- **PDF Upload:** `FilePicker` → bytes → `MultipartFile.fromBytes` → POST
- **Manual Entry Dialog:** Date picker → description with autocomplete → amount → type → classification → category → bank dropdowns
- **Supported Banks:** Static chip list

#### Transactions Screen
- **Search bar:** Real-time `ilike` search on description
- **Filter row:** Classification chips (All/Mandatory/Discretionary/Income) + Category dropdown + Date range button
- **List:** Paginated via `TransactionProvider` (50/page), infinite scroll, swipe-to-delete
- **Tap:** Opens recategorization dialog with choice chips
- **Export:** Download button (CSV/JSON) uses `url_launcher`

#### Insights Screen
- **Metric row:** Mandatory%, Discretionary%, Transaction count
- **Insight cards:** Full list with savings icons
- **Category breakdown:** Horizontal progress bars per category

### 4.6 Widgets

| Widget | Location | Purpose |
|--------|----------|---------|
| `EmptyState` | `widgets/common/empty_state.dart` | Centered icon + text + action button |
| `TransactionTile` | `widgets/common/transaction_tile.dart` | Card showing description, date, bank, amount, category badge |
| `CategoryBadge` | `widgets/common/category_badge.dart` | Color-coded chip (green=mandatory, orange=discretionary, blue=income, grey=other) |

---

## 5. Security

| Area | Implementation |
|------|---------------|
| **CORS** | Environment-aware via `CORS_ORIGINS` env var; defaults to `*` for local dev |
| **File size** | 50MB hard cap on PDF upload (HTTP 413 if exceeded) |
| **Input validation** | Pydantic schemas validate all inputs (length, type, regex, range) |
| **SQL injection** | SQLAlchemy ORM with parameterized queries throughout |
| **File handling** | Write to `tempfile.NamedTemporaryFile` → process → immediate `os.unlink` |
| **Dependencies** | All packages from official PyPI/pub.dev |
| **Local-first** | All data in local SQLite; no cloud dependency |
| **No secrets** | No API keys, no user authentication, no session management |

---

## 6. Dependencies

### Python (`requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥0.110.0 | REST API framework |
| `uvicorn` | ≥0.27.0 | ASGI server |
| `sqlalchemy` | ≥2.0.25 | ORM (async) |
| `aiosqlite` | ≥0.19.0 | Async SQLite driver |
| `python-multipart` | ≥0.0.6 | File upload parsing |
| `pdfplumber` | ≥0.10.0 | PDF text extraction |
| `pypdfium2` | ≥4.0.0 | PDF→image rendering for OCR |
| `pytesseract` | ≥0.3.10 | (Fallback — not directly imported; `tesserocr` used instead) |

System dependencies (bundled):
- `tesseract-ocr` 5.3.4
- `liblept5` 1.82.0
- `libtesseract5` 5.3.4

### Flutter (`pubspec.yaml`)

| Package | Version | Purpose |
|---------|---------|---------|
| `provider` | ^6.1.2 | State management |
| `http` | ^1.2.2 | HTTP client |
| `fl_chart` | ^0.69.2 | Bar and pie charts |
| `file_picker` | ^8.1.6 | PDF file selection |
| `intl` | ^0.19.0 | Date formatting |
| `url_launcher` | ^6.3.1 | Download URLs |

---

## 7. How to Run

### 7.1 Backend

```bash
# 1. Navigate to backend
cd backend

# 2. Activate virtual environment
source venv/bin/activate

# 3. Set TESSDATA_PREFIX for OCR
export TESSDATA_PREFIX=backend/local_tesseract/tessdata

# 4. Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API is available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

**Important:** For Flutter web, use the WSL2 IP (e.g., `192.168.119.164:8000`) instead of `localhost` because Windows `localhost` doesn't forward to WSL2. Find your WSL2 IP with:
```bash
ip addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'
```

### 7.2 Frontend (Flutter Web)

```bash
# 1. Navigate to frontend
cd frontend

# 2. Get dependencies
flutter pub get

# 3. Run in development
flutter run -d chrome

# 4. Or build for production
flutter build web
```

### 7.3 Without Flutter (Using Backend Only)

The backend can be tested directly via the API docs at `http://localhost:8000/docs` or with curl:

```bash
# Upload a PDF
curl -X POST -F "file=@StatementsForProject/SBICashbackStatements.pdf" http://localhost:8000/upload/pdf

# Add manual transaction
curl -X POST -H "Content-Type: application/json" \
  -d '{"transaction_date":"2025-01-15","description":"Test Purchase","amount":1500,"type":"debit"}' \
  http://localhost:8000/upload/manual

# Get analysis
curl http://localhost:8000/analysis/overview
```

### 7.4 Building APK (Android)

```bash
cd frontend

# Build APK
flutter build apk --release

# Build app bundle (Play Store)
flutter build appbundle --release

# For specific Android architecture
flutter build apk --release --target-platform android-arm64
```

The APK will be at `frontend/build/app/outputs/flutter-apk/app-release.apk`.

**Android Manifest Note:** Ensure `android/app/src/main/AndroidManifest.xml` has:
```xml
<uses-permission android:name="android.permission.INTERNET"/>
<application android:usesCleartextTraffic="true" ...>
```
(The `usesCleartextTraffic` is needed for `http://` connections to the backend.)

### 7.5 Building for Desktop

```bash
# Windows
flutter build windows

# Linux
flutter build linux

# macOS
flutter build macos
```

### 7.6 Building iOS

```bash
cd frontend
flutter build ios --release  # Requires Xcode on macOS
```

---

## 8. WSL2 + Flutter Web Setup

Since the backend runs in WSL2 and Flutter web runs in Windows:

1. Find WSL2 IP: `ip addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'`
2. The `ApiService` automatically uses `192.168.119.164:8000` for web
3. Windows Firewall might block connections — ensure WSL2 is allowed
4. Start backend with `--host 0.0.0.0` to bind to all interfaces

If the IP changes (WSL2 IP can change on reboot), update in `ApiService` or use `setBaseUrl()`.

---

## 9. Extending the App

### 9.1 Adding a New Bank Parser

1. Study the bank's PDF format
2. Create `backend/app/parsers/new_bank.py`
3. Implement `BaseParser` subclass with `@register` decorator
4. Add `from app.parsers import new_bank` to `app/parsers/__init__.py`
5. Update supported banks list in `upload_screen.dart` and `_ManualEntryForm`
6. Update `PLAN.md` and `DESIGN.md` documentation
7. Test with a sample PDF

**Parser patterns to follow:**
- `can_parse()`: Check for bank name + document type in text
- `parse()`: Split text by lines, use regex for date pattern, handle multi-row descriptions
- Return dicts matching the expected parser output format
- Use `re` module. The `_fix_ocr_amounts()` helper in `generic.py` can be reused.

### 9.2 Adding Classification Rules

Edit `app/classifier/rules.py`:

```python
# Add to existing classification
CLASSIFICATION_RULES["mandatory"]["NewCategory"] = ["KEYWORD1", "KEYWORD2"]

# Or add new keywords to existing category
CLASSIFICATION_RULES["mandatory"]["Groceries"].append("NEW_STORE")

# Or add new income/fee rule
INCOME_RULES.append("CASHBACK_BONUS")
```

### 9.3 Adding a New API Endpoint

1. Add the route to the appropriate router in `backend/app/routers/`
2. Create a Pydantic schema if needed in `backend/app/schemas/transaction.py`
3. Add frontend method in `lib/services/api_service.dart`
4. Add provider method in the relevant provider
5. Connect to UI

### 9.4 Adding a New Analysis Insight

Edit `backend/app/analyzer/insights.py`, add a new insight dict to the `insights` list:

```python
insights.append({
    "title": "Your Insight Title",
    "description": f"Detailed description with ₹{amount:,.0f}",
    "savings_potential": 1234.56,
    "category": "CategoryName",
})
```

---

## 10. Testing

### 10.1 Backend Tests

Test directory is at `backend/tests/` (currently has only `__init__.py`).

To run tests:
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### 10.2 Frontend Tests

```bash
cd frontend
flutter test
```

### 10.3 Manual Testing

1. Start backend with `--reload`
2. Use `http://localhost:8000/docs` (Swagger UI) to test endpoints
3. Upload each sample PDF and verify transaction count
4. Check classification accuracy
5. Run Flutter web and verify UI renders correctly

---

## 11. Known Limitations

| Limitation | Details |
|------------|---------|
| **No user authentication** | Single-user, no login/session management |
| **No cloud sync** | Data is local SQLite only; no backup to cloud |
| **ML classification** | Rule-based only; no ML model yet (planned for future) |
| **AU Zenith+ partial** | Previously only processed first page; fix applied for multi-page but need verification |
| **WSL2 IP volatility** | WSL2 IP changes on reboot; must update `ApiService.baseUrl` |
| **Flutter compile check** | Flutter SDK not available in dev environment; compile manually before deployment |
| **No pagination on analysis** | `/analysis/overview` loads ALL transactions into memory |
| **Basic error handling** | Some edge cases (e.g., malformed PDFs) may produce unhelpful errors |
| **No caching** | Every analysis request recomputes from scratch |

---

## 12. Classification Rules Reference

### Mandatory Categories

| Category | Keywords |
|----------|----------|
| **Housing** | RENT, LEASE, MAINTENANCE, HDFC ERGO, PROPERTY |
| **Groceries** | DMART, GROCERY, BIG BASKET, MILANO, SUPERMARKET, FRESH, INSTAMART, GROFERS, BLINKIT, ZEPTO |
| **Utilities** | BBPS, ELECTRICITY, RECHARGE, BROADBAND, WATER, GAS, BILLPAY, RELIANCE, AIRTEL, JIO |
| **Insurance** | INSURANCE, POLICY, HDFC ERGO, HDFCERGOGINS, LIC, HEALTH INSURANCE |
| **EMI/Loans** | EMI, FLEXIPAY, ENCASH, LOAN, DEPOSITOR INV, PZCRE, LOAN REPAYMENT |
| **Fuel** | PETROL, FUEL, BP, AYUSHMAN FUELS, INDIAN OIL, SHELL, HPCL |
| **Medical** | MEDICAL, CLINIC, MED WORLD, DR SUHA, PHARMACY, APOLLO |
| **Transport** | METRO, UBER, OLA, BUS, TRAIN, RAPIDO, YANDEX, FINNET, ONAY |
| **Education** | COACHING, COURSE, TRAINING, RD COACHING, UNIVERSITY, SCHOOL |
| **Investment** | ZERODHA, NACH/EIH, NACH/MAHINDRA, NACH/TPOWER, NACH/HINDUSTAN, NACH/TATAMOTOR, NACH/IHCL |
| **Tax** | ITDTAX, INCOME TAX |

### Discretionary Categories

| Category | Keywords |
|----------|----------|
| **Dining** | ZOMATO, SWIGGY, RESTAURANT, MILANO ICE CREAM, DOMINOS, PIZZA, CAFE, EAZYDINER, HEDONNE, DISTRICT DINING, CORNER HOUSE, CORNER HOUSE ICE CREA |
| **Entertainment** | SONYLIV, NETFLIX, HOTSTAR, SPOTIFY, PRIME VIDEO, YOUTUBE, OTT, GOOGLE PLAY, DISTRICT MOVIE |
| **Gaming** | STEAM, STEAMGAMES, STEAM PURCHASE, PLAYSTATION, XBOX, RIOT, EPIC GAMES |
| **Lounge** | DREAMFOLKS, 080 DOM, 080 INTL, ENCALM, AIRPORT LOUNGE |
| **Shopping** | AMAZON, MYNTRA, URBANCLAP, HEADPHONE, FLIPKART, SHOP, E COMMERC |
| **Travel** | CLEARTRIP, FLIGHT, HOTEL, MAKEMYTRIP, AIR, HOLIDAY, TRAVEL, BUNGALOWS, BOOKING, PELAGO, GETYOURGUIDE |
| **Fitness** | MUSCLE NECTAR, GYM, FITNESS, SUPPLEMENT |
| **Personal Care** | BEAUTY, SALON, OH WOW BEAUTY, SPA, GROOMING |
| **Subscriptions** | SPOTIFY SI, SONYLIV, NETFLIX, PRIME, MEMBERSHIP |

### Income Keywords

CASHBACK, CASH BACK, REFUND, REVERSAL, WAIVER, PAYMENT RECEIVED, CREDITINTEREST, INTEREST, BBPS PAYMENT, TELE TRANSFER, NETBANKING TRANSFER, CC PAYMENT, TRANSFERFROM, SALARY

### Fee Keywords (Evaluated Before General Rules)

ANNUAL MEMBERSHIP FEE, MEMBERSHIP FEE, SURCHARGE, GST, IGST, FOREIGN CURRENCY MARKUP, LATE FEE, FUEL SURCHARGE, FUEL FEE, CHARGE:AMB

### Catch-all Categories

| Pattern | Category | Classification |
|---------|----------|---------------|
| UPI/, UPI_, UPI- | UPI | uncategorized |
| POS-, POS | POS | uncategorized |
| TRANSFERTO, DEBIT-TRANSFER, IMPS/, IMPS-, NEFT/ | Transfer | uncategorized |
| Empty description | Fees & Charges | mandatory |
| No match | Uncategorized | uncategorized |

---

## 13. Bank Statement Format Reference

| Bank | Date Format | Amount Format | Section Markers | Special Features |
|---|---|---|---|---|
| SBI Savings | `DDMMMYYYY` | Debit/Credit columns | TRANSFERFROM, TRANSFERTO prefixes | Multi-row narration lines |
| SBI Cashback CC | `DD Mon YY` | `1,234.00 D` / `C` | "TRANSACTIONS FOR [name]" | EMI marker `(Pay in EMIs)` |
| ICICI Amazon Pay CC | `DD/MM/YYYY` | Amount or `Amount CR` | "SPENDS OVERVIEW" section | Merchant category keywords |
| YES BANK KLICK CC | `DD/MM/YYYY` | `Amount Dr` / `Cr` | "Statement Details" section | Merchant category column |
| AU Zenith+ CC | `DD / MM / YYYY` | `Amount Dr.` / `Cr.` | "Transaction Summary" section | Multi-row foreign currency |
| AMEX Platinum Travel | `Month DD` | Plain number | "domestic transactions" section | Statement period year resolution |
| HDFC Swiggy CC | `DD/MM/YYYY` | `Amount` / `Amount Cr` | "Domestic Transactions" section | OCR-required (scanned) |
| HSBC TravelOne CC | `DDMON` | `Amount` / `Amount CR` | "DATE TRANSACTION DETAILS" section | OCR-required (scanned) |
| IDFC FIRST Savings | `DD-Mon-YYYY` | Withdrawal/Deposit | "STATEMENT OF ACCOUNT" | OCR-required (scanned) |
| IndusInd Savings | `DD Mon YYYY` | 3-column table | "Transaction History" section | OCR-required (scanned) |

---

## 14. How to Launch (Local Development)

### 14.1 Backend (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Run Development Server
> [!IMPORTANT]
> When running inside **WSL2 on an NTFS mount (`/mnt/d/...`)**, avoid `uvicorn --reload` because the inotify filesystem watcher fails on DrvFs mounts. Always run directly via `python -m app.main`:
```bash
venv/bin/python -m app.main
```
The server binds to `0.0.0.0:8000`. Test it with:
```bash
curl http://127.0.0.1:8000/
# Swagger UI available at: http://127.0.0.1:8000/docs
```

### 14.2 Frontend (Flutter Web)

```bash
cd frontend
flutter pub get

# Launch on Chrome in debug mode
flutter run -d chrome

# Or launch pointing to a specific backend URL (e.g., cloud backend):
flutter run -d chrome --dart-define=BACKEND_URL=https://spend-analyzer-ghj9.onrender.com
```

---

## 15. Testing Guide

The test suite contains **22 automated tests** covering parsing, classification, authentication, and endpoint lifecycles.

### Run All Backend Tests
```bash
cd backend
venv/bin/pytest -v
```

### Test Suite Breakdown

1. **`tests/test_parsers.py`**:
   - Tests regex parsers for SBI, SBI Cashback, ICICI, YES Bank, AU Zenith, and AMEX statements.
2. **`tests/test_classifier.py`**:
   - Tests mandatory vs. discretionary spend categorization.
   - Tests fee prioritization (`ANNUAL MEMBERSHIP FEE` must map to `Fees & Charges`, not `Subscriptions`).
   - Tests newly added categories (Gaming, Lounge, Taxi, Groceries, Dining, Transfers).
3. **`tests/test_auth.py`**:
   - Tests user registration, password hashing verification, and JWT login token issuance.
   - Tests 35-transaction demo data generation and session isolation.
   - Tests transient / incognito session creation and full session cleanup.
4. **`tests/test_api.py`**:
   - Tests `/upload/pdf`, `/upload/batch`, `/upload/manual`, and database reset lifecycle.
   - Validates multi-file batch upload error handling and aggregate responses.

---

## 16. Cloud Deployment & Hosting Architecture

### Architecture Diagram
```
User Browser
    │
    ▼
Netlify Global CDN (https://spend-analyzer.arkaseth.com)
  [Flutter Web compiled bundle + netlify.toml / _redirects]
    │
    │  HTTPS REST API (JWT Bearer / X-Session-ID)
    ▼
Render Cloud Service (https://spend-analyzer-ghj9.onrender.com)
  [Docker Container: Debian + Python 3.12 + Tesseract 5.3.4 + FastAPI]
    │
    ▼
SQLite / Postgres Database (User Isolation & Deduplicated Hashes)
```

### 16.1 Backend on Render (Docker)
- **Repo**: Connected to GitHub `arkaseth/spend-analyzer`
- **Config**: Root directory `backend`, Dockerfile `backend/Dockerfile`
- **Tesseract OCR**: Pre-packaged in the Docker image via `apt-get install -y tesseract-ocr tesseract-ocr-eng`.
- **Live URL**: `https://spend-analyzer-ghj9.onrender.com`

### 16.2 Frontend on Netlify
- **Subdomain**: `spend-analyzer.arkaseth.com`
- **Build Pipeline**: Configured via `netlify.toml` to automatically download the Flutter SDK, run `flutter build web --release --dart-define=BACKEND_URL=https://spend-analyzer-ghj9.onrender.com`, and publish `frontend/build/web`.

---

## 17. Troubleshooting & FAQ

### Backend won't start: `[Errno 98] Address already in use`
- A previous process is still bound to port 8000:
  ```bash
  fuser -k 8000/tcp
  ```

### Windows Chrome resolves `localhost` to IPv6 `[::1]`
- If Chrome fails to connect to `localhost:8000`, use `http://127.0.0.1:8000`. The frontend `ApiService` already defaults to IPv4 `127.0.0.1` on web.

### Scanned PDFs requiring OCR
- If a scanned image PDF is uploaded on a machine without Tesseract, the API returns a clear 400 error explaining that OCR is required.
- Install Tesseract on Linux: `sudo apt-get install -y tesseract-ocr tesseract-ocr-eng`. In Docker, it is installed automatically.

### Signed out screen still shows data
- Signed-out mode enforces **Strict Guest Privacy**. If transactions were previously uploaded prior to enabling authentication, reset the database via the **Upload** tab while signed out to purge legacy unassigned records.
