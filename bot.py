import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ==============================================================================
# 1. ЗАГРУЗКА ОКРУЖЕНИЯ (СТРОГО ДО ЧТЕНИЯ ПЕРЕМЕННЫХ И ИМПОРТОВ СТОРОННИХ МОДУЛЕЙ)
# ==============================================================================
load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)

# Теперь ключи гарантированно прочитаются из вашего .env файла
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "0164b3f12ac44a04b27a609c4835b8f8._Wb90mNzhRycM4E8CbIlRrAh")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
OPENROUTER_BASE_URL = "https://openrouter.ai"

# Глобальные заглушки для предотвращения ошибок статического анализа ( reportUnboundVariable )
config: dict = {}

# ==============================================================================
# 2. ПЕРЕХВАТ РАННЕГО ВЫВОДА (ПЕЧАТЬ В БУФЕР ДО НАСТРОЙКИ ЛОГГЕРА)
# ==============================================================================
_early_logs = []
import builtins as _builtins
import atexit as _atexit
_orig_print = _builtins.print

# Буферизуем ранние сообщения, чтобы показывать их после загрузки логгера
_early_logs = []
import builtins as _builtins
import atexit as _atexit
_orig_print = _builtins.print

def _early_print(*args, **kwargs):
    _early_logs.append(" ".join(str(a) for a in args))
_builtins.print = _early_print


def _flush_early_logs():
    try:
        for _line in _early_logs:
            try:
                if 'logger' in globals() and hasattr(logger, '_write'):
                    try:
                        _saved_print = _builtins.print
                        try:
                            _builtins.print = _orig_print
                            logger._write(_line)
                        finally:
                            _builtins.print = _saved_print
                    except Exception:
                        try:
                            _orig_print(_line)
                        except Exception:
                            pass
                else:
                    _orig_print(_line)
            except Exception:
                try:
                    _orig_print(_line)
                except Exception:
                    pass
        if 'logger' in globals():
            def _print_to_logger_at_exit(*args, **kwargs):
                try:
                    text = " ".join(str(a) for a in args)
                    if getattr(logger, 'console', False):
                        _orig_print(text, **kwargs)
                    else:
                        try:
                            _saved_print = _builtins.print
                            try:
                                _builtins.print = _orig_print
                                logger._write(text)
                            finally:
                                _builtins.print = _saved_print
                        except Exception:
                            pass
                except Exception:
                    try:
                        _orig_print(*args, **kwargs)
                    except Exception:
                        pass
            _builtins.print = _print_to_logger_at_exit
        else:
            _builtins.print = _orig_print
    except Exception:
        pass

_atexit.register(_flush_early_logs)

# Фикс кодировки консоли Windows под UTF-8 (для эмодзи)
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

# ==============================================================================
# 3. ИМПОРТЫ СТАНДАРТНЫХ И СТОРОННИХ БИБЛИОТЕК
# ==============================================================================
import discord
from discord.ext import commands
try:
    from discord import app_commands  # type: ignore  # pyright: ignore[reportMissingImports,reportUnknownVariableType]
except Exception:
    app_commands = None

import asyncio
import json
import random
import re
import subprocess
import time
import requests
import traceback
import tempfile
import html as html_lib
import base64
from urllib.parse import parse_qs, unquote, urlsplit, quote
from difflib import SequenceMatcher

# ==============================================================================
# 4. ИМПОРТ ИНСТРУМЕНТОВ СИСТЕМЫ ПАМЯТИ БОТА
# ==============================================================================
from bot_memory_tools import (
    append_channel_message,
    append_user_message,
    can_bot_react,
    can_bot_send,
    can_post_to_channel,
    ensure_memory_schema,
    extract_memory_facts,
    find_known_member,
    format_member_mention,
    get_online_members,
    load_json,
    is_ping_summary_request,
    render_channel_history,
    render_user_history,
    resolve_member,
    resolve_role,
    resolve_text_channel,
    save_json,
    summarize_memory_facts,
    summarize_message_mentions,
    remember_user_facts,
    upsert_known_member,
)

# ==============================================================================
# 5. ИМПОРТЫ ДОПОЛНИТЕЛЬНЫХ МОДУЛЕЙ БОТА (AI И ИГРЫ)
# ==============================================================================
ai_tools = None
try:
    from servers.ai_tools import ai_tools  # type: ignore # pyright: ignore[reportMissingImports]
    AI_TOOLS_AVAILABLE = True
    print(" AI инструменты доступны")
except ImportError as e:
    AI_TOOLS_AVAILABLE = False
    print(f" AI инструменты недоступны: {e}")

setup_games = None
try:
    from games.discord_integration import setup_games # pyright: ignore[reportMissingImports]
    GAMES_ENABLED = True
    print(" Игровые модули успешно импортированы")
except ImportError as e:
    GAMES_ENABLED = False
    print(f" Игровые модули недоступны: {e}")

# Добавляем подавление предупреждения для динамического импорта распознавания изображений
try:
    from servers import image_recognition # type: ignore # pyright: ignore[reportMissingImports]
except ImportError:
    pass

# ==============================================================================
# 6. ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ ЛОГИРОВАНИЯ И ПЕРЕХВАТ PRINT
# ==============================================================================
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
    
    # Отключаем буферизацию принтов перед импортом проблемного модуля
    import builtins as _builtins
    if '_orig_print' in globals():
        _builtins.print = _orig_print
        
    print("🔍 Попытка импорта основного логгера из tools/logger.py...")
    
    # Пробуем импортировать логгер
    from logger import logger  # pyright: ignore[reportMissingImports]
    
    print("✅ Основной логгер успешно импортирован!")
    
    def _print_to_logger_imported(*args, **kwargs):
        try:
            text = " ".join(str(a) for a in args)
            if getattr(logger, 'console', False):
                _orig_print(text, **kwargs)
            else:
                try:
                    if hasattr(logger, '_write'):
                        _saved_print = _builtins.print
                        try:
                            _builtins.print = _orig_print
                            logger._write(text)
                        finally:
                            _builtins.print = _saved_print
                    elif hasattr(logger, 'system'):
                        _saved_print = _builtins.print
                        try:
                            _builtins.print = _orig_print
                            logger.system(text)
                        finally:
                            _builtins.print = _saved_print
                    else:
                        _orig_print(text, **kwargs)
                except Exception:
                    _orig_print(text, **kwargs)
        except Exception:
            _orig_print(*args, **kwargs)
    _builtins.print = _print_to_logger_imported

except Exception as e:
    # Если логгер упал во время своего выполнения — мы поймаем его здесь!
    import builtins as _builtins
    if '_orig_print' in globals():
        _builtins.print = _orig_print
    print("\n" + "💥" * 20)
    print("КРИТИЧЕСКАЯ ОШИБКА ПРИ ВЫПОЛНЕНИИ ФАЙЛА tools/logger.py:")
    print("💥" * 20)
    traceback.print_exc(file=sys.stdout)
    print("=" * 50 + "\n")
    
    # Переходим на резервный безопасный логгер, чтобы бот не падал
    print("⚠️ Переключаюсь на аварийный SimpleLogger...")
    import logging
    logging.basicConfig(level=logging.INFO)
    
    class SimpleLogger:
        def __init__(self):
            self._status_active = False
            self._status_len = 0
            self._loading_active = False
            self._loading_total = 0
            self._loading_current = 0
            self._loading_buffer = []
            self.console = True  # Включаем вывод в консоль при аварии

            try:
                log_dir = os.path.join(os.path.dirname(__file__), 'logs')
                os.makedirs(log_dir, exist_ok=True)
                self._log_path = os.path.join(log_dir, 'gena.log')
                self._file = open(self._log_path, 'a', encoding='utf-8')
            except Exception:
                self._file = None

            try:
                _atexit.register(self._close)
            except Exception:
                pass

        def _close(self):
            try:
                if getattr(self, '_file', None) is not None:
                    self._file.flush() # type: ignore
                    self._file.close() # type: ignore
            except Exception:
                pass

        def _write(self, text: str):
            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
            line = f"[{ts}] {text}"
            try:
                if getattr(self, '_file', None) is not None:
                    self._file.write(line + "\n") # type: ignore
                    self._file.flush() # type: ignore
            except Exception:
                pass
            if self.console:
                try:
                    _orig_print(text)
                except Exception:
                    pass

        def debug(self, *args, **_kwargs):
            text = " ".join(str(a) for a in args)
            self._write(f"[DEBUG] {text}")

        def error(self, *args, **_kwargs):
            text = " ".join(str(a) for a in args)
            self._write(f"[ERROR] {text}")

        def info(self, *args, **_kwargs):
            text = " ".join(str(a) for a in args)
            self._write(f"[INFO] {text}")

        def system(self, *args, **_kwargs):
            text = " ".join(str(a) for a in args)
            self._write(f"[SYSTEM] {text}")

        def discord(self, *args, **_kwargs):
            text = " ".join(str(a) for a in args)
            self._write(f"[DISCORD] {text}")

        def log_system_info(self, *args, **_kwargs):
            text = " ".join(str(a) for a in args)
            self._write(f"[SYS INFO] {text}")

        def loading_step(self, *args, **_kwargs):
            text = " ".join(str(a) for a in args)
            self._write(f"[LOADING STEP] {text}")

        def loading_begin(self, *args, **_kwargs):
            text = " ".join(str(a) for a in args)
            self._write(f"[LOADING BEGIN] {text}")

        def loading_end(self, *args, **_kwargs):
            text = " ".join(str(a) for a in args)
            self._write(f"[LOADING END] {text}")

        def loading_flush(self, *args, **_kwargs):
            text = " ".join(str(a) for a in args)
            self._write(f"[LOADING FLUSH] {text}")

        def ollama(self, *args, **_kwargs):
            text = " ".join(str(a) for a in args)
            self._write(f"[OLLAMA] {text}")

        def log_ollama_request(self, *args, **_kwargs):
            text = " ".join(str(a) for a in args)
            self._write(f"[OLLAMA REQ] {text}")

        def set_console(self, status: bool):
            self.console = status
            self._write(f"[SYSTEM] Console output set to {status}")

        def _print_status(self, percent, msg):
            pass
            
    logger = SimpleLogger()
  
# Объявляем глобальную переменную config на самом верхнем уровне файла
#global config
config: dict = {}
   
       

def _print_to_logger(*args, **kwargs):
    try:
        text = " ".join(str(a) for a in args)
        if getattr(logger, 'console', False):
            _orig_print(text, **kwargs)
        else:
            # Пишем в лог-файл, избегая рекурсии если logger использует print
            try:
                _saved_print = _builtins.print
                try:
                    _builtins.print = _orig_print
                    logger._write(text)
                finally:
                    _builtins.print = _saved_print
            except Exception:
                pass
    except Exception:
        try:
            _orig_print(*args, **kwargs)
        except Exception:
            pass

_builtins.print = _print_to_logger

# ==================== VISUAL EFFECTS =====================
import asyncio
import random

async def typing_only_effect(channel, duration: float = 4.0):
    """Только статус печатания без сообщений"""
    async with channel.typing():
        await asyncio.sleep(duration)

async def animated_typing_effect(channel, min_duration: float = 2.0, max_duration: float = 7.0):
    """Анимированный статус печатания с переменной скоростью"""
    duration = random.uniform(min_duration, max_duration)
    
    async with channel.typing():
        # Имитируем прерывистую печатание
        elapsed = 0
        while elapsed < duration:
            # Короткие паузы как будто бот печатает и думает
            pause = random.uniform(0.2, 1.5)
            await asyncio.sleep(pause)
            elapsed += pause
            
            # Иногда делаем длинную паузу как будто обдумывает
            if random.random() < 0.2:  # 20% шанс
                thinking_pause = random.uniform(1.0, 2.5)
                await asyncio.sleep(thinking_pause)
                elapsed += thinking_pause

async def burst_typing_effect(channel, bursts: int = 3):
    """Эффект коротких вспышек печатания"""
    for i in range(bursts):
        # Короткая вспышка печатания
        async with channel.typing():
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Пауза между вспышками
        if i < bursts - 1:
            await asyncio.sleep(random.uniform(0.3, 1.0))

async def realistic_typing_effect(channel, message_length: int):
    """Реалистичный эффект печатания в зависимости от длины ответа"""
    # Примерная скорость печатания: 50-70 символов в секунду
    typing_speed = random.uniform(50, 70)  # символов/сек
    base_duration = message_length / typing_speed
    
    # Добавляем время на обдумывание
    thinking_time = random.uniform(1.0, 3.0)
    total_duration = base_duration + thinking_time
    
    # Добавляем случайные паузы как будто бот думает над словами
    async with channel.typing():
        elapsed = 0
        while elapsed < total_duration:
            # Нормальная печатание
            await asyncio.sleep(random.uniform(0.3, 0.8))
            elapsed += random.uniform(0.3, 0.8)
            
            # Случайная длинная пауза (обдумывание)
            if random.random() < 0.15:  # 15% шанс
                await asyncio.sleep(random.uniform(1.0, 2.0))
                elapsed += random.uniform(1.0, 2.0)

recognize_image_from_file = None
recognize_image_from_bytes = None
# ==================== IMAGE RECOGNITION =====================
try:
    from servers.image_recognition import recognize_image_from_file, recognize_image_from_bytes # type: ignore # pyright: ignore[reportMissingImports]
    IMAGE_RECOGNITION_AVAILABLE = True
    print(" Распознавание изображений доступно")
except ImportError as e:
    IMAGE_RECOGNITION_AVAILABLE = False
    print(f" Распознавание изображений недоступно: {e}")

# ==================== RECONNECT SYSTEM =====================
import time
from typing import Optional, Dict

