"""Xato javob shakli — docs/API.md: {"error": {"code","message"}}."""

from httpx import AsyncClient


async def test_404_on_unknown_route_has_contract_shape(app_client: AsyncClient):
    resp = await app_client.get("/v1/does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert set(body.keys()) == {"error"}
    assert set(body["error"].keys()) == {"code", "message"}
    assert body["error"]["code"] == "not_found"


async def test_422_validation_error_shape(app_client: AsyncClient, auth_headers):
    # position_sec talab qilinadi — yubormasak 422
    resp = await app_client.put(
        "/v1/me/progress", json={"title_id": 1, "duration_sec": 10}, headers=auth_headers
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


async def test_streaming_router_error_renders_contract_shape(app_client: AsyncClient):
    # streaming moduli o'z HTTPException'ini {"code","message"} detail bilan ko'taradi —
    # bizning handler buni ham to'g'ri kontrakt shakliga o'tkazishi kerak.
    resp = await app_client.get("/v1/stream/not-a-real-token/video.mp4")
    assert resp.status_code == 403
    body = resp.json()
    assert set(body.keys()) == {"error"}
    assert body["error"]["code"] == "forbidden"
    assert "message" in body["error"]
