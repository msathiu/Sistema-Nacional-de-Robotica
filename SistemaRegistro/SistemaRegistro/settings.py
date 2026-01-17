import os
import dj_database_url
from pathlib import Path
  # Recomendado: pip install dj-database-url

BASE_DIR = Path(__file__).resolve().parent.parent

# SEGURIDAD: Leer desde variables de entorno (configuradas en tu .env)
SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-de-desarrollo-muy-simple')

# NUNCA dejes DEBUG = True en produccion
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Configuracion de Hosts
#ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,151.187.25.253').split(',')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terceros
    'crispy_forms',
    'crispy_bootstrap5',
    'django_extensions',
    # Apps Propias
    'registry',
    'users',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'SistemaRegistro.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'SistemaRegistro.wsgi.application'

# BASE DE DATOS: Usando la URL de conexion de Docker
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600
    )
}

# Localizaci  n
LANGUAGE_CODE = 'es-ve'
TIME_ZONE = 'America/Caracas'
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS EST ^aTICOS Y MEDIA ---
# URL para acceder desde el navegador
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# Carpetas donde buscas archivos en desarrollo
STATICFILES_DIRS = [BASE_DIR / 'static']

# Carpeta donde collectstatic DEPOSITA todo para Nginx (Ruta dentro del contenedor)
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/dashboard/'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'home'

# Validadores de Password (iguales a tu versi  n)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'users.validators.UppercaseValidator'},
    {'NAME': 'users.validators.LowercaseValidator'},
    {'NAME': 'users.validators.SymbolValidator'},
]

# --- CONFIGURACIÓN DE EMAIL ---

# Si DEBUG es True, los correos se muestran en la terminal (consola)
#if DEBUG:
    #EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#else:
    # En producción (DEBUG=False), se envían por SMTP real
   # EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

  #EMAIL_HOST = os.environ.get('EMAIL_HOST')
  #EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 2525))
  #EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
  #EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
  #EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
  #DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Webmaster <noreply@tudominio.com>')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_HOST_USER = '6faaeaec5086ff'
EMAIL_HOST_PASSWORD = '9a0f4ab61fc09b'
EMAIL_PORT = '2525'
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False


# settings.py
DEFAULT_FROM_EMAIL = 'registro@fvrc.org.ve' #Correo
SITE_NAME = 'Sistema Nacional de Robótica' #Nombre de la app
BASE_URL = 'https://registro.fvrc.org.ve' #dominio