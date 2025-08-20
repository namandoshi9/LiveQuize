from django.db import models
from django.utils import timezone

class Room(models.Model):
    code = models.CharField(max_length=10, unique=True)
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.code

class Player(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="players")
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=50)
    class_name = models.CharField(max_length=100)
    inst = models.CharField(max_length=150, blank=True, default="")
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("room", "roll_number")

    def __str__(self):
        return f"{self.name} ({self.roll_number})"

class Submission(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name="submission")
    answers = models.JSONField(default=list, blank=True)
    score = models.IntegerField(default=0)
    time_ms = models.IntegerField(default=0)  # milliseconds
    submitted_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.player} - {self.score}"
