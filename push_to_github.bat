@echo off
title Push Office Heist to GitHub
echo ========================================================
echo   PUSH OFFICE HEIST TO GITHUB
echo ========================================================
echo.
echo 1. Go to https://github.com/new in your browser
echo 2. Repository name: office-heist
echo 3. Click "Create repository"
echo 4. Copy the URL (e.g. https://github.com/your-username/office-heist.git)
echo.
set /p REPO_URL="Paste your GitHub repository URL here: "

if "%REPO_URL%"=="" (
    echo No URL entered. Exiting.
    pause
    exit /b
)

echo.
echo Connecting to GitHub repository: %REPO_URL% ...
git remote remove origin 2>nul
git remote add origin %REPO_URL%
git branch -M main
echo Pushing files to main branch...
git push -u origin main

echo.
if %ERRORLEVEL% equ 0 (
    echo ========================================================
    echo  SUCCESS! Your code is now live on GitHub!
    echo ========================================================
    echo Next step: Go to https://dashboard.render.com and deploy!
) else (
    echo.
    echo If GitHub prompted for login, please sign in to complete push.
)
echo.
pause
