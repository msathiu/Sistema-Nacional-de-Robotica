import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# 1. Cargar variables de entorno al inicio
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURIDAD ---
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-default-change-me")

# DEBUG debe ser False por defecto por seguridad extrema
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Manejo de Hosts dinámico y limpio
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# --- APLICACIONES ---
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "crispy_forms",
    "crispy_bootstrap5",
    "django_extensions",
]

LOCAL_APPS = [
    "registry",
    "users",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# --- CONFIGURACIÓN DE UI ---
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# --- MIDDLEWARE ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise para servir archivos estáticos en Docker/Producción de forma eficiente
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "SistemaRegistro.urls"

# --- TEMPLATES ---
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Procesador personalizado para datos globales del sitio
                # "registry.context_processors.site_info",
            ],
        },
    },
]

WSGI_APPLICATION = "SistemaRegistro.wsgi.application"

# --- BASE DE DATOS ---
# Combinación profesional: DATABASE_URL para prod, SQLite para desarrollo rápido
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/db.sqlite3"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# --- LOCALIZACIÓN ---
LANGUAGE_CODE = "es-ve"
TIME_ZONE = "America/Caracas"
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS Y MEDIA ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Optimización para producción: compresión y cache de archivos estáticos
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- AUTENTICACIÓN ---
LOGIN_REDIRECT_URL = "/dashboard/"
LOGIN_URL = "login"
LOGOUT_REDIRECT_URL = "home"

# --- VALIDADORES DE CONTRASEÑA ---
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "users.validators.UppercaseValidator"},
    {"NAME": "users.validators.LowercaseValidator"},
    {"NAME": "users.validators.SymbolValidator"},
]

# --- CONFIGURACIÓN DE EMAIL (Segura) ---
# Usamos variables de entorno incluso para Mailtrap para no dejar rastro en GitHub
# EMAIL_BACKEND = os.getenv(
#     "EMAIL_BACKEND",
#     "django.core.mail.backends.smtp.EmailBackend",  # Usar SMTP por defecto
# )
# EMAIL_HOST = os.getenv("EMAIL_HOST", "sandbox.smtp.mailtrap.io")  # Y
# EMAIL_PORT = int(os.getenv("EMAIL_PORT", 2525))
# EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
# EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
# DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "registro@fvrc.org.ve")
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "sandbox.smtp.mailtrap.io"
EMAIL_HOST_USER = "6faaeaec5086ff"
EMAIL_HOST_PASSWORD = "9a0f4ab61fc09b"
EMAIL_PORT = "2525"
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
# --- VARIABLES GLOBALES DEL SISTEMA ---
SITE_NAME = "Registro Nacional para Robótica Creativa"  # Nombre del sitio
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")  # URL base del sitio

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"  # Evita warnings en modelos nuevos

# CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "http://localhost:8000").split(",")
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# USE_X_FORWARDED_HOST = True # Permite manejar correctamente los hosts cuando se usa un proxy inverso
# SESSION_COOKIE_SECURE = not DEBUG# Asegura que la cookie de sesión solo se envíe por HTTPS en producción
# CSRF_COOKIE_SECURE = not DEBUG# Asegura que la cookie CSRF solo se envíe por HTTPS en producción
