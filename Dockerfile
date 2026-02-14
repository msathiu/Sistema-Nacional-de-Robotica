# --- ETAPA 1: Base común ---
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app

# Instalamos solo lo mínimo para ejecutar Postgres
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# --- ETAPA 2: Constructor (Builder) ---
FROM base AS builder

# Instalamos herramientas de compilación
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY SistemaRegistro/requirements.txt .
# Instalamos las librerías en un directorio separado para luego copiarlas
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- ETAPA 3: Desarrollo (Development) ---
FROM builder AS development
# En desarrollo sí copiamos el código para auditorías y tests
COPY SistemaRegistro/ /app/
# Instalamos herramientas de seguridad adicionales que usamos hoy
RUN pip install bandit safety pip-audit
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# --- ETAPA 4: Producción (Final) ---
FROM base AS production

# Creamos un usuario no-root para máxima seguridad
RUN addgroup --system django && adduser --system --group django

# Copiamos solo las librerías instaladas (sin el GCC ni basura de compilación)
COPY --from=builder /install /usr/local
COPY SistemaRegistro/ /app/

# Ajustamos permisos para los logs y carpetas de medios
RUN chown -R django:django /app
USER django

EXPOSE 8000
CMD ["gunicorn", "SistemaRegistro.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
