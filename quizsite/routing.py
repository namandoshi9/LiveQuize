from django.urls import re_path
from quiz.consumers import LeaderboardConsumer

websocket_urlpatterns = [
    re_path(r"^ws/leaderboard/(?P<room_code>[A-Z0-9]+)/$", LeaderboardConsumer.as_asgi()),
]
