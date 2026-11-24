from fastapi import APIRouter, HTTPException, Query, Response, status

from prilozhenie.servisy.vyvozy import (
    create_pickup as create_pickup_service,
    delete_pickup as delete_pickup_service,
    get_pickup as get_pickup_service,
    list_pickups as list_pickups_service,
)
from prilozhenie.skhemy.vyvoz import PickupCreate, PickupRead

router = APIRouter(prefix="/api/pickups", tags=["Вывозы"])


@router.post(
    "",
    response_model=PickupRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать акт вывоза",
    description="Создаёт документ в MongoDB. Повторный запрос с тем же idempotency_key возвращает уже созданный акт (код 200).",
)
async def create_pickup(data: PickupCreate, response: Response):
    pickup, created = await create_pickup_service(data)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return pickup


@router.get(
    "",
    response_model=list[PickupRead],
    summary="Список актов вывоза",
    description="Все акты вывоза, новые сверху. Можно отфильтровать по task_id.",
)
async def get_pickups(task_id: str | None = Query(default=None, examples=["T-245"])):
    return await list_pickups_service(task_id)


@router.get(
    "/{pickup_id}",
    response_model=PickupRead,
    summary="Получить акт вывоза по ID",
)
async def get_pickup(pickup_id: str):
    pickup = await get_pickup_service(pickup_id)
    if pickup is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Акт вывоза не найден",
        )
    return pickup


@router.delete(
    "/{pickup_id}",
    summary="Удалить акт вывоза",
    description="Удаляет документ из MongoDB. После удаления GET по этому ID возвращает 404.",
)
async def delete_pickup(pickup_id: str):
    deleted = await delete_pickup_service(pickup_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Акт вывоза не найден",
        )
    return {"message": "Акт вывоза удалён", "pickup_id": pickup_id}
