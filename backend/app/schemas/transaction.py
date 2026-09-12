from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

VALID_CLASSIFICATIONS = {"mandatory", "discretionary", "income", "uncategorized"}


class ManualTransactionCreate(BaseModel):
    transaction_date: date
    description: str = Field(..., min_length=1, max_length=1000)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    bank_name: str = Field(default="Manual", max_length=100)
    account_type: str = Field(default="manual", max_length=50)
    type: str = Field(default="debit", pattern=r"^(debit|credit)$")
    merchant_category: str | None = Field(default=None, max_length=200)
    is_emi: bool = False
    is_recurring: bool = False


class TransactionUpdate(BaseModel):
    category: str | None = Field(default=None, max_length=100)
    classification: str | None = Field(default=None, max_length=50)
    tags: str | None = Field(default=None, max_length=500)
    type: str | None = Field(default=None, pattern=r"^(debit|credit)?$")
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("classification")
    @classmethod
    def validate_classification(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_CLASSIFICATIONS:
            raise ValueError(f"classification must be one of {VALID_CLASSIFICATIONS}")
        return v


class TransactionCreate(BaseModel):
    bank_name: str
    account_type: str = "credit_card"
    source: str = "pdf_upload"
    transaction_date: date
    description: str
    amount: Decimal
    type: str = "debit"
    category: str = "Uncategorized"
    classification: str = "uncategorized"
    merchant_category: Optional[str] = None
    is_emi: bool = False
    is_recurring: bool = False
    tags: Optional[str] = None
    statement_file: Optional[str] = None


class TransactionResponse(TransactionCreate):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TransactionFilter(BaseModel):
    bank_name: Optional[str] = None
    category: Optional[str] = None
    classification: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    search: Optional[str] = None
    type: Optional[str] = None


class CategorySummary(BaseModel):
    category: str
    classification: str
    total: Decimal
    count: int
    percentage: float


class MonthlyTrend(BaseModel):
    month: str
    mandatory: Decimal
    discretionary: Decimal
    total: Decimal


class Insight(BaseModel):
    title: str
    description: str
    savings_potential: Optional[Decimal] = None
    category: Optional[str] = None


class AnalysisResponse(BaseModel):
    total_spend: Decimal
    mandatory_spend: Decimal
    discretionary_spend: Decimal
    mandatory_percentage: float
    discretionary_percentage: float
    monthly_trends: list[MonthlyTrend]
    category_breakdown: list[CategorySummary]
    insights: list[Insight]
