@echo off
chcp 65001 >nul
echo ========================================
echo Установка Tesseract OCR (альтернативная)
echo ========================================
echo.

echo Проверяем разрядность системы...
systeminfo | findstr /B /C:"Тип системы" | find "x64" >nul
if %errorlevel%==0 (
    set ARCH=win64
    echo Обнаружена 64-битная система
) else (
    set ARCH=win32
    echo Обнаружена 32-битная система
)

echo.
echo Выберите способ установки:
echo 1. Через Chocolatey (рекомендуется)
echo 2. Ручная загрузка
echo 3. Инструкции по установке
echo.

set /p choice="Ваш выбор (1-3): "

if "%choice%"=="1" goto chocolatey
if "%choice%"=="2" goto manual
if "%choice%"=="3" goto instructions
goto end

:chocolatey
echo.
echo 1. Установка Chocolatey...
powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"

echo.
echo 2. Установка Tesseract через Chocolatey...
choco install tesseract --yes

echo.
echo 3. Установка русского языка...
choco install tesseract-language-rus --yes

echo.
echo ========================================
echo Установка через Chocolatey завершена!
echo ========================================
goto end

:manual
echo.
echo Скачивание Tesseract для %ARCH%...
if "%ARCH%"=="win64" (
    set URL=https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w64-setup-5.3.3.exe
) else (
    set URL=https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w32-setup-5.3.3.exe
)

echo URL: %URL%
echo.
echo Если скачивание не работает, скачайте вручную:
echo %URL%
echo.
pause

echo.
echo Запустите установщик вручную и следуйте инструкциям.
echo После установки установите русский язык:
echo https://github.com/tesseract-ocr/tessdata/raw/main/rus.traineddata
echo.
echo Скопируйте rus.traineddata в папку:
echo C:\Program Files\Tesseract-OCR\tessdata\
goto end

:instructions
echo.
echo ========================================
echo ИНСТРУКЦИЯ ПО РУЧНОЙ УСТАНОВКЕ
echo ========================================
echo.
echo 1. СКАЧАТЬ TESSERACT:
echo    - 64-bit: https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w64-setup-5.3.3.exe
echo    - 32-bit: https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w32-setup-5.3.3.exe
echo.
echo 2. УСТАНОВИТЬ:
echo    - Запустите скачанный файл
echo    - Выберите путь установки: C:\Program Files\Tesseract-OCR
echo    - Отметьте галочкой "Add Tesseract to your PATH"
echo.
echo 3. УСТАНОВИТЬ РУССКИЙ ЯЗЫК:
echo    - Скачайте: https://github.com/tesseract-ocr/tessdata/raw/main/rus.traineddata
echo    - Скопируйте в: C:\Program Files\Tesseract-OCR\tessdata\
echo.
echo 4. УСТАНОВИТЬ PYTHON БИБЛИОТЕКИ:
echo    pip install pytesseract pillow opencv-python numpy requests
echo.
echo 5. ПРОВЕРИТЬ УСТАНОВКУ:
echo    tesseract --version
echo.
echo ========================================
goto end

:end
echo.
echo Для продолжения нажмите любую клавишу . . .
pause >nul
