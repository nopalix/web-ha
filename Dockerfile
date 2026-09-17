FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copiar dependencias desde la carpeta backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p backend/uploads/audio backend/uploads/imagenes logs

EXPOSE 8001

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
