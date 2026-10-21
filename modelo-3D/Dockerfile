FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias de compilación si NumPy las requiere
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# No correr como root
RUN useradd --system --uid 10001 app
USER app

# --ws-max-size: tope de 4 KB por mensaje WebSocket (el visor envía ~150 bytes)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--ws-max-size", "4096"]