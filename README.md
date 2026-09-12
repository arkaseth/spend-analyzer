# Spend Analyzer 💸

A personal finance analytics and statement extraction system built with **FastAPI**, **Flutter**, **pdfplumber**, and **Tesseract OCR**. Spend Analyzer automatically parses credit card and bank account statements, categorizes expenses, separates mandatory vs. discretionary spending, flags EMIs and recurring subscriptions, and provides actionable savings recommendations.

---

## Features

- 📑 **Multi-Bank Statement Parsing**:
  - Auto-detection for 10+ Indian banks/cards: **HDFC Swiggy, ICICI Amazon Pay, HSBC, SBI, YES Bank, AU Zenith+, AMEX, IDFC FIRST, IndusInd**, and more.
  - Text-based and scanned OCR extraction (Tesseract fallback).
- 📂 **Multi-File Batch Upload**:
  - Select and process multiple statement PDFs concurrently in one operation with per-file status reports.
- 🏷️ **Smart Categorization & Classification**:
  - Over 20 expense categories (Housing, Groceries, Utilities, Dining, Gaming, Subscriptions, Lounge, Travel, etc.).
  - Automatic classification into **Mandatory (Needs)** vs. **Discretionary (Wants)**.
  - Interactive manual recategorization and database-wide rule reclassification.
- 🔒 **User Accounts & Strict Privacy**:
  - Persistent user accounts with PBKDF2-HMAC-SHA256 password hashing and JWT authentication.
  - **Incognito / Transient Mode**: Analyze statements on a temporary session that auto-purges all data on exit.
  - Strict guest privacy preventing unauthorized access to database records.
- ✨ **Demo Mode**:
  - Explore the application with 35 realistic sample transactions spanning 3 months without uploading personal statements.
- 📊 **Visual Analytics & Insights**:
  - Monthly trends bar charts, category breakdown pie charts, discretionary spend ratios, and automated savings suggestions.
- 💾 **Data Export**:
  - Filtered or full transaction exports in CSV and JSON formats.

---

## Tech Stack

| Component | Technologies |
|---|---|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy (Async), SQLite/PostgreSQL, pdfplumber, pytesseract |
| **Frontend** | Flutter Web 3.x, Provider, FL Chart, Google Fonts |
| **Containerization** | Docker, Docker Compose |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX |

---

## Project Structure

```
spendAnalyzer/
├── backend/
│   ├── app/
│   │   ├── classifier/      # Categorization engine & keyword rules
│   │   ├── models/          # SQLAlchemy models (User, Transaction)
│   │   ├── ocr/             # Tesseract OCR engine
│   │   ├── parsers/         # Bank statement format parsers
│   │   ├── routers/         # API routers (auth, upload, transactions, analysis)
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Auth, JWT, Demo data generator
│   │   ├── database.py      # Async database connection & migrations
│   │   └── main.py          # FastAPI application entry point
│   ├── tests/               # Pytest automated test suite
│   ├── Dockerfile           # Backend container with Tesseract OCR
│   └── requirements.txt
├── frontend/
│   ├── lib/
│   │   ├── models/          # Transaction & Analysis data models
│   │   ├── providers/       # AuthProvider, TransactionProvider, AnalysisProvider
│   │   ├── screens/         # Dashboard, Upload, Transactions, Insights
│   │   ├── services/        # ApiService (with JWT and session headers)
│   │   ├── widgets/         # Charts, LoginDialog, SessionBanner, Account Chip
│   │   └── main.dart
│   └── web/
│       └── _redirects       # SPA redirects for Netlify/Render
├── render.yaml              # Render deployment blueprint
├── DESIGN.md                # System design & architecture details
└── README.md
```

---

## Getting Started Locally

### 1. Prerequisites
- Python 3.11+
- Flutter 3.x
- (Optional) `tesseract-ocr` and `tesseract-ocr-eng` for scanned image PDFs:
  ```bash
  sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
  ```

### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run automated tests
pytest

# Start the development server
python -m app.main
```
The API documentation will be available at `http://127.0.0.1:8000/docs`.

### 3. Frontend Setup
```bash
cd frontend
flutter pub get
flutter run -d chrome
```

---

## Docker Deployment

Build and run the backend container locally:
```bash
cd backend
docker build -t spend-analyzer-backend .
docker run -p 8000:8000 spend-analyzer-backend
```

---

## Cloud Hosting

### Backend (Render / Railway / Fly.io)
The backend includes a Dockerfile with Tesseract OCR pre-installed:
1. Connect this GitHub repository to [Render](https://render.com).
2. Create a **Web Service** pointing to `backend/Dockerfile` or use `render.yaml`.
3. Set environment variable: `PORT=8000`.

### Frontend (Netlify / Vercel / Cloudflare Pages)
1. Build the production web bundle:
   ```bash
   cd frontend
   flutter build web --release
   ```
2. Deploy the `frontend/build/web` directory.
3. Configure the backend API URL using the built-in **"Change URL"** settings button in the app or via the `_redirects` proxy.

---

## License
MIT
