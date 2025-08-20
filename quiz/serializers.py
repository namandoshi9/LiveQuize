from rest_framework import serializers
from .models import Room, Player, Submission

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["code", "is_open", "created_at"]

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ["id", "name", "roll_number", "class_name", "inst", "joined_at"]

class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ["player", "answers", "score", "time_ms", "submitted_at"]
