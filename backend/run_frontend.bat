@echo off
cd /d "%~dp0frontend"
echo Starting React frontend...
echo.
echo First time only, run:
echo npm install
echo.
echo Open this URL in your browser:
echo http://127.0.0.1:5173
echo.
npm run dev
pause
