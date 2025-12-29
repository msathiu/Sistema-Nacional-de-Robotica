import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-tu-clave-secreta-aqui'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms', 
    'crispy_bootstrap5',
    'django_extensions',  
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'es-ve'
TIME_ZONE = 'America/Caracas'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/dashboard/'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'home'

# SistemaRegistro/settings.py

AUTH_PASSWORD_VALIDATORS = [
    {
        # Verifica que la contraseña no sea demasiado similar a la información del usuario
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        # Verifica que la contraseña no sea una contraseña comúnmente utilizada
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            # Asegúrate de que la longitud mínima sea razonable (ej: 8 o más)
            'min_length': 8, 
        }
    },
    {
        # Requiere al menos un número (0-9)
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        # Requiere al menos una letra mayúscula (A-Z)
        'NAME': 'users.validators.UppercaseValidator', 
    },
    {
        # Requiere al menos una letra minúscula (a-z)
        'NAME': 'users.validators.LowercaseValidator', 
    },
    {
        # Requiere al menos un caracter especial/símbolo (¡#$@...)
        'NAME': 'users.validators.SymbolValidator', 
    },
]
