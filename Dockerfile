FROM python:3.11-slim

# Установка системных утилит и Curl для установки Ollama
RUN apt-get update && apt-get install -y curl procps && rm -rf /var/lib/apt/lists/*

# Скачивание и установка Ollama внутрь контейнера
RUN curl -fsSL https://ollama.com | sh

WORKDIR /app

# Установка библиотек бота
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Даем права на запуск стартового скрипта
RUN chmod +x start.sh

# Запуск через менеджер процессов
CMD ["./start.sh"]
