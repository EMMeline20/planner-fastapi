@echo off
cd /d "%~dp0"

set "MONGO_DBPATH=D:\pr9_tko_mongo"
if not exist "%MONGO_DBPATH%" set "MONGO_DBPATH=.data\mongo"
if not exist "%MONGO_DBPATH%" mkdir "%MONGO_DBPATH%"

powershell -NoProfile -Command "if (-not (Get-NetTCPConnection -LocalPort 27017 -State Listen -ErrorAction SilentlyContinue)) { Start-Process -FilePath 'C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe' -ArgumentList '--dbpath','%MONGO_DBPATH%','--port','27017','--bind_ip','127.0.0.1' -WindowStyle Hidden }"

timeout /t 4 >nul

echo.
echo Interface:  http://127.0.0.1:8090/
echo Swagger:    http://127.0.0.1:8090/docs
echo.
.venv\Scripts\python.exe -m uvicorn prilozhenie.glavnyy:app --host 127.0.0.1 --port 8090 --reload
