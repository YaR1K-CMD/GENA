@echo off
echo ========================================
echo Установка Tesseract OCR для бота
echo ========================================
echo.

echo 1. Скачивание Tesseract...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w64-setup-5.3.3.exe' -OutFile 'tesseract_installer.exe'"

if exist tesseract_installer.exe (
    echo 2. Установка Tesseract...
    tesseract_installer.exe /S
    
    echo 3. Скачивание русского языка...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/rus.traineddata' -OutFile 'rus.traineddata'"
    
    echo 4. Копирование русского языка...
    if exist "C:\Program Files\Tesseract-OCR\tessdata" (
        copy "rus.traineddata" "C:\Program Files\Tesseract-OCR\tessdata\"
        echo Русский язык установлен!
    ) else (
        echo Папка Tesseract не найдена. Проверьте установку.
    )
    
    echo 5. Очистка...
    del tesseract_installer.exe
    del rus.traineddata
    
    echo.
    echo ========================================
    echo Установка завершена!
    echo ========================================
    echo.
    echo Теперь установите Python библиотеки:
    echo pip install pytesseract pillow opencv-python
    echo.
) else (
    echo Ошибка скачивания установщика!
)

pause
