import os
import sys
import time
import traceback
from datetime import datetime

class BotLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self._status_active = False
        self._loading_active = False
        self._loading_total = 0
        self._loading_current = 0
        self._loading_buffer = []
        self.setup_logging()
    
    def setup_logging(self):
        """Создаем директорию для логов"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Создаем файл лога с датой
        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(self.log_dir, f"bot_{today}.txt")
        
        # Создаем файл ошибок
        self.error_file = os.path.join(self.log_dir, f"errors_{today}.txt")
        
        # Создаем файл системных событий
        self.system_file = os.path.join(self.log_dir, f"system_{today}.txt")
        
        # Создаем файл Discord событий
        self.discord_file = os.path.join(self.log_dir, f"discord_{today}.txt")
        
        # Создаем файл Ollama событий
        self.ollama_file = os.path.join(self.log_dir, f"ollama_{today}.txt")
    
    def write_log(self, filename, message, level="INFO"):
        """Записываем сообщение в лог файл"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Ошибка записи в лог: {e}")

    def _print_status(self, percent, message):
        """Однострочный статус загрузки с прогрессом."""
        self._status_active = True
        width = 34
        filled = int(width * percent / 100)
        bar = "#" * filled + " " * (width - filled)
        line = f"GEN OS |{bar}| {percent:3d}%  {message}"
        self._status_len = len(line)
        print(line, flush=True)

    def _clear_status(self):
        if self._status_active:
            # Try to clear the previous status line (ANSI). Fallback to spaces.
            try:
                print("\x1b[1A\x1b[2K", end="", flush=True)
            except Exception:
                pad = " " * max(getattr(self, "_status_len", 0), 0)
                print("\r" + pad + "\r", end="", flush=True)
            self._status_active = False

    def loading_begin(self, total_steps: int):
        self._loading_active = True
        self._loading_total = max(total_steps, 1)
        self._loading_current = 0
        self._loading_start_ts = time.time()
        # ASCII-арт заголовок
        banner = [
            "██████╗ ███████╗███╗   ██╗ ██████╗ ███████╗",
            "██╔════╝ ██╔════╝████╗  ██║██╔═══██╗██╔════╝",
            "██║  ███╗█████╗  ██╔██╗ ██║██║   ██║███████╗",
            "██║   ██║██╔══╝  ██║╚██╗██║██║   ██║╚════██║",
            "╚██████╔╝███████╗██║ ╚████║╚██████╔╝███████║",
            " ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝",
        ]
        for line in banner:
            print(line)

    def loading_step(self, message: str):
        if not self._loading_active:
            return
        # Небольшая задержка для визуального эффекта
        time.sleep(0.2)
        self._loading_current = min(self._loading_current + 1, self._loading_total)
        percent = int(self._loading_current / self._loading_total * 100)
        self._print_status(percent, message)

    def loading_end(self):
        if not self._loading_active:
            return
        self._print_status(100, "SUCCESS LOAD")
        self._loading_active = False

    def loading_flush(self):
        """Печатаем отложенные сообщения после полной загрузки."""
        if self._loading_buffer:
            for line in self._loading_buffer:
                print(line)
            self._loading_buffer.clear()
    
    def info(self, message):
        """Информационное сообщение"""
        self.write_log(self.log_file, message, "INFO")
        if self._loading_active:
            self._loading_buffer.append(f"ℹ️ {message}")
            return
        self._clear_status()
        print(f"ℹ️ {message}")
    
    def error(self, message, exception=None):
        """Сообщение об ошибке"""
        self.write_log(self.error_file, message, "ERROR")
        if exception:
            self.write_log(self.error_file, f"Exception: {str(exception)}", "ERROR")
            self.write_log(self.error_file, f"Traceback:\n{traceback.format_exc()}", "ERROR")
        if self._loading_active:
            self._loading_buffer.append(f"❌ {message}")
            return
        self._clear_status()
        print(f"❌ {message}")
    
    def system(self, message):
        """Системное сообщение"""
        self.write_log(self.system_file, message, "SYSTEM")
        if self._loading_active:
            self._loading_buffer.append(f"🔧 {message}")
            return
        self._clear_status()
        print(f"🔧 {message}")
    
    def discord(self, message):
        """Discord событие"""
        self.write_log(self.discord_file, message, "DISCORD")
        if self._loading_active:
            self._loading_buffer.append(f"💬 {message}")
            return
        self._clear_status()
        print(f"💬 {message}")
    
    def ollama(self, message):
        """Ollama событие"""
        self.write_log(self.ollama_file, message, "OLLAMA")
        if self._loading_active:
            self._loading_buffer.append(f"🤖 {message}")
            return
        self._clear_status()
        print(f"🤖 {message}")
    
    def debug(self, message):
        """Отладочное сообщение"""
        self.write_log(self.log_file, message, "DEBUG")
        if self._loading_active:
            self._loading_buffer.append(f"🔍 {message}")
            return
        self._clear_status()
        print(f"🔍 {message}")
    
    def log_system_info(self):
        """Логируем системную информацию"""
        import platform
        import psutil
        
        self.system("=" * 50)
        self.system("СИСТЕМНАЯ ИНФОРМАЦИЯ")
        self.system("=" * 50)
        self.system(f"ОС: {platform.system()} {platform.release()}")
        self.system(f"Python: {sys.version}")
        self.system(f"CPU: {psutil.cpu_percent()}%")
        self.system(f"Память: {psutil.virtual_memory().percent}%")
        self.system(f"Диск: {psutil.disk_usage('/').percent}%")
        self.system(f"Рабочая директория: {os.getcwd()}")
        
        # Проверяем файлы
        files_to_check = ["bot_v3.py", ".env", "user_memory.json", "bot_knowledge.json"]
        for file in files_to_check:
            if os.path.exists(file):
                size = os.path.getsize(file)
                self.system(f"Файл {file}: {size} bytes")
            else:
                self.system(f"Файл {file}: НЕ НАЙДЕН")
        
        self.system("=" * 50)
    
    def log_discord_connection(self, success, error=None):
        """Логируем подключение к Discord"""
        if success:
            self.discord("✅ Успешное подключение к Discord")
        else:
            self.discord(f"❌ Ошибка подключения к Discord: {error}")
    
    def log_ollama_request(self, model, prompt_length, response_length=None, error=None):
        """Логируем запрос к Ollama"""
        if error:
            self.ollama(f"❌ Ошибка Ollama: {error}")
        else:
            self.ollama(f"📤 Запрос к {model} (промпт: {prompt_length} символов)")
            if response_length:
                self.ollama(f"📥 Ответ: {response_length} символов")
    
    def log_memory_operation(self, operation, user_id, details=""):
        """Логируем операции с памятью"""
        self.system(f"🧠 Память: {operation} для {user_id} {details}")

# Глобальный логгер
logger = BotLogger()
