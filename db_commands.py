import asyncio

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from models.events import Event


async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.planner, document_models=[Event])

    # 1. CREATE — вставить запись в коллекцию events
    event = Event(
        title="Субботник",
        image="img.png",
        description="Весенняя уборка парка",
        tags=["eco", "volunteers"],
        location="Ufa",
    )
    await event.insert()
    print("1. ВСТАВЛЕНА ЗАПИСЬ, _id:", event.id)

    # 2. READ — все записи (аналог SELECT * FROM events)
    all_events = await Event.find_all().to_list()
    print("2. ВСЕ ЗАПИСИ:", [(e.title, e.location) for e in all_events])

    # 3. READ — поиск по условию (аналог SELECT ... WHERE)
    one = await Event.find_one(Event.title == "Субботник")
    print("3. НАЙДЕНО ПО title:", one.title, one.location)

    # 4. UPDATE — обновление поля (аналог UPDATE ... SET)
    await one.update({"$set": {"location": "Hybrid"}})
    updated = await Event.get(one.id)
    print("4. ОБНОВЛЕНО, location:", updated.location)

    # 5. DELETE — удаление записи (аналог DELETE FROM)
    await updated.delete()
    left = await Event.find_all().to_list()
    print("5. УДАЛЕНО. ОСТАЛОСЬ ЗАПИСЕЙ:", len(left))

    client.close()


asyncio.run(main())