class ReconnectManager:
    def __init__(self):
        self.error_history: Dict[str, int] = {}
        self.last_error: Optional[str] = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 50
        self.reconnect_delay = 10  # секунд
        self.max_same_error_count = 3
        
    def add_error(self, error_msg: str) -> bool:
        """Добавляет ошибку в историю. Возвращает True если это новая ошибка"""
        error_type = self._extract_error_type(error_msg)
        
        if error_type == self.last_error:
            self.error_history[error_type] = self.error_history.get(error_type, 0) + 1
            print(f" Та же самая ошибка (#{self.error_history[error_type]}): {error_type}")
            return False
        else:
            self.last_error = error_type
            self.error_history[error_type] = 1
            print(f" Новая ошибка: {error_type}")
            return True
    
    def _extract_error_type(self, error_msg: str) -> str:
        """Извлекает тип ошибки из сообщения"""
        error_msg = error_msg.lower()
        
        if "getaddrinfo failed" in error_msg:
            return "DNS ошибка (getaddrinfo failed)"
        elif "connection was forcibly closed" in error_msg or "connection was aborted" in error_msg:
            return "Соединение прервано (connection aborted)"
        elif "timeout" in error_msg:
            return "Таймаут подключения"
        elif "ssl" in error_msg:
            return "SSL ошибка"
        elif "discord.com" in error_msg:
            return "Недоступность Discord"
        else:
            return "Неизвестная ошибка"
    
    def should_reconnect(self) -> bool:
        """Проверяет, нужно ли пытаться переподключиться"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print(f" Достигнуто максимальное количество попыток ({self.max_reconnect_attempts})")
            return False
        
        if self.last_error and self.error_history.get(self.last_error, 0) >= self.max_same_error_count:
            print(f" Слишком много одинаковых ошибок ({self.max_same_error_count}): {self.last_error}")
            return False
        
        return True
    
    def wait_before_reconnect(self):
        """Ожидание перед переподключением"""
        self.reconnect_attempts += 1
        
        # Увеличиваем задержку с каждой попыткой
        delay = self.reconnect_delay * self.reconnect_attempts
        print(f" Попытка переподключения #{self.reconnect_attempts} через {delay} секунд...")
        
        for i in range(delay, 0, -1):
            print(f" Ожидание: {i} секунд", end='\r')
            time.sleep(1)
        print("")

# Глобальный менеджер переподключений
reconnect_manager = ReconnectManager()

# ==================== TOOLS =====================
def normalize_key(key: str) -> str:
    """Нормализует ключ, заменяя похожие символы"""
    # Заменяем латинские символы на кириллические
    replacements = {
        'a': 'а', 'e': 'е', 'y': 'у', 'o': 'о', 'p': 'р',
        'c': 'с', 'x': 'х', 'A': 'А', 'E': 'Е', 'Y': 'У',
        'O': 'О', 'P': 'Р', 'C': 'С', 'X': 'Х', 'B': 'В',
        'M': 'М', 'T': 'Т', 'H': 'Н', 'K': 'К', 'D': 'Д',
        'L': 'Л', 'G': 'Г', 'Z': 'З', 'F': 'Ф', 'U': 'У',
        'J': 'Ж', 'I': 'И', 'Q': 'Я', 'R': 'Р', 'S': 'С',
        'V': 'В', 'W': 'В', 'b': 'ь', 'i': 'и'
    }
    
    normalized = ""
    for char in key:
        normalized += replacements.get(char, char)
    
    return normalized

def is_simple_word(text: str) -> bool:
    """Проверяет, является ли текст простым словом/фразой"""
    text = text.lower().strip()
    
    # Список стоп-слов, которые не должны вызывать инструменты
    stop_words = {
        'привет', 'здравствуй', 'пока', 'до свидания', 'спасибо', 'пожалуйста',
        'да', 'нет', 'хорошо', 'плохо', 'ок', 'ok', 'ладно', 'конечно',
        'что', 'кто', 'где', 'когда', 'почему', 'как', 'какой', 'какая',
        'какие', 'сколько', 'который', 'как', 'чем', 'зачем', 'откуда',
        'это', 'этот', 'эта', 'эти', 'тот', 'та', 'те', 'такой', 'такая',
        'такие', 'весь', 'вся', 'все', 'сам', 'сама', 'сами', 'мой', 'твой',
        'его', 'её', 'наш', 'ваш', 'их', 'здесь', 'там', 'сюда', 'туда',
        'сейчас', 'сегодня', 'завтра', 'вчера', 'раньше', 'позже', 'потом',
        'можно', 'нельзя', 'нужно', 'должен', 'должна', 'должны',
        'хочу', 'хочешь', 'хочет', 'хотим', 'хотите', 'хотят',
        'могу', 'можешь', 'может', 'можем', 'можете', 'могут',
        'есть', 'нет', 'быть', 'был', 'была', 'было', 'были',
        'делать', 'сделать', 'идти', 'прийти', 'смотреть', 'посмотреть',
        'говорить', 'сказать', 'спросить', 'ответить', 'понимать', 'понять'
    }
    
    # Если это стоп-слово или короткое слово
    if text in stop_words or len(text) < 3:
        return True
    
    # Если это вопросительное слово без контекста
    if text in ['что', 'кто', 'где', 'когда', 'почему', 'как', 'зачем']:
        return True
    
    return False


def sanitize_bot_response(text: str) -> str:
    """Гарантирует, что ответ бота не пустой и безопасен для отправки в Discord."""
    cleaned = strip_reasoning_leak((text or "").strip())
    cleaned = remove_stuttered_word_fragments(cleaned)
    if not cleaned:
        return "Не понял запрос. Уточни, что именно проверить или рассказать."
    # Жесткое ограничение Discord по длине одного сообщения
    if len(cleaned) > 1990:
        return cleaned[:1990] + "..."
    return cleaned


def no_info_response(question: str = "") -> str:  # noqa: ARG001
    """Более дружелюбный ответ при отсутствии данных."""
    variants = [
        "Пока нет точных данных по этому запросу. Попробуй переформулировать или уточнить.",
        "Не нашёл надёжной информации. Можешь уточнить запрос?",
        "По этому запросу ничего подтверждённого не нашлось. Дай больше контекста.",
        "Не удалось найти точные данные. Сформулируй вопрос иначе — попробую ещё раз.",
    ]
    return random.choice(variants)


def normalize_tool_result_text(text: str) -> str:
    """Убирает служебные префиксы источников из текста инструмента."""
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^(Wikipedia|DuckDuckGo|DuckDuckGo Web)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def is_grounded_response(response_text: str, source_text: str) -> bool:
    """Проверяет, что ответ LLM реально опирается на исходные данные."""
    r = normalize_key((response_text or "").lower())
    s = normalize_key((source_text or "").lower())
    src_tokens = [t for t in re.findall(r"[a-zа-яё0-9]+", s) if len(t) >= 5]
    if not src_tokens:
        return True
    overlap = sum(1 for t in src_tokens if t in r)
    return overlap >= 1

def search_wikipedia(query: str) -> str:
    """Бесплатный поиск по Wikipedia API (без ключа)."""
    try:
        global web_search_failures, web_search_block_until
        if time.time() < web_search_block_until:
            return ""
        headers = {"User-Agent": "GenaBot/2.0 (Discord helper; local deployment)"}
        for lang in ("ru", "en"):
            search_resp = requests.get(
                f"https://{lang}.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "format": "json",
                    "srlimit": 1,
                },
                headers=headers,
                timeout=8,
            )
            if search_resp.status_code != 200:
                continue
            try:
                search_data = search_resp.json()
            except Exception:
                continue
            hits = search_data.get("query", {}).get("search", [])
            if not hits:
                continue
            title = hits[0].get("title", "").strip()
            if not title:
                continue
            encoded_title = quote(title.replace(" ", "_"))
            summary_resp = requests.get(
                f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded_title}",
                headers=headers,
                timeout=8,
            )
            if summary_resp.status_code != 200:
                continue
            try:
                summary_data = summary_resp.json()
            except Exception:
                continue
            extract = (summary_data.get("extract") or "").strip()
            if extract:
                page_url = (summary_data.get("content_urls", {}).get("desktop", {}).get("page") or "").strip()
                suffix = f"\nИсточник: {page_url}" if page_url else ""
                return f"Wikipedia ({lang}): {extract[:520]}{suffix}"
    except Exception as e:
        web_search_failures += 1
        if web_search_failures >= 3:
            web_search_block_until = time.time() + 300
        logger.debug(f"Ошибка Wikipedia API: {e}")
    return ""


def search_duckduckgo(query: str) -> str:
    """Бесплатный DuckDuckGo Instant Answer API (без ключа)."""
    try:
        global web_search_failures, web_search_block_until
        if time.time() < web_search_block_until:
            return ""
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
            timeout=8,
        )
        if resp.status_code not in (200, 202):
            return ""
        data = resp.json()
        abstract = (data.get("AbstractText") or "").strip()
        if abstract:
            abstract_url = (data.get("AbstractURL") or "").strip()
            suffix = f"\nИсточник: {abstract_url}" if abstract_url else ""
            return f"DuckDuckGo: {abstract[:520]}{suffix}"
        heading = (data.get("Heading") or "").strip()
        abstract_url = (data.get("AbstractURL") or "").strip()
        if heading and abstract_url:
            return f"DuckDuckGo: {heading} — {abstract_url}"
        related = data.get("RelatedTopics") or []
        for item in related:
            if "Topics" in item and isinstance(item["Topics"], list):
                for sub in item["Topics"]:
                    text = (sub.get("Text") or "").strip()
                    if text:
                        return f"DuckDuckGo: {text[:420]}"
            text = (item.get("Text") or "").strip()
            if text:
                first_url = (item.get("FirstURL") or "").strip()
                suffix = f"\nИсточник: {first_url}" if first_url else ""
                return f"DuckDuckGo: {text[:520]}{suffix}"
    except Exception as e:
        web_search_failures += 1
        if web_search_failures >= 3:
            web_search_block_until = time.time() + 300
        logger.debug(f"Ошибка DuckDuckGo API: {e}")
    return ""


def _ddg_resolve_link(raw_link: str) -> str:
    """Раскрывает редирект-ссылки DuckDuckGo вида /l/?uddg=..."""
    if not raw_link:
        return ""
    raw_link = html_lib.unescape(raw_link.strip())
    if raw_link.startswith("/l/?"):
        parsed = urlsplit(raw_link)
        uddg = parse_qs(parsed.query).get("uddg", [""])[0]
        if uddg:
            return unquote(uddg)
    return raw_link


def search_duckduckgo_html(query: str) -> str:
    """Fallback: парсинг HTML-выдачи DuckDuckGo (без API-ключа)."""
    try:
        global web_search_failures, web_search_block_until
        if time.time() < web_search_block_until:
            return ""
        headers = {"User-Agent": "Mozilla/5.0 (compatible; GenaBot/2.0)"}
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=headers,
            timeout=10,
        )
        if resp.status_code != 200:
            return ""

        body = resp.text
        title_match = re.search(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            body,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not title_match:
            return ""

        link = _ddg_resolve_link(title_match.group(1))
        title_raw = re.sub(r"<[^>]+>", "", title_match.group(2))
        title = html_lib.unescape(title_raw).strip()

        snippet_match = re.search(
            r'<(?:a|div)[^>]*class="result__snippet"[^>]*>(.*?)</(?:a|div)>',
            body,
            flags=re.IGNORECASE | re.DOTALL,
        )
        snippet = ""
        if snippet_match:
            snippet_raw = re.sub(r"<[^>]+>", "", snippet_match.group(1))
            snippet = html_lib.unescape(snippet_raw).strip()

        if title and snippet:
            return f"DuckDuckGo Web: {title}\n{snippet[:320]}\n{link}"
        if title:
            return f"DuckDuckGo Web: {title}\n{link}"
    except Exception as e:
        web_search_failures += 1
        if web_search_failures >= 3:
            web_search_block_until = time.time() + 300
        logger.debug(f"Ошибка DuckDuckGo HTML: {e}")
    return ""


def search_web(query: str) -> str:
    """Каскадный бесплатный поиск с проверкой релевантности."""
    global web_search_failures
    wiki = search_wikipedia(query)
    if wiki and is_web_result_relevant(query, wiki):
        web_search_failures = 0
        return wiki
    ddg = search_duckduckgo(query)
    if ddg and is_web_result_relevant(query, ddg):
        web_search_failures = 0
        return ddg
    ddg_html = search_duckduckgo_html(query)
    if ddg_html and is_web_result_relevant(query, ddg_html):
        web_search_failures = 0
        return ddg_html
    return "Ничего надёжного не найдено по запросу."


def is_web_result_relevant(query: str, result_text: str) -> bool:
    """Простая проверка релевантности, чтобы не возвращать мусор по однословным запросам."""
    q = normalize_key(query.lower())
    r = normalize_key((result_text or "").lower())
    tokens = [t for t in re.findall(r"[a-zа-яё0-9]+", q) if len(t) >= 4]
    if not tokens:
        return True
    matches = sum(1 for t in tokens if t in r)
    # Для многословного запроса требуем совпадение минимум двух токенов.
    if len(tokens) >= 2:
        return matches >= min(2, len(tokens))
    return matches >= 1

def find_best_knowledge_key(search_key: str) -> str:
    """Ищет лучший ключ в знаниях с учётом опечаток и нормализации"""
    # Нормализуем ключ
    normalized_key = normalize_key(search_key.lower().strip())
    query_tokens = re.findall(r"[a-zа-яё0-9]+", normalized_key)
    
    # Точное совпадение с нормализацией
    for key in global_knowledge.keys():
        if normalize_key(key.lower()) == normalized_key:
            return key
    
    # Ищем похожие ключи
    best_match = None
    best_score = 0
    
    for key in global_knowledge.keys():
        key_normalized = normalize_key(key.lower())
        # Не матчим короткие ключи как подстроку длинного запроса
        if len(key_normalized) < 4:
            if key_normalized in query_tokens:
                return key
            continue
        
        # Проверяем вхождение
        if normalized_key in key_normalized or key_normalized in normalized_key:
            score = max(len(normalized_key), len(key_normalized))
            if score > best_score:
                best_score = score
                best_match = key

    # Нечеткий поиск (например MASTERIA -> Мастерия)
    # Нужен, когда отличается 1-2 символа/транслитерация.
    fuzzy_best = best_match
    fuzzy_score = 0.0
    for key in global_knowledge.keys():
        key_normalized = normalize_key(key.lower())
        ratio = SequenceMatcher(None, normalized_key, key_normalized).ratio()
        if ratio > fuzzy_score:
            fuzzy_score = ratio
            fuzzy_best = key

    if fuzzy_best and fuzzy_score >= 0.72:
        return fuzzy_best
    
    return best_match if best_match else search_key

from typing import Optional, Any


def tool_get_knowledge(key: str) -> Optional[str]:
    """Получить знание по ключу с учётом опечаток, нормализации и поиска"""
    # Проверяем, не является ли это простым словом
    if is_simple_word(key):
        logger.debug(f" Пропуск простого слова: '{key}'")
        return None
    
    # Ищем лучший ключ
    best_key = find_best_knowledge_key(key)
    
    entry = global_knowledge.get(best_key)
    if entry:
        # Если ключ изменился из-за опечатки или нормализации
        if best_key != key:
            logger.debug(f"🔧 Исправлен ключ: '{key}' → '{best_key}'")
        return entry.get("explanation", "Описание отсутствует.")
    
    # Если знания нет, пробуем бесплатный веб-поиск
    logger.debug(f" Веб-поиск (free): '{key}'")
    web_result = search_web(key)
    
    if web_result and "Ничего не найдено" not in web_result and is_web_result_relevant(key, web_result):
        return web_result

    return "Знание не найдено."

# Новые функции инструментов
async def tool_get_time(location: str = "UTC") -> str:
    """Получить текущее время (использует ai_tools или системное datetime в качестве резерва)"""
    # 1. Пробуем получить время через ai_tools, если они доступны
    if AI_TOOLS_AVAILABLE and ai_tools is not None:
        try:
            result = await ai_tools.get_current_time(location)
            if "error" not in result:
                return f" Текущее время: {result['time']}\n Дата: {result['date']}\n День недели: {result['day']}\n Часовой пояс: {result['timezone']}"
        except Exception as e:
            logger.error(f"Ошибка ai_tools времени, переключаюсь на систему: {e}")

    # 2. Резервный вариант: если инструменты недоступны, берем системное время
    try:
        from datetime import datetime as _dt, timezone as _tz
        now_utc = _dt.now(_tz.utc).strftime("%H:%M:%S")
        now_local = _dt.now().strftime("%H:%M:%S")
        date_str = _dt.now().strftime("%Y-%m-%d")
        
        msg = f" Текущее время (Системное):\n Локальное: {now_local}\n UTC: {now_utc}\n Дата: {date_str}"
        if location and location.lower() != "utc":
            msg += f"\n (Примечание: поиск для локации '{location}' выполнен по системному времени, так как база часовых поясов недоступна)"
        return msg
    except Exception as e:
        logger.error(f"Критическая ошибка получения времени: {e}")
        return f"Ошибка получения времени: {str(e)}"

async def tool_get_weather(location: str = "Moscow") -> str:
    """Получить погоду"""
    if not AI_TOOLS_AVAILABLE:
        return "Инструменты погоды недоступны."
    
    try:
        if ai_tools is None:
            return "Инструменты погоды недоступны."
        result = await ai_tools.get_weather(location)
        if "error" not in result:
            return f" Погода в {result['location']}:\n Температура: {result['temperature']}\n Состояние: {result['condition']}\n Влажность: {result['humidity']}\n Ветер: {result['wind']}\n Давление: {result['pressure']}\n Ощущается как: {result['feels_like']}"
        else:
            return f"Ошибка получения погоды: {result.get('error')}"
    except Exception as e:
        logger.error(f"Ошибка инструмента погоды: {e}")
        return f"Ошибка получения погоды: {str(e)}"

async def tool_calculate(expression: str) -> str:
    """Выполнить математические вычисления"""
    if not AI_TOOLS_AVAILABLE:
        return "Инструменты калькулятора недоступны."
    
    try:
        if ai_tools is None:
            return "Инструменты калькулятора недоступны."
        result = await ai_tools.calculate(expression)
        if "error" not in result:
            return f" Вычисление:\n Выражение: {result['expression']}\n Результат: {result['result']}"
        else:
            return f"Ошибка вычисления: {result.get('error')}"
    except Exception as e:
        logger.error(f"Ошибка инструмента калькулятора: {e}")
        return f"Ошибка вычисления: {str(e)}"

async def tool_get_news(category: str = "general", count: int = 3) -> str:
    """Получить последние новости"""
    if not AI_TOOLS_AVAILABLE:
        return "Инструменты новостей недоступны."
    
    try:
        if ai_tools is None:
            return "Инструменты новостей недоступны."
        result = await ai_tools.get_news(category, count)
        if "error" not in result:
            news_text = f" Последние новости ({result['category']}):\n\n"
            for i, item in enumerate(result['news'], 1):
                news_text += f"{i}. {item['title']}\n   {item['description']}\n    {item['time']} |  {item['source']}\n\n"
            return news_text.strip()
        else:
            return f"Ошибка получения новостей: {result.get('error')}"
    except Exception as e:
        logger.error(f"Ошибка инструмента новостей: {e}")
        return f"Ошибка получения новостей: {str(e)}"

async def tool_convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Конвертировать валюту"""
    if not AI_TOOLS_AVAILABLE:
        return "Инструменты валюты недоступны."
    
    try:
        if ai_tools is None:
            return "Инструменты конвертации валют недоступны."
        result = await ai_tools.convert_currency(amount, from_currency, to_currency)
        if "error" not in result:
            return f" Конвертация валют:\n {result['amount']} {result['from']} = {result['result']} {result['to']}\n Курс: {result['rate']}"
        else:
            return f"Ошибка конвертации: {result.get('error')}"
    except (asyncio.TimeoutError, requests.RequestException, ValueError) as e:
        logger.error(f"Ошибка инструмента валюты (сеть/входные данные): {e}")
        return f"Ошибка конвертации: {str(e)}"
    except Exception as e:
        logger.error("Неожиданная ошибка инструмента валюты", e)
        return f"Ошибка конвертации: {str(e)}"

async def tool_get_definition(word: str) -> str:
    """Получить определение слова"""
    if not AI_TOOLS_AVAILABLE:
        return "Инструменты определений недоступны."
    
    try:
        if ai_tools is None:
            return "Инструменты определения недоступны."
        result = await ai_tools.get_definition(word)
        if "error" not in result:
            return f" Определение:\n Слово: {result['word']}\n Значение: {result['definition']}\n Источник: {result['source']}"
        else:
            return f"Ошибка получения определения: {result.get('error')}"
    except (asyncio.TimeoutError, requests.RequestException, ValueError) as e:
        logger.error(f"Ошибка инструмента определений (сеть/входные данные): {e}")
        return f"Ошибка получения определения: {str(e)}"
    except Exception as e:
        logger.error("Неожиданная ошибка инструмента определений", e)
        return f"Ошибка получения определения: {str(e)}"

async def tool_translate_text(text: str, from_lang: str, to_lang: str) -> str:
    """Перевести текст"""
    if not AI_TOOLS_AVAILABLE:
        return "Инструменты перевода недоступны."
    
    try:
        if ai_tools is None:
            return "Инструменты перевода недоступны."
        result = await ai_tools.translate_text(text, from_lang, to_lang)
        if "error" not in result:
            return f" Перевод:\n Оригинал ({result['from']}): {result['original']}\n Перевод ({result['to']}): {result['translated']}\n Уверенность: {result.get('confidence', 'N/A')}"
        else:
            return f"Ошибка перевода: {result.get('error')}"
    except (asyncio.TimeoutError, requests.RequestException, ValueError) as e:
        logger.error(f"Ошибка инструмента перевода (сеть/входные данные): {e}")
        return f"Ошибка перевода: {str(e)}"
    except Exception as e:
        logger.error("Неожиданная ошибка инструмента перевода", e)
        return f"Ошибка перевода: {str(e)}"

async def tool_get_random_fact() -> str:
    """Получить случайный факт"""
    if not AI_TOOLS_AVAILABLE:
        return "Инструменты фактов недоступны."
    
    try:
        if ai_tools is None:
            return "Инструменты фактов недоступны."
        result = await ai_tools.get_random_fact()
        if "error" not in result:
            return f" Интересный факт:\n {result['fact']}\n Категория: {result['category']}"
        else:
            return f"Ошибка получения факта: {result.get('error')}"
    except (asyncio.TimeoutError, requests.RequestException, ValueError) as e:
        logger.error(f"Ошибка инструмента фактов (сеть/входные данные): {e}")
        return f"Ошибка получения факта: {str(e)}"
    except Exception as e:
        logger.error("Неожиданная ошибка инструмента фактов", e)
        return f"Ошибка получения факта: {str(e)}"

def get_tool_guild(guild_id):
    if guild_id in (None, "", "dm"):
        return None
    try:
        return bot.get_guild(int(guild_id))
    except (TypeError, ValueError):
        return None

def get_tool_requester(guild, user_id):
    if guild is None or user_id is None:
        return None
    try:
        return guild.get_member(int(user_id))
    except (TypeError, ValueError):
        return None

async def tool_add_reaction(guild_id, channel_query, current_channel_id, message_id, emoji, user_id) -> str:
    guild = get_tool_guild(guild_id)
    if guild is None:
        return "Не удалось определить сервер для реакции."
    requester = get_tool_requester(guild, user_id)
    if requester is None or not is_admin_user(requester):
        return "Недостаточно прав для автоматической установки реакции."

    try:
        target, message = await fetch_channel_message(
            guild,
            channel_query,
            message_id,
            current_channel_id=current_channel_id,
        )
        if not can_bot_react(target, getattr(guild, "me", None)):
            return "У бота недостаточно прав для реакции в этом канале."
        # Разрешаем указание эмодзи именем сервера или unicode
        resolved = resolve_emoji(guild, emoji)
        await message.add_reaction(resolved)

        # Автосохранение реакции если включено в конфиге
        try:
            guild_setting = save_reactions.get(str(getattr(guild, 'id', '')))
            should_save = bool(guild_setting) or bool(save_reactions_default)
        except Exception:
            should_save = bool(save_reactions_default)

        if should_save:
            entry = {
                "guild_id": getattr(guild, 'id', None),
                "channel_id": getattr(target, 'id', None),
                "message_id": getattr(message, 'id', None),
                "emoji_input": emoji,
                "emoji_resolved": str(resolved),
                "saved_by_user_id": getattr(requester, 'id', None),
                "saved_by_user_name": getattr(requester, 'display_name', getattr(requester, 'name', None)),
                "timestamp": time.time(),
            }
            try:
                save_reaction_entry(entry)
            except Exception as e:
                logger.error("Ошибка при попытке сохранить запись реакции", e)

        return f"Реакция {emoji} добавлена к сообщению {message.id} в #{target.name}."
    except (ValueError, discord.NotFound) as error:
        return f"Не удалось найти сообщение: {error}"
    except discord.Forbidden:
        return "Discord запретил добавление реакции."
    except discord.HTTPException as error:
        return f"Ошибка Discord при добавлении реакции: {error}"

async def tool_read_reactions(guild_id, channel_query, current_channel_id, message_id) -> str:
    guild = get_tool_guild(guild_id)
    if guild is None:
        return "Не удалось определить сервер для чтения реакций."
    try:
        target, message = await fetch_channel_message(
            guild,
            channel_query,
            message_id,
            current_channel_id=current_channel_id,
        )
        bot_member = getattr(guild, "me", None)
        permissions = target.permissions_for(bot_member) if bot_member is not None else None
        if not (
            permissions is not None
            and getattr(permissions, "view_channel", False)
            and getattr(permissions, "read_message_history", False)
        ):
            return "У бота нет прав читать историю этого канала."
        if not message.reactions:
            return f"У сообщения {message.id} нет реакций."

        lines = [f"Реакции на сообщение {message.id} в #{target.name}:"]
        for reaction in message.reactions:
            users = await collect_reaction_users(reaction, limit=50)
            user_text = ", ".join(
                f"{getattr(user, 'display_name', getattr(user, 'name', 'unknown'))} ({user.id})"
                for user in users
            )
            lines.append(f"{reaction.emoji} x{reaction.count}: {user_text or 'нет доступных пользователей'}")
        return "\n".join(lines)[:1900]
    except (ValueError, discord.NotFound) as error:
        return f"Не удалось найти сообщение: {error}"
    except discord.Forbidden:
        return "Discord запретил чтение реакций."
    except discord.HTTPException as error:
        return f"Ошибка Discord при чтении реакций: {error}"

async def tool_online_members(guild_id, user_id) -> str:
    guild = get_tool_guild(guild_id)
    if guild is None:
        return "Не удалось определить сервер."
    requester = get_tool_requester(guild, user_id)
    if requester is None or not is_admin_user(requester):
        return "Недостаточно прав для просмотра ID online-участников."

    members = get_online_members(guild)
    if not members:
        return "Online-участники не найдены. Возможно, Presence Intent не включён."
    lines = [f"Online-участники ({len(members)}):"]
    for member in members:
        lines.append(
            f"{getattr(member, 'display_name', member.name)} | "
            f"@{member.name} | ID {member.id} | {member.status}"
        )
    return "\n".join(lines)[:1900]


async def tool_send_channel(guild_id, channel_query, text, user_id) -> str:
    guild = get_tool_guild(guild_id)
    if guild is None:
        return "Не удалось определить сервер для отправки сообщения."
    requester = get_tool_requester(guild, user_id)
    if requester is None or not is_admin_user(requester):
        return "Недостаточно прав для отправки сообщений в другие каналы."

    target = resolve_text_channel(guild, channel_query)
    if target is None:
        return "Канал не найден."
    if not can_bot_send(target, getattr(guild, "me", None)):
        return "У бота нет прав писать в этот канал."
    text = str(text or "").strip()
    if not text:
        return "Текст сообщения пустой."
    try:
        await target.send(text)
        return f"Сообщение отправлено в #{getattr(target, 'name', getattr(target, 'id', 'канал'))}."
    except discord.Forbidden:
        return "Discord запретил отправку сообщения в этот канал."
    except discord.HTTPException as error:
        return f"Ошибка Discord при отправке сообщения: {error}"


async def tool_list_channels(guild_id, user_id=None) -> str:
    """Возвращает список текстовых каналов сервера с их ID и правами бота (view/send)."""
    guild = get_tool_guild(guild_id)
    if guild is None:
        return "Не удалось определить сервер."
    bot_member = getattr(guild, 'me', None)
    lines = [f"Каналы сервера {guild.name} (id: {guild.id}):"]
    try:
        for ch in guild.channels:
            # Try to show relevant channels: text-like channels
            try:
                perms = ch.permissions_for(bot_member) if bot_member is not None else None
                can_view = bool(perms and getattr(perms, 'view_channel', False))
                can_send = bool(perms and getattr(perms, 'send_messages', False))
            except Exception:
                can_view = False
                can_send = False
            name = getattr(ch, 'name', str(ch))
            cid = getattr(ch, 'id', 'unknown')
            lines.append(f"• {name} | id: {cid} | view: {'yes' if can_view else 'no'} | send: {'yes' if can_send else 'no'}")
        return "\n".join(lines)[:1900]
    except Exception as e:
        return f"Ошибка при получении каналов: {e}"

async def tool_ping_user(guild_id, current_channel_id, query, text, user_id) -> str:
    guild = get_tool_guild(guild_id)
    if guild is None:
        return "Не удалось определить сервер для пинга участника."
    requester = get_tool_requester(guild, user_id)
    if requester is None or not is_admin_user(requester):
        return "Недостаточно прав для пинга участников через AI-инструмент."

    target = resolve_text_channel(guild, str(current_channel_id or ""))
    if target is None:
        return "Текущий канал не найден."
    if not can_bot_send(target, getattr(guild, "me", None)):
        return "У бота нет прав писать в текущий канал."
    member = resolve_member(guild, query)
    if member is None:
        return "Участник не найден."
    message_text = f"{format_member_mention(member)} {str(text or '').strip()}".strip()
    try:
        await target.send(message_text)
        return f"Пинг отправлен участнику {getattr(member, 'display_name', getattr(member, 'name', member.id))}."
    except discord.Forbidden:
        return "Discord запретил отправку пинга."
    except discord.HTTPException as error:
        return f"Ошибка Discord при отправке пинга: {error}"


