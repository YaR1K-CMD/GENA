@echo off
chcp 65001 >nul
echo ========================================
echo Простая установка Tesseract OCR
echo ========================================
echo.

echo Обнаружена 32-битная система
echo.

echo Скачивание Tesseract...
echo URL: https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w32-setup-5.3.3.exe
echo.

echo Если автоматическое скачивание не сработает:
echo 1. Откройте браузер
echo 2. Перейдите по ссылке выше
echo 3. Скачайте файл tesseract-ocr-w32-setup-5.3.3.exe
echo 4. Запустите установщик
echo 5. Выберите папку: C:\Program Files\Tesseract-OCR
echo 6. Отметьте "Add Tesseract to your PATH"
echo.

pause

echo Попытка автоматического скачивания...
powershell -Command "try { Invoke-WebRequest -Uri 'https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w32-setup-5.3.3.exe' -OutFile 'tesseract_installer.exe'; Write-Host '✅ Скачивание успешно!' } catch { Write-Host '❌ Ошибка скачивания' }"

if exist tesseract_installer.exe (
    echo.
    echo Запуск установщика...
    tesseract_installer.exe
    
    echo.
    echo Скачивание русского языка...
    powershell -Command "try { Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/rus.traineddata' -OutFile 'rus.traineddata'; Write-Host '✅ Русский язык скачан!' } catch { Write-Host '❌ Ошибка скачивания языка' }"
    
    if exist rus.traineddata (
        echo.
        echo Копирование русского языка...
        if exist "C:\Program Files\Tesseract-OCR\tessdata" (
            copy "rus.traineddata" "C:\Program Files\Tesseract-OCR\tessdata\"
            echo ✅ Русский язык установлен!
        ) else (
            echo ❌ Папка Tesseract не найдена. Скопируйте rus.traineddata вручную в:
            echo C:\Program Files\Tesseract-OCR\tessdata\
        )
        
        del rus.traineddata
    )
    
    del tesseract_installer.exe
    
    echo.
    echo ========================================
    echo Установка завершена!
    echo ========================================
    echo.
    echo Теперь установите Python библиотеки:
    echo pip install pytesseract pillow opencv-python
    echo.
    echo Проверка установки:
    echo tesseract --version
) else (
    echo.
    echo ========================================
    echo АВТОМАТИЧЕСКОЕ СКАЧИВАНИЕ НЕ СРАБОТАЛО
    echo ========================================
    echo.
    echo Пожалуйста, установите Tesseract вручную:
    echo.
    echo 1. СКАЧАЙТЕ:
    echo https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w32-setup-5.3.3.exe
    echo.
    echo 2. УСТАНОВИТЕ:
    echo - Запустите скачанный файл
    echo - Путь: C:\Program Files\Tesseract-OCR
    echo - Галочка: "Add Tesseract to your PATH"
    echo.
    echo 3. РУССКИЙ ЯЗЫК:
    echo - Скачайте: https://github.com/tesseract-ocr/tessdata/raw/main/rus.traineddata
    echo - Скопируйте в: C:\Program Files\Tesseract-OCR\tessdata\
    echo.
    echo 4. PYTHON БИБЛИОТЕКИ:
    echo pip install pytesseract pillow opencv-python
)

echo.
pause
