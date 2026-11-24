from datetime import datetime, timezone
from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from prilozhenie.modeli.vyvoz import Pickup
from prilozhenie.skhemy.vyvoz import PickupCreate


def _utc_now_ms() -> datetime:
    """Время с точностью до миллисекунд — ровно так его хранит MongoDB."""
    now = datetime.now(timezone.utc)
    return now.replace(microsecond=(now.microsecond // 1000) * 1000)


async def create_pickup(data: PickupCreate) -> tuple[Pickup, bool]:
    """Создать акт вывоза. При повторе по idempotency_key вернуть старый.

    Возвращает пару (документ, создан_ли_новый).
    """

    existing = await Pickup.find_one(Pickup.idempotency_key == data.idempotency_key)
    if existing is not None:
        return existing, False

    confirmed_at = data.confirmed_at or _utc_now_ms()
    confirmed_at = confirmed_at.replace(
        microsecond=(confirmed_at.microsecond // 1000) * 1000
    )

    pickup = Pickup(
        pickup_id="P-" + uuid4().hex[:8].upper(),
        task_id=data.task_id,
        stop_seq=data.stop_seq,
        stops_total=data.stops_total,
        container_id=data.container_id,
        address=data.address,
        district=data.district,
        waste_type=data.waste_type,
        volume_m3=data.volume_m3,
        fill_before=data.fill_before,
        fill_after=data.fill_after,
        driver=data.driver,
        vehicle=data.vehicle,
        confirmed_at=confirmed_at,
        status="confirmed",
        idempotency_key=data.idempotency_key,
    )

    try:
        await pickup.insert()
    except DuplicateKeyError:
        existing = await Pickup.find_one(Pickup.idempotency_key == data.idempotency_key)
        if existing is not None:
            return existing, False
        raise

    return pickup, True


async def get_pickup(pickup_id: str) -> Pickup | None:
    return await Pickup.find_one(Pickup.pickup_id == pickup_id)


async def list_pickups(task_id: str | None = None) -> list[Pickup]:
    query = Pickup.find(Pickup.task_id == task_id) if task_id else Pickup.find()
    return await query.sort(-Pickup.confirmed_at).to_list()


async def delete_pickup(pickup_id: str) -> bool:
    pickup = await get_pickup(pickup_id)
    if pickup is None:
        return False
    await pickup.delete()
    return True
