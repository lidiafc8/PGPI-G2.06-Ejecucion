# Usamos Python 3.11 slim
FROM python:3.11-slim

# Evitar escribir archivos .pyc y ver logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Carpeta de trabajo
WORKDIR /app

# Copiamos dependencias e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el proyecto
COPY . .

# --- CORRECCIÓN AQUÍ ---
# Pasamos variables falsas (dummy) para que Django no falle al cargar settings.py
# Cloudinary y la DB no son necesarias para recolectar CSS, pero Django comprueba que existan.
RUN SECRET_KEY=dummy-key-build-only \
    DATABASE_URL=sqlite:///dummy.db \
    CLOUDINARY_CLOUD_NAME=dummy \
    CLOUDINARY_API_KEY=123456789 \
    CLOUDINARY_API_SECRET=dummy \
    python manage.py collectstatic --noinput

# --- COMANDO DE ARRANQUE ---
CMD sh -c "python manage.py migrate && gunicorn mundo_jardin.wsgi:application --bind 0.0.0.0:8080"