from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_

from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_session_context,
    get_required_user,
    SessionContext,
)
from app.services.demo_data import generate_demo_transactions

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=4, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


@router.post("/register")
async def register_user(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()
    res = await db.execute(select(User).where(User.email == email_clean))
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )

    pw_hash, salt = hash_password(req.password)
    user = User(
        email=email_clean,
        username=req.username.strip(),
        password_hash=pw_hash,
        salt=salt,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.email, user.username)
    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
        },
        "message": "Account registered successfully",
    }


@router.post("/login")
async def login_user(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()
    res = await db.execute(select(User).where(User.email == email_clean))
    user = res.scalar_one_or_none()
    if not user or not verify_password(req.password, user.salt, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id, user.email, user.username)
    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
        },
        "message": "Logged in successfully",
    }


@router.get("/me")
async def get_me(user: User = Depends(get_required_user)):
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "created_at": user.created_at.isoformat(),
    }


@router.post("/seed-demo")
async def seed_demo_data(
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db),
):
    # Clear existing demo transactions for this user or session
    conditions = [Transaction.source == "demo_seed"]
    if context.user_id:
        conditions.append(Transaction.user_id == context.user_id)
    elif context.session_id:
        conditions.append(Transaction.session_id == context.session_id)
    else:
        conditions.append(Transaction.user_id.is_(None))

    await db.execute(delete(Transaction).where(and_(*conditions)))

    demo_txns = generate_demo_transactions(
        user_id=context.user_id,
        session_id=context.session_id,
        is_transient=context.is_transient,
    )
    for txn in demo_txns:
        db.add(txn)

    await db.commit()
    return {
        "message": f"Successfully loaded {len(demo_txns)} demo transactions",
        "count": len(demo_txns),
    }


@router.post("/clear-demo")
async def clear_demo_data(
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Transaction.source == "demo_seed"]
    if context.user_id:
        conditions.append(Transaction.user_id == context.user_id)
    elif context.session_id:
        conditions.append(Transaction.session_id == context.session_id)

    res = await db.execute(delete(Transaction).where(and_(*conditions)))
    await db.commit()
    return {"message": "Demo data cleared successfully"}


@router.post("/transient/clear")
async def clear_transient_session(
    context: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_db),
):
    if not context.session_id and not context.is_transient:
        return {"message": "No active transient session to clear", "deleted": 0}

    conditions = [Transaction.is_transient == True]
    if context.session_id:
        conditions.append(Transaction.session_id == context.session_id)

    res = await db.execute(delete(Transaction).where(and_(*conditions)))
    await db.commit()
    return {
        "message": "Transient session data cleared permanently",
        "deleted": True,
    }
