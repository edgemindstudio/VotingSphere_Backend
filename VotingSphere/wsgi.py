# VotingSphere/wsgi.py

"""
WSGI config for VotingSphere project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Optional: load .env for platforms where env vars aren't injected
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

# Use the split settings – prod for WSGI (gunicorn/uwsgi)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "VotingSphere.settings.prod")

application = get_wsgi_application()


# import os
# import dotenv
#
# dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
#
# from django.core.wsgi import get_wsgi_application
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VotingSphere.settings')
#
# application = get_wsgi_application()