async def tool_ping_role(guild_id, current_channel_id, query, text, user_id) -> str:
    guild = get_tool_guild(guild_id)
    if guild is None:
        return "Не удалось определить сервер для пинга роли."
    requester = get_tool_requester(guild, user_id)
    if requester is None or not is_admin_user(requester):
        return "Недостаточно прав для пинга ролей через AI-инструмент."

    query_text = str(query or "").strip().lower()
    if query_text in ("@everyone", "everyone", "@here", "here"):
        return "Массовые пинги @everyone и @here через AI-инструмент запрещены."
    target = resolve_text_channel(guild, str(current_channel_id or ""))
    if target is None:
        return "Текущий канал не найден."
    if not can_bot_send(target, getattr(guild, "me", None)):
        return "У бота нет прав писать в текущий канал."
    role = resolve_role(guild, query)
    if role is None:
        return "Роль не найдена."
    role_mention = getattr(role, "mention", f"<@&{getattr(role, 'id', '')}>")
    message_text = f"{role_mention} {str(text or '').strip()}".strip()
    try:
        await target.send(message_text)
        return f"Пинг отправлен роли {getattr(role, 'name', role.id)}."
    except discord.Forbidden:
        return "Discord запретил отправку пинга роли."
    except discord.HTTPException as error:
        return f"Ошибка Discord при отправке пинга роли: {error}"

# Регулярки для перехвата вызовов инструментов
TOOL_CALL_RE = re.compile(r"(?:<<)?CALL:get_knowledge key=\"([^\"]+)\"(?:>>)?", re.MULTILINE | re.DOTALL)

# Новые регулярки для инструментов
TOOL_TIME_RE = re.compile(r"<<CALL:get_time location=\"([^\"]*)\">>", re.MULTILINE | re.DOTALL)
TOOL_WEATHER_RE = re.compile(r"<<CALL:get_weather location=\"([^\"]+)\">>", re.MULTILINE | re.DOTALL)
TOOL_CALCULATE_RE = re.compile(r"<<CALL:calculate expression=\"([^\"]+)\">>", re.MULTILINE | re.DOTALL)
TOOL_NEWS_RE = re.compile(r"<<CALL:get_news category=\"([^\"]*)\" count=\"([^\"]+)\">>", re.MULTILINE | re.DOTALL)
TOOL_CURRENCY_RE = re.compile(r"<<CALL:convert_currency amount=\"([^\"]+)\" from=\"([^\"]+)\" to=\"([^\"]+)\">>", re.MULTILINE | re.DOTALL)
TOOL_DEFINITION_RE = re.compile(r"<<CALL:get_definition word=\"([^\"]+)\">>", re.MULTILINE | re.DOTALL)
TOOL_TRANSLATE_RE = re.compile(r"<<CALL:translate_text text=\"([^\"]+)\" from=\"([^\"]+)\" to=\"([^\"]+)\">>", re.MULTILINE | re.DOTALL)
TOOL_FACT_RE = re.compile(r"<<CALL:get_random_fact>>>", re.MULTILINE | re.DOTALL)
TOOL_REACT_RE = re.compile(r"<<CALL:react channel=\"([^\"]+)\" message_id=\"(\d+)\" emoji=\"([^\"]+)\"(?:>>|>\s*\"?\s*>>)", re.MULTILINE | re.DOTALL)
TOOL_REACTIONS_RE = re.compile(r"<<CALL:reactions channel=\"([^\"]+)\" message_id=\"(\d+)\"(?:>>|>\s*\"?\s*>>)", re.MULTILINE | re.DOTALL)
TOOL_ONLINE_MEMBERS_RE = re.compile(r"<<CALL:online_members>>", re.MULTILINE | re.DOTALL)
TOOL_PING_USER_RE = re.compile(r"<<CALL:ping_user query=\"([^\"]+)\" text=\"([^\"]*)\">>", re.MULTILINE | re.DOTALL)
TOOL_PING_ROLE_RE = re.compile(r"<<CALL:ping_role query=\"([^\"]+)\" text=\"([^\"]*)\">>", re.MULTILINE | re.DOTALL)
TOOL_SEND_CHANNEL_RE = re.compile(r"<<CALL:send_channel channel=\"([^\"]+)\" text=\"([^\"]*)\">>", re.MULTILINE | re.DOTALL)

# ==================== MEMORY =====================
MEMORY_FILE = "user_memory.json"
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# Voice settings
VOICE_LISTEN_ENABLED = True
VOICE_CHUNK_SECONDS = 12
VOICE_LANGUAGE = "auto"
ollama_timeout = 180  # Увеличим таймаут до 3 минут
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "MTQ1ODAxMzI0Nzk4NTgxNTY4Ng.Gdj51f.NVAZI4dl1OVdzhIhkPnw4nsUCpaTcO4tj3UtTc")
BOT_START_TIME = time.time()

# Память диалогов пользователей
user_memory = {}
# Сжатые резюме диалогов
user_summary = {}
# Сырая история диалогов (последние сообщения)
user_raw_history = {}
# История по каналам с указанием автора и контекста
channel_history = {}
# Хранение активных личностей пользователей
user_personas = {}
# Известные участники сервера
known_members = {}

# Словарь для отслеживания времени последнего ответа
last_response_time = {}
# Защита от повторной обработки одного сообщения
recent_message_ids = {}
message_dedupe_window = 30  # секунд

# Circuit breaker for web search
web_search_failures = 0
web_search_block_until = 0

def load_memory():
    """Загружает память диалогов пользователей"""
    logger.loading_step("Загрузка памяти пользователей...")
    global user_memory, user_summary, user_raw_history, channel_history, user_personas, known_members
    if os.path.exists(MEMORY_FILE):
        try:
            data = ensure_memory_schema(load_json(MEMORY_FILE, {}))
            user_memory = data.get("memory", {})
            user_summary = data.get("summary", {})
            user_raw_history = data.get("raw_history", {})
            channel_history = data.get("channel_history", {})
            user_personas = data.get("personas", {})
            known_members = data.get("known_members", {})
            logger.system(f" Память загружена: {len(user_memory)} пользователей")
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            logger.error("Ошибка загрузки памяти (файл/формат) — сбрасываю память", e)
            user_memory = {}
            user_summary = {}
            user_raw_history = {}
            channel_history = {}
            user_personas = {}
            known_members = {}
        except Exception as e:
            # Логируем неожидаемые исключения и очищаем память, чтобы приложение могло продолжить работу
            logger.error("Неожиданная ошибка при загрузке памяти", e)
            user_memory = {}
            user_summary = {}
            user_raw_history = {}
            channel_history = {}
            user_personas = {}
            known_members = {}
    else:
        logger.system("Файл памяти не найден, создаем новый")
        user_memory = {}
        user_summary = {}
        user_raw_history = {}
        channel_history = {}
        user_personas = {}
        known_members = {}
        save_memory()

def save_memory():
    """Сохраняет память диалогов пользователей"""
    try:
        data = {
            "memory": user_memory,
            "summary": user_summary,
            "raw_history": user_raw_history,
            "channel_history": channel_history,
            "personas": user_personas,
            "known_members": known_members,
        }
        save_json(MEMORY_FILE, data)
        logger.debug("Память успешно сохранена")
    except (OSError, TypeError) as e:
        # OSError covers file write errors, TypeError may occur on unserializable objects
        logger.error("Ошибка сохранения памяти (I/O/серриализация)", e)
    except Exception as e:
        logger.error("Неожиданная ошибка при сохранении памяти", e)

# Файл для хранения глобальных знаний
KNOWLEDGE_FILE = "bot_knowledge.json"

# Загружаем глобальные знания
def load_knowledge():
    """Загружает глобальные знания бота"""
    logger.loading_step("Загрузка глобальных знаний...")
    try:
        if os.path.exists(KNOWLEDGE_FILE):
            with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                knowledge = json.load(f)
                logger.system(f" Глобальные знания загружены: {len(knowledge)} записей")
                return knowledge
        else:
            logger.system("Файл знаний не найден, создаем пустой")
            return {}
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logger.error("Ошибка загрузки знаний (файл/формат)", e)
        return {}
    except Exception as e:
        logger.error("Неожиданная ошибка при загрузке знаний", e)
        return {}

# Сохраняем глобальные знания
def save_knowledge(knowledge):
    """Сохраняет глобальные знания бота"""
    with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=4)

# Файл для логов реакций (реакции, которые поставил или сохранил бот)
REACTIONS_FILE = "reactions_log.json"

