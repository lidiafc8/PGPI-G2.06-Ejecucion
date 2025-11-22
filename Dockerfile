# Usamos Python 3.11 slim
FROM python:3.11-slim

# Evitar escribir archivos .pyc y que el output se vea en tiempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Carpeta de trabajo
WORKDIR /app

# Copiamos y instalamos las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el proyecto
COPY . .

# Comando para ejecutar Django con Gunicorn en el puerto 8080 (Koyeb usa este puerto)
CMD ["gunicorn", "tu_proyecto.wsgi:application", "--bind", "0.0.0.0:8080"]
