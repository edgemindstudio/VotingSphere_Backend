# manage.py

#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv  # pip install python-dotenv
except Exception:
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent
if load_dotenv:
    load_dotenv(BASE_DIR / ".env")

def main():
    """Run administrative tasks."""
    # Prefer env var; fallback to prod so PaaS builds work out-of-the-box.
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        os.getenv("DJANGO_SETTINGS_MODULE", "VotingSphere.settings.prod"),
    )
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()

