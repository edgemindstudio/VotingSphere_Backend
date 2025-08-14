# VotingSphere/settings/prod.py

from .base import *  # noqa
import os
from datetime import timedelta
import dj_database_url

# --- REQUIRED ---
DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]  # must be set in env

# If you defined env_list in base.py, this uses it. Otherwise replace with .split(',')
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "api.example.com")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "https://example.com,https://www.example.com")
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "https://app.example.com")

# --- Security hardening ---
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
# Django ≥4.1: use SECURE_REFERRER_POLICY; older: REFERRER_POLICY
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# --- Static files via WhiteNoise ---
# Only add if not already present in base.py
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- Database (requires DATABASE_URL) ---
# Example: postgres://user:pass@host:5432/dbname
DATABASES = {
    "default": dj_database_url.parse(
        os.environ["DATABASE_URL"],
        conn_max_age=600,
        ssl_require=True,  # set False only if your DB doesn't support SSL
    )
}

# --- Channels / Redis ---
# Prefer REDIS_URL (e.g., redis://host:6379/0). If not set, falls back to base.py config.
if os.getenv("REDIS_URL"):
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [os.environ["REDIS_URL"]]},
        }
    }

# --- JWT lifetimes (env-overridable) ---
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(
    minutes=int(os.getenv("JWT_ACCESS_MINUTES", "20"))
)
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = timedelta(
    days=int(os.getenv("JWT_REFRESH_DAYS", "10"))
)

# --- Optional: basic logging for prod ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}