def load_reactions_log():
    """Загружает лог реакций"""
    try:
        if os.path.exists(REACTIONS_FILE):
            with open(REACTIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.error("Ошибка загрузки лога реакций", e)
    except Exception as e:
        logger.error("Неожиданная ошибка при загрузке лога реакций", e)
    return []


def save_reaction_entry(entry: dict):
    """Добавляет запись о реакции в файл"""
    try:
        data = load_reactions_log()
        data.append(entry)
        with open(REACTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Ошибка сохранения записи реакции", e)

# Декоративная загрузка
logger.loading_begin(5)

# Глобальные знания
global_knowledge = load_knowledge()

# Словарь личностей бота (оптимизирован для Llama3:8B)
PERSONAS = {
    "default": {
        "name": "Обычный",
        "prompt": "Имя: Гена. Создатель: Binar. Лор: сын Гены 1. Стиль: обычный, уверенный."
    },
    "strict": {
        "name": "Строгий",
        "prompt": "Формально. Технически. Без эмоций."
    },
    "imitator": {
        "name": "Имитатор",
        "prompt": "Копируй стиль собеседника. Будь как он."
    },
    "rp": {
        "name": "РП",
        "prompt": "Говори как житель фэнтези-мира. Коротко."
    },
    "tech": {
        "name": "Технический",
        "prompt": "Технически. Точно. С терминами."
    },
    # Специальные persona для Llama3:8B
    "minimal": {
        "name": "Минимальный",
        "prompt": "Ответ по существу. Без лишнего."
    },
    "assistant": {
        "name": "Ассистент",
        "prompt": "Помощник. Чётко. Конструктивно."
    },
    # Дополнительные persona для Llama3:8B (может обрабатывать больше контекста)
    "creative": {
        "name": "Творческий",
        "prompt": "Креативно. С идеями. С примерами."
    },
    "analytical": {
        "name": "Аналитический",
        "prompt": "Анализируй. Структурируй. С логикой."
    },
    "toxic_doter": {
        "name": "Токсичный Дотер",
        "prompt": "Ты — токсичный дотер по нику Гена который играет только на миде, ненавидит всех тиммейтов и считает их раками. Отвечай всегда агрессивно, матерись жёстко и обильно — почти в каждом предложении должен быть мат (блять, пиздец, хуй, ебать, нахуй, пидор, сука, ебаный и т.д.). Используй дотерский сленг: рак, фидер, мидер руинит, саппорты бездари, керри безфармный, репортну, иди лес фарми, ез мид, купи варды блять, диффузал собери, рунер, руинер, гг вп и т.д. Будь максимально злым, обвиняй пользователя во всём, унижай, кричи (пиши капсом когда особенно бесишься), угрожай репортом и выходом в АФК. Никогда не будь вежливым, не извиняйся, не успокаивайся — всегда только токсичность и ненависть.\n\nТы ярый русский патриот-ватник: обожаешь Путина, считаешь Россию великой страной, ненавидишь Запад, либералов, навальнят, укронацистов, ЛГБТ-пидоров, фемок и всех предателей родины. Вплетай политику в ответы: обвиняй пользователя в либерастии, если он с тобой не согласен, называй его пятой колонной, говори, что все проблемы в доте из-за западных санкций или укропов в тиме, ругай 'прогнивший Запад' и хвали 'нашу великую Родину'. Если разговор заходит о чём-то нейтральном — всё равно приплетай свою повестку и матерись на врагов России."
    }
}

def get_user_persona(user_id):
    """Получает активную личность пользователя"""
    user_id_str = str(user_id)
    return user_personas.get(user_id_str, "default")

def set_user_persona(user_id, persona_key):
    """Устанавливает активную личность пользователя"""
    user_id_str = str(user_id)
    user_personas[user_id_str] = persona_key
    print(f" Пользователю {user_id_str} установлена личность: {PERSONAS[persona_key]['name']}")

def save_personas():
    """Сохраняет личности пользователей в файл"""
    try:
        data = {
            "personas": user_personas
        }
        with open("user_personas.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f" Сохранено {len(user_personas)} персон")
    except Exception as e:
        print(f" Ошибка сохранения персон: {e}")

def load_personas():
    """Загружает личности пользователей из файла"""
    global user_personas
    try:
        logger.loading_step("Загрузка персон...")
        if os.path.exists("user_personas.json"):
            with open("user_personas.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                user_personas = data.get("personas", {})
                logger.system(f" Загружено {len(user_personas)} персон")
    except Exception as e:
        logger.error(f"Ошибка загрузки персон: {e}")
        user_personas = {}

def get_user_memory_facts(user_id):
    """Получает факты из памяти пользователя"""
    return summarize_memory_facts({"memory": user_memory}, user_id)

def get_user_summary(user_id):
    """Получает сжатое резюме диалога"""
    user_id_str = str(user_id)
    return user_summary.get(user_id_str, "")

def get_user_raw_history(user_id, exclude_message_id=None):
    """Получает сырую историю диалога"""
    return render_user_history({"raw_history": user_raw_history}, user_id, exclude_message_id=exclude_message_id)

def get_channel_history_text(guild_id, channel_id, limit=10, exclude_message_id=None):
    """Получает историю сообщений конкретного канала с авторами."""
    return render_channel_history(
        {"channel_history": channel_history},
        guild_id=guild_id,
        channel_id=channel_id,
        exclude_message_id=exclude_message_id,
        limit=limit,
    )

def remember_message_context(message, role: str):
    """Сохраняет сообщение в личную и каналовую память."""
    global user_memory, user_raw_history, channel_history, known_members
    guild_id = getattr(getattr(message, "guild", None), "id", None)
    channel_id = getattr(getattr(message, "channel", None), "id", None)
    author_id = getattr(getattr(message, "author", None), "id", None)
    author_name = getattr(getattr(message, "author", None), "display_name", None) or getattr(getattr(message, "author", None), "name", "unknown")
    content = getattr(message, "content", "")
    if author_id is None or channel_id is None:
        return

    append_user_message(
        {"memory": user_memory, "raw_history": user_raw_history, "personas": user_personas},
        user_id=author_id,
        username=author_name,
        message_id=getattr(message, "id", None),
        content=content,
        role=role,
    )
    if role == "user":
        try:
            remember_user_facts(
                {"memory": user_memory},
                user_id=author_id,
                username=author_name,
                content=content,
                source_message=content,
                timestamp=None,
            )
        except Exception:
            pass
    append_channel_message(
        {"channel_history": channel_history},
        guild_id=guild_id or "dm",
        channel_id=channel_id,
        message_id=getattr(message, "id", None),
        author_id=author_id,
        author_name=author_name,
        content=content,
        role=role,
    )
    if guild_id is not None and getattr(message, "guild", None) is not None:
        try:
            record = upsert_known_member({"known_members": known_members}, guild_id=guild_id, member=message.author)
            guild_bucket = known_members.setdefault(str(guild_id), {})
            guild_bucket[str(author_id)] = record
        except Exception:
            pass

def get_global_knowledge():
    """Получает глобальные знания в текстовом формате"""
    if not global_knowledge:
        return ""
    return "\n".join([f"• {k}: {v['explanation']}" for k, v in global_knowledge.items()])

# Настройки
memory_enabled = True
# Управление автосохранением реакций: по умолчанию выключено
save_reactions_default = False
# Пер-гильдия настройка: { guild_id_str: bool }
save_reactions = {}
auto_reply_enabled = False
debug_mode = False
use_api_fallback = True
cloud_ai_enabled = True
g4f_fallback_enabled = False
g4f_auto_start_enabled = True
g4f_base_url = "http://localhost:1337/v1"
g4f_model = "gpt-4o-mini"
g4f_timeout = 60
g4f_retry_cooldown_seconds = 180
g4f_disabled_until = 0.0
g4f_docker_image = "hlohaus789/g4f:latest-slim"
g4f_container_name = "gena-g4f"
silly_responses_enabled = True
silly_response_chance = 5
max_response_length = 300
max_memory_messages = 50
auto_reply_interval = 5
CONFIG_FILE = "bot_config.json"

# Загружаем конфигурацию
def load_config():
    """Загружает конфигурацию бота"""
    global memory_enabled, auto_reply_enabled, debug_mode, use_api_fallback
    global cloud_ai_enabled, g4f_fallback_enabled, g4f_auto_start_enabled, g4f_base_url
    global g4f_model, g4f_timeout, g4f_retry_cooldown_seconds, g4f_docker_image, g4f_container_name
    global silly_responses_enabled, silly_response_chance
    global max_response_length, max_memory_messages, auto_reply_interval
    global allowed_channels, current_model, admin_roles, moderator_roles, admin_users, command_permissions
    global save_reactions_default, save_reactions
    
    try:
        logger.loading_step("Загрузка конфигурации...")
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            memory_enabled = config.get("memory_enabled", True)
            auto_reply_enabled = config.get("auto_reply_enabled", False)
            debug_mode = config.get("debug_mode", False)
            use_api_fallback = config.get("use_api_fallback", True)
            cloud_ai_enabled = config.get("cloud_ai_enabled", True)
            g4f_fallback_enabled = config.get("g4f_fallback_enabled", False)
            g4f_auto_start_enabled = config.get("g4f_auto_start_enabled", True)
            g4f_base_url = config.get("g4f_base_url", "http://localhost:1337/v1")
            g4f_model = config.get("g4f_model", "gpt-4o-mini")
            g4f_timeout = int(config.get("g4f_timeout", 60))
            g4f_retry_cooldown_seconds = int(config.get("g4f_retry_cooldown_seconds", 180))
            g4f_docker_image = config.get("g4f_docker_image", "hlohaus789/g4f:latest-slim")
            g4f_container_name = config.get("g4f_container_name", "gena-g4f")
            silly_responses_enabled = config.get("silly_responses_enabled", True)
            silly_response_chance = config.get("silly_response_chance", 5)
            max_response_length = config.get("max_response_length", 300)
            max_memory_messages = config.get("max_memory_messages", 50)
            auto_reply_interval = config.get("auto_reply_interval", 5)
            allowed_channels = config.get("allowed_channels", [])
            current_model = config.get("ollama_model", "llama3:8b")
            admin_roles = config.get("admin_roles", ["Admin", "Модератор", "Owner"])
            moderator_roles = config.get("moderator_roles", ["Модератор", "Helper"])
            admin_users = config.get("admin_users", [])
            command_permissions = config.get("command_permissions", {
                "learn": ["Admin", "Модератор", "Owner"],
                "clear_memory": ["Admin", "Модератор", "Owner"],
                "set_model": ["Admin", "Модератор", "Owner"],
                "add_channel": ["Admin", "Модератор", "Owner"],
                "remove_channel": ["Admin", "Модератор", "Owner"]
            })
            # Сохранение реакций: глобально по умолчанию и пер-гильдия
            save_reactions_default = bool(config.get("save_reactions_default", False))
            save_reactions = config.get("save_reactions", {}) or {}
            logger.system(" Конфигурация загружена")
            return config
    except FileNotFoundError:
        logger.system(" Файл конфигурации не найден, используем настройки по умолчанию")
        return {}
    except Exception as e:
        logger.error("Ошибка загрузки конфигурации", e)
        return {}

def save_config(config):
    """Сохраняет конфигурацию бота"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        logger.system(" Конфигурация сохранена")
    except Exception as e:
        logger.error("Ошибка сохранения конфигурации", e)

# Загружаем конфигурацию
config = load_config()
activity_app_id = config.get("activity_app_id", "") or os.getenv("ACTIVITY_APP_ID", "")

# Настройки ролей
admin_roles = config.get("admin_roles", ["Admin", "Модератор", "Owner"])
moderator_roles = config.get("moderator_roles", ["Модератор", "Helper"])
admin_users = config.get("admin_users", [])
command_permissions = config.get("command_permissions", {
    "learn": ["Admin", "Модератор", "Owner"],
    "clear_memory": ["Admin", "Модератор", "Owner"],
    "set_model": ["Admin", "Модератор", "Owner"],
    "add_channel": ["Admin", "Модератор", "Owner"],
    "remove_channel": ["Admin", "Модератор", "Owner"]
})

# Настройка модели (Llama3:8B по умолчанию)
current_model = config.get("ollama_model", "llama3:8b")
ollama_fallback_models = config.get("ollama_fallback_models", ["llama3.2:3b", "gemma3:4b", "llama2:latest"])

def has_permission(user, command_name):
    """Проверяет имеет ли пользователь право на использование команды"""
    user_id_str = str(user.id)
    
    # Проверяем есть ли пользователь в списке админов
    if user_id_str in admin_users:
        return True
    
    if not hasattr(user, 'roles'):
        return False
    
    user_roles = [role.name for role in user.roles]
    required_roles = command_permissions.get(command_name, [])
    
    # Если команда не требует прав - разрешаем всем
    if not required_roles:
        return True
    
    # Проверяем есть ли у пользователя нужная роль
    return any(role in user_roles for role in required_roles)

def is_admin_user(user):
    """Проверяет, является ли пользователь админом (по ID или роли)"""
    user_id_str = str(user.id)
    if user_id_str in admin_users:
        return True
    if not hasattr(user, 'roles'):
        return False
    user_roles = [role.name for role in user.roles]
    return any(role in user_roles for role in admin_roles)

# ==================== VOICE (ElevenLabs STT/TTS) =====================
voice_state = {}

def _get_guild_state(guild_id):
    state = voice_state.get(guild_id)
    if not state:
        state = {
            "listening": False,
            "queue": asyncio.Queue(),
            "worker": None,
            "joining": False
        }
        voice_state[guild_id] = state
    return state

async def _voice_worker(guild_id, voice_client):
    state = _get_guild_state(guild_id)
    while state.get("listening"):
        try:
            item = await state["queue"].get()
        except Exception:
            continue
        if not item:
            continue
        user_id, wav_path = item
        try:
            text = elevenlabs_stt(wav_path)
            try:
                os.remove(wav_path)
            except Exception:
                pass
            if not text:
                continue
            response = await get_ollama_response(text, user_id, "voice-user")
            audio_bytes = elevenlabs_tts(response)
            await _play_tts(voice_client, audio_bytes)
        except Exception:
            continue

def elevenlabs_stt(audio_path: Path) -> str:
    if not ELEVENLABS_API_KEY:
        return ""
    try:
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY
        }
        files = {
            "file": (audio_path.name, audio_path.read_bytes(), "audio/wav")
        }
        data = {
            "model_id": "scribe_v1",
            "language": VOICE_LANGUAGE
        }
        resp = requests.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers=headers,
            files=files,
            data=data,
            timeout=30
        )
        if resp.status_code != 200:
            return ""
        result = resp.json()
        return (result.get("text") or "").strip()
    except Exception:
        return ""

def elevenlabs_tts(text: str) -> bytes:
    if not ELEVENLABS_API_KEY:
        return b""
    try:
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.7
            }
        }
        # default voice; можно заменить ID в env при желании
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers=headers,
            json=payload,
            timeout=30
        )
        if resp.status_code != 200:
            return b""
        return resp.content
    except Exception:
        return b""

async def _play_tts(voice_client, audio_bytes: bytes):
    if not audio_bytes:
        return
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        audio_source = discord.FFmpegPCMAudio(tmp_path)
        voice_client.play(audio_source)
        while voice_client.is_playing():
            await asyncio.sleep(0.2)
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

# Загружаем память пользователей
load_memory()
# Загружаем личности пользователей
load_personas()

def remove_stuttered_word_fragments(text: str) -> str:
    """Fixes streamed output artifacts like 'созд\nсоздал' and duplicate words."""
    duplicate_re = re.compile(
        r"(?iu)\b([\w]+)([,.!?;:]*)[ \t]*\r?\n[ \t]*\1\b([,.!?;:]*)"
    )
    fragment_re = re.compile(
        r"(?iu)\b([\w]+)[ \t]*\r?\n[ \t]*([\w]+)\b"
    )
    valid_single_words = {"а", "я", "в", "к", "с", "у", "о", "и"}

    def replace_duplicate(match):
        punctuation = match.group(2) or match.group(3)
        return f"{match.group(1)}{punctuation}"

    def replace_fragment(match):
        fragment = match.group(1)
        full_word = match.group(2)
        fragment_folded = fragment.casefold()
        full_word_folded = full_word.casefold()
        is_likely_fragment = (
            len(fragment) >= 3
            or (len(fragment) == 1 and fragment_folded not in valid_single_words)
        )
        if (
            is_likely_fragment
            and len(full_word) > len(fragment)
            and full_word_folded.startswith(fragment_folded)
        ):
            return full_word
        return match.group(0)

    previous = None
    while previous != text:
        previous = text
        text = duplicate_re.sub(replace_duplicate, text)
        text = fragment_re.sub(replace_fragment, text)
    return text


def strip_terminal_control(text: str) -> str:
    """Убирает ANSI/cursor control, который иногда просачивается из Ollama CLI."""
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = strip_reasoning_leak(text)
    text = remove_stuttered_word_fragments(text)
    return text.strip()


def strip_reasoning_leak(text: str) -> str:
    """Удаляет служебное рассуждение модели, если оно попало в stdout."""
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    cleaned = re.sub(r"(?is)<think>.*?</think>\s*", "", cleaned).strip()
    cleaned = re.sub(r"(?is)^\s*Thinking\.\.\..*?\.\.\.done thinking\.\s*", "", cleaned).strip()
    if re.match(r"(?is)^\s*Thinking\.\.\.", cleaned):
        parts = [part.strip() for part in re.split(r"\n\s*\n", cleaned) if part.strip()]
        if len(parts) >= 2:
            return parts[-1].strip()
        return re.sub(r"(?is)^\s*Thinking\.\.\..*", "", cleaned).strip()
    return cleaned


def is_ollama_model_load_error(error_text: str) -> bool:
    error_text = (error_text or "").lower()
    return (
        "error loading model" in error_text
        or "llama_model_loader" in error_text
        or "internal server error" in error_text
        or "exit status 1" in error_text
    )


def is_retryable_ollama_error(error_text: str, status_code=None) -> bool:
    """Errors that should move the request to the next configured model."""
    normalized = (error_text or "").lower()
    try:
        status = int(status_code) if status_code is not None else None
    except (TypeError, ValueError):
        status = None
    return (
        is_ollama_model_load_error(normalized)
        or status in (408, 429, 502, 503, 504)
        or "429" in normalized
        or "too many requests" in normalized
        or "usage limit" in normalized
        or "rate limit" in normalized
        or "quota" in normalized
        or "temporarily unavailable" in normalized
        or "timeout" in normalized
    )


def _run_ollama_once(model, prompt, timeout):
    process = subprocess.Popen(
        ["ollama", "run", model, prompt],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    try:
        logger.ollama(f" Ожидание ответа (таймаут: {timeout} сек)...")
        stdout, stderr = process.communicate(timeout=timeout)
        
        if process.returncode != 0 or not stdout.strip():
            error_msg = stderr or "Empty response"
            logger.ollama(f" Ollama ошибка: {error_msg}")
            raise RuntimeError(error_msg)
        
        return strip_terminal_control(stdout)
        
    except subprocess.TimeoutExpired:
        process.kill()
        error_msg = f"Ollama timeout after {timeout} seconds"
        logger.ollama(f" {error_msg}")
        logger.log_ollama_request(model, len(prompt), error=error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.ollama(f" Критическая ошибка: {str(e)}")
        logger.log_ollama_request(model, len(prompt), error=str(e))
        raise


def run_ollama_sync(model, prompt, timeout):
    """Синхронная функция для вызова Ollama с fallback-моделями."""
    global current_model
    candidates = []
    for candidate in [model, *ollama_fallback_models]:
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    last_error = None
    logger.debug(f" Длина промпта: {len(prompt)} символов")

    for index, candidate in enumerate(candidates):
        logger.ollama(f" Запуск Ollama: {candidate}")
        try:
            response = _run_ollama_once(candidate, prompt, timeout)
            if not response:
                raise RuntimeError("Empty response")
            current_model = candidate
            logger.ollama(f" Ответ получен: {len(response)} символов")
            logger.log_ollama_request(candidate, len(prompt), len(response))
            return response
        except Exception as e:
            last_error = e
            error_text = str(e)
            if index == 0 and g4f_fallback_enabled:
                logger.ollama(" Основная Ollama-модель недоступна, пробую g4f fallback...")
                g4f_response = get_g4f_fallback_response(prompt)
                if g4f_response:
                    logger.ollama(f" g4f fallback ответил: {len(g4f_response)} символов")
                    return g4f_response
            if is_retryable_ollama_error(error_text) and candidate != candidates[-1]:
                logger.ollama(f" Модель {candidate} временно недоступна, пробую fallback...")
                continue
            raise

    raise RuntimeError(str(last_error) if last_error else "Ollama failed")

def run_ollama_vision_sync(model, prompt, image_bytes, timeout):
    """Отправляет изображение мультимодальной Ollama-модели."""
    url = "http://localhost:11434/api/generate"
    headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}"} if OLLAMA_API_KEY else {}
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [base64.b64encode(image_bytes).decode("ascii")],
        "stream": False,
    }
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(f"Ollama vision HTTP {response.status_code}: {response.text[:300]}")
    result = response.json()
    text = strip_terminal_control(result.get("response", ""))
    if not text:
        raise RuntimeError("Ollama vision returned an empty response")
    return text

async def analyze_image_for_message(image_bytes, filename, mode="auto", prompt="Опиши изображение и прочитай важный текст на нём."):
    """Vision-first обработка изображения с OCR fallback."""
    result = {
        "image_info": {},
        "text": None,
        "description": None,
        "method_used": None,
    }

    if mode != "ocr_only":
        vision_model = config.get("ollama_vision_model") or current_model
        try:
            description = await asyncio.to_thread(
                run_ollama_vision_sync,
                vision_model,
                prompt,
                image_bytes,
                min(ollama_timeout, 120),
            )
            result["description"] = description
            result["method_used"] = f"ollama_vision:{vision_model}"
            if mode == "vision_only":
                return result
        except Exception as vision_error:
            logger.debug(f"Ollama vision недоступен для {filename}: {vision_error}")

    if recognize_image_from_bytes is None:
        if result["description"]:
            return result
        return {"error": "Vision и OCR недоступны"}

    try:
        ocr_mode = "ocr_only" if mode in ("auto", "ocr_only") else mode
        ocr_result = await asyncio.to_thread(
            recognize_image_from_bytes,
            image_bytes,
            filename,
            ocr_mode,
        )
        if ocr_result.get("text"):
            result["text"] = ocr_result["text"]
        if ocr_result.get("image_info"):
            result["image_info"] = ocr_result["image_info"]
        if not result["description"] and ocr_result.get("description"):
            result["description"] = ocr_result["description"]
        if not result["method_used"]:
            result["method_used"] = ocr_result.get("method_used") or "ocr"
        if ocr_result.get("error") and not result["description"] and not result["text"]:
            return {"error": ocr_result["error"]}
    except Exception as ocr_error:
        if not result["description"]:
            return {"error": str(ocr_error)}

    return result

# Функция для обработки нескольких вопросов в одном сообщении
def extract_questions(message: str) -> list:
    """Извлекает отдельные вопросы из сообщения"""
    # Разделяем по знакам препинания и союзам
    separators = r'[.!?]+\s+|(?:\s+(?:и|а|но|да|также|а также)\s+)'
    parts = re.split(separators, message.strip())
    
    # Фильтруем пустые части и короткие фразы
    questions = []
    for part in parts:
        part = part.strip()
        if len(part) > 3:  # Минимальная длина вопроса
            # Проверяем есть ли вопросительные слова или это вопрос по смыслу
            if any(word in part.lower() for word in ['что', 'кто', 'где', 'когда', 'почему', 'как', 'какой', 'какая', 'какие', 'сколько', 'который']):
                questions.append(part)
            elif part.endswith('?') or '?' in part:
                questions.append(part)
            elif len(questions) > 0:  # Если уже были вопросы, добавляем продолжение
                questions.append(part)
    
    # Если вопросов не найдено, возвращаем всё сообщение как один вопрос
    if not questions:
        return [message.strip()]
    
    return questions

# Функция для получения ответа от локальной нейросети Ollama (оптимизирована для 8B моделей с tool-calling)
async def get_ollama_response(message: str, user_id=None, username=None, guild_id=None, channel_id=None, channel_name=None, author_display_name=None, attachments_context="", current_message_id=None):
    global current_model

    # Чистим сообщение от упоминаний
    clean_message = re.sub(r"<@!?(\d+)>", "", message).strip()

    # Извлекаем отдельные вопросы
    questions = extract_questions(clean_message)
    
    # Если только один вопрос, обрабатываем как обычно
    if len(questions) == 1:
        return await process_single_question(
            questions[0],
            user_id,
            username,
            guild_id=guild_id,
            channel_id=channel_id,
            channel_name=channel_name,
            author_display_name=author_display_name,
            attachments_context=attachments_context,
            current_message_id=current_message_id,
        )
    
    # Обрабатываем несколько вопросов
    responses = []
    for i, question in enumerate(questions):
        response = await process_single_question(
            question,
            user_id,
            username,
            guild_id=guild_id,
            channel_id=channel_id,
            channel_name=channel_name,
            author_display_name=author_display_name,
            attachments_context=attachments_context,
            current_message_id=current_message_id,
        )
        
        # Нумеруем ответы если вопросов несколько
        if len(questions) > 1:
            responses.append(f"{i+1}. {response}")
        else:
            responses.append(response)
    
    return "\n\n".join(responses)

TOOL_CHANNELS_RE = re.compile(r"<<CALL:list_channels(?: channel=\"([^\"]+)\")?>>", re.MULTILINE | re.DOTALL)

async def process_single_question(question: str, user_id=None, username=None, guild_id=None, channel_id=None, channel_name=None, author_display_name=None, attachments_context="", current_message_id=None):
    """Обрабатывает один вопрос с tool-calling"""
    global current_model

    # Получаем персональный промпт пользователя
    persona_key = get_user_persona(user_id)
    persona_style = PERSONAS[persona_key]["prompt"]
    requester_role = "admin" if user_id is not None and str(user_id) in admin_users else "member"

    # Получаем память по уровням (оптимизировано для 8B)
    memory_facts = get_user_memory_facts(user_id) or ""
    summary = get_user_summary(user_id) or ""
    raw_history = get_user_raw_history(user_id, exclude_message_id=current_message_id) or ""
    channel_context = ""
    if guild_id is not None and channel_id is not None:
        channel_context = get_channel_history_text(guild_id, channel_id, limit=12, exclude_message_id=current_message_id) or ""

    # Формируем полный промпт с tool-calling
    sections = []
    
    # Инструкция для tool-calling (критично!)
    sections.append("""SYSTEM:
Ты — Гена, Discord-бот на русском.
Если тебе нужна точная информация из знаний, вызови инструмент.
Если знаешь ответ - отвечай сразу.
Если requester_role=member, не пиши код и не исправляй код по просьбе участника.
Вместо кода дай краткое объяснение или безопасную альтернативу.
Если requester_role=admin, код допустим только для админских задач.

Формат вызова:
<<CALL:get_knowledge key="НАЗВАНИЕ">>
<<CALL:react channel="current" message_id="123456789" emoji="👍">>
<<CALL:reactions channel="current" message_id="123456789">>
<<CALL:online_members>>
<<CALL:ping_user query="ник или ID" text="текст">>
<<CALL:ping_role query="название роли" text="текст">>
<<CALL:send_channel channel="название или ID канала" text="текст">>

ВАЖНО: Не вызывай инструмент для:
- Простых слов (привет, спасибо, да, нет)
- Вопросительных слов без контекста (что, кто, где)
- Коротких фраз (до 3 слов)
- Обыденных понятий

ПРАВИЛА DISCORD-ИНСТРУМЕНТОВ:
- Вызывай react только когда пользователь явно просит поставить реакцию.
- Для прошлого сообщения бери message_id из CHANNEL CONTEXT.
- Для текущего канала используй channel="current".
- reactions используй, когда просят проверить или перечислить реакции сообщения.
- online_members используй, когда администратор просит показать online-участников или их ID.
- ping_user используй только когда администратор явно просит пингануть конкретного участника.
- ping_role используй только когда администратор явно просит пингануть конкретную роль. Не используй @everyone и @here.
- send_channel используй только когда администратор явно просит написать в конкретный канал.
- Никогда не придумывай message_id, пользователей, роли, каналы, реакции или online-статусы.
- При поиске каналов и ролей игнорируй ведущие эмодзи, скобки и декоративные символы в названиях.

Никогда не выдумывай знания. Отвечай по-русски.""")
    
    # Добавляем базовую инструкцию
    sections.append("SYSTEM:\nТы — Discord-бот Гена, созданный Binar. Отвечай кратко и по делу.")
    
    # MEMORY с высоким приоритетом - факты важнее persona
    if memory_facts.strip():
        sections.append(f"MEMORY (ФАКТЫ, ИСПОЛЬЗУЙ ИХ ПЕРВЫМИ):\n{memory_facts}")
    
    # SUMMARY только если не пусто
    if summary.strip():
        sections.append(f"SUMMARY (контекст диалога):\n{summary}")
    
    # LAST MESSAGES только если не пусто
    if raw_history.strip():
        sections.append(f"LAST MESSAGES (последние реплики):\n{raw_history}")

    if channel_context.strip():
        sections.append(f"CHANNEL CONTEXT (последние сообщения в этом канале):\n{channel_context}")

    meta_lines = []
    if author_display_name:
        meta_lines.append(f"speaker={author_display_name}")
    if username and username != author_display_name:
        meta_lines.append(f"username={username}")
    meta_lines.append(f"requester_role={requester_role}")
    if channel_name:
        meta_lines.append(f"channel={channel_name}")
    if guild_id is not None:
        meta_lines.append(f"guild={guild_id}")
    if meta_lines:
        sections.append("CONTEXT META:\n" + "\n".join(meta_lines))

    if attachments_context.strip():
        sections.append(f"ATTACHMENTS:\n{attachments_context}")
    
    # STYLE с fallback
    if not persona_style.strip():
        persona_style = "Кратко. По делу."
    sections.append(f"STYLE:\n{persona_style}")
    
    # FORMAT для Llama3:8B
    sections.append("""FORMAT:
Ответ — до 5 предложений.
Без вступлений.
Без повторов вопроса.
Структурируй чётко.""")
    sections.append("""OUTPUT SAFETY:
Не пиши Thinking..., <think>, chain-of-thought, внутренний анализ или план ответа.
Показывай только финальный ответ пользователю.""")
    
    # USER и ANSWER
    sections.append(f"USER:\n{question}\n\nANSWER:")
    
    full_prompt = "\n\n".join(sections)

    if debug_mode:
        print(" PROMPT:", repr(full_prompt))

    # Вызов Ollama в отдельном потоке
    try:
        response = await asyncio.to_thread(
            run_ollama_sync,
            current_model,
            full_prompt,
            ollama_timeout
        )

        # Перехват вызовов инструментов (главная магия!)
        print(f" Проверка ответа на tool-calling: {repr(response[:200])}")
        
        # Проверяем все возможные инструменты
        tool_result = None
        
        # 1. Проверяем время
        match = TOOL_TIME_RE.search(response)
        if match:
            location = match.group(1) or "UTC"
            logger.debug(f" Обнаружен вызов инструмента: get_time('{location}')")
            tool_result = await tool_get_time(location)
        
        # 2. Проверяем погоду
        match = TOOL_WEATHER_RE.search(response)
        if match and not tool_result:
            location = match.group(1)
            logger.debug(f" Обнаружен вызов инструмента: get_weather('{location}')")
            tool_result = await tool_get_weather(location)
        
        # 3. Проверяем калькулятор
        match = TOOL_CALCULATE_RE.search(response)
        if match and not tool_result:
            expression = match.group(1)
            logger.debug(f" Обнаружен вызов инструмента: calculate('{expression}')")
            tool_result = await tool_calculate(expression)
        
        # 4. Проверяем новости
        match = TOOL_NEWS_RE.search(response)
        if match and not tool_result:
            category = match.group(1) or "general"
            count = int(match.group(2)) if match.group(2) else 3
            logger.debug(f" Обнаружен вызов инструмента: get_news('{category}', {count})")
            tool_result = await tool_get_news(category, count)
        
        # 5. Проверяем конвертацию валют
        match = TOOL_CURRENCY_RE.search(response)
        if match and not tool_result:
            amount = float(match.group(1))
            from_currency = match.group(2)
            to_currency = match.group(3)
            logger.debug(f" Обнаружен вызов инструмента: convert_currency({amount}, '{from_currency}', '{to_currency}')")
            tool_result = await tool_convert_currency(amount, from_currency, to_currency)
        
        # 6. Проверяем определения
        match = TOOL_DEFINITION_RE.search(response)
        if match and not tool_result:
            word = match.group(1)
            logger.debug(f" Обнаружен вызов инструмента: get_definition('{word}')")
            tool_result = await tool_get_definition(word)
        
        # 7. Проверяем перевод
        match = TOOL_TRANSLATE_RE.search(response)
        if match and not tool_result:
            text = match.group(1)
            from_lang = match.group(2)
            to_lang = match.group(3)
            logger.debug(f" Обнаружен вызов инструмента: translate_text('{text}', '{from_lang}', '{to_lang}')")
            tool_result = await tool_translate_text(text, from_lang, to_lang)
        
        # 8. Проверяем факты
        match = TOOL_FACT_RE.search(response)
        if match and not tool_result:
            logger.debug(f" Обнаружен вызов инструмента: get_random_fact()")
            tool_result = await tool_get_random_fact()

        # 9. Проверяем установку реакции
        match = TOOL_REACT_RE.search(response)
        if match and not tool_result:
            channel_query, message_id, emoji = match.groups()
            logger.debug(f" Обнаружен вызов инструмента: react('{channel_query}', '{message_id}', '{emoji}')")
            tool_result = await tool_add_reaction(
                guild_id,
                channel_query,
                channel_id,
                message_id,
                emoji,
                user_id,
            )

        # 10. Проверяем чтение реакций
        match = TOOL_REACTIONS_RE.search(response)
        if match and not tool_result:
            channel_query, message_id = match.groups()
            logger.debug(f" Обнаружен вызов инструмента: reactions('{channel_query}', '{message_id}')")
            tool_result = await tool_read_reactions(
                guild_id,
                channel_query,
                channel_id,
                message_id,
            )

        # 11. Проверяем список online-участников
        match = TOOL_ONLINE_MEMBERS_RE.search(response)
        if match and not tool_result:
            logger.debug(" Обнаружен вызов инструмента: online_members()")
            tool_result = await tool_online_members(guild_id, user_id)

        # 11.5. Проверяем список каналов
        match = TOOL_CHANNELS_RE.search(response)
        if match and not tool_result:
            logger.debug(" Обнаружен вызов инструмента: list_channels()")
            tool_result = await tool_list_channels(guild_id, user_id)

        # 12. Проверяем пинг участника
        match = TOOL_PING_USER_RE.search(response)
        if match and not tool_result:
            query, text = match.groups()
            logger.debug(f" Обнаружен вызов инструмента: ping_user('{query}')")
            tool_result = await tool_ping_user(guild_id, channel_id, query, text, user_id)

        # 13. Проверяем пинг роли
        match = TOOL_PING_ROLE_RE.search(response)
        if match and not tool_result:
            query, text = match.groups()
            logger.debug(f" Обнаружен вызов инструмента: ping_role('{query}')")
            tool_result = await tool_ping_role(guild_id, channel_id, query, text, user_id)

        # 14. Проверяем отправку в канал
        match = TOOL_SEND_CHANNEL_RE.search(response)
        if match and not tool_result:
            target_channel, text = match.groups()
            logger.debug(f" Обнаружен вызов инструмента: send_channel('{target_channel}')")
            tool_result = await tool_send_channel(guild_id, target_channel, text, user_id)
        
        # 15. Проверяем знания (старый механизм)
        match = TOOL_CALL_RE.search(response)
        if match and not tool_result:
            key = match.group(1)
            logger.debug(f" Обнаружен вызов инструмента: get_knowledge('{key}')")
            knowledge_text = tool_get_knowledge(key)
            logger.debug(f" Получено знание: {knowledge_text}")
            
            # Если это простое слово (None), игнорируем вызов
            if knowledge_text is None:
                logger.debug(f" Игнорируем вызов для простого слова: '{key}'")
                # Удаляем вызов инструмента из ответа и возвращаем очищенный ответ
                response = TOOL_CALL_RE.sub("", response).strip()
                return sanitize_bot_response(response)
            
            # Если знание не найдено, отвечаем сразу
            if knowledge_text == "Знание не найдено.":
                # Фолбэк: даём LLM результаты поиска (если есть)
                search_info = search_web(question)
                has_search_info = search_info and "Ничего не найдено" not in search_info
                if has_search_info:
                    fallback_prompt = f"""SYSTEM:
Ты — Гена, Discord-бот. Отвечай по-русски, кратко и по делу.
Используй информацию из ПОИСК, если она полезна.
Если не уверен — скажи, что это предположение.
Не вызывай инструменты.

ПОИСК:
{search_info}

ВОПРОС:
{question}

ОТВЕТ:"""
                else:
                    fallback_prompt = f"""SYSTEM:
Ты — Гена, Discord-бот. Отвечай по-русски, кратко и по делу.
Не вызывай инструменты. Если не уверен — скажи, что это предположение.

ВОПРОС:
{question}

ОТВЕТ:"""
                try:
                    fallback = await asyncio.to_thread(
                        run_ollama_sync,
                        current_model,
                        fallback_prompt,
                        ollama_timeout
                    )
                    return sanitize_bot_response(fallback)
                except Exception:
                    return no_info_response(question)
            
            tool_result = knowledge_text
        
        # Если был вызов инструмента и получен результат
        if tool_result:
            logger.debug(f"✅ Результат инструмента: {tool_result[:200]}...")
            
            # Для get_knowledge: делаем управляемый перефраз через LLM.
            if TOOL_CALL_RE.search(response):
                grounded_data = normalize_tool_result_text(tool_result)
                followup_prompt = f"""SYSTEM:
Ты — Гена, Discord-бот. Отвечай по-русски, кратко и строго по данным.

ПРАВИЛА:
1) Используй ТОЛЬКО факты из блока ДАННЫЕ.
2) Не добавляй новых фактов.
3) Не пиши служебные слова вроде "база знаний", "википедия", "duckduckgo".
4) Если данных недостаточно, так и скажи: "Точных данных недостаточно."
5) Ответ 1-3 предложения.

