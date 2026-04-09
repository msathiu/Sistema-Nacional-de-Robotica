# Usamos una imagen ligera de Python 3.12
FROM python:3.12-slim-bookworm

# 1. Variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 2. Establecer directorio de trabajo
WORKDIR /app

# 3. Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 4. Gestión de Usuarios y Carpetas (ANTES de copiar el código)
# Creamos el usuario y todas las carpetas que necesitarán permisos de escritura
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs /app/staticfiles /app/media /tmp/gunicorn && \
    chown -R appuser:appuser /app /tmp/gunicorn

# 5. Instalar dependencias de Python
COPY SistemaRegistro/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar el código del proyecto
# Usamos --chown para que los archivos ya entren con el dueño correcto
COPY --chown=appuser:appuser SistemaRegistro/ /app/

# 7. Cambiar al usuario no-root
USER appuser

# 8. Exponer puerto y comando
EXPOSE 8000
CMD ["gunicorn", "SistemaRegistro.wsgi:application", "--bind", "0.0.0.0:8000"]