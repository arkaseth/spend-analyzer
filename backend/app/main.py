import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import upload, transactions, analysis, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


origins = os.environ.get("CORS_ORIGINS", "*")
allow_origins = [o.strip() for o in origins.split(",")] if origins != "*" else ["*"]

app = FastAPI(
    title="Spend Analyzer API",
    description="Parse bank/credit card statements, categorize transactions, and get spending insights.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(transactions.router)
app.include_router(analysis.router)


@app.get("/")
async def root():
    return {"message": "Spend Analyzer API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

