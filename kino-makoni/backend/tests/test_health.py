from httpx import AsyncClient


async def test_health_ok(app_client: AsyncClient):
    resp = await app_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["db"] is True
    assert body["telegram"] is False  # streaming stub — hech qachon ulanmaydi
    assert body["catalog_synced_at"] is None  # sinxronizatsiya hali ishlamagan
