from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PickupCreate(BaseModel):
    """Тело запроса POST /api/pickups."""

    task_id: str = Field(min_length=1, examples=["T-245"])
    stop_seq: int = Field(ge=1, examples=[1])
    stops_total: int = Field(ge=1, examples=[10])
    container_id: str = Field(min_length=1, examples=["c14"])
    address: str = Field(min_length=1, examples=["ул. Менделеева, 15"])
    district: str = Field(min_length=1, examples=["Ленинский"])
    waste_type: str = Field(min_length=1, examples=["ТКО"])
    volume_m3: float = Field(gt=0, examples=[0.75])
    fill_before: int = Field(ge=0, le=100, examples=[82])
    fill_after: int = Field(default=0, ge=0, le=100, examples=[0])
    driver: str = Field(min_length=1, examples=["Петров А.С."])
    vehicle: str = Field(min_length=1, examples=["Мусоровоз №1"])
    idempotency_key: str = Field(min_length=1, examples=["T-245:c14"])
    confirmed_at: datetime | None = None

    @model_validator(mode="after")
    def check_stop(self) -> "PickupCreate":
        if self.stop_seq > self.stops_total:
            raise ValueError("stop_seq не может быть больше stops_total")
        return self


class PickupRead(BaseModel):
    """Ответ API: ровно те поля, которые лежат в MongoDB."""

    model_config = ConfigDict(from_attributes=True)

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
    fill_after: int
    driver: str
    vehicle: str
    confirmed_at: datetime
    status: str
    idempotency_key: str
