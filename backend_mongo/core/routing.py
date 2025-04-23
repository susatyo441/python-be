from django.urls import re_path
from core.consumers.video_consumer import VideoStreamConsumer

websocket_urlpatterns = [
    re_path(r"ws/video/$", VideoStreamConsumer.as_asgi()),
]
