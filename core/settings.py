# ============================================================
#                     SETTINGS.PY - SERMINCO
# ============================================================
# Configuración principal del sistema de control de asignaciones
# ============================================================

from pathlib import Path
import os
from django.contrib.messages import constants as messages

# ------------------------------------------------------------
# BASE / SEGURIDAD
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-secret-key"
DEBUG = True
ALLOWED_HOSTS = ["*"]

# ------------------------------------------------------------
# APLICACIONES INSTALADAS
# ------------------------------------------------------------
INSTALLED_APPS = [
    # Django Core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # App principal
    "asignaciones.apps.AsignacionesConfig",
]

# ------------------------------------------------------------
# MIDDLEWARE
# ------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    
    # Middleware personalizado para control de acceso por roles
    "asignaciones.middleware.RoleAccessMiddleware",

    # 🔹 Middleware de refuerzo para evitar que Django mantenga sesión después de logout
    "asignaciones.middleware_logoutfix.ForceLogoutMiddleware",
]

# ------------------------------------------------------------
# CONFIGURACIÓN DE URLS Y WSGI
# ------------------------------------------------------------
ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

# ------------------------------------------------------------
# PLANTILLAS Y CONTEXT PROCESSORS
# ------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # carpeta global de plantillas
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                # Context processor personalizado
                "asignaciones.context_processors.anuncios_context",
            ],
        },
    },
]

# ------------------------------------------------------------
# BASE DE DATOS (PostgreSQL)
# ------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "control_asignaciones",
        "USER": "control_user",
        "PASSWORD": "Control2025",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

# ------------------------------------------------------------
# LOCALIZACIÓN
# ------------------------------------------------------------
LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------
# ARCHIVOS ESTÁTICOS
# ------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ============================================================
#               CONFIGURACIÓN DE LOGIN / LOGOUT
# ============================================================

# Página de login personalizada (vinculada a views.login_demo)
LOGIN_URL = "asignaciones:login"

# Redirección tras inicio de sesión exitoso (redirige según rol)
LOGIN_REDIRECT_URL = "asignaciones:home_router"

# Redirección después del logout
LOGOUT_REDIRECT_URL = "asignaciones:login"

# ------------------------------------------------------------
# SESIÓN / COOKIES / AUTENTICACIÓN
# ------------------------------------------------------------
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1200  # 20 minutos
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Cambia a True si usas HTTPS
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False

# ------------------------------------------------------------
# OPCIONAL: CONFIGURACIÓN DE MENSAJES
# ------------------------------------------------------------
MESSAGE_TAGS = {
    messages.DEBUG: "debug",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "error",
}

# ============================================================
#                     CONFIGURACIÓN EXTRA
# ============================================================

# Permitir desarrollo local
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
