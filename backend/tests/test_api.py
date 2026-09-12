import pytest

try:
    from httpx import AsyncClient, ASGITransport
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

from app.main import app
from app.database import init_db

pytestmark = pytest.mark.skipif(not HAS_HTTPX, reason="httpx is not installed (run: pip install httpx)")


@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Spend Analyzer API" in data.get("message", "")


@pytest.mark.asyncio
async def test_list_supported_banks():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/upload/banks")
    assert response.status_code == 200
    data = response.json()
    assert "banks" in data
    assert len(data["banks"]) > 0


@pytest.mark.asyncio
async def test_categories_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/transactions/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert len(data["categories"]) > 0


@pytest.mark.asyncio
async def test_reset_and_manual_transaction_lifecycle():
    await init_db()
    headers = {"X-Session-ID": "test-session-api"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Reset all data
        reset_resp = await ac.post("/upload/reset", headers=headers)
        assert reset_resp.status_code == 200
        assert reset_resp.json().get("deleted") is True

        # 2. Add manual transaction
        manual_payload = {
            "bank_name": "Test Bank",
            "account_type": "savings",
            "transaction_date": "2026-05-01",
            "description": "DMART SUPERMARKET",
            "amount": 1250.50,
            "type": "debit",
        }
        create_resp = await ac.post("/upload/manual", json=manual_payload, headers=headers)
        assert create_resp.status_code == 200
        assert "id" in create_resp.json()

        # 3. Fetch transactions list
        list_resp = await ac.get("/transactions/", headers=headers)
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["total"] >= 1
        txns = list_data["transactions"]
        matching = [t for t in txns if t["description"] == "DMART SUPERMARKET"]
        assert len(matching) == 1
        assert matching[0]["category"] == "Groceries"
        assert matching[0]["classification"] == "mandatory"

        # 4. Fetch overview analysis
        analysis_resp = await ac.get("/analysis/overview", headers=headers)
        assert analysis_resp.status_code == 200
        analysis_data = analysis_resp.json()
        assert "total_spend" in analysis_data
        assert analysis_data["total_spend"] >= 1250.50

        # Clean up
        await ac.post("/upload/reset", headers=headers)


@pytest.mark.asyncio
async def test_batch_upload_validation():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test empty files list returns 400 or handled
        resp = await ac.post("/upload/batch", files=[])
        assert resp.status_code in [400, 422]

        # Test uploading non-pdf file in batch
        files = [
            ("files", ("test.txt", b"not a pdf content", "text/plain")),
        ]
        resp = await ac.post("/upload/batch", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_files"] == 1
        assert data["successful_files"] == 0
        assert data["results"][0]["status"] == "error"

