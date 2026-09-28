import uuid

from httpx import AsyncClient


async def test_device_auth_creates_user(app_client: AsyncClient):
    device_id = f"device-{uuid.uuid4().hex}"
    resp = await app_client.post(
        "/v1/auth/device",
        json={"device_id": device_id, "platform": "ios", "app_version": "1.0.0"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert isinstance(body["access_token"], str) and body["access_token"]
    assert body["user"]["id"] > 0
    assert body["user"]["created_at"].endswith("Z")


async def test_device_auth_same_device_returns_same_user(app_client: AsyncClient):
    device_id = f"device-{uuid.uuid4().hex}"
    first = await app_client.post("/v1/auth/device", json={"device_id": device_id})
    second = await app_client.post("/v1/auth/device", json={"device_id": device_id})
    assert first.json()["user"]["id"] == second.json()["user"]["id"]


async def test_protected_endpoint_without_token_is_401(app_client: AsyncClient):
    resp = await app_client.get("/v1/me")
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "unauthorized"


async def test_protected_endpoint_with_garbage_token_is_401(app_client: AsyncClient):
    resp = await app_client.get("/v1/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


async def test_me_with_valid_token(app_client: AsyncClient, auth_headers: dict[str, str]):
    resp = await app_client.get("/v1/me", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] > 0
    assert "created_at" in body
