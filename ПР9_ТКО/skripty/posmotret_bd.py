"""Показать коллекцию pickups: таблица и полный JSON последнего документа.

Это прямой запрос к MongoDB через Beanie — без Swagger и без интерфейса.
Запуск из корня проекта:
    .venv\\Scripts\\python.exe skripty\\posmotret_bd.py
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from prilozhenie.db.podkluchenie import init_db  # noqa: E402
from prilozhenie.modeli.vyvoz import Pickup  # noqa: E402
from prilozhenie.nastroiki import settings  # noqa: E402


def cut(value: object, width: int) -> str:
    text = str(value)
    return text if len(text) <= width else text[: width - 1] + "…"


async def main() -> None:
    await init_db()
    documents = await Pickup.find_all().sort(-Pickup.confirmed_at).to_list()

    print(f"База данных: {settings.mongodb_db}")
    print("Коллекция:  pickups")
    print(f"Документов: {len(documents)}")
    print()

    if not documents:
        print("Коллекция пуста. Нажмите «ВЫВЕЗЕНО» в интерфейсе.")
        return

    header = (
        f"{'№':>2} | {'pickup_id':<11} | {'task':<5} | {'точка':<7} | "
        f"{'адрес':<24} | {'заполн.':<9} | {'статус':<9} | время"
    )
    print(header)
    print("-" * len(header))

    for index, document in enumerate(documents, start=1):
        print(
            f"{index:>2} | {cut(document.pickup_id, 11):<11} | "
            f"{cut(document.task_id, 5):<5} | "
            f"{str(document.stop_seq) + '/' + str(document.stops_total):<7} | "
            f"{cut(document.address, 24):<24} | "
            f"{str(document.fill_before) + '→' + str(document.fill_after) + ' %':<9} | "
            f"{cut(document.status, 9):<9} | "
            f"{document.confirmed_at.isoformat()}"
        )

    latest = documents[0]
    print("\nПолный документ (JSON):")
    print(json.dumps(latest.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
