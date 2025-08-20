from django.contrib import admin
from django.urls import path, include
from quiz import views as quiz_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", quiz_views.home, name="home"),
    path("host/", quiz_views.host_page, name="host"),
    path("join/", quiz_views.join_page, name="join"),
    path("api/", include("quiz.urls")),
]
