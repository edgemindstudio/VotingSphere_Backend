# VotingSphere/settings/dev.py

from .base import *
import os
import dj_database_url

DEBUG = True
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

# --- Database (prefer DATABASE_URL for dev Postgres) ---
if os.getenv("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=0)
    }
elif os.getenv("DB_NAME"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER", ""),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }
else:
    # fallback (handy when contributors don’t have Postgres)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# --- CORS/CSRF for local web UIs ---
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)

# Channels: use in-memory unless a REDIS_URL is set
if os.getenv("REDIS_URL"):
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [os.environ["REDIS_URL"]]},
        }
    }
else:
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

# Friendlier JWT for dev (optional)
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "60")))
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "1")))

# Don’t add WhiteNoise here (keep it in prod)
