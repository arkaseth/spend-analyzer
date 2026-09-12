import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./spend_analyzer.db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
OCR_ENABLED = os.getenv("OCR_ENABLED", "false").lower() == "true"
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
