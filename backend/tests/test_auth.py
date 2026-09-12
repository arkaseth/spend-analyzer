import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db


@pytest.mark.asyncio
async def test_auth_registration_and_login():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        email = "testuser@example.com"
        password = "SecurePassword123"
        username = "Test User"

        # Register
        reg_resp = await ac.post("/auth/register", json={
            "email": email,
            "username": username,
            "password": password,
        })
        assert reg_resp.status_code in [200, 400]  # 400 if already exists from prior run

        # Login
        login_resp = await ac.post("/auth/login", json={
            "email": email,
            "password": password,
        })
        assert login_resp.status_code == 200
        data = login_resp.json()
        assert "token" in data
        assert data["user"]["email"] == email

        token = data["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Verify /auth/me
        me_resp = await ac.get("/auth/me", headers=headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == email


@pytest.mark.asyncio
async def test_demo_data_seeding_and_clearing():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        session_id = "test_transient_session_123"
        headers = {"X-Session-ID": session_id, "X-Transient-Mode": "true"}

        # Seed demo data for this transient session
        seed_resp = await ac.post("/auth/seed-demo", headers=headers)
        assert seed_resp.status_code == 200
        assert seed_resp.json()["count"] > 0

        # Verify transactions exist in overview for this session
        overview_resp = await ac.get("/analysis/overview", headers=headers)
        assert overview_resp.status_code == 200
        overview_data = overview_resp.json()
        assert overview_data["total_transactions"] > 0
        assert overview_data["total_spend"] > 0

        # Verify list transactions has items
        txns_resp = await ac.get("/transactions/", headers=headers)
        assert txns_resp.status_code == 200
        assert len(txns_resp.json()["transactions"]) > 0

        # Clear transient data
        clear_resp = await ac.post("/auth/transient/clear", headers=headers)
        assert clear_resp.status_code == 200
        assert clear_resp.json()["deleted"] is True

        # Verify transactions are now 0 for this session
        after_clear_resp = await ac.get("/transactions/", headers=headers)
        assert after_clear_resp.status_code == 200
        assert after_clear_resp.json()["total"] == 0
