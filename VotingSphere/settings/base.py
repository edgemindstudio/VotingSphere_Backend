# VotingSphere/settings/base.py

import os
from datetime import timedelta
from pathlib import Path
import dj_database_url  # pip install dj-database-url

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def env_list(name: str, default: str = ""):
    raw = os.getenv(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]

# -------------------------------------------------
# Core
# -------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-not-secret")
DEBUG = False
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "")

SITE_ID = int(os.getenv("SITE_ID", "1"))

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    # Third-party
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_extensions",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    # add providers you actually use, e.g.:
    # "allauth.socialaccount.providers.google",
    # "allauth.socialaccount.providers.facebook",

    "channels",
    "drf_spectacular",

    # Local
    "accounts",
    "voting",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",   # as high as possible, before CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # required by allauth >=0.63
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "VotingSphere.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "VotingSphere.wsgi.application"
ASGI_APPLICATION = "VotingSphere.asgi.application"

# Channels (Redis override in prod.py)
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
}

# -------------------------------------------------
# Database (env DATABASE_URL, fallback sqlite)
# -------------------------------------------------
DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=60,
    )
}

# -------------------------------------------------
# Auth & REST
# -------------------------------------------------
AUTH_USER_MODEL = "accounts.CustomUser"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # admin/browseable API
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("DRF_RATE_ANON", "200/day"),
        "user": os.getenv("DRF_RATE_USER", "2000/day"),
        "vote": os.getenv("DRF_RATE_VOTE", "5/min"),   # used by VoteViewSet.throttle_scope
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": int(os.getenv("PAGE_SIZE", "20")),
}

# SimpleJWT (tightened in prod.py via env)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.getenv("JWT_ACCESS_MINUTES", "60"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.getenv("JWT_REFRESH_DAYS", "7"))
    ),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

# -------------------------------------------------
# Static / Media
# -------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# -------------------------------------------------
# CORS / CSRF (final values tightened in prod.py)
# -------------------------------------------------
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGIN_REGEXES = env_list("CORS_ALLOWED_ORIGIN_REGEXES", "")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")

# Email (dev override uses console)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Basic logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}


