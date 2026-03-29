FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopencv-dev \
    fonts-open-sans \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
