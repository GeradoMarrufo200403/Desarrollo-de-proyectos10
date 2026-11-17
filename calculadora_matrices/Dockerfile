FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# No correr como root: si hay una RCE, el atacante no es root dentro del contenedor
RUN useradd --system --uid 10001 app
USER app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
