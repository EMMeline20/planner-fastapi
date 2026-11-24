import pytest


def payload(**overrides):
    data = {
        "task_id": "T-245",
        "stop_seq": 1,
        "stops_total": 10,
        "container_id": "c14",
        "address": "ул. Менделеева, 15",
        "district": "Ленинский",
        "waste_type": "ТКО",
        "volume_m3": 0.75,
        "fill_before": 82,
        "fill_after": 0,
        "driver": "Петров А.С.",
        "vehicle": "Мусоровоз №1",
        "idempotency_key": "T-245:c14",
    }
    data.update(overrides)
    return data


async def test_create_and_get(client):
    response = await client.post("/api/pickups", json=payload())
    assert response.status_code == 201
    created = response.json()

    assert created["pickup_id"].startswith("P-")
    assert created["status"] == "confirmed"
    assert created["address"] == "ул. Менделеева, 15"
    assert created["fill_before"] == 82
    assert created["fill_after"] == 0
    assert created["idempotency_key"] == "T-245:c14"

    response = await client.get(f"/api/pickups/{created['pickup_id']}")
    assert response.status_code == 200
    assert response.json() == created


async def test_list_and_filter_by_task(client):
    await client.post("/api/pickups", json=payload())
    await client.post(
        "/api/pickups",
        json=payload(
            stop_seq=2,
            container_id="c11",
            address="ул. Аксакова, 7",
            idempotency_key="T-245:c11",
        ),
    )

    response = await client.get("/api/pickups")
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = await client.get("/api/pickups", params={"task_id": "T-245"})
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = await client.get("/api/pickups", params={"task_id": "T-999"})
    assert response.status_code == 200
    assert response.json() == []


async def test_idempotency_returns_existing_record(client):
    first = await client.post("/api/pickups", json=payload())
    second = await client.post("/api/pickups", json=payload())

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["pickup_id"] == second.json()["pickup_id"]

    response = await client.get("/api/pickups")
    assert len(response.json()) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("fill_before", 101),
        ("fill_before", -1),
        ("volume_m3", 0),
        ("stop_seq", 11),
        ("stops_total", 0),
    ],
)
async def test_validation_returns_422(client, field, value):
    response = await client.post("/api/pickups", json=payload(**{field: value}))
    assert response.status_code == 422


async def test_get_unknown_returns_404(client):
    response = await client.get("/api/pickups/P-UNKNOWN")
    assert response.status_code == 404
    assert response.json()["detail"] == "Акт вывоза не найден"


async def test_delete_then_get_404(client):
    created = (await client.post("/api/pickups", json=payload())).json()

    response = await client.delete(f"/api/pickups/{created['pickup_id']}")
    assert response.status_code == 200
    assert response.json()["pickup_id"] == created["pickup_id"]

    response = await client.get(f"/api/pickups/{created['pickup_id']}")
    assert response.status_code == 404

    response = await client.delete(f"/api/pickups/{created['pickup_id']}")
    assert response.status_code == 404


async def test_invalid_json_returns_422(client):
    """Негативный тест: тело не является JSON — ожидаем 422, а не падение сервера."""
    response = await client.post(
        "/api/pickups",
        content="{bad json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    detail = response.json()["detail"][0]
    assert detail["type"] == "json_invalid"
    assert "JSON" in detail["msg"]


async def test_missing_idempotency_key_returns_422(client):
    """Негативный тест: пропущено обязательное поле — 422 с указанием поля."""
    data = payload()
    data.pop("idempotency_key")
    response = await client.post("/api/pickups", json=data)
    assert response.status_code == 422
    assert any(item["loc"][-1] == "idempotency_key" for item in response.json()["detail"])
