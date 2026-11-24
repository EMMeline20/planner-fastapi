from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from prilozhenie.modeli.vyvoz import Pickup
from prilozhenie.nastroiki import settings

_client: AsyncIOMotorClient | None = None


async def init_db() -> None:
    """Подключить MongoDB и зарегистрировать документы Beanie."""

    global _client
    if _client is None:
        # tz_aware=True — MongoDB отдаёт confirmed_at с часовым поясом (UTC),
        # чтобы интерфейс и Swagger показывали одно и то же время.
        _client = AsyncIOMotorClient(settings.mongodb_url, tz_aware=True)

    await init_beanie(
        database=_client[settings.mongodb_db],
        document_models=[Pickup],
    )


async def close_db() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
