# Usamos Python 3.11 slim
FROM python:3.11-slim

# Evitar escribir archivos .pyc y ver logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Carpeta de trabajo
WORKDIR /app

# Copiamos dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el proyecto
COPY . .

# --- PASO NUEVO IMPORTANTE ---
# Generamos los archivos estáticos para Whitenoise
# Usamos una dummy key temporal porque a veces falla si no detecta la variable de entorno en el build
RUN SECRET_KEY=dummy-key-build-only python manage.py collectstatic --noinput

# --- COMANDO DE ARRANQUE MEJORADO ---
# 1. Ejecuta migraciones (actualiza la DB)
# 2. Arranca Gunicorn
CMD sh -c "python manage.py migrate && gunicorn mundo_jardin.wsgi:application --bind 0.0.0.0:8080"