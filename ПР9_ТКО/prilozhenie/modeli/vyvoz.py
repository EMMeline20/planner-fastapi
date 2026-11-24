from datetime import datetime

from beanie import Document
from pymongo import ASCENDING, IndexModel


class Pickup(Document):
    """Акт вывоза контейнера — один документ MongoDB."""

    pickup_id: str
    task_id: str
    stop_seq: int
    stops_total: int
    container_id: str
    address: str
    district: str
    waste_type: str
    volume_m3: float
    fill_before: int
    fill_after: int = 0
    driver: str
    vehicle: str
    confirmed_at: datetime
    status: str = "confirmed"
    idempotency_key: str

    class Settings:
        name = "pickups"
        indexes = [
            IndexModel(
                [("pickup_id", ASCENDING)],
                unique=True,
                name="uniq_pickup_id",
            ),
            IndexModel(
                [("idempotency_key", ASCENDING)],
                unique=True,
                name="uniq_idempotency_key",
            ),
        ]
