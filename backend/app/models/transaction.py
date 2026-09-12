import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import String, Boolean, Date, DateTime, Text
from sqlalchemy.types import DECIMAL as SqlDecimal
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bank_name: Mapped[str] = mapped_column(String(100), index=True)
    account_type: Mapped[str] = mapped_column(String(50))
    source: Mapped[str] = mapped_column(String(50))
    transaction_date: Mapped[date] = mapped_column(Date, index=True)
    description: Mapped[str] = mapped_column(Text)
    amount: Mapped[Decimal] = mapped_column(SqlDecimal(12, 2))
    type: Mapped[str] = mapped_column(String(10))
    category: Mapped[str] = mapped_column(String(100), default="Uncategorized")
    classification: Mapped[str] = mapped_column(String(50), default="uncategorized")
    merchant_category: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_emi: Mapped[bool] = mapped_column(Boolean, default=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    statement_file: Mapped[str | None] = mapped_column(String(500), nullable=True)
    txn_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    is_transient: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    session_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)

