# VotingSphere/asgi.py

import os
import dotenv
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import voting.routing

# Load .env variables
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VotingSphere.settings')

# Define ASGI application with both HTTP and WebSocket support
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            voting.routing.websocket_urlpatterns
        )
    ),
})