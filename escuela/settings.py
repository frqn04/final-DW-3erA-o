"""
Django settings for escuela project.

Sistema de Gestión Escolar - Django 5.2.5 con Python 3.13

Arquitectura diseñada para un sistema de gestión escolar con las siguientes aplicaciones:
- users: Gestión de usuarios personalizados (estudiantes, profesores, administradores, padres)
- escuelas: Gestión de instituciones educativas
- students: Gestión de estudiantes y su información académica
- enrollments: Gestión de matrículas e inscripciones
- core: Funcionalidades centrales y utilities compartidas

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables support (opcional, para configuraciones avanzadas)
try:
    import environ
    env = environ.Env(
        DEBUG=(bool, False),
        SECRET_KEY=(str, ''),
        DATABASE_URL=(str, ''),
        ALLOWED_HOSTS=(list, []),
    )
    # Take environment variables from .env file if it exists
    environ.Env.read_env(BASE_DIR / '.env')
    USE_ENV = True
except ImportError:
    USE_ENV = False

# SECURITY WARNING: keep the secret key used in production secret!
if USE_ENV:
    SECRET_KEY = env('SECRET_KEY', default='django-insecure-^%zh33r+q4qqvt@yhqbcso5709lyt1j4$6utu$5&_-+=*m1cbh')
else:
    SECRET_KEY = 'django-insecure-^%zh33r+q4qqvt@yhqbcso5709lyt1j4$6utu$5&_-+=*m1cbh'

# SECURITY WARNING: don't run with debug turned on in production!
if USE_ENV:
    DEBUG = env('DEBUG', default=True)
else:
    DEBUG = True

if USE_ENV:
    ALLOWED_HOSTS = env('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '0.0.0.0'])
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Application definition

# Django Core Apps
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # Para formatear números y fechas
]

# Third Party Apps
THIRD_PARTY_APPS = [
    'django_bootstrap5',    # Bootstrap 5 integration
    'django_filters',       # Filtros avanzados para queryset
    'django_tables2',       # Tablas HTML dinámicas
    # 'widget_tweaks',        # Personalización de widgets (instalar si es necesario)
    # 'crispy_forms',         # Formularios con mejor presentación (instalar si es necesario)
    # 'crispy_bootstrap5',    # Crispy forms con Bootstrap 5 (instalar si es necesario)
]

# Local Apps del Sistema Escolar
LOCAL_APPS = [
    'core',         # Funcionalidades centrales del sistema
    'users',        # Gestión de usuarios personalizados
    'escuelas',     # Gestión de instituciones educativas
    'students',     # Gestión de estudiantes
    'enrollments',  # Gestión de matrículas
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'users.middleware.ForcePasswordChangeMiddleware',  # Middleware personalizado para forzar cambio de contraseña
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Para soporte de internacionalización
]

ROOT_URLCONF = 'escuela.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # Directorio principal de plantillas
            BASE_DIR / 'templates' / 'core',
            BASE_DIR / 'templates' / 'users',
            BASE_DIR / 'templates' / 'escuelas',
            BASE_DIR / 'templates' / 'students',
            BASE_DIR / 'templates' / 'enrollments',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
            ],
        },
    },
]

WSGI_APPLICATION = 'escuela.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Configuración de base de datos con soporte para SQLite (default) y PostgreSQL
if USE_ENV and env('DATABASE_URL'):
    # Configuración para PostgreSQL usando DATABASE_URL
    DATABASES = {
        'default': env.db()
    }
else:
    # Configuración por defecto con SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 300,  # 5 minutos de timeout
            }
        }
    }

# Custom User Model
# https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#substituting-a-custom-user-model
AUTH_USER_MODEL = 'users.User'

# Authentication backends
# https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#authentication-backends
AUTHENTICATION_BACKENDS = [
    'users.auth_backends.EmailDNIBackend',  # Backend personalizado para email + DNI
    'django.contrib.auth.backends.ModelBackend',  # Backend por defecto (fallback)
]

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'email', 'first_name', 'last_name'),
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-es'  # Configurado para español

TIME_ZONE = 'America/Mexico_City'  # Configurar según tu zona horaria

USE_I18N = True

USE_TZ = True

# Idiomas disponibles
LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Directorios de archivos estáticos
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # Directorio principal de archivos estáticos
    BASE_DIR / 'static' / 'css',
    BASE_DIR / 'static' / 'js',
    BASE_DIR / 'static' / 'img',
    BASE_DIR / 'static' / 'vendor',  # Para librerías de terceros
]

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication URLs and redirects
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# Session configuration
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Django Bootstrap 5 configuration
BOOTSTRAP5 = {
    'base_url': None,
    'css_url': None,
    'javascript_url': None,
    'jquery_url': None,
    'jquery_slim_url': None,
    'popper_url': None,
    'theme_url': None,
    'success_css_class': '',
    'set_placeholder': False,
    'set_required': False,
    'form_renderers': {
        'default': 'django_bootstrap5.renderers.BootstrapRenderer',
    },
}

# Django Tables2 configuration
DJANGO_TABLES2_TEMPLATE = 'django_tables2/bootstrap5.html'

# Email configuration (configurar según necesidades)
if DEBUG:
    # En desarrollo, enviar emails a la consola
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # En producción, configurar SMTP real
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    if USE_ENV:
        EMAIL_HOST = env('EMAIL_HOST', default='')
        EMAIL_PORT = env('EMAIL_PORT', default=587)
        EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
        EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
        EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True)
        DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@escuela.com')
    else:
        EMAIL_HOST = ''
        EMAIL_PORT = 587
        EMAIL_HOST_USER = ''
        EMAIL_HOST_PASSWORD = ''
        EMAIL_USE_TLS = True
        DEFAULT_FROM_EMAIL = 'noreply@escuela.com'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'escuela': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'escuela-cache',
    }
}

# Configuración específica para el sistema escolar
ESCUELA_SETTINGS = {
    'MAX_STUDENTS_PER_CLASS': 30,
    'ACADEMIC_YEAR_START_MONTH': 9,  # Septiembre
    'ENABLE_GRADE_CALCULATIONS': True,
    'REQUIRE_PARENT_CONTACT': True,
    'ENABLE_ATTENDANCE_TRACKING': True,
    'ENABLE_HOMEWORK_ASSIGNMENTS': True,
}

# Configuración de paginación
PAGINATION_SETTINGS = {
    'DEFAULT_PAGE_SIZE': 25,
    'MAX_PAGE_SIZE': 100,
    'STUDENTS_PER_PAGE': 20,
    'ENROLLMENTS_PER_PAGE': 30,
}

# Development settings
if DEBUG:
    # Django Debug Toolbar (opcional, para desarrollo)
    try:
        import debug_toolbar
        if 'debug_toolbar' not in INSTALLED_APPS:
            INSTALLED_APPS += ['debug_toolbar']
        if 'debug_toolbar.middleware.DebugToolbarMiddleware' not in MIDDLEWARE:
            MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        INTERNAL_IPS = ['127.0.0.1']
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
        }
    except ImportError:
        pass

# Production settings
if not DEBUG:
    # Configuraciones adicionales para producción
    if USE_ENV:
        SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT', default=False)
        SECURE_HSTS_SECONDS = env('SECURE_HSTS_SECONDS', default=31536000)
        SECURE_HSTS_INCLUDE_SUBDOMAINS = env('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
        SECURE_HSTS_PRELOAD = env('SECURE_HSTS_PRELOAD', default=True)
    
    # Configuración de archivos estáticos para producción
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
