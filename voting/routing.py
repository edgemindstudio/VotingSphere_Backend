# voting/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/elections/(?P<election_id>\d+)/$', consumers.VoteConsumer.as_asgi()),
]

