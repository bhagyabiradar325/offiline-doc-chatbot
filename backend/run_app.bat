@echo off
cd /d "%~dp0"
echo Starting Offline Doc Chatbot...
echo.
echo Open this URL in your browser:
echo http://127.0.0.1:8000
echo.
echo Keep this window open while using the app.
echo Press Ctrl+C to stop the server.
echo.
".venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
