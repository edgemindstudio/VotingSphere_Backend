# VotingSphere/asgi.py

import os
from pathlib import Path
from django.core.asgi import get_asgi_application

# (Optional) load .env in environments where vars aren't injected
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

# Default to production settings for ASGI servers (Daphne/Uvicorn).
# When you run `python manage.py runserver`, manage.py sets this to dev.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "VotingSphere.settings.prod")

# Create the Django ASGI app first (sets up Django)
django_asgi_app = get_asgi_application()

# Now import Channels bits and your routing (safe after settings are set)
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.auth import AuthMiddlewareStack  # noqa: E402
import voting.routing  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(voting.routing.websocket_urlpatterns)
    ),
})


# import os
# import dotenv
# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# import voting.routing
#
# # Load .env variables
# dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
#
# # Set default Django settings module
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VotingSphere.settings')
#
# # Define ASGI application with both HTTP and WebSocket support
# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             voting.routing.websocket_urlpatterns
#         )
#     ),
# })