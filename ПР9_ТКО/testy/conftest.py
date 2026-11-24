"""Общие фикстуры: отдельный mongod для тестов и HTTP-клиент приложения."""

import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

import pytest
import pytest_asyncio

ROOT = Path(__file__).resolve().parents[1]
MONGOD_EXE = Path(r"C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


TEST_MONGO_PORT = _free_port()
os.environ["MONGODB_URL"] = f"mongodb://127.0.0.1:{TEST_MONGO_PORT}"
os.environ["MONGODB_DB"] = "tko_test"


def _wait_port(port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError(f"Порт {port} не открылся за {timeout} секунд")


@pytest.fixture(scope="session", autouse=True)
def mongod_server(tmp_path_factory):
    """Поднимает отдельный mongod на свободном порту и гасит его после тестов."""
    if not MONGOD_EXE.exists():
        pytest.skip(f"Не найден mongod: {MONGOD_EXE}")

    # Тестовая база — в рабочей папке проекта и удаляется после прогона.
    # Так на диске не остаются 100-МБ журналы WiredTiger от каждого запуска.
    test_root = Path(os.environ.get("TEST_MONGO_DBPATH", str(ROOT / ".data" / "mongo_test")))
    try:
        test_root.mkdir(parents=True, exist_ok=True)
        dbpath = test_root / f"run_{os.getpid()}_{int(time.time())}"
        dbpath.mkdir()
        remove_after = True
    except OSError:
        dbpath = tmp_path_factory.mktemp("mongo_test")
        remove_after = False

    process = subprocess.Popen(
        [
            str(MONGOD_EXE),
            "--dbpath",
            str(dbpath),
            "--port",
            str(TEST_MONGO_PORT),
            "--bind_ip",
            "127.0.0.1",
            "--quiet",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_port(TEST_MONGO_PORT)
        yield TEST_MONGO_PORT
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        if remove_after:
            shutil.rmtree(dbpath, ignore_errors=True)


@pytest_asyncio.fixture
async def client(mongod_server):
    """На каждый тест: свежее подключение Beanie, чистая коллекция, ASGI-клиент."""
    from httpx import ASGITransport, AsyncClient

    from prilozhenie.db.podkluchenie import close_db, init_db
    from prilozhenie.glavnyy import app
    from prilozhenie.modeli.vyvoz import Pickup

    await init_db()
    await Pickup.delete_all()

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as http_client:
            yield http_client
    finally:
        await close_db()
