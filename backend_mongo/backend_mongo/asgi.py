"""
ASGI config for backend_mongo project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from core.routing import websocket_urlpatterns
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_mongo.settings')
django.setup()

application = ProtocolTypeRouter({
    # Untuk WebSocket
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
       "http": get_asgi_application(),
  
})
