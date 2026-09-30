@echo off
title The Resistance: Office Heist - Fun Friday
echo ========================================================
echo   THE RESISTANCE: OFFICE HEIST - FUN FRIDAY EDITION
echo ========================================================
echo.
echo Starting web server on http://localhost:8088 ...
echo You can also connect from mobile phones on the same Wi-Fi.
echo.
start "" http://localhost:8088
py server.py
pause
