"""
Django settings for mundo_jardin project.
CORREGIDO PARA DESPLIEGUE EN KOYEB
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================
# CONFIGURACIÓN DE SEGURIDAD E IDENTIDAD
# ==============================================

# SECRET_KEY: Intenta leerla de Koyeb, si no existe usa una de prueba (SOLO para local)
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-cambiar-en-prod")

DEBUG = os.environ.get('DEBUG', 'True') != 'False'

# ALLOWED_HOSTS: "*" permite que Koyeb haga sus chequeos internos sin dar error 500.
ALLOWED_HOSTS = ["*"]

# ==============================================
# RUTAS DE LOGIN
# ==============================================
LOGIN_URL = 'inicio_sesion:login'
LOGIN_REDIRECT_URL = 'inicio_sesion:post_login_redirect'

# ==============================================
# APLICACIONES INSTALADAS
# ==============================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'cloudinary',
    # Tus apps
    'home',
    'adminpanel',
    'ventas_admin',
    'catalogo_admin',
    'clientes_admin',
    'registro_usuario',
    'inicio_sesion',
    'perfil',
    'pedidos_admin',
    'info_tienda',
    'carrito',
]

# ==============================================
# MIDDLEWARE
# ==============================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mundo_jardin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'home.context_processors.productos_en_cesta',
            ],
        },
    },
]

WSGI_APPLICATION = 'mundo_jardin.wsgi.application'

# ==============================================
# BASE DE DATOS
# ==============================================

DATABASES = {
    "default": dj_database_url.config(default="postgresql://neondb_owner:npg_6vaikg7lJsBr@ep-sweet-sky-aeyouodp-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
}

# ==============================================
# AUTENTICACIÓN Y PASSWORD
# ==============================================
AUTH_USER_MODEL = 'home.Usuario'

AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

AUTHENTICATION_BACKENDS = [
    'inicio_sesion.backends.ClienteBackend', 
    'django.contrib.auth.backends.ModelBackend',
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher'
]

# ==============================================
# INTERNACIONALIZACIÓN
# ==============================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ==============================================
# ARCHIVOS ESTÁTICOS (CSS, JS, IMÁGENES)
# ==============================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [ BASE_DIR / 'static' ]
STATIC_ROOT = BASE_DIR / 'staticfiles_collect'

# Archivos Multimedia (Subidos por usuario)
# NOTA: En Koyeb sin S3, estos archivos se borran al redesplegar.
MEDIA_ROOT = BASE_DIR / 'Imgproductos'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', 'djfgts1ii'),
    'API_KEY':    os.environ.get('CLOUDINARY_API_KEY', '238934691739344'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', 'rQq0rMASZAao8qWDtoC1KWzbF28'),
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Esto es solo para referencia interna, Cloudinary pondrá https://res.cloudinary...
MEDIA_URL = '/Imgproductos/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================
# SEGURIDAD INTELIGENTE (Local vs Producción)
# ==============================================

# Estas configuraciones son seguras y no molestan en local
CSRF_TRUSTED_ORIGINS = ["https://good-nadiya-pgpi-mundojardin-be6bfb0f.koyeb.app"]
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
WHITENOISE_USE_FINDERS = True

# AQUÍ ESTÁ LA MAGIA:
# Si DEBUG es False (Producción/Koyeb), activamos la seguridad HTTPS fuerte.
# Si DEBUG es True (Local), la desactivamos para poder trabajar.

if not DEBUG:
    # --- CONFIGURACIÓN PARA KOYEB (Producción) ---
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    # --- CONFIGURACIÓN PARA TU PC (Local) ---
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

