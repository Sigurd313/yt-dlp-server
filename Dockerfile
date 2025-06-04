FROM python:3.11-slim

# Установим зависимости и Chrome
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 libnspr4 libnss3 \
    libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 xdg-utils \
    chromium \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Обновим pip и установим Python-зависимости
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы
COPY . .

# Команда по умолчанию
CMD ["python3", "app.py"]

