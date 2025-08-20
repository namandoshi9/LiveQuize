from django.urls import path
from . import views

urlpatterns = [
    path("room/create/", views.room_create, name="room_create"),
    path("room/<str:code>/open/", views.room_open, name="room_open"),
    path("room/<str:code>/close/", views.room_close, name="room_close"),
    path("room/<str:code>/join/", views.room_join, name="room_join"),
    path("room/<str:code>/quiz/", views.quiz_data, name="quiz_data"),
    path("room/<str:code>/submit/", views.submit_answers, name="submit_answers"),
    path("room/<str:code>/leaderboard/", views.leaderboard, name="leaderboard"),
]
