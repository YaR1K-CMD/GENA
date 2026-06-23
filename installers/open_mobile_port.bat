@echo off
echo 🔓 ОТКРЫТИЕ ПОРТА ДЛЯ МОБИЛЬНОГО СЕРВЕРА
echo =====================================
echo.

echo 📋 Открываем порт 8003 для внешнего доступа...
echo.

netsh advfirewall firewall delete rule name="Gennady Mobile Server" >nul 2>&1
netsh advfirewall firewall add rule name="Gennady Mobile Server" dir=in action=allow protocol=TCP localport=8003

if %ERRORLEVEL% EQU 0 (
    echo ✅ Порт 8003 успешно открыт!
    echo.
    echo 📱 Теперь можешь подключаться с телефона:
    echo http://192.168.0.11:8003
    echo.
    echo 💡 Не забудь:
    echo - Телефон должен быть подключен к тому же Wi-Fi
    echo - Антивирус может блокировать соединение
    echo - Проверь настройки брандмауэра если не работает
) else (
    echo ❌ Не удалось открыть порт!
    echo.
    echo 💡 Попробуй:
    echo 1. Запусти этот файл от имени администратора
    echo 2. Открой порт вручную в настройках брандмауэра
    echo 3. Временно отключи антивирус для проверки
)

echo.
pause