# # VotingSphere/settings.py
#
# import os
# from pathlib import Path
# from datetime import timedelta
# from dotenv import load_dotenv
# from django.utils.translation import gettext_lazy as _
#
#
# load_dotenv()
#
# # Project paths
# BASE_DIR = Path(__file__).resolve().parent.parent
#
# # Custom user model
# AUTH_USER_MODEL = 'accounts.CustomUser'
#
# # Security settings
# SECRET_KEY = os.environ.get('SECRET_KEY')
# DEBUG = os.environ.get('DEBUG', 'True') == 'True'
# ALLOWED_HOSTS = os.environ.get(
#     'ALLOWED_HOSTS',
#     'localhost,127.0.0.1,10.0.2.2'
# ).split(',')
#
# # Application definition
# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#     'django.contrib.sites',
#
#     # Third-party apps
#     'rest_framework',
#     'rest_framework_simplejwt',
#     'corsheaders',
#     'django_extensions',
#     'dj_rest_auth',
#     'dj_rest_auth.registration',
#     'rest_framework.authtoken',
#     'allauth',
#     'allauth.account',
#     'allauth.socialaccount',
#     'allauth.socialaccount.providers.google',
#     'allauth.socialaccount.providers.facebook',
#     'sslserver',
#     "django.contrib.sites",
#     "allauth.socialaccount",
#     "dj_rest_auth.registration",
#
#     # Local apps
#     'channels',
#     'accounts',
#     'voting',
# ]
#
# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'whitenoise.middleware.WhiteNoiseMiddleware',
#     'corsheaders.middleware.CorsMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'allauth.account.middleware.AccountMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
#
# ]
#
# ROOT_URLCONF = 'VotingSphere.urls'
# WSGI_APPLICATION = 'VotingSphere.wsgi.application'
# ASGI_APPLICATION = 'VotingSphere.asgi.application'
#
# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]
#
# # Database (PostgreSQL)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get('DB_NAME'),
#         'USER': os.environ.get('DB_USER'),
#         'PASSWORD': os.environ.get('DB_PASSWORD'),
#         'HOST': os.environ.get('DB_HOST', 'localhost'),
#         'PORT': os.environ.get('DB_PORT', '5432'),
#     }
# }
#
# # Password validation
# AUTH_PASSWORD_VALIDATORS = [
#     {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
# ]
#
# # Internationalization
# LANGUAGE_CODE = 'en'
# TIME_ZONE = 'UTC'
# USE_I18N = True
# USE_TZ = True
#
# # DRF defaults to trailing slashes; be explicit to prevent 301s
# APPEND_SLASH = True
#
# LANGUAGES = [
#     ('en', _('English')),
#     ('fr', _('French')),
# ]
#
# LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]
#
# # Static files
# STATIC_URL = '/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
#
# # --- CORS (dev defaults; override via env if you like) ---
# CORS_ALLOWED_ORIGINS = [
#     origin.strip() for origin in os.environ.get(
#         'CORS_ALLOWED_ORIGINS',
#         'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000'
#     ).split(',') if origin.strip()
# ]
#
# CORS_ALLOWED_ORIGIN_REGEXES = [
#     r"^http://localhost:\d+$",
#     r"^http://127\.0\.0\.1:\d+$",
# ]
# CORS_ALLOW_CREDENTIALS = False  # using Authorization header, not cookies
#
# # --- CSRF (only relevant for browser clients) ---
# CSRF_TRUSTED_ORIGINS = [
#     'http://localhost:5173',
#     'http://127.0.0.1:5173',
#     'http://localhost:3000',
#     'http://127.0.0.1:3000',
# ]
#
# # REST Framework
# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#         'rest_framework.authentication.SessionAuthentication',
#     ),
#     'DEFAULT_PERMISSION_CLASSES': (
#         'rest_framework.permissions.IsAuthenticated',
#     ),
#     'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
#     'PAGE_SIZE': 10,
#     'DEFAULT_THROTTLE_CLASSES': [
#         'rest_framework.throttling.UserRateThrottle',
#         'rest_framework.throttling.AnonRateThrottle',
#         # 'voting.throttles.VoteRateThrottle',
#     ],
#     'DEFAULT_THROTTLE_RATES': {
#         'user': '100/day',
#         'anon': '10/hour',
#         'vote': '5/minute',
#     },
# }
#
# # JWT
# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
#     'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
#     'ROTATE_REFRESH_TOKENS': False,
#     'BLACKLIST_AFTER_ROTATION': False,
#     'AUTH_HEADER_TYPES': ('Bearer',),
# }
#
# # Channels (Redis)
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             'hosts': [(os.environ.get('REDIS_HOST', '127.0.0.1'), int(os.environ.get('REDIS_PORT', '6379')))],
#         },
#     },
# }
#
# SPECTACULAR_SETTINGS = {
#     "TITLE": "VotingSphere API",
#     "DESCRIPTION": "OpenAPI schema for VotingSphere",
#     "VERSION": "v1",
#     # If you want the Swagger UI at /api/docs/ to include schema endpoint:
#     "SERVE_INCLUDE_SCHEMA": False,
# }
#
#
# # Allauth + dj-rest-auth config (no deprecated fields)
# SITE_ID = 1
# ACCOUNT_EMAIL_VERIFICATION = 'none'
# SOCIALACCOUNT_QUERY_EMAIL = True
#
# AUTHENTICATION_BACKENDS = (
#     'django.contrib.auth.backends.ModelBackend',
#     'allauth.account.auth_backends.AuthenticationBackend',
# )
#
# ACCOUNT_LOGIN_METHODS = ['username', 'email']  # replaces deprecated ACCOUNT_AUTHENTICATION_METHOD
# ACCOUNT_SIGNUP_FIELDS = ['username*', 'email*', 'password1*', 'password2*']
#
# ACCOUNT_SIGNUP_REDIRECT_URL = '/'
# ACCOUNT_LOGOUT_REDIRECT_URL = '/'
#
# # Enable JWT support in dj-rest-auth
# REST_USE_JWT = True
#
# # Fix deprecation warnings
# REST_AUTH = {
#     'USE_JWT': True,
#     'REGISTER_SERIALIZER': 'dj_rest_auth.registration.serializers.RegisterSerializer',
#     'SIGNUP_FIELDS': {
#         'username': {'required': True},
#         'email': {'required': True},
#     }
# }
#
#
# # Social auth
# SOCIALACCOUNT_PROVIDERS = {
#     'google': {
#         'APP': {
#             'client_id': os.getenv('GOOGLE_CLIENT_ID'),
#             'secret': os.getenv('GOOGLE_CLIENT_SECRET'),
#             'key': ''
#         }
#     },
#     'facebook': {
#         'APP': {
#             'client_id': os.getenv('FACEBOOK_APP_ID'),
#             'secret': os.getenv('FACEBOOK_APP_SECRET'),
#             'key': ''
#         }
#     }
# }
#
#
# # =====================================================
# # Security Headers for Production
# # =====================================================
#
# # Prevent XSS in modern browsers
# SECURE_BROWSER_XSS_FILTER = True
#
# # Prevent content sniffing (MIME attacks)
# SECURE_CONTENT_TYPE_NOSNIFF = True
#
# # HTTP Strict Transport Security (HSTS)
# # Redirect all HTTP → HTTPS automatically
# # --- HTTPS/security: strict in prod, relaxed in dev ---
# if DEBUG:
#     SECURE_SSL_REDIRECT = False
#     SESSION_COOKIE_SECURE = False
#     CSRF_COOKIE_SECURE = False
#     CHANNEL_LAYERS = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}
#     SECURE_HSTS_SECONDS = 0
# else:
#     # Ensure cookies are only sent over HTTPS
#     SECURE_SSL_REDIRECT = True
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True
#     SECURE_HSTS_SECONDS = 31536000
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#     SECURE_HSTS_PRELOAD = True
#
# INSTALLED_APPS += ["drf_spectacular"]
# REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"
#
# # Gzipped CSS/JS for faster loading & Cache-busting filenames
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
#
# # Serve media files securely (user uploads)
# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
