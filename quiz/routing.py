# Not used directly (we route from project), but left for modularity if needed later.
from django.urls import re_path
from .consumers import LeaderboardConsumer

websocket_urlpatterns = [
    re_path(r"^ws/leaderboard/(?P<room_code>[A-Z0-9]+)/$", LeaderboardConsumer.as_asgi()),
]
