"""Сквозной тест: кнопка в интерфейсе → POST → MongoDB → GET.

Playwright открывает driver.html в реальном браузере, нажимает «ВЫВЕЗЕНО»,
читает созданный ID из карточки результата, затем проверяет тот же документ
через API и напрямую в MongoDB.
"""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import sync_playwright
from pymongo import MongoClient

from conftest import ROOT, TEST_MONGO_PORT

E2E_DB = "tko_e2e"

# Playwright создаёт временные каталоги; в системном %TEMP% политика Windows
# может запрещать mkdtemp, поэтому уводим их в каталог проекта.
TMP_DIR = Path(os.environ.get("PLAYWRIGHT_TMP", str(ROOT / ".data" / "tmp")))
TMP_DIR.mkdir(parents=True, exist_ok=True)
os.environ["TMP"] = str(TMP_DIR)
os.environ["TEMP"] = str(TMP_DIR)
os.environ["TMPDIR"] = str(TMP_DIR)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


E2E_PORT = _free_port()
BASE_URL = f"http://127.0.0.1:{E2E_PORT}"


@pytest.fixture(scope="module")
def live_server(mongod_server):
    mongo = MongoClient(f"mongodb://127.0.0.1:{TEST_MONGO_PORT}")
    mongo.drop_database(E2E_DB)

    env = os.environ.copy()
    env["MONGODB_URL"] = f"mongodb://127.0.0.1:{TEST_MONGO_PORT}"
    env["MONGODB_DB"] = E2E_DB
    env["PYTHONUNBUFFERED"] = "1"

    log_path = ROOT / ".data" / "e2e_uvicorn.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "prilozhenie.glavnyy:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(E2E_PORT),
            "--log-level",
            "warning",
        ],
        cwd=ROOT,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

    try:
        deadline = time.time() + 60
        last_error = None
        while time.time() < deadline:
            if process.poll() is not None:
                break
            try:
                response = httpx.get(f"{BASE_URL}/docs", timeout=2, trust_env=False)
                if response.status_code == 200:
                    break
            except Exception as error:  # noqa: BLE001
                last_error = error
            time.sleep(0.5)
        else:
            raise RuntimeError(f"Сервер не запустился: {last_error}")

        if process.poll() is not None:
            raise RuntimeError(f"Сервер упал. Лог: {log_path}")

        yield BASE_URL
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        log_file.close()
        mongo.drop_database(E2E_DB)
        mongo.close()


def _launch_browser(playwright):
    try:
        return playwright.chromium.launch(
            channel="msedge", headless=True, args=["--no-proxy-server"]
        )
    except Exception:
        return playwright.chromium.launch(headless=True, args=["--no-proxy-server"])


def _result_rows(page) -> dict[str, str]:
    rows = page.locator("#resultBody .result-row")
    data: dict[str, str] = {}
    for index in range(rows.count()):
        label = rows.nth(index).locator("span").inner_text().strip()
        value = rows.nth(index).locator("b").inner_text().strip()
        data[label] = value
    return data


def test_ui_creates_record_and_db_matches(live_server):
    mongo = MongoClient(f"mongodb://127.0.0.1:{TEST_MONGO_PORT}")

    with sync_playwright() as playwright:
        browser = _launch_browser(playwright)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto(live_server + "/", wait_until="networkidle")

        assert page.locator("#currentAddr").inner_text() == "ул. Менделеева, 15"
        assert page.locator("#currentFill").inner_text() == "82 %"

        page.click("#btnPickup")
        page.wait_for_selector("#resultPanel:not(.hidden)", timeout=20000)

        data = _result_rows(page)
        pickup_id = data["ID записи"]
        assert pickup_id.startswith("P-")
        assert data["Задание"] == "T-245"
        assert data["Точка"] == "1 из 10"
        assert data["Адрес"] == "ул. Менделеева, 15"
        assert data["Заполненность"] == "82 % → 0 %"
        assert data["Статус"] == "Вывезено (confirmed)"

        response = httpx.get(
            f"{live_server}/api/pickups/{pickup_id}", trust_env=False, timeout=10
        )
        assert response.status_code == 200
        record = response.json()
        assert record["address"] == data["Адрес"]
        assert record["fill_before"] == 82
        assert record["fill_after"] == 0
        assert record["confirmed_at"] == data["Время (UTC, ISO)"]

        document = mongo[E2E_DB]["pickups"].find_one({"pickup_id": pickup_id})
        assert document is not None
        assert document["address"] == record["address"]
        assert document["fill_before"] == record["fill_before"]
        assert document["fill_after"] == record["fill_after"]
        assert document["status"] == record["status"]

        page.screenshot(path=str(ROOT / ".data" / "ui_result.png"), full_page=True)
        browser.close()

    mongo.close()


def test_ui_shows_error_on_422(live_server):
    """Негативный UI-тест: сервер отвечает 422, интерфейс показывает ошибку."""
    with sync_playwright() as playwright:
        browser = _launch_browser(playwright)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.route(
                "**/api/pickups",
                lambda route: route.fulfill(
                    status=422,
                    content_type="application/json",
                    body=json.dumps(
                        {"detail": "Некорректные данные"}, ensure_ascii=False
                    ),
                ),
            )
            page.goto(live_server + "/", wait_until="networkidle")
            page.click("#btnPickup")
            page.wait_for_function(
                "() => document.querySelector('#statusText').textContent.includes('Не удалось сохранить')",
                timeout=10000,
            )

            status = page.locator("#statusText").inner_text()
            toast = page.locator(".toast").inner_text()
            assert "Не удалось сохранить" in status
            assert "Некорректные данные" in status or "Некорректные данные" in toast

            page.screenshot(
                path=str(ROOT / "docs" / "ui_error.png"), full_page=True
            )
        finally:
            browser.close()
