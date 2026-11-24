from datetime import datetime

from prilozhenie.modeli.vyvoz import Pickup


def payload():
    return {
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


async def test_document_matches_api(client):
    created = (await client.post("/api/pickups", json=payload())).json()
    document = await Pickup.find_one(Pickup.pickup_id == created["pickup_id"])

    assert document is not None
    for field in (
        "pickup_id",
        "task_id",
        "stop_seq",
        "stops_total",
        "container_id",
        "address",
        "district",
        "waste_type",
        "volume_m3",
        "fill_before",
        "fill_after",
        "driver",
        "vehicle",
        "status",
        "idempotency_key",
    ):
        assert getattr(document, field) == created[field], field

    assert isinstance(document.confirmed_at, datetime)
    assert document.confirmed_at.isoformat() == datetime.fromisoformat(
        created["confirmed_at"].replace("Z", "+00:00")
    ).isoformat()


async def test_delete_removes_document(client):
    created = (await client.post("/api/pickups", json=payload())).json()
    assert await Pickup.find_one(Pickup.pickup_id == created["pickup_id"]) is not None

    response = await client.delete(f"/api/pickups/{created['pickup_id']}")
    assert response.status_code == 200
    assert await Pickup.find_one(Pickup.pickup_id == created["pickup_id"]) is None