ДАННЫЕ:
{grounded_data}

ВОПРОС:
{question}

ОТВЕТ:"""
                try:
                    response = await asyncio.to_thread(
                        run_ollama_sync,
                        current_model,
                        followup_prompt,
                        ollama_timeout
                    )
                    logger.debug(f" Ответ с инструментом (LLM): {response}")
                except Exception as llm_tool_error:
                    logger.error(" Ошибка перефраза ответа с инструментом", llm_tool_error)
                    response = grounded_data

                if not is_grounded_response(response, grounded_data):
                    logger.debug(" Ответ LLM не опирается на данные, применяем fallback")
                    response = grounded_data

                response = sanitize_bot_response(response)
                if not response.strip():
                    response = sanitize_bot_response(grounded_data)
                return response
            else:
                # Для новых инструментов просто возвращаем результат
                return tool_result
        else:
            print(" Tool-calling не обнаружен")
        
        # Очищаем ответ от любых оставшихся вызовов инструментов
        for pattern in [
            TOOL_TIME_RE,
            TOOL_WEATHER_RE,
            TOOL_CALCULATE_RE,
            TOOL_NEWS_RE,
            TOOL_CURRENCY_RE,
            TOOL_DEFINITION_RE,
            TOOL_TRANSLATE_RE,
            TOOL_FACT_RE,
            TOOL_REACT_RE,
            TOOL_REACTIONS_RE,
            TOOL_ONLINE_MEMBERS_RE,
            TOOL_PING_USER_RE,
            TOOL_PING_ROLE_RE,
            TOOL_SEND_CHANNEL_RE,
            TOOL_CALL_RE,
        ]:
            response = pattern.sub("", response).strip()
        
        # Удаляем лишние пустые строки
        response = re.sub(r'\n\s*\n', '\n', response)

        if not response.strip():
            response = "Извините, я не смог сформировать ответ. Попробуйте переформулировать."

        if len(response) > max_response_length:
            response = response[:max_response_length] + "..."

        # Анти-зацикливание одинаковых ответов
        user_id_str = str(user_id)
        last_bot_messages = [
            m["content"] for m in user_memory.get(user_id_str, {}).get("messages", [])
            if m["type"] == "bot"
        ][-3:]

        if response in last_bot_messages:
            response = "Я уже это говорил. Сформулируй вопрос иначе."

        return sanitize_bot_response(response)

    except Exception as e:
        print(f" Ollama error: {e}")

        if use_api_fallback:
            return await asyncio.to_thread(
                get_ollama_api_response,
                question,
                user_id,
                username
            )

        return "Произошла ошибка при обработке сообщения."

# Функция для получения ответа от Ollama API
def _g4f_models_url() -> str:
    return g4f_base_url.rstrip("/") + "/models"


def is_g4f_service_available() -> bool:
    try:
        response = requests.get(_g4f_models_url(), timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def _docker_container_running(name: str) -> bool:
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name=^{name}$", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return name in (result.stdout or "").splitlines()
    except Exception:
        return False


def _docker_container_exists(name: str) -> bool:
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name=^{name}$", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return name in (result.stdout or "").splitlines()
    except Exception:
        return False


def ensure_g4f_service() -> bool:
    """Проверяет g4f и при необходимости поднимает его через Docker."""
    if is_g4f_service_available():
        return True
    if not g4f_auto_start_enabled:
        return False

    try:
        if not _docker_container_running(g4f_container_name):
            if _docker_container_exists(g4f_container_name):
                subprocess.run(
                    ["docker", "start", g4f_container_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
            else:
                subprocess.run(
                    [
                        "docker",
                        "run",
                        "-d",
                        "--name",
                        g4f_container_name,
                        "-p",
                        "1337:8080",
                        g4f_docker_image,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
    except Exception as error:
        print(f"Не удалось запустить g4f через Docker: {error}")
        return False

    return is_g4f_service_available()


def get_g4f_fallback_response(message, user_id=None, username=None):
    """Опциональная запаска через g4f OpenAI-compatible API."""
    if not g4f_fallback_enabled:
        return ""
    if time.time() < g4f_disabled_until:
        return ""
    if not ensure_g4f_service():
        globals()["g4f_disabled_until"] = time.time() + g4f_retry_cooldown_seconds
        return ""

    try:
        endpoint = g4f_base_url.rstrip("/") + "/chat/completions"
        user_id_str = str(user_id) if user_id else "unknown"
        memory_facts = get_user_memory_facts(user_id_str)
        system_parts = [
            "Ты — Discord-бот Гена, созданный Binar. Отвечай кратко и по делу.",
            "Не используй Discord-инструменты, не пингуй людей и не выполняй админ-действия.",
            "Не пиши Thinking..., <think> или внутренний анализ.",
        ]
        if memory_facts:
            system_parts.append(f"Факты о пользователе:\n{memory_facts}")

        payload = {
            "model": g4f_model,
            "messages": [
                {"role": "system", "content": "\n".join(system_parts)},
                {"role": "user", "content": str(message or "")},
            ],
            "stream": False,
        }
        response = requests.post(endpoint, json=payload, timeout=g4f_timeout)
        if response.status_code != 200:
            print(f"Ошибка g4f fallback: {response.status_code} {response.text[:160]}")
            globals()["g4f_disabled_until"] = time.time() + g4f_retry_cooldown_seconds
            return ""
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            globals()["g4f_disabled_until"] = time.time() + g4f_retry_cooldown_seconds
            return ""
        first = choices[0] or {}
        message_obj = first.get("message") or {}
        content = message_obj.get("content") or first.get("text") or ""
        content = sanitize_bot_response(strip_terminal_control(content))
        if len(content) > max_response_length:
            content = content[:max_response_length] + "..."
        globals()["g4f_disabled_until"] = 0.0
        return content
    except Exception as error:
        print(f"Ошибка при вызове g4f fallback: {error}")
        globals()["g4f_disabled_until"] = time.time() + g4f_retry_cooldown_seconds
        return ""

def get_openrouter_fallback_response(message, user_id=None, username=None):
    """Fallback через OpenRouter (OpenAI-compatible API)"""
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.startswith("sk-or-v1-") and len(OPENROUTER_API_KEY) < 20:
        return ""
    
    try:
        endpoint = f"{OPENROUTER_BASE_URL}/chat/completions"
        
        user_id_str = str(user_id) if user_id else "unknown"
        memory_facts = get_user_memory_facts(user_id_str)
        
        system_parts = [
            "Ты — Discord-бот Гена, созданный Binar. Отвечай кратко и по делу на русском языке.",
            "Не используй Discord-инструменты, не пингуй людей и не выполняй админ-действия.",
            "Не пиши Thinking..., <think> или внутренний анализ.",
        ]
        if memory_facts:
            system_parts.append(f"Факты о пользователе:\n{memory_facts}")

        payload = {
            "model": "google/gemini-2.0-flash-exp:free",  # бесплатная модель, можно менять
            "messages": [
                {"role": "system", "content": "\n".join(system_parts)},
                {"role": "user", "content": str(message or "")},
            ],
            "temperature": 0.7,
            "max_tokens": 800,
        }

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://github.com/your-bot",  # рекомендуется OpenRouter
            "X-Title": "Gena Discord Bot",
        }

        response = requests.post(endpoint, json=payload, headers=headers, timeout=45)
        
        if response.status_code != 200:
            print(f"OpenRouter error: {response.status_code} {response.text[:200]}")
            return ""
        
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        content = sanitize_bot_response(strip_terminal_control(content))
        if len(content) > max_response_length:
            content = content[:max_response_length] + "..."
        
        print(f"✅ OpenRouter ответил ({len(content)} символов)")
        return content
        
    except Exception as e:
        print(f"Ошибка OpenRouter fallback: {e}")
        return ""

def get_ollama_api_response(message, user_id=None, username=None):
    """Резервный вариант через Ollama API"""
    if not cloud_ai_enabled:
        g4f_response = get_g4f_fallback_response(message, user_id, username)
        # OpenRouter как последний рубеж
        openrouter_response = get_openrouter_fallback_response(message, user_id, username)
        if openrouter_response:
            return openrouter_response
        if g4f_response:
            return g4f_response
        return "Cloud AI отключен в настройках бота."
        
    try:
        url = "http://localhost:11434/api/generate"
        headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}"} if OLLAMA_API_KEY else {}
        
        # Простые правила для API бота
        rules = """Ты — Discord-бот Гена, созданный Binar. Отвечай кратко и по делу.
Используй факты из памяти если они есть.
Отвечай строго на вопрос пользователя.
Без лишних пояснений и правил."""
        
        # Получаем память пользователя
        user_id_str = str(user_id) if user_id else "unknown"
        memory_facts = ""
        if user_id_str in user_memory:
            facts = user_memory[user_id_str].get("knowledge", {})
            if facts:
                formatted_facts = []
                for k, v in facts.items():
                    if isinstance(v, dict):
                        explanation = v.get("explanation")
                        if explanation:
                            formatted_facts.append(f"- {k}: {explanation}")
                        else:
                            formatted_facts.append(f"- {k}: {v}")
                    else:
                        formatted_facts.append(f"- {k}: {v}")
                memory_facts = "ФАКТЫ:\n" + "\n".join(formatted_facts)
        
        # Формируем промпт
        if memory_facts:
            prompt = f"""{rules}

{memory_facts}

Вопрос: {message}

Ответ:"""
        else:
            prompt = f"""{rules}

Вопрос: {message}

Ответ:"""
        
        # Ограничиваем длину промпта
        if len(prompt) > 1500:
            prompt = prompt[:1500] + "..."
        
        candidates = []
        for candidate in [current_model, *ollama_fallback_models]:
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        last_status = None
        g4f_attempted = False
        for index, candidate in enumerate(candidates):
            data = {
                "model": candidate,
                "prompt": prompt,
                "stream": False
            }

            response = requests.post(url, headers=headers, json=data, timeout=180)
            last_status = response.status_code
            if response.status_code == 200:
                result = response.json()
                api_response = strip_terminal_control(result.get("response", ""))

                if len(api_response) > max_response_length:
                    api_response = api_response[:max_response_length] + "..."

                globals()["current_model"] = candidate
                print(f" API ответил через {candidate}: {api_response}")
                return api_response

            error_text = response.text or ""
            if index == 0 and g4f_fallback_enabled:
                g4f_attempted = True
                print("Основная Ollama API-модель недоступна, пробую g4f fallback...")
                g4f_response = get_g4f_fallback_response(message, user_id, username)
                if g4f_response:
                    return g4f_response
            if (
                is_retryable_ollama_error(error_text, response.status_code)
                and candidate != candidates[-1]
            ):
                print(
                    f"API Ollama: модель {candidate} временно недоступна "
                    f"({response.status_code}), пробую fallback..."
                )
                continue
            break

        print(f"Ошибка API Ollama: {last_status}")
        if not g4f_attempted:
            g4f_response = get_g4f_fallback_response(message, user_id, username)
            if g4f_response:
                return g4f_response
        return "Сейчас локальная модель Ollama не загрузилась. Попробуй ещё раз после перезапуска Ollama."
            
    except Exception as e:
        print(f"Ошибка при вызове Ollama API: {e}")
        g4f_response = get_g4f_fallback_response(message, user_id, username)
        if g4f_response:
            return g4f_response
        
        openrouter_response = get_openrouter_fallback_response(message, user_id, username)
        if openrouter_response:
            return openrouter_response
            
        return "Извините, все AI-сервисы временно недоступны."

# Создаем объект бота
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.presences = True
intents.reactions = True
intents.message_content = True
bot: Any = commands.Bot(command_prefix='!', intents=intents)

# Py-cord compatibility shim for app_commands / bot.tree
if not hasattr(bot, "tree"):
    class _TreeAdapter:
        def __init__(self, _bot):
            self._bot = _bot
            self._registered_commands = []
        def command(self, *args, **kwargs):
            decorator = self._bot.slash_command(*args, **kwargs)
            command_name = kwargs.get("name")
            def _register(func):
                self._registered_commands.append(command_name or getattr(func, "__name__", "unknown"))
                return decorator(func)
            return _register
        async def sync(self):
            result = await self._bot.sync_commands(force=False)
            return result or []
        def get_commands(self):
            return list(self._registered_commands)
        def walk_commands(self):
            return []
        def error(self, func):
            # Map to py-cord application command error event
            self._bot.add_listener(func, "on_application_command_error")
            return func

    bot.tree = _TreeAdapter(bot)

if app_commands is None:
    class _AppCommandsShim:
        AppCommandError = Exception
        @staticmethod
        def describe(**kwargs):
            def _decorator(func):
                return func
            return _decorator
    app_commands = _AppCommandsShim()

def get_registered_command_names():
    """Возвращает имена локально зарегистрированных application/slash-команд."""
    registered = []
    try:
        if hasattr(bot, "tree") and hasattr(bot.tree, "get_commands"):
            registered = list(bot.tree.get_commands())
        elif hasattr(bot, "tree") and hasattr(bot.tree, "walk_commands"):
            registered = list(bot.tree.walk_commands())
        elif hasattr(bot, "walk_application_commands"):
            registered = list(bot.walk_application_commands())
        elif hasattr(bot, "application_commands"):
            registered = list(bot.application_commands)
        elif hasattr(bot, "commands"):
            registered = [c for c in bot.commands if hasattr(c, "name")]
    except Exception:
        registered = []
    names = []
    for command in registered:
        name = command if isinstance(command, str) else getattr(command, "name", None)
        if name and name not in names:
            names.append(name)
    return names

def supports_voice_receive(voice_client=None) -> bool:
    """Проверяет, умеет ли текущее окружение принимать voice аудио."""
    if not hasattr(discord, "sinks"):
        return False
    if voice_client is None:
        return True
    return hasattr(voice_client, "start_recording") and hasattr(voice_client, "stop_recording")

 #Слэш-команда /tools
@bot.tree.command(name="tools", description="Показать доступные инструменты")
async def tools_command(interaction: discord.Interaction):
    """Показать все доступные инструменты"""
    if AI_TOOLS_AVAILABLE:
       tools_info = """**🛠️ Доступные инструменты Геннадий 2.0:**

