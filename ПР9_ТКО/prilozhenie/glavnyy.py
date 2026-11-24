import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from prilozhenie.api.vyvozy import router as pickups_router
from prilozhenie.db.podkluchenie import init_db
from prilozhenie.nastroiki import settings

BASE_DIR = Path(__file__).resolve().parent.parent
INTERFEYS_DIR = BASE_DIR / "interfeys"
LOGS_DIR = BASE_DIR / "logs"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """При старте подключаем MongoDB, при остановке — закрываем клиент."""
    await init_db()
    yield


app = FastAPI(
    title="ТКО-Логистика — ПР9",
    description=(
        "Один сценарий К5.2: подтверждение вывоза контейнера. "
        "Цепочка: интерфейс → POST /api/pickups → MongoDB → GET /api/pickups/{pickup_id}."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(pickups_router)


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(INTERFEYS_DIR / "driver.html")


@app.post("/api/log", include_in_schema=False)
async def log_event(payload: dict):
    """Совместимость с logger.js прототипа: события пишутся в logs/events.jsonl."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    record = {"received_at": datetime.now(timezone.utc).isoformat(), **payload}
    with (LOGS_DIR / "events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"ok": True}


app.mount("/", StaticFiles(directory=INTERFEYS_DIR, html=True), name="interfeys")


if __name__ == "__main__":
    uvicorn.run(
        "prilozhenie.glavnyy:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
