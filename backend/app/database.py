from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


from sqlalchemy import text


async def init_db():
    async with engine.begin() as conn:
        from app.models.user import User
        from app.models.transaction import Transaction
        from app.models.category import CategoryRule
        await conn.run_sync(Base.metadata.create_all)

        def migrate_sqlite(connection):
            res = connection.execute(text("PRAGMA table_info(transactions)"))
            columns = [row[1] for row in res.fetchall()]
            if columns:
                if "txn_hash" not in columns:
                    connection.execute(text("ALTER TABLE transactions ADD COLUMN txn_hash VARCHAR(64)"))
                    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_transactions_txn_hash ON transactions (txn_hash)"))
                if "user_id" not in columns:
                    connection.execute(text("ALTER TABLE transactions ADD COLUMN user_id VARCHAR(36)"))
                    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_transactions_user_id ON transactions (user_id)"))
                if "is_transient" not in columns:
                    connection.execute(text("ALTER TABLE transactions ADD COLUMN is_transient BOOLEAN DEFAULT 0"))
                    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_transactions_is_transient ON transactions (is_transient)"))
                if "session_id" not in columns:
                    connection.execute(text("ALTER TABLE transactions ADD COLUMN session_id VARCHAR(64)"))
                    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_transactions_session_id ON transactions (session_id)"))

        await conn.run_sync(migrate_sqlite)

