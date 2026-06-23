#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль распознавания изображений для бота Геннадий 2.0
Поддержка OCR и анализа изображений с помощью различных API
"""

import os
import io
import base64
import tempfile
import requests
import json
from typing import Optional, Dict, List, Any
from PIL import Image, ImageEnhance
import pytesseract
import cv2
import numpy as np

class ImageRecognition:
    def __init__(self):
        # Настройки OCR
        self.tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe' if os.name == 'nt' else '/usr/bin/tesseract'
        
        # API ключи (можно добавить в .env)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.google_vision_key = os.getenv("GOOGLE_VISION_API_KEY", "")
        
        # Поддерживаемые форматы
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        
        # Настройки Tesseract
        if os.name == 'nt' and os.path.exists(self.tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            
    def is_image_file(self, filename: str) -> bool:
        """Проверяет, является ли файл изображением"""
        return any(filename.lower().endswith(ext) for ext in self.supported_formats)
    
    def preprocess_image(self, image_path: str) -> Optional[Image.Image]:
        """Предобработка изображения для лучшего OCR"""
        try:
            # Открываем изображение
            img = Image.open(image_path)
            
            # Конвертируем в RGB если нужно
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Увеличиваем контрастность
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            
            # Увеличиваем резкость
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)
            
            # Увеличиваем размер для лучшего OCR
            if img.width < 1000 or img.height < 1000:
                img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
            
            return img
            
        except Exception as e:
            print(f"❌ Ошибка предобработки изображения: {e}")
            return None
    
    def extract_text_tesseract(self, image_path: str, language: str = 'rus+eng') -> Optional[str]:
        """Извлекает текст с помощью Tesseract OCR"""
        try:
            # Предобработка изображения
            img = self.preprocess_image(image_path)
            if not img:
                return None
            
            # Извлекаем текст
            text = pytesseract.image_to_string(img, lang=language, config='--psm 6')
            
            # Очищаем текст
            text = text.strip()
            if text:
                print(f"✅ Tesseract извлёк текст: {len(text)} символов")
                return text
            else:
                print("⚠️ Tesseract не нашёл текст на изображении")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка Tesseract OCR: {e}")
            return None
    
    def extract_text_google_vision(self, image_path: str) -> Optional[str]:
        """Извлекает текст с помощью Google Vision API"""
        if not self.google_vision_key:
            print("⚠️ Google Vision API ключ не настроен")
            return None
            
        try:
            # Читаем изображение
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            # Подготавливаем запрос
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.google_vision_key}"
            
            data = {
                "requests": [
                    {
                        "image": {
                            "content": base64.b64encode(content).decode('utf-8')
                        },
                        "features": [
                            {
                                "type": "TEXT_DETECTION",
                                "maxResults": 10
                            }
                        ]
                    }
                ]
            }
            
            # Отправляем запрос
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            # Обрабатываем ответ
            result = response.json()
            if 'responses' in result and result['responses']:
                if 'textAnnotations' in result['responses'][0]:
                    texts = result['responses'][0]['textAnnotations']
                    if texts:
                        full_text = texts[0]['description']
                        print(f"✅ Google Vision извлёк текст: {len(full_text)} символов")
                        return full_text.strip()
            
            print("⚠️ Google Vision не нашёл текст на изображении")
            return None
            
        except Exception as e:
            print(f"❌ Ошибка Google Vision API: {e}")
            return None
    
    def analyze_image_openai(self, image_path: str, prompt: str = "Опиши что изображено на этой картинке") -> Optional[str]:
        """Анализирует изображение с помощью OpenAI Vision API"""
        if not self.openai_api_key:
            print("⚠️ OpenAI API ключ не настроен")
            return None
            
        try:
            # Кодируем изображение
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Подготавливаем запрос
            url = "https://api.openai.com/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500
            }
            
            # Отправляем запрос
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            # Обрабатываем ответ
            result = response.json()
            if 'choices' in result and result['choices']:
                description = result['choices'][0]['message']['content']
                print(f"✅ OpenAI проанализировал изображение")
                return description.strip()
            
            print("⚠️ OpenAI не смог проанализировать изображение")
            return None
            
        except Exception as e:
            print(f"❌ Ошибка OpenAI Vision API: {e}")
            return None
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """Получает базовую информацию об изображении"""
        try:
            with Image.open(image_path) as img:
                return {
                    "format": img.format,
                    "size": img.size,
                    "mode": img.mode,
                    "file_size": os.path.getsize(image_path)
                }
        except Exception as e:
            print(f"❌ Ошибка получения информации об изображении: {e}")
            return {}
    
    def recognize_image(self, image_path: str, mode: str = "auto") -> Dict[str, Any]:
        """Основная функция распознавания изображения"""
        if not os.path.exists(image_path):
            return {"error": "Файл не найден"}
        
        if not self.is_image_file(image_path):
            return {"error": "Неподдерживаемый формат файла"}
        
        print(f"🔍 Распознавание изображения: {image_path}")
        print(f"📊 Режим: {mode}")
        
        result = {
            "image_info": self.get_image_info(image_path),
            "text": None,
            "description": None,
            "method_used": None
        }
        
        try:
            if mode == "ocr_only":
                # Только OCR
                text = self.extract_text_tesseract(image_path)
                if text:
                    result["text"] = text
                    result["method_used"] = "tesseract"
                else:
                    # Пробуем Google Vision
                    text = self.extract_text_google_vision(image_path)
                    if text:
                        result["text"] = text
                        result["method_used"] = "google_vision"
                        
            elif mode == "vision_only":
                # Только анализ изображения
                description = self.analyze_image_openai(image_path)
                if description:
                    result["description"] = description
                    result["method_used"] = "openai_vision"
                    
            else:  # auto
                # Пробуем OCR сначала
                text = self.extract_text_tesseract(image_path)
                if text:
                    result["text"] = text
                    result["method_used"] = "tesseract"
                else:
                    # Пробуем Google Vision
                    text = self.extract_text_google_vision(image_path)
                    if text:
                        result["text"] = text
                        result["method_used"] = "google_vision"
                
                # Если есть OpenAI, делаем анализ
                if self.openai_api_key:
                    description = self.analyze_image_openai(image_path)
                    if description:
                        result["description"] = description
                        if not result["method_used"]:
                            result["method_used"] = "openai_vision"
            
            print(f"✅ Распознавание завершено. Метод: {result['method_used']}")
            return result
            
        except Exception as e:
            print(f"❌ Ошибка распознавания изображения: {e}")
            result["error"] = str(e)
            return result

# Глобальный экземпляр
image_recognizer = ImageRecognition()

def recognize_image_from_file(image_path: str, mode: str = "auto") -> Dict[str, Any]:
    """Функция для распознавания изображения из файла"""
    return image_recognizer.recognize_image(image_path, mode)

def recognize_image_from_bytes(image_bytes: bytes, filename: str = "image.png", mode: str = "auto") -> Dict[str, Any]:
    """Функция для распознавания изображения из байтов"""
    suffix = os.path.splitext(filename)[1].lower() or ".png"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(image_bytes)
            temp_path = f.name
        
        result = recognize_image_from_file(temp_path, mode)
            
        return result
        
    except Exception as e:
        print(f"❌ Ошибка обработки изображения из байтов: {e}")
        return {"error": str(e)}
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

if __name__ == "__main__":
    # Тестирование модуля
    print("🧪 Тестирование распознавания изображений")
    
    # Проверяем Tesseract
    try:
        import pytesseract
        print(f"✅ Tesseract доступен: {pytesseract.get_tesseract_version()}")
    except ImportError:
        print("❌ Tesseract не установлен")
    
    # Тест с изображением (если есть)
    test_image = "test_image.png"
    if os.path.exists(test_image):
        result = recognize_image_from_file(test_image)
        print(f"📊 Результат: {result}")
    else:
        print(f"⚠️ Тестовое изображение не найдено: {test_image}")
