import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# 1. Cargar variables de entorno al inicio
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURIDAD ---
# DEBUG debe cargarse PRIMERO para usarlo en SECRET_KEY
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "django-insecure-default-change-me":
    if DEBUG:
        SECRET_KEY = "django-insecure-dev-key-only"
    else:
        raise ValueError("SECRET_KEY debe estar configurada en producción")

# Manejo de Hosts dinámico y limpio
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# --- APLICACIONES ---
DJANGO_APPS = [
    "jazzmin",  # Debe ir ANTES de django.contrib.admin
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
    "users.apps.UsersConfig",
    "registry.apps.RegistryConfig",
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
    # Middlewares de seguridad personalizados
    "users.middleware.RateLimitMiddleware",
    "users.middleware.SecurityHeadersMiddleware",
    # Middleware para restringir superusuarios solo al admin
    "users.middleware.SuperuserAdminOnlyMiddleware",
    # Middleware para control de acceso basado en roles
    "users.middleware.RoleBasedAccessMiddleware",
    # Middleware para expiración de sesión por inactividad
    "users.middleware.SessionTimeoutMiddleware",
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
                # Context processor para notificaciones no leídas
                "registry.context_processors.notificaciones_no_leidas",
                # Context processor para roles de usuario
                "registry.context_processors.user_roles",
                # Context processor para clubes pendientes (federación)
                "registry.context_processors.clubes_pendientes_federacion",
                # Context processor para solicitudes de eliminación pendientes
                "registry.context_processors.solicitudes_eliminacion_pendientes",
                # Context processor para menú del sidebar dinámico
                "users.context_processors.sidebar_menu",
            ],
        },
    },
]

WSGI_APPLICATION = "SistemaRegistro.wsgi.application"

# --- BASE DE DATOS ---
# Combinación profesional: DATABASE_URL para prod, SQLite para desarrollo rápido

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL no está definida. PostgreSQL es obligatorio."
    )

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=os.getenv("DB_SSL_REQUIRE", "False").lower() == "true",
    )
}

# --- LOCALIZACIÓN ---
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Caracas"
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS Y MEDIA ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- AUTENTICACIÓN ---
LOGIN_REDIRECT_URL = "/dashboard/"
LOGIN_URL = "login"
LOGOUT_REDIRECT_URL = "home"

# Configuraciones de sesión para seguridad y expiración
SESSION_COOKIE_AGE = 1800  # 30 minutos absolutos como respaldo
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Expira al cerrar navegador

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
# Usamos variables de entorno para no exponer credenciales
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "sandbox.smtp.mailtrap.io")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "2525"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() == "true"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "registro@fvrc.org.ve")

# --- VARIABLES GLOBALES DEL SISTEMA ---
SITE_NAME = "Registro Nacional para Robótica Creativa"
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- CONFIGURACIONES DE SEGURIDAD PARA PRODUCCIÓN ---
if not DEBUG:
    # CSRF y seguridad de cookies
    CSRF_TRUSTED_ORIGINS = os.getenv(
        "CSRF_TRUSTED_ORIGINS", "http://localhost:8000"
    ).split(",")
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    CSRF_COOKIE_SAMESITE = 'Strict'
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False").lower() == "true"
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = "DENY"
else:
    # Configuraciones de desarrollo
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# --- CREAR CARPETA DE LOGS SI NO EXISTE ---
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# --- CONFIGURACIÓN DE LOGGING ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


# --- CONFIGURACIÓN JAZZMIN (ADMIN PROFESIONAL) ---
JAZZMIN_SETTINGS = {
    "site_title": "FVRC Admin",
    "site_header": "Sistema Nacional de Robótica",
    "site_brand": "FVRC-PRO",
    "site_logo": None,
    "welcome_sign": "Bienvenido al Panel de Administración",
    "copyright": "FVRC - Federación Venezolana de Robótica Creativa",
    
    "show_sidebar": True,
    "navigation_expanded": True,
    
    "theme": "flatly",
    "dark_mode_theme": "darkly",
    
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin_dashboard", "icon": "fas fa-tachometer-alt"},
        {"name": "Ver Logs", "url": "admin_logs", "icon": "fas fa-file-alt"},

    ],
    
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "users.userprofile": "fas fa-id-card",
        "registry.estado": "fas fa-map-marked-alt",
        "registry.municipio": "fas fa-map-marker-alt",
        "registry.parroquia": "fas fa-map-pin",
        "registry.institucion": "fas fa-school",
        "registry.participante": "fas fa-user-graduate",
        "registry.evento": "fas fa-calendar-alt",
        "registry.grupo": "fas fa-users",
        "registry.club": "fas fa-robot",
    },
    
    "order_with_respect_to": ["auth", "users", "registry"],
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "flatly",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

# --- CONFIGURACIÓN PARA DOCKER Y POSTGRESQL ---
# Configuración de cache para desarrollo con Docker
if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
