FROM python:3.13-slim

WORKDIR /app

# Dependencias del sistema necesarias para psycopg2-binary y pymupdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar solo los ficheros de dependencias primero (capa cacheada)
COPY pyproject.toml .
COPY README.md .

# Instalar dependencias de producción (sin dev extras)
RUN pip install --no-cache-dir -e .

# Copiar el resto del código
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

# Carpeta de descargas persistente (se monta como volumen)
RUN mkdir -p downloads

EXPOSE 8089

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8089"]