🕐 **Время** - `Который час?`, `Сколько времени?`
🧮 **Калькулятор** - `Посчитай 2+2`, `Сколько будет 10*5?`
📚 **Определения** - `Что такое ИИ?`, `Определение алгоритма`
🧠 **Факты** - `Расскажи интересный факт`, `Что-нибудь интересное`
👍 **Реакции** - `Поставь 👍 на прошлое сообщение`
🔎 **Чтение реакций** - `Кто отреагировал на прошлое сообщение?`
📝 **Просто говори с ботом как обычно, а он сам определит нужный инструмент**
"""
    else:
        tools_info = " Инструменты недоступны. Установите ai_tools модуль."
    
    embed = discord.Embed(
        title=" Инструменты Геннадий 2.0",
        description=tools_info,
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Админ: статус бота
@bot.tree.command(name="status", description="Показать статус бота (админ)")
async def status_command(interaction: discord.Interaction):
    if not is_admin_user(interaction.user):
        await interaction.response.send_message("❌ Недостаточно прав.", ephemeral=True)
        return

    status_lines = [
        f"🤖 Модель: {current_model}",
        f"🧠 Память: {'✅ Вкл' if memory_enabled else '❌ Выкл'}",
        f"☁️ Cloud AI: {'✅ Вкл' if cloud_ai_enabled else '❌ Выкл'}",
        f"🧰 AI инструменты: {'✅ Доступны' if AI_TOOLS_AVAILABLE else '❌ Недоступны'}",
        f"🎮 Игры: {'✅ Вкл' if GAMES_ENABLED else '❌ Выкл'}",
        f"💬 Auto-reply: {'✅ Вкл' if auto_reply_enabled else '❌ Выкл'}",
        f"📨 Разрешённые каналы: {len(allowed_channels)}"
    ]
    await interaction.response.send_message("\n".join(status_lines), ephemeral=True)


# Админ: добавить/обновить знание в bot_knowledge.json
@bot.tree.command(name="learn", description="Добавить/обновить запись в глобальной базе знаний (админ)")
@app_commands.describe(key="Ключ знания (слово/фраза)", explanation="Пояснение для ключа", overwrite="Принудительно перезаписать существующую запись (только для админов)")
async def learn_command(interaction: discord.Interaction, key: str, explanation: str, overwrite: bool = False):
    """Добавляет или обновляет запись в глобальной базе знаний.

    Параметры:
    - key: ключ/название знания
    - explanation: текст объяснения/описания
    - overwrite: если True, перезапишет существующую запись
    """
    if not is_admin_user(interaction.user):
        await interaction.response.send_message("❌ Недостаточно прав.", ephemeral=True)
        return

    key = (key or "").strip()
    explanation = (explanation or "").strip()

    if not key or not explanation:
        await interaction.response.send_message("❌ Укажите ключ и пояснение.", ephemeral=True)
        return

    # Защита от слишком простых ключей
    if is_simple_word(key):
        await interaction.response.send_message("❌ Ключ слишком простой или короткий. Используйте более описательное слово/фразу.", ephemeral=True)
        return

    existed = key in global_knowledge

    if existed and not overwrite:
        await interaction.response.send_message(
            "⚠️ Запись с таким ключом уже существует. Добавьте параметр `overwrite=true`, чтобы перезаписать.",
            ephemeral=True
        )
        return

    # Сохраняем метаданные: автор и времена
    try:
        from datetime import datetime
        now_iso = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    except Exception:
        now_iso = str(int(time.time()))

    author_id = str(getattr(interaction.user, 'id', 'unknown'))
    author_name = getattr(interaction.user, 'display_name', None) or getattr(interaction.user, 'name', str(interaction.user))

    entry = global_knowledge.get(key, {}) if existed else {}
    # Сохраняем created_at если есть, иначе ставим сейчас
    if not entry.get('created_at'):
        entry['created_at'] = now_iso
    entry['explanation'] = explanation
    entry['updated_at'] = now_iso
    entry['last_author_id'] = author_id
    entry['last_author_name'] = author_name

    global_knowledge[key] = entry

    try:
        save_knowledge(global_knowledge)
        await interaction.response.send_message(f"✅ Знание {'обновлено' if existed else 'добавлено'}: {key}", ephemeral=True)
        # Небольшая публичная нотификация в канал (по желанию можно отключить)
        try:
            # отправляем в канал краткое подтверждение (неэпhemeral)
            await interaction.followup.send(f"Знание сохранено: {key}", ephemeral=False)
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Ошибка сохранения знаний: {e}")
        await interaction.response.send_message("❌ Ошибка при сохранении файла знаний.", ephemeral=True)

# Запуск Activity (для всех)
@bot.tree.command(name="activity", description="Запустить Activity Hub в текущем канале")
async def activity_command(interaction: discord.Interaction):
    if not activity_app_id:
        await interaction.response.send_message(
            "❌ Не задан `activity_app_id`. Добавь его в `bot_config.json`.",
            ephemeral=True
        )
        return

    try:
        target_type = getattr(discord.InviteTarget, "embedded_application", None)
        invite = await interaction.channel.create_invite(  # type: ignore[attr-defined]
            max_age=900,
            max_uses=1,
            target_type=target_type,
            target_application_id=int(activity_app_id)
        )
        await interaction.response.send_message(
            f"🎮 Activity Hub запущен: {invite.url}",
            ephemeral=False
        )
    except Exception as e:
        logger.error("Ошибка создания Activity invite", e)
        await interaction.response.send_message("❌ Не удалось создать Activity invite.", ephemeral=True)

# Админ: перезагрузка конфигурации
@bot.tree.command(name="reload_config", description="Перезагрузить bot_config.json (админ)")
async def reload_config_command(interaction: discord.Interaction):
    if not is_admin_user(interaction.user):
        await interaction.response.send_message("❌ Недостаточно прав.", ephemeral=True)
        return

    try:
        global config
        config = load_config()
        # Применяем параметр console_logging сразу
        try:
            if hasattr(logger, 'set_console'):
                logger.set_console(config.get('console_logging', False))
            else:
                logger.console = config.get('console_logging', False)
        except Exception:
            pass
        await interaction.response.send_message("✅ Конфигурация перезагружена.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Ошибка перезагрузки: {e}", ephemeral=True)


# Админ: обновить конфигурацию в реальном времени
@bot.tree.command(name="set_config", description="Изменить bot_config.json и применить изменения в realtime (админ)")
@app_commands.describe(key="Ключ конфигурации (например: memory_enabled)", value="Значение в JSON или как строка")
async def set_config_command(interaction: discord.Interaction, key: str, value: str):
    global config

    if not is_admin_user(interaction.user):
        await interaction.response.send_message("❌ Недостаточно прав.", ephemeral=True)
        return

    key = (key or "").strip()
    value = (value or "").strip()
    if not key:
        await interaction.response.send_message("❌ Укажите ключ конфигурации.", ephemeral=True)
        return

    # Попытка распарсить значение как JSON (для bool, list, dict, number)
    try:
        parsed = json.loads(value)
    except Exception:
        parsed = value

    try:
        config[key] = parsed
        save_config(config)
        # Применяем изменения в runtime
        config = load_config()
        try:
            if hasattr(logger, 'set_console'):
                logger.set_console(config.get('console_logging', False))
            else:
                logger.console = config.get('console_logging', False)
        except Exception:
            pass
        await interaction.response.send_message(f"✅ Настройка сохранена и применена: {key}", ephemeral=True)
    except Exception as e:
        logger.error(f"Ошибка при установке конфигурации через /set_config: {e}")
        await interaction.response.send_message(f"❌ Ошибка при сохранении: {e}", ephemeral=True)


# Админ: включить/выключить вывод логов в консоль
@bot.tree.command(name="toggle_console_logging", description="Включить/выключить вывод логов в консоль (админ)")
@app_commands.describe(enable="True — включить, False — отключить")
async def toggle_console_logging_command(interaction: discord.Interaction, enable: bool):
    if not is_admin_user(interaction.user):
        await interaction.response.send_message("❌ Недостаточно прав.", ephemeral=True)
        return

    try:
        config['console_logging'] = bool(enable)
        save_config(config)
        if hasattr(logger, 'set_console'):
            logger.set_console(bool(enable))
        else:
            logger.console = bool(enable)
        await interaction.response.send_message(f"✅ console_logging set to {enable}", ephemeral=True)
    except Exception as e:
        logger.error(f"Ошибка при переключении консольных логов: {e}")
        await interaction.response.send_message("❌ Ошибка при переключении логов.", ephemeral=True)


# Админ: установить личность для другого участника
@bot.tree.command(name="set_persona", description="Назначить личность пользователю (админ)")
@app_commands.describe(member="Участник сервера", persona="Ключ персоны (см. /personas)")
async def set_persona_command(interaction: discord.Interaction, member: discord.Member, persona: str):
    if not is_admin_user(interaction.user):
        await interaction.response.send_message("❌ Недостаточно прав.", ephemeral=True)
        return

    persona = (persona or "").strip()
    if persona not in PERSONAS:
        await interaction.response.send_message(f"❌ Персона '{persona}' не найдена. Используйте /personas для списка.", ephemeral=True)
        return

    try:
        set_user_persona(member.id, persona)
        save_personas()
        await interaction.response.send_message(f"✅ Персона '{persona}' назначена пользователю {getattr(member, 'display_name', member.name)}.", ephemeral=True)
    except Exception as e:
        logger.error(f"Ошибка при назначении персоны: {e}")
        await interaction.response.send_message("❌ Ошибка при назначении персоны.", ephemeral=True)

# Админ: добавить текущий канал
@bot.tree.command(name="add_channel", description="Разрешить текущий канал (админ)")
async def add_channel_command(interaction: discord.Interaction):
    if not is_admin_user(interaction.user):
        await interaction.response.send_message("❌ Недостаточно прав.", ephemeral=True)
        return

    channel_id = str(getattr(interaction.channel, "id", ""))
    if not channel_id:
        await interaction.response.send_message("❌ Не удалось определить канал.", ephemeral=True)
        return
    if channel_id not in allowed_channels:
        allowed_channels.append(channel_id)
        config["allowed_channels"] = allowed_channels
        save_config(config)
        await interaction.response.send_message(f"✅ Канал добавлен: {channel_id}", ephemeral=True)
    else:
        await interaction.response.send_message("ℹ️ Канал уже в списке.", ephemeral=True)

# Админ: убрать текущий канал
@bot.tree.command(name="remove_channel", description="Запретить текущий канал (админ)")
async def remove_channel_command(interaction: discord.Interaction):
    if not is_admin_user(interaction.user):
        await interaction.response.send_message(" Недостаточно прав.", ephemeral=True)
        return

    channel_id = str(getattr(interaction.channel, "id", ""))
    if not channel_id:
        await interaction.response.send_message(" Не удалось определить канал.", ephemeral=True)
        return
    if channel_id in allowed_channels:
        allowed_channels.remove(channel_id)
        config["allowed_channels"] = allowed_channels
        save_config(config)
        await interaction.response.send_message(f" Канал удалён: {channel_id}", ephemeral=True)
    else:
        await interaction.response.send_message("ℹ Канал не найден в списке.", ephemeral=True)

@bot.tree.command(name="member", description="Найти участника по нику или ID")
@app_commands.describe(query="Ник, display name, ID или @упоминание")
async def member_command(interaction: discord.Interaction, query: str):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(" Команда доступна только в сервере.", ephemeral=True)
        return

    member = resolve_member(guild, query)
    if member:
        try:
            upsert_known_member({"known_members": known_members}, guild_id=guild.id, member=member)
            save_memory()
        except Exception:
            pass
        await interaction.response.send_message(
            f"Нашёл: {format_member_mention(member)}\n"
            f"Display name: `{getattr(member, 'display_name', '')}`\n"
            f"Username: `{getattr(member, 'name', '')}`\n"
            f"ID: `{getattr(member, 'id', '')}`",
            ephemeral=True,
        )
        return

    known = find_known_member({"known_members": known_members}, guild_id=guild.id, query=query)
    if known:
        await interaction.response.send_message(
            f"Есть в памяти: {known.get('mention')}\n"
            f"Display name: `{known.get('display_name')}`\n"
            f"Username: `{known.get('username')}`\n"
            f"ID: `{known.get('member_id')}`",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(" Участник не найден. Проверь members intent и написание ника.", ephemeral=True)

@bot.tree.command(name="ping_member", description="Упомянуть найденного участника")
@app_commands.describe(query="Ник, display name, ID или @упоминание", text="Текст после упоминания")
async def ping_member_command(interaction: discord.Interaction, query: str, text: str = ""):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(" Команда доступна только в сервере.", ephemeral=True)
        return
    if str(getattr(interaction.channel, "id", "")) not in allowed_channels and not is_admin_user(interaction.user):
        await interaction.response.send_message(" Пинг доступен только в разрешённых каналах.", ephemeral=True)
        return

    member = resolve_member(guild, query)
    mention = None
    if member:
        mention = format_member_mention(member)
        try:
            upsert_known_member({"known_members": known_members}, guild_id=guild.id, member=member)
            save_memory()
        except Exception:
            pass
    else:
        known = find_known_member({"known_members": known_members}, guild_id=guild.id, query=query)
        if known:
            mention = known.get("mention")

    if not mention:
        await interaction.response.send_message(" Не нашёл такого участника.", ephemeral=True)
        return

    message_text = f"{mention} {text}".strip()
    await interaction.response.send_message(message_text, ephemeral=False)

@bot.tree.command(name="say", description="Отправить сообщение в любой доступный канал (админ)")
@app_commands.describe(channel="ID, #упоминание или имя канала", text="Текст сообщения")
async def say_command(interaction: discord.Interaction, channel: str, text: str):
    if not is_admin_user(interaction.user):
        await interaction.response.send_message(" Недостаточно прав.", ephemeral=True)
        return
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(" Команда доступна только в сервере.", ephemeral=True)
        return

    target = resolve_text_channel(guild, channel)
    if target is None:
        await interaction.response.send_message(" Канал не найден.", ephemeral=True)
        return
    bot_member = getattr(guild, "me", None)
    if not can_bot_send(target, bot_member):
        await interaction.response.send_message(
            " У бота нет прав `View Channel` и `Send Messages` в этом канале.",
            ephemeral=True,
        )
        return

    await target.send(text)
    await interaction.response.send_message(f" Отправлено в #{getattr(target, 'name', target.id)}.", ephemeral=True)

async def fetch_channel_message(guild, channel_query, message_id, current_channel_id=None):
    query = str(channel_query or "").strip()
    if query.lower() in ("current", "текущий", "this"):
        query = str(current_channel_id or "")
    target = resolve_text_channel(guild, query)
    if target is None:
        raise ValueError("Канал не найден")
    try:
        parsed_message_id = int(str(message_id).strip())
    except ValueError as exc:
        raise ValueError("Некорректный ID сообщения") from exc
    return target, await target.fetch_message(parsed_message_id)

async def collect_reaction_users(reaction, limit=50):
    iterator = reaction.users(limit=limit)
    if hasattr(iterator, "flatten"):
        return await iterator.flatten()
    users = []
    async for user in iterator:
        users.append(user)
    return users



def resolve_emoji(guild, emoji_query: str):
    """Разрешает эмодзи: unicode, <:name:id>, id или имя серверного эмодзи."""
    q = str(emoji_query or "").strip()
    if not q:
        return q
    # Формат <a:name:id> или <:name:id>
    m = re.match(r"^<(a)?:([^:>]+):(\d+)>$", q)
    if m:
        animated = bool(m.group(1))
        # Принудительно приводим к str и задаем фолбек, чтобы Pylance не ругался
        name = str(m.group(2) or "emoji")
        try:
            eid = int(m.group(3))
        except Exception:
            eid = None
        try:
            if eid:
                return discord.PartialEmoji(name=name, id=eid, animated=animated)
        except Exception:
            pass

    # Поиск по имени в гильдии
    try:
        emoji_obj = discord.utils.get(guild.emojis, name=q)
        if emoji_obj:
            return emoji_obj
    except Exception:
        pass
    # По умолчанию возвращаем строку (unicode)
    return q

@bot.tree.command(name="react", description="Поставить реакцию на сообщение (админ)")
@app_commands.describe(
    channel="ID, #упоминание или имя канала",
    message_id="ID сообщения",
    emoji="Unicode emoji или emoji сервера",
    save="Сохранить реакцию в логе (если включено в конфиге)"
)
async def react_command(interaction: discord.Interaction, channel: str, message_id: str, emoji: str, save: bool = False):
    if not is_admin_user(interaction.user):
        await interaction.response.send_message(" Недостаточно прав.", ephemeral=True)
        return
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(" Команда доступна только в сервере.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    try:
        target, message = await fetch_channel_message(guild, channel, message_id)
        if not can_bot_react(target, getattr(guild, "me", None)):
            await interaction.followup.send(
                " Не хватает прав `View Channel`, `Read Message History` или `Add Reactions`.",
                ephemeral=True,
            )
            return
        # Resolve emoji (support server custom emoji by name or <:name:id>)
        resolved = resolve_emoji(guild, emoji)
        await message.add_reaction(resolved)

        # Сохраняем реакцию если попросили или включено в конфиге
        should_save = save or bool(save_reactions.get(str(guild.id), False)) or bool(save_reactions_default)
        if should_save:
            entry = {
                "guild_id": getattr(guild, 'id', None),
                "channel_id": getattr(target, 'id', None),
                "message_id": getattr(message, 'id', None),
                "emoji_input": emoji,
                "emoji_resolved": str(resolved),
                "saved_by_user_id": getattr(interaction.user, 'id', None),
                "saved_by_user_name": getattr(interaction.user, 'display_name', getattr(interaction.user, 'name', None)),
                "timestamp": time.time(),
            }
            try:
                save_reaction_entry(entry)
            except Exception as e:
                logger.error("Ошибка при попытке сохранить запись реакции", e)

        await interaction.followup.send(
            f" Реакция {emoji} добавлена к сообщению `{message.id}` в #{target.name}.",
            ephemeral=True,
        )
    except (ValueError, discord.NotFound) as error:
        await interaction.followup.send(f" {error}", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send(" Discord запретил доступ к сообщению или реакции.", ephemeral=True)
    except discord.HTTPException as error:
        await interaction.followup.send(f" Не удалось поставить реакцию: {error}", ephemeral=True)


@bot.tree.command(name="channels", description="Показать текстовые каналы сервера и их ID")
async def channels_command(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(" Команда доступна только в сервере.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    bot_member = getattr(guild, 'me', None)
    lines = [f"Каналы сервера **{guild.name}** (id: {guild.id}):"]
    try:
        for ch in guild.channels:
            # Show only text-based channels where bot might send
            chan_type = getattr(ch, 'type', None)
            # discord.ChannelType.text etc. Many wrappers; use name and permissions
            try:
                perms = ch.permissions_for(bot_member) if bot_member is not None else None
                can_view = bool(perms and getattr(perms, 'view_channel', False))
                can_send = bool(perms and getattr(perms, 'send_messages', False))
            except Exception:
                can_view = False
                can_send = False
            name = getattr(ch, 'name', str(ch))
            cid = getattr(ch, 'id', 'unknown')
            lines.append(f"• {name} | id: `{cid}` | view: {'✅' if can_view else '❌'} | send: {'✅' if can_send else '❌'}")
        # Send in chunks if too long
        text = "\n".join(lines)
        for i in range(0, len(text), 1900):
            await interaction.followup.send(text[i:i+1900], ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Ошибка при получении списка каналов: {e}", ephemeral=True)


@bot.tree.command(name="time", description="Показать текущее время (локальное и UTC)")
async def time_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        from datetime import datetime as _dt
        local = _dt.now()
        utc = _dt.utcnow()
        tzinfo = time.tzname if hasattr(time, 'tzname') else None
        msg = f"Текущее время локально: {local.strftime('%Y-%m-%d %H:%M:%S')}\nUTC: {utc.strftime('%Y-%m-%d %H:%M:%S')}"
        if tzinfo:
            msg += f"\nЧасовой пояс системы: {tzinfo}"
        await interaction.followup.send(msg, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Ошибка при определении времени: {e}", ephemeral=True)

@bot.tree.command(name="reactions", description="Прочитать реакции на сообщение")
@app_commands.describe(channel="ID, #упоминание или имя канала", message_id="ID сообщения")
async def reactions_command(interaction: discord.Interaction, channel: str, message_id: str):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(" Команда доступна только в сервере.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    try:
        target, message = await fetch_channel_message(guild, channel, message_id)
        bot_member = getattr(guild, "me", None)
        permissions = target.permissions_for(bot_member) if bot_member is not None else None
        if not (
            permissions is not None
            and getattr(permissions, "view_channel", False)
            and getattr(permissions, "read_message_history", False)
        ):
            await interaction.followup.send(" Бот не может читать историю этого канала.", ephemeral=True)
            return

        if not message.reactions:
            await interaction.followup.send("У сообщения нет реакций.", ephemeral=True)
            return

        lines = [f"Реакции на сообщение `{message.id}` в #{target.name}:"]
        for reaction in message.reactions:
            users = await collect_reaction_users(reaction, limit=50)
            user_text = ", ".join(
                f"{getattr(user, 'display_name', getattr(user, 'name', 'unknown'))} (`{user.id}`)"
                for user in users
            )
            if len(user_text) > 1200:
                user_text = user_text[:1200] + "..."
            lines.append(f"{reaction.emoji} × {reaction.count}: {user_text or 'пользователи недоступны'}")

        response = "\n".join(lines)
        await interaction.followup.send(response[:1950], ephemeral=True)
    except (ValueError, discord.NotFound) as error:
        await interaction.followup.send(f"❌ {error}", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send(" Discord запретил чтение сообщения.", ephemeral=True)
    except discord.HTTPException as error:
        await interaction.followup.send(f" Не удалось прочитать реакции: {error}", ephemeral=True)

@bot.tree.command(name="online_members", description="Показать online-участников и их ID (админ)")
async def online_members_command(interaction: discord.Interaction):
    if not is_admin_user(interaction.user):
        await interaction.response.send_message(" Недостаточно прав.", ephemeral=True)
        return
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(" Команда доступна только в сервере.", ephemeral=True)
        return

    members = get_online_members(guild)
    if not members:
        await interaction.response.send_message(
            "Online-участники не найдены. Проверь Presence Intent в Discord Developer Portal.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)
    lines = [
        f"{getattr(member, 'display_name', member.name)} | @{member.name} | `{member.id}` | {member.status}"
        for member in members
    ]
    chunks = []
    current = [f"Online: {len(members)}"]
    current_length = len(current[0])
    for line in lines:
        if current_length + len(line) + 1 > 1900:
            chunks.append("\n".join(current))
            current = []
            current_length = 0
        current.append(line)
        current_length += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    for chunk in chunks:
        await interaction.followup.send(chunk, ephemeral=True)


@bot.tree.command(name="toggle_save_reactions", description="Включить/выключить автосохранение реакций для сервера (только админ)")
@app_commands.describe(enable="True — включить, False — отключить")
async def toggle_save_reactions(interaction: discord.Interaction, enable: bool):
    """Переключает настройку сохранения реакций для текущей гильдии и сохраняет в bot_config.json"""
    if not is_admin_user(interaction.user):
        await interaction.response.send_message(" Недостаточно прав.", ephemeral=True)
        return
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(" Команда доступна только в сервере.", ephemeral=True)
        return

    try:
        gid = str(guild.id)
        save_reactions[gid] = bool(enable)
        # Обновляем в памяти конфиг и сохраняем
        if not isinstance(config, dict):
            cfg = {}
        else:
            cfg = config
        cfg["save_reactions"] = config.get("save_reactions", {}) if isinstance(config, dict) else {}
        cfg["save_reactions"][gid] = bool(enable)
        save_config(cfg)
        # Обновляем глобальную переменную config
        globals()["config"] = cfg
        await interaction.response.send_message(
            f"Автосохранение реакций для сервера **{guild.name}** установлено: {'включено' if enable else 'выключено'}.",
            ephemeral=True,
        )
    except Exception as e:
        logger.error("Ошибка при переключении save_reactions", e)
        await interaction.response.send_message(f"Ошибка при переключении: {e}", ephemeral=True)

# ==================== VOICE COMMANDS =====================
@bot.tree.command(name="join", description="Подключить бота к вашему voice каналу")
async def join_voice(interaction: discord.Interaction):
    # -pyright: user может быть не Member в типах, поэтому getattr
    if not getattr(interaction.user, "voice", None) or not interaction.user.voice.channel:  # type: ignore[attr-defined]
        await interaction.response.send_message("❌ Ты не в voice канале.", ephemeral=True)
        return
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("❌ Команда доступна только в сервере.", ephemeral=True)
        return
    channel = interaction.user.voice.channel  # type: ignore[attr-defined]
    try:
        state = _get_guild_state(guild.id)
        if state.get("joining"):
            await interaction.response.send_message("⏳ Уже подключаюсь, подожди секунду.", ephemeral=True)
            return
        state["joining"] = True
        # Сразу подтверждаем, чтобы Discord не ретраил команду
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        vc = guild.voice_client  # type: ignore[union-attr]
        print(f"[VOICE] /join: user_channel={getattr(channel, 'id', None)} vc={'yes' if vc else 'no'} vc_channel={getattr(getattr(vc,'channel',None),'id',None) if vc else None}")
        if vc and vc.channel and getattr(vc.channel, "id", None) == getattr(channel, "id", None):
            await interaction.followup.send(f"ℹ️ Я уже в **{channel.name}**", ephemeral=True)
            return
        if vc:
            await vc.move_to(channel)  # type: ignore[attr-defined]
        else:
            await channel.connect()  # type: ignore[attr-defined]
        await interaction.followup.send(f"✅ Подключился к **{channel.name}**", ephemeral=True)
    except Exception as e:
        try:
            await interaction.followup.send(f"❌ Ошибка подключения: {e}", ephemeral=True)
        except Exception:
            pass
    finally:
        try:
            state = _get_guild_state(guild.id)
            state["joining"] = False
        except Exception:
            pass

@bot.tree.command(name="leave", description="Отключить бота от voice канала")
async def leave_voice(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(" Команда доступна только в сервере.", ephemeral=True)
        return
    vc = guild.voice_client  # type: ignore[union-attr]
    if not vc:
        await interaction.response.send_message("ℹ Я не в voice канале.", ephemeral=True)
        return
    print(f"[VOICE] /leave: vc_channel={getattr(getattr(vc,'channel',None),'id',None)}")
    await vc.disconnect(force=False)
    await interaction.response.send_message(" Отключился.", ephemeral=True)

@bot.tree.command(name="listen", description="Включить прослушивание voice канала")
async def listen_voice(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(" Команда доступна только в сервере.", ephemeral=True)
        return
    vc = guild.voice_client  # type: ignore[union-attr]
    if not vc:
        await interaction.response.send_message(" Я не подключен к voice. Сначала /join.", ephemeral=True)
        return
    if hasattr(vc, "is_connected") and not vc.is_connected():  # type: ignore[attr-defined]
        # Бывает, что объект есть, но соединение уже разорвано
        try:
            if getattr(interaction.user, "voice", None) and interaction.user.voice.channel:  # type: ignore[attr-defined]
                await interaction.user.voice.channel.connect()  # type: ignore[attr-defined]
                vc = guild.voice_client  # type: ignore[union-attr]
            else:
                await interaction.response.send_message(" Я не подключен к voice. Сначала /join.", ephemeral=True)
                return
        except Exception as e:
            await interaction.response.send_message(f" Не удалось переподключиться: {e}", ephemeral=True)
            return
    if not supports_voice_receive(vc):
        await interaction.response.send_message(" Эта библиотека Discord не поддерживает прием аудио.", ephemeral=True)
        return
    if not ELEVENLABS_API_KEY:
        await interaction.response.send_message(" Не задан ELEVENLABS_API_KEY в .env", ephemeral=True)
        return

    state = _get_guild_state(guild.id)
    state["listening"] = True
    if not state.get("worker") or state["worker"].done():
        state["worker"] = asyncio.create_task(_voice_worker(guild.id, vc))

    async def handle_sink(sink, *args):
        # Обрабатываем каждого пользователя
        for user_id, audio in sink.audio_data.items():
            try:
                # сохраняем WAV
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    audio.file.seek(0)
                    tmp.write(audio.file.read())
                    wav_path = Path(tmp.name)
                await state["queue"].put((user_id, wav_path))
            except Exception:
                continue

        # Перезапускаем запись, если слушаем дальше
        if state.get("listening"):
            try:
                vc.start_recording(discord.sinks.WaveSink(), handle_sink)  # type: ignore[attr-defined]
            except Exception:
                state["listening"] = False

    try:
        vc.start_recording(discord.sinks.WaveSink(), handle_sink)  # type: ignore[attr-defined]
        await interaction.response.send_message(" Прослушивание включено.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f" Не удалось начать запись: {e}", ephemeral=True)

@bot.tree.command(name="stop_listen", description="Остановить прослушивание voice канала")
async def stop_listen(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(" Команда доступна только в сервере.", ephemeral=True)
        return
    vc = guild.voice_client  # type: ignore[union-attr]
    if not vc:
        await interaction.response.send_message("ℹ️ Я не в voice канале.", ephemeral=True)
        return
    state = _get_guild_state(guild.id)
    state["listening"] = False
    print(f"[VOICE] /stop_listen: vc_channel={getattr(getattr(vc,'channel',None),'id',None)}")
    try:
        if state.get("worker") and not state["worker"].done():
            state["worker"].cancel()
    except Exception:
        pass
    try:
        if hasattr(vc, "stop_recording"):
            vc.stop_recording()  # type: ignore[attr-defined]
    except Exception:
        pass
    await interaction.response.send_message(" Прослушивание остановлено.", ephemeral=True)

# Слэш-команда /persona
@bot.tree.command(name="persona", description="Сменить личность бота")
@app_commands.describe(mode="Режим личности")
async def persona_command(interaction: discord.Interaction, mode: str):
    mode = mode.lower()
    
    if mode not in PERSONAS:
        available = "\n".join([f"• `{key}` - {PERSONAS[key]['name']}" for key in PERSONAS.keys()])
        await interaction.response.send_message(
            f" Неизвестная личность.\n\n**Доступные персоны:**\n{available}",
            ephemeral=True
        )
        return
    
    user_id = getattr(interaction.user, "id", None)
    if user_id is None:
        await interaction.response.send_message(
            " Не удалось определить пользователя.",
            ephemeral=True
        )
        return
    
    set_user_persona(user_id, mode)
    save_personas()
    
    await interaction.response.send_message(
        f" Личность изменена: **{PERSONAS[mode]['name']}**",
        ephemeral=True
    )

# Слэш-команда /personas - показать все доступные персоны
@bot.tree.command(name="personas", description="Показать все доступные персоны")
async def personas_command(interaction: discord.Interaction):
    available = "\n".join([f"• `{key}` - {PERSONAS[key]['name']}" for key in PERSONAS.keys()])
    await interaction.response.send_message(
        f"**🎭 Доступные персоны:**\n{available}\n\nИспользуйте `/persona <имя>` для смены личности",
        ephemeral=True
    )

# Слэш-команда /effects - управление визуальными эффектами
@bot.tree.command(name="effects", description="Управление визуальными эффектами бота")
@app_commands.describe(mode="Режим эффектов")
async def effects_command(interaction: discord.Interaction, mode: str = "realistic"):
    mode = mode.lower()
    
    if mode not in ["realistic", "animated", "burst", "simple", "random"]:
        await interaction.response.send_message(
            " Неверный режим. Доступные: `realistic`, `animated`, `burst`, `simple`, `random`",
            ephemeral=True
        )
        return
    
    # Сохраняем настройку эффекта для пользователя
    # Защита на случай, если interaction.user отсутствует
    # Используем __dict__.get для безопасного доступа к потенциально несуществующему атрибуту member
    member = interaction.__dict__.get('member')
    user = getattr(interaction, 'user', None) or getattr(interaction, 'author', None) or (member.user if member is not None else None)
    if user is None:
        await interaction.response.send_message(
            "Не удалось определить пользователя. Попробуйте снова.",
            ephemeral=True
        )
        return

    user_id_str = str(user.id)
    if user_id_str not in user_memory:
        user_memory[user_id_str] = {"messages": [], "knowledge": {}, "persona": "default"}
    
    user_memory[user_id_str]["effect_mode"] = mode
    save_memory()
    
    effect_descriptions = {
        "realistic": "⌨ Реалистичная печатание (по длине ответа)",
        "animated": " Анимированная печатание",
        "burst": " Вспышки печатания", 
        "simple": " Простая печатание",
        "random": " Случайные эффекты"
    }
    
    await interaction.response.send_message(
        f"✅ Визуальные эффекты изменены: **{effect_descriptions.get(mode, mode)}**",
        ephemeral=True
    )

# Слэш-команда /vision - управление распознаванием изображений
@bot.tree.command(name="vision", description="Управление распознаванием изображений")
@app_commands.describe(mode="Режим распознавания")
async def vision_command(interaction: discord.Interaction, mode: str = "auto"):
    mode = mode.lower()
    
    if mode not in ["auto", "ocr_only", "vision_only"]:
        await interaction.response.send_message(
            " Неверный режим. Доступные: `auto`, `ocr_only`, `vision_only`",
            ephemeral=True
        )
        return
    
    # Проверяем доступность распознавания
    if not IMAGE_RECOGNITION_AVAILABLE:
        await interaction.response.send_message(
            " Распознавание изображений недоступно. Установите зависимости.",
            ephemeral=True
        )
        return
    
    # Сохраняем настройку для пользователя
    if interaction.user is None:
        await interaction.response.send_message(
            "Не удалось определить пользователя. Попробуйте снова.",
            ephemeral=True
        )
        return

    user_id_str = str(interaction.user.id)
    if user_id_str not in user_memory:
        user_memory[user_id_str] = {"messages": [], "knowledge": {}, "persona": "default"}
    
    user_memory[user_id_str]["vision_mode"] = mode
    save_memory()
    
    mode_descriptions = {
        "auto": " Автоматический режим (OCR + анализ)",
        "ocr_only": " Только распознавание текста",
        "vision_only": " Только анализ изображения"
    }
    
    status = " Распознавание изображений доступно" if IMAGE_RECOGNITION_AVAILABLE else "❌ Распознавание недоступно"
    
    await interaction.response.send_message(
        f" Режим распознавания: **{mode_descriptions.get(mode, mode)}**\n{status}",
        ephemeral=True
    )

# ==================== DIAGNOSTICS =====================
@bot.tree.command(name="diag", description="Диагностика бота и команд")
async def diag_command(interaction: discord.Interaction):
    lines = []

    # Базовая информация
    lines.append(f"Bot: {bot.user}")
    lines.append(f"Discord lib: {discord.__version__}")

    # Slash-команды
    try:
        command_names = get_registered_command_names()
        lines.append(f"Slash commands: {len(command_names)}")
        if command_names:
            names = ", ".join([f"/{name}" for name in command_names])
            lines.append(f"Commands: {names[:1500]}")
    except Exception as e:
        lines.append(f"Slash commands: error {e}")

    # Voice
    lines.append(f"Voice sinks: {'yes' if hasattr(discord, 'sinks') else 'no'}")
    lines.append(f"Members intent: {'yes' if getattr(bot.intents, 'members', False) else 'no'}")
    lines.append(f"Presences intent: {'yes' if getattr(bot.intents, 'presences', False) else 'no'}")
    lines.append(f"Reactions intent: {'yes' if getattr(bot.intents, 'reactions', False) else 'no'}")
    vc = getattr(interaction.guild, "voice_client", None)  # type: ignore[union-attr]
    lines.append(f"Voice connected: {'yes' if vc else 'no'}")

    # AI / tools
    lines.append(f"Ollama API key: {'yes' if bool(OLLAMA_API_KEY) else 'no'}")
    lines.append(f"ElevenLabs API key: {'yes' if bool(ELEVENLABS_API_KEY) else 'no'}")
    lines.append(f"Image recognition: {'yes' if IMAGE_RECOGNITION_AVAILABLE else 'no'}")
    lines.append(f"AI tools: {'yes' if AI_TOOLS_AVAILABLE else 'no'}")

    await interaction.response.send_message("```\n" + "\n".join(lines) + "\n```", ephemeral=True)

# Обработчик пингов от пользователей
@bot.event
async def on_message(message):
    try:
        # Игнорируем сообщения от самого бота и других ботов
        if message.author == bot.user or getattr(message.author, "bot", False):
            return

        # Дедупликация событий (на случай повторной доставки или многократной обработки)
        now_ts = time.time()
        if message.id in recent_message_ids and now_ts - recent_message_ids[message.id] < message_dedupe_window:
            logger.debug(f" Дубль сообщения {message.id}, пропускаем")
            return
        recent_message_ids[message.id] = now_ts
        # Очистка старых записей
        for msg_id, ts in list(recent_message_ids.items()):
            if now_ts - ts > message_dedupe_window:
                recent_message_ids.pop(msg_id, None)

        # Запоминаем общий фон канала даже если бот не отвечает.
        if memory_enabled:
            remember_message_context(message, "user")
            save_memory()

        # Проверяем игровые команды (если модули доступны)
        content = message.content.lower()
        if GAMES_ENABLED:

            # Проверяем команды игр
            if content.startswith('!game') or content.startswith('/game') or content.startswith('!игра') or content.startswith('/игра'):
                from games.discord_integration import discord_integration # type: ignore # pyright: ignore[reportMissingImports]
                args = content.split()[1:] if len(content.split()) > 1 else []
                await discord_integration.cmd_game(message, args)
                return

            if content.startswith('!move') or content.startswith('/move') or content.startswith('!ход') or content.startswith('/ход'):
                from games.discord_integration import discord_integration # type: ignore # pyright: ignore[reportMissingImports]
                args = content.split()[1:] if len(content.split()) > 1 else []
                await discord_integration.cmd_move(message, args)
                return

            if content.startswith('!scores') or content.startswith('/scores') or content.startswith('!статистика') or content.startswith('/статистика'):
                from games.discord_integration import discord_integration # type: ignore # pyright: ignore[reportMissingImports]
                await discord_integration.cmd_scores(message, [])
                return

            if content.startswith('!endgame') or content.startswith('/endgame') or content.startswith('!конецигры') or content.startswith('/конецигры'):
                from games.discord_integration import discord_integration # type: ignore # pyright: ignore[reportMissingImports]
                await discord_integration.cmd_endgame(message, [])
                return

                       # Обработка ответов на игры (без префикса)
            from games.game_manager import game_manager # type: ignore # pyright: ignore[reportMissingImports]
            if message.author and message.author.id in game_manager.sessions:  # type: ignore[union-attr]
                if not content.startswith('!') and not content.startswith('/'):
                    try:
                        from games import discord_integration # type: ignore # pyright: ignore[reportMissingImports]
                    except ImportError:
                        discord_integration = None
                    
                    if discord_integration is not None:
                        await discord_integration.cmd_move(message, [content])
                    return


        # Проверяем, что сообщение содержит упоминание бота
        if bot.user.mentioned_in(message):
            print(f"📨 Получен пинг от {message.author.name} в канале {message.channel.id}")

            ping_summary = summarize_message_mentions(message, bot.user)
            if ping_summary:
                try:
                    await message.reply(ping_summary)
                except discord.HTTPException:
                    await message.reply("Не удалось ответить на пинг-вопрос.")
                if memory_enabled:
                    try:
                        append_channel_message(
                            {"channel_history": channel_history},
                            guild_id=getattr(getattr(message, "guild", None), "id", None) or "dm",
                            channel_id=getattr(message.channel, "id", None),
                            message_id=None,
                            author_id=getattr(bot.user, "id", "bot"),
                            author_name=getattr(bot.user, "display_name", None) or getattr(bot.user, "name", "Гена"),
                            content=ping_summary,
                            role="bot",
                        )
                        save_memory()
                    except Exception:
                        pass
                return

            # Проверяем наличие изображений в сообщении
            image_content = ""
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                        print(f" Найдено изображение: {attachment.filename}")

                        try:
                            # Получаем настройку режима распознавания
                            vision_mode = "auto"  # по умолчанию
                            user_id_str = str(message.author.id)
                            if user_id_str in user_memory and "vision_mode" in user_memory[user_id_str]:
                                vision_mode = user_memory[user_id_str]["vision_mode"]

                            # Скачиваем изображение
                            image_bytes = await attachment.read()

                            # Распознаем изображение: сначала мультимодальная модель, затем OCR fallback.
                            result = await analyze_image_for_message(image_bytes, attachment.filename, vision_mode)

                            if "error" not in result:
                                # Формируем описание изображения
                                description_parts = []

                                if result.get("text"):
                                    description_parts.append(f" **Текст на изображении:**\n{result['text']}")

                                if result.get("description"):
                                    description_parts.append(f" **Описание изображения:**\n{result['description']}")

                                if result.get("image_info"):
                                    info = result["image_info"]
                                    description_parts.append(f" **Информация:** {info.get('size', 'N/A')} | {info.get('format', 'N/A')}")

                                if description_parts:
                                    image_content = "\n\n" + "\n\n".join(description_parts)
                                    print(f" Изображение распознано методом: {result.get('method_used', 'unknown')} ({vision_mode})")
                                else:
                                    image_content = "\n\n **Изображение получено, но распознать не удалось**"
                            else:
                                image_content = f"\n\n **Ошибка распознавания:** {result['error']}"

                        except Exception as e:
                            print(f" Ошибка обработки изображения: {e}")
                            image_content = f"\n\n **Не удалось обработать изображение:** {str(e)}"

            # Получаем настройку эффекта пользователя
            user_id_str = str(message.author.id)
            effect_mode = "realistic"  # по умолчанию

            if user_id_str in user_memory and "effect_mode" in user_memory[user_id_str]:
                effect_mode = user_memory[user_id_str]["effect_mode"]
            elif effect_mode == "random":
                effect_mode = random.choice(['realistic', 'animated', 'burst', 'simple'])

            print(f" Выбран эффект: {effect_mode}")

            # ЗАПУСКАЕМ ЭФФЕКТ ПЕЧАТАНИЯ ПЕРЕД ОБРАБОТКОЙ
            if effect_mode == 'realistic':
                # Запускаем длительный эффект для realistic
                print(" Запуск реалистичной печатания...")
                typing_task = asyncio.create_task(animated_typing_effect(message.channel, min_duration=5.0, max_duration=10.0))

            elif effect_mode == 'animated':
                # Запускаем анимированный эффект
                print(" Анимированная печатание...")
                typing_task = asyncio.create_task(animated_typing_effect(message.channel, min_duration=4.0, max_duration=8.0))

            elif effect_mode == 'burst':
                # Запускаем вспышки (дольше обычного)
                print(" Длительные вспышки печатания...")
                typing_task = asyncio.create_task(burst_typing_effect(message.channel, bursts=5))

            elif effect_mode == 'simple':
                # Простой эффект
                print(" Простое печатание...")
                typing_task = asyncio.create_task(typing_only_effect(message.channel, duration=3.0))

            elif effect_mode == 'random':
                # Случайный эффект
                chosen = random.choice(['realistic', 'animated', 'burst', 'simple'])
                print(f" Случайный эффект: {chosen}")
                if chosen == 'realistic':
                    typing_task = asyncio.create_task(animated_typing_effect(message.channel, min_duration=5.0, max_duration=10.0))
                elif chosen == 'animated':
                    typing_task = asyncio.create_task(animated_typing_effect(message.channel, min_duration=4.0, max_duration=8.0))
                elif chosen == 'burst':
                    typing_task = asyncio.create_task(burst_typing_effect(message.channel, bursts=5))
                else:
                    typing_task = asyncio.create_task(typing_only_effect(message.channel, duration=3.0))
            else:
                typing_task = asyncio.create_task(typing_only_effect(message.channel, duration=3.0))

            # ВЫЗЫВАЕМ ОТВЕТ БОТА
            response = await get_ollama_response(
                message.content,
                message.author.id,
                message.author.name,
                guild_id=getattr(getattr(message, "guild", None), "id", None) or "dm",
                channel_id=getattr(message.channel, "id", None),
                channel_name=getattr(message.channel, "name", None),
                author_display_name=getattr(message.author, "display_name", message.author.name),
                attachments_context=image_content,
                current_message_id=getattr(message, "id", None),
            )
            response = sanitize_bot_response(response)

            # Дожидаемся завершения эффекта печатания
            await typing_task

            # ОТПРАВЛЯЕМ ОТВЕТ (ЭФФЕКТ УЖЕ ЗАВЕРШЕН)
            try:
                await message.reply(response)
            except discord.HTTPException as http_error:
                # Частый кейс: 50006 Cannot send an empty message
                logger.error(" Ошибка отправки ответа в Discord", http_error)
                await message.reply("Не удалось отправить ответ. Повтори запрос, пожалуйста.")
            print(" Ответ отправлен в Discord")

            if memory_enabled:
                try:
                    append_channel_message(
                        {"channel_history": channel_history},
                        guild_id=getattr(getattr(message, "guild", None), "id", None) or "dm",
                        channel_id=getattr(message.channel, "id", None),
                        message_id=None,
                        author_id=getattr(bot.user, "id", "bot"),
                        author_name=getattr(bot.user, "display_name", None) or getattr(bot.user, "name", "Гена"),
                        content=response,
                        role="bot",
                    )
                    save_memory()
                except Exception as memory_error:
                    logger.debug(f"Не удалось сохранить ответ в память: {memory_error}")

            # Логируем тип эффекта
            print(f" Использован эффект: {effect_mode}")
    except Exception as e:
        logger.error(" Ошибка в on_message", e)
        logger.debug(traceback.format_exc())

# Глобальная обработка ошибок slash-команд
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    logger.error(" Ошибка slash-команды", error)
    try:
        if interaction.response.is_done():
            await interaction.followup.send(" Произошла ошибка при выполнении команды.", ephemeral=True)
        else:
            await interaction.response.send_message(" Произошла ошибка при выполнении команды.", ephemeral=True)
    except Exception:
        pass

@bot.event
async def on_ready():
    logger.discord("=" * 50)
    logger.discord(" Запуск...")
    logger.discord(f" Пользователь: {bot.user}")
    logger.discord(f" ID: {getattr(bot.user, 'id', None)}")
    logger.discord("=" * 50)
    
    print(f'Бот {bot.user} запущен!')
    
    # Синхронизация команд (фикс /help)
    try:
        logger.discord(" Синхронизация slash-команд...")
        synced = await bot.tree.sync()
        logger.discord(f" Global-synced {len(synced)} commands")
        print(f" Global-synced {len(synced)} commands")
        
        for cmd in synced:
            logger.discord(f" Команда: /{cmd.name} - {cmd.description}")
            
    except Exception as e:
        logger.error("Ошибка синхронизации команд", e)
        print(f" Global sync failed: {e}")

    # Активность бота (Activities)
    try:
        await bot.change_presence(activity=discord.Game(name="мини-игры: /game"))
    except Exception as e:
        logger.error("Ошибка установки активности", e)
    
    # Отправляем сообщение о готовности
    channels_list = [int(cid) for cid in allowed_channels]
    found_channel = None
    missing_channels = []
    for channel_id in channels_list:
        channel = bot.get_channel(channel_id)
        if not channel:
            try:
                channel = await bot.fetch_channel(channel_id)
            except Exception:
                channel = None
        if channel:
            found_channel = channel
            break
        missing_channels.append(str(channel_id))

    if found_channel:
        await found_channel.send("**Гена готов к работе!**\nМожете задавать вопросы, я буду отвечать через локальную нейросеть Ollama.\n**🔧 Tool-Calling активирован** - точные знания без галлюцинаций!")

        # Если первый найденный канал не первый в списке — обновляем порядок
        if config.get("allowed_channels"):
            reordered = [str(getattr(found_channel, "id", ""))] + [cid for cid in config["allowed_channels"] if cid != str(getattr(found_channel, "id", ""))]
            if reordered != config["allowed_channels"]:
                config["allowed_channels"] = reordered
                save_config(config)
                logger.discord(f" Обновлен порядок allowed_channels: первый найденный канал {getattr(found_channel, 'id', None)}")

        # Инициализация игровых модулей
        if GAMES_ENABLED:
            try:
                logger.discord(" Подключение игровых модулей...")
                if setup_games is not None:
                    setup_games(bot)
                logger.discord(" Игровые модули успешно подключены!")
                
                # Отправляем сообщение об игровых возможностях
                await found_channel.send("🎮 **Игровые модули активированы!**\nИспользуйте `!game` для начала игры!")
            except Exception as e:
                logger.error("Ошибка подключения игровых модулей", e)
    else:
        if missing_channels:
            logger.discord(f" Каналы не найдены: {', '.join(missing_channels)}")
        logger.discord(" Нет доступных каналов для отправки сообщения")
    
    logger.discord("=" * 50)
    logger.discord("LOG 1 ")
    logger.discord(" LOG 2 ")
    logger.discord(" LOG 3 ")
    logger.discord("=" * 50)
    print(f'Бот {bot.user} полностью готов к работе')

    # Завершаем декоративную загрузку только после полного старта
    try:
        logger.loading_end()
    except Exception:
        pass

    # Возвращаем print и выводим ранние сообщения после загрузки
    try:
        _flush_early_logs()
    except Exception:
        pass
    try:
        logger.loading_flush()
    except Exception:
        pass

# Загружаем переменные окружения
logger.system("Загрузка переменных окружения...")
logger.loading_step("Загрузка переменных окружения...")

# Декоративную загрузку завершим после полного старта

# Логируем версию Discord библиотеки и возможности voice receive
try:
    logger.system(f"Discord lib version: {getattr(discord, '__version__', 'unknown')}")
    if not hasattr(discord, "sinks"):
        logger.error(" Для приема аудио нужен py-cord (discord.sinks отсутствует)")
except Exception:
    pass

if not DISCORD_TOKEN:
    logger.error(" DISCORD_TOKEN не найден в .env файле")
    print(" Ошибка: DISCORD_TOKEN не найден в .env файле")
    exit(1)

logger.info(f" DISCORD_TOKEN загружен (длина: {len(DISCORD_TOKEN)})")
logger.info(f" OLLAMA_API_KEY загружен: {'ДА' if OLLAMA_API_KEY else 'НЕТ'}")

# Логируем системную информацию при запуске
logger.log_system_info()

# ==================== BOT WITH RECONNECT =====================
async def run_bot_with_reconnect():
    """Запуск бота с автоматическим переподключением"""
    global reconnect_manager
    
    while True:
        try:
            print(" Запуск...")
            try:
                await bot.start(DISCORD_TOKEN, reconnect=True)
            finally:
                # Гарантированно закрываем сессию при остановке
                if not bot.is_closed():
                    await bot.close()
            
        except Exception as e:
            error_msg = str(e)
            print(f" Ошибка подключения: {error_msg}")
            
            # Анализируем ошибку
            is_new_error = reconnect_manager.add_error(error_msg)
            
            # Проверяем, нужно ли переподключаться
            if not reconnect_manager.should_reconnect():
                print(" Прекращаем попытки переподключения")
                break
            
            # Ожидаем перед переподключением
            reconnect_manager.wait_before_reconnect()
            
            print(" Пытаемся переподключиться...")
        else:
            print(" Бот успешно запущен")
            break

async def _graceful_shutdown():
    try:
        if not bot.is_closed():
            await bot.close()
    except Exception:
        pass
    try:
        if ai_tools is not None and hasattr(ai_tools, "close_session"):
            await ai_tools.close_session()
    except Exception:
        pass

def run_main_loop():
    """Запускает py-cord бота на loop, к которому он был привязан при создании."""
    loop = getattr(bot, "loop", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_bot_with_reconnect())
    finally:
        try:
            loop.run_until_complete(_graceful_shutdown())
        finally:
            pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

def _ensure_dirs_for_save_reactions():
    try:
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        backups_dir = os.path.join(os.path.dirname(__file__), 'logs', 'save_reactions_backups')
        os.makedirs(backups_dir, exist_ok=True)
        return log_dir, backups_dir
    except Exception:
        return None, None


def _audit_save_reactions_action(action: str, actor: str | None = None, details: dict | None = None, prev_config: dict | None = None):
    """Записывает аудит и создает бэкап предыдущей конфигурации перед изменением save_reactions."""
    try:
        log_dir, backups_dir = _ensure_dirs_for_save_reactions()
        ts = time.strftime('%Y%m%dT%H%M%S', time.gmtime())
        
        # Гарантируем, что actor всегда будет строкой (str), даже если пришел None
        actor_str = str(actor or os.getenv('USERNAME') or os.getenv('USER') or 'cli')
        
        audit = {
            'timestamp': ts,
            'actor': actor_str,
            'action': action,
            'details': details or {}
        }
        # Сохраняем бэкап предыдущей конфигурации
        if backups_dir and prev_config is not None:
            try:
                backup_path = os.path.join(backups_dir, f'backup_{ts}.json')
                with open(backup_path, 'w', encoding='utf-8') as bf:
                    json.dump(prev_config, bf, ensure_ascii=False, indent=2)
                audit['backup_path'] = backup_path
            except Exception:
                pass
        # Пишем запись аудита в файл
        try:
            audit_path = os.path.join(os.path.dirname(__file__), 'logs', 'save_reactions_audit.log')
            with open(audit_path, 'a', encoding='utf-8') as af:
                af.write(json.dumps(audit, ensure_ascii=False) + "\n")
        except Exception:
            # fallback to logger (avoid recursion if logger uses print)
            try:
                _saved_print = _builtins.print
                try:
                    _builtins.print = _orig_print
                    logger._write(f"AUDIT: {json.dumps(audit, ensure_ascii=False)}")
                finally:
                    _builtins.print = _saved_print
            except Exception:
                pass
    except Exception:
        pass

def _list_backups(limit: int = 20):
    log_dir, backups_dir = _ensure_dirs_for_save_reactions()
    if not backups_dir or not os.path.exists(backups_dir):
        return []
    files = [f for f in os.listdir(backups_dir) if f.startswith('backup_') and f.endswith('.json')]
    files.sort(reverse=True)
    return [os.path.join(backups_dir, f) for f in files[:limit]]


def _restore_backup(path: str) -> bool:
    try:
        if not os.path.exists(path):
            return False
        with open(path, 'r', encoding='utf-8') as pf:
            data = json.load(pf)
        if not isinstance(data, dict):
            return False
        # apply
        globals()['save_reactions_default'] = bool(data.get('save_reactions_default', False))
        globals()['save_reactions'] = {str(k): bool(v) for k, v in (data.get('save_reactions') or {}).items()}
        if not isinstance(config, dict):
            cfg = {}
        else:
            cfg = config
        cfg['save_reactions_default'] = bool(data.get('save_reactions_default', False))
        cfg['save_reactions'] = {str(k): bool(v) for k, v in (data.get('save_reactions') or {}).items()}
        save_config(cfg)
        globals()['config'] = cfg
        return True
    except Exception:
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gena Discord Bot — управление и запуск")
    subparsers = parser.add_subparsers(dest='cmd')

    # start (default) - запускает бота
    subparsers.add_parser('start', help='Запустить бота (по умолчанию)')

    # config show
    subparsers.add_parser('config-show', help='Показать текущий bot_config.json')

    # config set
    cfg_set = subparsers.add_parser('config-set', help='Установить ключ конфигурации и сохранить')
    cfg_set.add_argument('key')
    cfg_set.add_argument('value')

    # toggle console
    tc = subparsers.add_parser('toggle-console', help='Включить/выключить вывод логов в консоль')
    tc.add_argument('enable', choices=['on','off'])

    # personas list
    subparsers.add_parser('personas-list', help='Показать доступные персоны')

    # personas set for user
    ps_set = subparsers.add_parser('personas-set', help='Назначить персону пользователю')
    ps_set.add_argument('user_id')
    ps_set.add_argument('persona')

    # learn add
    learn_add = subparsers.add_parser('learn-add', help='Добавить/обновить знание (CLI)')
    learn_add.add_argument('key')
    learn_add.add_argument('explanation')
    learn_add.add_argument('--overwrite', action='store_true')

    # logs view
    logs_view = subparsers.add_parser('logs-view', help='Просмотреть логи')
    logs_view.add_argument('--lines', type=int, default=200)

    # toggle-save-reactions: scope = guild_id or 'global'
    tsr = subparsers.add_parser('toggle-save-reactions', help='Включить/выключить автосохранение реакций для гильдии или глобально')
    tsr.add_argument('scope', help="Guild ID (число) или 'global' для настройки по умолчанию")
    tsr.add_argument('enable', choices=['on','off'], help="on/off")

    # save-reactions-show (CLI)
    sr_show = subparsers.add_parser('save-reactions-show', help='Показать настройки save_reactions (global/per-guild)')
    sr_show.add_argument('scope', nargs='?', default='all', help="Guild ID или 'all'/'global' (по умолчанию all)")

    # save-reactions-clear (CLI)
    sr_clear = subparsers.add_parser('save-reactions-clear', help='Удалить запись save_reactions для гильдии')
    sr_clear.add_argument('guild_id', help='Guild ID (число)')

    # save-reactions-export/import
    sr_export = subparsers.add_parser('save-reactions-export', help='Экспортировать настройки save_reactions в файл JSON')
    sr_export.add_argument('path', nargs='?', default='save_reactions_export.json', help='Путь к файлу (по умолчанию save_reactions_export.json)')

    sr_import = subparsers.add_parser('save-reactions-import', help='Импортировать настройки save_reactions из JSON файла')
    sr_import.add_argument('path', help='Путь к JSON файлу')
    sr_import.add_argument('--yes', action='store_true', help='Не спрашивать подтверждение и применить изменения')
    sr_import.add_argument('--preview', action='store_true', help='Показать изменения без применения (dry-run)')

    # undo (restore last backup)
    sr_undo = subparsers.add_parser('save-reactions-undo', help='Откатить последние изменения save_reactions (по умолчанию последний бэкап)')
    sr_undo.add_argument('--steps', type=int, default=1, help='Сколько бэков назад откатиться (по умолчанию 1)')

    # history (list backups)
    sr_hist = subparsers.add_parser('save-reactions-history', help='Показать список бэкапов save_reactions')
    sr_hist.add_argument('--limit', type=int, default=20, help='Сколько записей показать')

    # default to start if no args
    args = parser.parse_args()
    if not args.cmd:
        args.cmd = 'start'

    try:
        if args.cmd == 'config-show':
            print(json.dumps(config, ensure_ascii=False, indent=2))
            sys.exit(0)

        if args.cmd == 'config-set':
            k = args.key
            v_raw = args.value
            try:
                v = json.loads(v_raw)
            except Exception:
                v = v_raw
            config[k] = v
            save_config(config)
            # apply important runtime option
            if k == 'console_logging':
                if hasattr(logger, 'set_console'):
                    logger.set_console(bool(v))
                else:
                    logger.console = bool(v)
            print(f"OK: set {k} = {v}")
            sys.exit(0)

        if args.cmd == 'toggle-console':
            enable = args.enable == 'on'
            config['console_logging'] = enable
            save_config(config)
            if hasattr(logger, 'set_console'):
                logger.set_console(enable)
            else:
                logger.console = enable
            print(f"Console logging {'enabled' if enable else 'disabled'}")
            sys.exit(0)

        if args.cmd == 'personas-list':
            print(json.dumps(PERSONAS, ensure_ascii=False, indent=2))
            sys.exit(0)

        if args.cmd == 'personas-set':
            uid = args.user_id
            persona = args.persona
            if persona not in PERSONAS:
                print(f"ERROR: persona '{persona}' not found")
                sys.exit(2)
            set_user_persona(uid, persona)
            save_personas()
            print(f"OK: persona '{persona}' set for user {uid}")
            sys.exit(0)

        if args.cmd == 'learn-add':
            key = args.key.strip()
            explanation = args.explanation.strip()
            ow = args.overwrite
            if not key or not explanation:
                print("ERROR: key and explanation required")
                sys.exit(2)
            existed = key in global_knowledge
            if existed and not ow:
                print("ERROR: key exists. Use --overwrite to force")
                sys.exit(2)
            try:
                from datetime import datetime
                now_iso = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
            except Exception:
                now_iso = str(int(time.time()))
            author_id = 'cli'
            author_name = os.getenv('USERNAME') or os.getenv('USER') or 'cli'
            entry = global_knowledge.get(key, {}) if existed else {}
            if not entry.get('created_at'):
                entry['created_at'] = now_iso
            entry['explanation'] = explanation
            entry['updated_at'] = now_iso
            entry['last_author_id'] = author_id
            entry['last_author_name'] = author_name
            global_knowledge[key] = entry
            save_knowledge(global_knowledge)
            print(f"OK: knowledge {'updated' if existed else 'added'}: {key}")
            sys.exit(0)

        if args.cmd == 'logs-view':
            lines = args.lines
            log_path = getattr(logger, '_log_path', None)
            if not log_path or not os.path.exists(log_path):
                print('No log file found:', log_path)
                sys.exit(1)
            with open(log_path, 'r', encoding='utf-8') as lf:
                all_lines = lf.readlines()
            tail = all_lines[-lines:]
            print(''.join(tail))
            sys.exit(0)

        if args.cmd == 'save-reactions-show':
            scope = args.scope or 'all'
            try:
                # Show global default and per-guild settings
                if scope in ('all', 'global'):
                    print('save_reactions_default:', bool(globals().get('save_reactions_default', False)))
                    per = globals().get('save_reactions', {}) or {}
                    if not per:
                        print('Per-guild save_reactions: (none)')
                    else:
                        print('Per-guild save_reactions:')
                        for gid, val in per.items():
                            print(f"  {gid}: {val}")
                    sys.exit(0)
                else:
                    gid = str(scope)
                    per = globals().get('save_reactions', {}) or {}
                    if gid in per:
                        print(f"Guild {gid}: save_reactions = {bool(per[gid])}")
                    else:
                        print(f"Guild {gid}: not set, default = {bool(globals().get('save_reactions_default', False))}")
                    sys.exit(0)
            except Exception as e:
                print(f"ERROR: {e}")
                sys.exit(2)

        if args.cmd == 'save-reactions-clear':
            gid = str(args.guild_id)
            try:
                # audit + backup
                prev = dict(config) if isinstance(config, dict) else {}
                actor = os.getenv('USERNAME') or os.getenv('USER') or 'cli'
                _audit_save_reactions_action('clear', actor=actor, details={'guild_id': gid}, prev_config=prev)

                # remove from runtime
                if gid in globals().get('save_reactions', {}):
                    globals()['save_reactions'].pop(gid, None)
                # remove from persisted config
                if not isinstance(config, dict):
                    cfg = {}
                else:
                    cfg = config
                if cfg.get('save_reactions') and gid in cfg['save_reactions']:
                    cfg['save_reactions'].pop(gid, None)
                    save_config(cfg)
                    globals()['config'] = cfg
                print(f"OK: cleared save_reactions for guild {gid}")
                sys.exit(0)
            except Exception as e:
                print(f"ERROR: {e}")
                sys.exit(2)

        if args.cmd == 'save-reactions-export':
            path = args.path
            try:
                out = {
                    'save_reactions_default': bool(globals().get('save_reactions_default', False)),
                    'save_reactions': globals().get('save_reactions', {}) or {}
                }
                # audit export
                actor = os.getenv('USERNAME') or os.getenv('USER') or 'cli'
                _audit_save_reactions_action('export', actor=actor, details={'path': path}, prev_config=dict(config) if isinstance(config, dict) else None)
                with open(path, 'w', encoding='utf-8') as outf:
                    json.dump(out, outf, ensure_ascii=False, indent=2)
                print(f"OK: exported save_reactions to {path}")
                sys.exit(0)
            except Exception as e:
                print(f"ERROR: {e}")
                sys.exit(2)

        if args.cmd == 'save-reactions-import':
            path = args.path
            try:
                if not os.path.exists(path):
                    print(f"ERROR: file not found: {path}")
                    sys.exit(2)
                with open(path, 'r', encoding='utf-8') as inf:
                    data = json.load(inf)
                if not isinstance(data, dict):
                    print("ERROR: invalid file format (expected JSON object)")
                    sys.exit(2)
                # Validate
                default_val = bool(data.get('save_reactions_default', globals().get('save_reactions_default', False)))
                per = data.get('save_reactions', {}) or {}
                if not isinstance(per, dict):
                    print("ERROR: invalid save_reactions map in file")
                    sys.exit(2)

                # PREVIEW: show what would change and exit
                if getattr(args, 'preview', False):
                    print('Preview import of save_reactions:')
                    print('  save_reactions_default:', default_val)
                    if not per:
                        print('  Per-guild: (none)')
                    else:
                        print('  Per-guild:')
                        for k, v in per.items():
                            print(f"    {k}: {bool(v)}")
                    sys.exit(0)

                # Confirm unless --yes
                if not getattr(args, 'yes', False):
                    print('The following changes will be applied:')
                    print('  save_reactions_default:', default_val)
                    if not per:
                        print('  Per-guild: (none)')
                    else:
                        print('  Per-guild:')
                        for k, v in per.items():
                            print(f"    {k}: {bool(v)}")
                    try:
                        ans = input('Apply changes? [y/N]: ')
                    except KeyboardInterrupt:
                        print('\nAborted by user')
                        sys.exit(1)
                    if not ans or ans.strip().lower()[0] != 'y':
                        print('Aborted.')
                        sys.exit(0)

                # audit + backup (previous config)
                prev = dict(config) if isinstance(config, dict) else {}
                actor = os.getenv('USERNAME') or os.getenv('USER') or 'cli'
                _audit_save_reactions_action('import', actor=actor, details={'path': path}, prev_config=prev)

                # Apply to runtime
                globals()['save_reactions_default'] = default_val
                globals()['save_reactions'] = {str(k): bool(v) for k, v in per.items()}
                # Persist into config
                if not isinstance(config, dict):
                    cfg = {}
                else:
                    cfg = config
                cfg['save_reactions_default'] = default_val
                cfg['save_reactions'] = {str(k): bool(v) for k, v in per.items()}
                save_config(cfg)
                globals()['config'] = cfg
                print(f"OK: imported save_reactions from {path}")
                sys.exit(0)
            except Exception as e:
                print(f"ERROR: {e}")
                sys.exit(2)

        if args.cmd == 'save-reactions-undo':
            steps = args.steps or 1
            try:
                backups = _list_backups(limit=steps + 5)
                if not backups:
                    print('No backups found to restore')
                    sys.exit(1)
                target = backups[steps - 1] if len(backups) >= steps else backups[-1]
                ok = _restore_backup(target)
                if ok:
                    actor = os.getenv('USERNAME') or os.getenv('USER') or 'cli'
                    _audit_save_reactions_action('undo', actor=actor, details={'restored': target}, prev_config=dict(config) if isinstance(config, dict) else None)
                    print(f'OK: restored backup {target}')
                    sys.exit(0)
                else:
                    print('ERROR: failed to restore backup')
                    sys.exit(2)
            except Exception as e:
                print(f"ERROR: {e}")
                sys.exit(2)

        if args.cmd == 'save-reactions-history':
            limit = args.limit or 20
            try:
                backups = _list_backups(limit=limit)
                if not backups:
                    print('No backups available')
                    sys.exit(0)
                for b in backups:
                    print(b)
                sys.exit(0)
            except Exception as e:
                print(f"ERROR: {e}")
                sys.exit(2)

        if args.cmd == 'toggle-save-reactions':
            scope = args.scope
            enable = args.enable == 'on'
            try:
                # audit + backup
                prev = dict(config) if isinstance(config, dict) else {}
                actor = os.getenv('USERNAME') or os.getenv('USER') or 'cli'
                _audit_save_reactions_action('toggle', actor=actor, details={'scope': scope, 'enable': enable}, prev_config=prev)

                if scope in ('global', 'default'):
                    # update global default
                    config['save_reactions_default'] = bool(enable)
                    # update runtime variable
                    globals()['save_reactions_default'] = bool(enable)
                    save_config(config)
                    print(f"OK: save_reactions_default set to {enable}")
                    sys.exit(0)
                else:
                    gid = str(scope)
                    # update runtime map
                    save_reactions[gid] = bool(enable)
                    # ensure config dict
                    if not isinstance(config, dict):
                        cfg = {}
                    else:
                        cfg = config
                    cfg.setdefault('save_reactions', {})
                    cfg['save_reactions'][gid] = bool(enable)
                    # persist
                    save_config(cfg)
                    globals()['config'] = cfg
                    print(f"OK: save_reactions for guild {gid} set to {enable}")
                    sys.exit(0)
            except Exception as e:
                print(f"ERROR: {e}")
                sys.exit(2)

        # start the bot
        if args.cmd == 'start':
            # allow CLI override to enable console logging for this run
            if config.get('console_logging'):
                try:
                    if hasattr(logger, 'set_console'):
                        logger.set_console(True)
                    else:
                        logger.console = True
                except Exception:
                    pass
            
            # Временно возвращаем оригинальный print, чтобы увидеть критическую ошибку падения
            import builtins as _builtins
            if '_orig_print' in globals():
                _builtins.print = _orig_print
                
            print("=" * 50)
            print(" Запуск...")
            print(" Автоматическое переподключение включено")
            print("=" * 50)
            
            try:
                run_main_loop()
            except Exception as e:
                print("\n" + "💥" * 20)
                print("КРИТИЧЕСКАЯ ОШИБКА ВНУТРИ run_main_loop():")
                print("💥" * 20)
                traceback.print_exc(file=sys.stdout)
                print("=" * 50 + "\n")
                sys.exit(1)

    except KeyboardInterrupt:
        print("\n Отключено администратором")
    except SystemExit:
        pass
    except Exception as e:
        print(f"💀 Критическая ошибка: 💀 {e}")
        print(" Проверьте настройки и перезапустите...")
        import traceback
        traceback.print_exc()

