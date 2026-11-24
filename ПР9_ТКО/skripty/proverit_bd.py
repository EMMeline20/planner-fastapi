"""Показать содержимое MongoDB: все записи или одну по pickup_id.

Запуск из корня проекта:
    .venv\\Scripts\\python.exe skripty\\proverit_bd.py
    .venv\\Scripts\\python.exe skripty\\proverit_bd.py P-XXXXXXXX
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from prilozhenie.db.podkluchenie import init_db  # noqa: E402
from prilozhenie.modeli.vyvoz import Pickup  # noqa: E402


async def main() -> None:
    await init_db()
    pickup_id = sys.argv[1] if len(sys.argv) > 1 else None

    if pickup_id:
        pickup = await Pickup.find_one(Pickup.pickup_id == pickup_id)
        if pickup is None:
            print(f"Запись {pickup_id} не найдена")
            return
        print(json.dumps(pickup.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return

    documents = await Pickup.find_all().sort(-Pickup.confirmed_at).to_list()
    print(f"Всего записей: {len(documents)}")
    for document in documents:
        print(json.dumps(document.model_dump(mode="json"), ensure_ascii=False, indent=2))
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())
