#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Инструменты для AI ассистента Геннадий 2.0
Время, погода, новости, калькулятор и т.д.
"""

import asyncio
import aiohttp
import json
import re
import math
import atexit
from datetime import datetime, timezone
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class AITools:
    """Класс с инструментами для AI ассистента"""
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_timeout = 300  # 5 минут кэша
    
    async def get_session(self):
        """Получаем HTTP сессию"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self.session
    
    async def close_session(self):
        """Закрываем HTTP сессию"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_cache_key(self, tool: str, params: str) -> str:
        """Генерирует ключ кэша"""
        return f"{tool}:{params}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Проверяет валидность кэша"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get('timestamp', 0)
        current_time = datetime.now().timestamp()
        return (current_time - cached_time) < self.cache_timeout
    
    def _set_cache(self, cache_key: str, data: Any):
        """Устанавливает кэш"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
    
    def _get_cache(self, cache_key: str) -> Optional[Any]:
        """Получает данные из кэша"""
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        return None
    
    async def get_current_time(self, location: str = "UTC") -> Dict[str, Any]:
        """Получает текущее время"""
        cache_key = self._get_cache_key("time", location)
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            if location.upper() == "UTC":
                now = datetime.now(timezone.utc)
                result = {
                    "time": now.strftime("%H:%M:%S"),
                    "date": now.strftime("%Y-%m-%d"),
                    "day": now.strftime("%A"),
                    "timezone": "UTC",
                    "timestamp": now.timestamp()
                }
            else:
                # Для других локаций используем простое определение
                now = datetime.now()
                result = {
                    "time": now.strftime("%H:%M:%S"),
                    "date": now.strftime("%Y-%m-%d"),
                    "day": now.strftime("%A"),
                    "timezone": location,
                    "timestamp": now.timestamp()
                }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения времени: {e}")
            return {"error": f"Не удалось получить время: {str(e)}"}
    
    async def get_weather(self, location: str = "Moscow") -> Dict[str, Any]:
        """Получает погоду (симуляция для демонстрации)"""
        cache_key = self._get_cache_key("weather", location)
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            # Симуляция данных погоды (в реальном приложении здесь будет API запрос но мне щас лень)
            weather_data = {
                "location": location,
                "temperature": f"{15 + hash(location) % 20}°C",
                "condition": ["Солнечно", "Облачно", "Дождь", "Снег"][hash(location) % 4],
                "humidity": f"{40 + hash(location) % 40}%",
                "wind": f"{5 + hash(location) % 15} км/ч",
                "pressure": f"{740 + hash(location) % 20} мм рт. ст.",
                "feels_like": f"{13 + hash(location) % 18}°C",
                "updated": datetime.now().strftime("%H:%M")
            }
            
            self._set_cache(cache_key, weather_data)
            return weather_data
            
        except Exception as e:
            logger.error(f"Ошибка получения погоды: {e}")
            return {"error": f"Не удалось получить погоду: {str(e)}"}
    
    async def calculate(self, expression: str) -> Dict[str, Any]:
        """Выполняет математические вычисления"""
        try:
            # Безопасная оценка математических выражений
            allowed_names = {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow, "sqrt": math.sqrt,
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "log": math.log, "log10": math.log10, "pi": math.pi,
                "e": math.e
            }
            
            # Очищаем выражение
            expression = expression.replace("^", "**")
            expression = re.sub(r"[^\d+\-*/().\s,a-zA-Z_]", "", expression)
            
            # Вычисляем
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            
            return {
                "expression": expression,
                "result": result,
                "type": type(result).__name__
            }
            
        except Exception as e:
            return {"error": f"Ошибка вычисления: {str(e)}"}
    
    async def get_news(self, category: str = "general", count: int = 5) -> Dict[str, Any]:
        """Получает новости (симуляция для демонстрации)"""
        cache_key = self._get_cache_key("news", f"{category}:{count}")
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            # Симуляция новостей (в реальном приложении здесь будет API запрос так же лень)
            news_templates = [
                "Новые технологии меняют мир: {topic}",
                "Ученые сделали открытие в области {topic}",
                "Экономические новости: {topic}",
                "Спортивные события: {topic}",
                "Культурные события: {topic}"
            ]
            
            topics = ["искусственного интеллекта", "медицины", "образования", "экологии", "экономики"]
            
            news_items = []
            for i in range(min(count, len(news_templates))):
                template = news_templates[i % len(news_templates)]
                topic = topics[i % len(topics)]
                news_items.append({
                    "title": template.format(topic=topic),
                    "description": f"Подробная информация о {topic}",
                    "time": f"{i}ч назад",
                    "source": f"Источник {i+1}"
                })
            
            result = {
                "category": category,
                "count": len(news_items),
                "news": news_items,
                "updated": datetime.now().strftime("%H:%M")
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения новостей: {e}")
            return {"error": f"Не удалось получить новости: {str(e)}"}
    
    async def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """Конвертация валют (симуляция)"""
        try:
            # Симуляция курсов (в реальном приложении здесь будет API запрос) леееень
            rates = {
                "USD": 1.0,
                "EUR": 0.85,
                "RUB": 90.0,
                "GBP": 0.73,
                "CNY": 7.2,
                "JPY": 110.0
            }
            
            from_currency = from_currency.upper()
            to_currency = to_currency.upper()
            
            if from_currency not in rates or to_currency not in rates:
                return {"error": "Неподдерживаемая валюта"}
            
            # Конвертируем через USD
            amount_in_usd = amount / rates[from_currency]
            result = amount_in_usd * rates[to_currency]
            
            return {
                "amount": amount,
                "from": from_currency,
                "to": to_currency,
                "result": round(result, 2),
                "rate": rates[to_currency] / rates[from_currency]
            }
            
        except Exception as e:
            return {"error": f"Ошибка конвертации: {str(e)}"}
    
    async def get_definition(self, word: str) -> Dict[str, Any]:
        """Получает определение слова (симуляция)"""
        cache_key = self._get_cache_key("definition", word.lower())
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            # Простая симуляция словаря
            definitions = {
                "искусственный интеллект": "Система способная обучаться и принимать решения",
                "программирование": "Процесс создания компьютерных программ",
                "алгоритм": "Последовательность инструкций для решения задачи",
                "данные": "Информация представленная в формализованном виде"
            }
            
            word_lower = word.lower()
            if word_lower in definitions:
                result = {
                    "word": word,
                    "definition": definitions[word_lower],
                    "source": "Внутренний словарь"
                }
            else:
                result = {
                    "word": word,
                    "definition": f"Определение для слова '{word}' не найдено",
                    "source": "Внутренний словарь"
                }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            return {"error": f"Ошибка получения определения: {str(e)}"}
    
    async def translate_text(self, text: str, from_lang: str, to_lang: str) -> Dict[str, Any]:
        """Перевод текста (симуляция)"""
        try:
            # Простая симуляция перевода
            if from_lang.lower() == to_lang.lower():
                return {
                    "original": text,
                    "translated": text,
                    "from": from_lang,
                    "to": to_lang,
                    "note": "Языки совпадают"
                }
            
            # В реальном приложении здесь будет API переводчика
            translated_text = f"[Перевод с {from_lang} на {to_lang}]: {text}"
            
            return {
                "original": text,
                "translated": translated_text,
                "from": from_lang,
                "to": to_lang,
                "confidence": 0.95
            }
            
        except Exception as e:
            return {"error": f"Ошибка перевода: {str(e)}"}
    
    async def get_random_fact(self) -> Dict[str, Any]:
        """Получает случайный факт"""
        try:
            facts = [
                "Каждый год Земля проходит 1.6 миллиона километров в космосе",
                "Ось Земли наклонена на 23.5 градусов",
                "Сердце кита может биться всего 9 раз в минуту",
                "Медузы существуют более 650 миллионов лет",
                "Человек может различать около 1 миллиона различных цветов",
                "Пчелы могут видеть ультрафиолет",
                "Каждую секунду Солнце теряет 4 миллиона тонн массы"
            ]
            
            import random
            fact = random.choice(facts)
            
            return {
                "fact": fact,
                "category": "Наука",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Ошибка получения факта: {str(e)}"}
    
    def detect_tool_intent(self, message: str) -> Optional[Dict[str, Any]]:
        """Определяет какой инструмент нужен по сообщению"""
        message_lower = message.lower()
        
        # Время
        if any(word in message_lower for word in ["время", "час", "сейчас", "который час"]):
            return {"tool": "time", "params": {}}
        
        # Погода
        if any(word in message_lower for word in ["погода", "температура", "дождь", "солнце"]):
            location = "Moscow"  # Можно улучшить извлечением локации
            return {"tool": "weather", "params": {"location": location}}
        
        # Калькулятор
        if any(word in message_lower for word in ["посчитай", "вычисли", "сколько", "+", "-", "*", "/"]):
            # Извлекаем математическое выражение
            math_expr = re.search(r'[\d+\-*/().\s]+', message)
            if math_expr:
                return {"tool": "calculate", "params": {"expression": math_expr.group()}}
        
        # Новости
        if any(word in message_lower for word in ["новости", "что нового", "события"]):
            return {"tool": "news", "params": {"count": 3}}
        
        # Валюта
        if any(word in message_lower for word in ["рубль", "доллар", "евро", "конвертировать"]):
            return {"tool": "currency", "params": {"amount": 100, "from": "USD", "to": "RUB"}}
        
        # Определение
        if any(word in message_lower for word in ["что такое", "определение", "объясни"]):
            # Извлекаем слово после "что такое"
            match = re.search(r'что такое\s+([а-яё\s]+)', message_lower)
            if match:
                word = match.group(1).strip()
                return {"tool": "definition", "params": {"word": word}}
        
        # Перевод
        if any(word in message_lower for word in ["переведи", "translate", "перевод"]):
            return {"tool": "translate", "params": {"text": message, "from": "ru", "to": "en"}}
        
        # Случайный факт
        if any(word in message_lower for word in ["факт", "интересно", "знал ли"]):
            return {"tool": "fact", "params": {}}
        
        return None
    
    async def execute_tool(self, tool_info: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет инструмент"""
        tool_name = tool_info["tool"]
        params = tool_info.get("params", {})
        
        try:
            if tool_name == "time":
                return await self.get_current_time(params.get("location", "UTC"))
            elif tool_name == "weather":
                return await self.get_weather(params.get("location", "Moscow"))
            elif tool_name == "calculate":
                return await self.calculate(params.get("expression", ""))
            elif tool_name == "news":
                return await self.get_news(params.get("category", "general"), params.get("count", 3))
            elif tool_name == "currency":
                return await self.convert_currency(
                    params.get("amount", 100),
                    params.get("from", "USD"),
                    params.get("to", "RUB")
                )
            elif tool_name == "definition":
                return await self.get_definition(params.get("word", ""))
            elif tool_name == "translate":
                return await self.translate_text(
                    params.get("text", ""),
                    params.get("from", "ru"),
                    params.get("to", "en")
                )
            elif tool_name == "fact":
                return await self.get_random_fact()
            else:
                return {"error": f"Неизвестный инструмент: {tool_name}"}
                
        except Exception as e:
            logger.error(f"Ошибка выполнения инструмента {tool_name}: {e}")
            return {"error": f"Ошибка выполнения: {str(e)}"}

# Глобальный экземпляр инструментов
ai_tools = AITools()

def _close_ai_tools_session():
    try:
        if ai_tools.session is None:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(ai_tools.close_session())
        else:
            asyncio.run(ai_tools.close_session())
    except Exception:
        pass

atexit.register(_close_ai_tools_session)
