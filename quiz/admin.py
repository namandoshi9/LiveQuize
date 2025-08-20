from django.contrib import admin
from .models import Room, Player, Submission

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("code", "is_open", "created_at")
    search_fields = ("code",)

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "roll_number", "class_name", "room")
    search_fields = ("name", "roll_number")

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("player", "score", "time_ms", "submitted_at")
    search_fields = ("player__name", "player__roll_number")
