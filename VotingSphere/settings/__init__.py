# VotingSphere/settings/__init__.py

# Intentionally empty: use DJANGO_SETTINGS_MODULE to pick dev/prod
# e.g. VotingSphere.settings.dev or VotingSphere.settings.prod
# chooses dev by default; prod will be selected via env in real deploy
import os
env_target = os.getenv("DJANGO_ENV", "dev")
if env_target == "prod":
    from .prod import *   # noqa
else:
    from .dev import *    # noqa