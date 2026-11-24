"""Добавить одну демонстрационную запись, если коллекция пуста.

Запуск из корня проекта:
    .venv\\Scripts\\python.exe skripty\\zapolnit_bd.py
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from prilozhenie.db.podkluchenie import init_db  # noqa: E402
from prilozhenie.modeli.vyvoz import Pickup  # noqa: E402


async def main() -> None:
    await init_db()
    if await Pickup.count() > 0:
        print("В базе уже есть записи — ничего не добавляю.")
        return

    pickup = Pickup(
        pickup_id="P-DEMO0001",
        task_id="T-245",
        stop_seq=1,
        stops_total=10,
        container_id="c14",
        address="ул. Менделеева, 15",
        district="Ленинский",
        waste_type="ТКО",
        volume_m3=0.75,
        fill_before=82,
        fill_after=0,
        driver="Петров А.С.",
        vehicle="Мусоровоз №1",
        confirmed_at=datetime.now(timezone.utc),
        status="confirmed",
        idempotency_key="T-245:c14",
    )
    await pickup.insert()
    print("Добавлена демонстрационная запись P-DEMO0001")


if __name__ == "__main__":
    asyncio.run(main())
