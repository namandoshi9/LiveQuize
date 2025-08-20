import random, string, json
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Room, Player, Submission
from django.views.decorators.csrf import csrf_exempt

# ---- QUIZ DATA (same as your previous quiz) ----
QUIZ = [
  {
    "q": "Which AI application excites you the most?",
    "opts": ["Self-driving cars 🚗","Healthcare AI 🏥","Chatbots (ChatGPT, Bard) 🤖","Gaming AI 🎮","Personalized recommendations 🍿🎶"],
    "correct": "ANY",
    "explain": "All are correct — ask who chose what, and explain how Python powers most of these via libraries, APIs, and tooling."
  },
  {
    "q": "Which company do you think uses AI the most?",
    "opts": ["Google","Amazon","Netflix","Tesla"],
    "correct": [0,1],
    "explain": "All use AI, but Google (Search, Maps, Translate, Gmail spam filter) and Amazon (recommendations, Alexa) are top examples."
  },
  {
    "q": "Which of these is NOT an AI/ML application?",
    "opts": ["Face unlock on your phone","Autocorrect in WhatsApp","Playing YouTube videos","Fraud detection in banking"],
    "correct": 2,
    "explain": "Playing a video itself isn't AI. But recommendations and search are driven by AI."
  },
  {
    "q": "What is the most used programming language for AI/ML?",
    "opts": ["Java","C++","Python","PHP"],
    "correct": 2,
    "explain": "Python wins due to TensorFlow, PyTorch, Pandas, NumPy and a huge ecosystem."
  },
  {
    "q": "Which AI tools do you use daily (without realizing)?",
    "opts": ["Google Maps","Instagram Filters","YouTube Recommendations","Voice Assistants (Siri, Alexa)"],
    "correct": "ANY",
    "explain": "All of them! Most students will raise hands multiple times — makes it fun."
  },
  {
    "q": "How does Netflix know what you want to watch?",
    "opts": ["Random guesses","Human staff choosing","Machine Learning algorithms","By spying on your microphone"],
    "correct": 2,
    "explain": "ML analyzes your watch history + similar viewers. Not your chai-time gossip. 😉"
  },
  {
    "q": "What is the main fuel of AI?",
    "opts": ["Data","Electricity","Expensive laptops","Luck"],
    "correct": 0,
    "explain": "Without diverse, high-quality data, AI fails."
  },
  {
    "q": "Which industry will be most disrupted by AI in the next 5 years?",
    "opts": ["Education","Healthcare","Transportation","Finance"],
    "correct": "ANY",
    "explain": "Trick: all of them. In India, Healthcare + Education are seeing huge AI boosts."
  },
  {
    "q": "Which AI fail do you find funniest?",
    "opts": ["Muffins vs chihuahuas","Siri calls Pizza Hut instead of Dad","Snow mistaken as a wolf","Autocorrect disasters"],
    "correct": "ANY",
    "explain": "No wrong answer — show memes and let the class laugh!"
  },
  {
    "q": "Will AI replace humans completely?",
    "opts": ["Yes","No","Maybe some jobs","AI and humans will work together"],
    "correct": 3,
    "explain": "AI replaces tasks, not people. Best future = humans + AI collaborating."
  }
]

def gen_code(n=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

# ---------- Pages ----------
def home(request):
    return render(request, "quiz/base.html")

def host_page(request):
    return render(request, "quiz/host.html")

def join_page(request):
    return render(request, "quiz/join.html")

# ---------- API ----------

@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def room_create(request):
    code = request.data.get("code") or gen_code()
    code = code.upper()
    room, created = Room.objects.get_or_create(code=code, defaults={"is_open": True})
    if not created:
        room.is_open = True
        room.save()
    return JsonResponse({"code": room.code, "is_open": room.is_open})

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def room_open(request, code):
    try:
        room = Room.objects.get(code=code.upper())
    except Room.DoesNotExist:
        return HttpResponseBadRequest("Room not found")
    room.is_open = True
    room.save()
    return JsonResponse({"ok": True})

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def room_close(request, code):
    try:
        room = Room.objects.get(code=code.upper())
    except Room.DoesNotExist:
        return HttpResponseBadRequest("Room not found")
    room.is_open = False
    room.save()
    return JsonResponse({"ok": True})

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def room_join(request, code):
    code = code.upper()
    name = (request.data.get("name") or "").strip()
    roll = (request.data.get("roll") or "").strip()
    class_name = (request.data.get("class_name") or "").strip()
    inst = (request.data.get("inst") or "").strip()
    if not (name and roll and class_name):
        return HttpResponseBadRequest("Missing fields")
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return HttpResponseBadRequest("Room not found")
    if not room.is_open:
        return HttpResponseBadRequest("Room closed")
    player, _ = Player.objects.get_or_create(room=room, roll_number=roll, defaults={
        "name": name, "class_name": class_name, "inst": inst
    })
    # Update name/class if changed
    player.name = name
    player.class_name = class_name
    player.inst = inst
    player.save()
    return JsonResponse({"ok": True, "player_id": player.id})

@api_view(["GET"])
@permission_classes([AllowAny])
def quiz_data(request, code):
    # Could vary by room later; for now return constant quiz
    return JsonResponse({"quiz": QUIZ, "count": len(QUIZ)})

def compute_score(answers):
    score = 0
    detailed = []
    for idx, q in enumerate(QUIZ):
        ans = answers[idx] if idx < len(answers) else -1
        correct = False
        if q["correct"] == "ANY":
            correct = True
        elif isinstance(q["correct"], list):
            correct = ans in q["correct"]
        else:
            correct = ans == q["correct"]
        if correct:
            score += 1
        detailed.append({
            "idx": idx,
            "correct": correct,
            "explain": q["explain"]
        })
    return score, detailed

def broadcast_leaderboard(room):
    # Build and send leaderboard via Channels
    subs = Submission.objects.filter(player__room=room).select_related("player")
    data = []
    for s in subs:
        data.append({
            "name": s.player.name,
            "roll": s.player.roll_number,
            "className": s.player.class_name,
            "score": s.score,
            "timeMs": s.time_ms,
            "when": int(s.submitted_at.timestamp()*1000),
        })
    data.sort(key=lambda x: (-x["score"], x["timeMs"] if x["timeMs"] is not None else 1e18))
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"room_{room.code}",
        {"type": "leaderboard_update", "data": data}
    )

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def submit_answers(request, code):
    code = code.upper()
    roll = (request.data.get("roll") or "").strip()
    answers = request.data.get("answers") or []
    time_ms = int(request.data.get("time_ms") or 0)
    if not roll or not isinstance(answers, list):
        return HttpResponseBadRequest("Invalid payload")
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return HttpResponseBadRequest("Room not found")
    if not room.is_open:
        return HttpResponseBadRequest("Room closed")

    try:
        player = Player.objects.get(room=room, roll_number=roll)
    except Player.DoesNotExist:
        return HttpResponseBadRequest("Player not joined")

    score, detailed = compute_score(answers)

    sub, _ = Submission.objects.update_or_create(
        player=player,
        defaults={"answers": answers, "score": score, "time_ms": time_ms, "submitted_at": timezone.now()}
    )

    # Broadcast new leaderboard to all connected clients
    broadcast_leaderboard(room)

    return JsonResponse({
        "ok": True,
        "score": score,
        "detail": detailed
    })

@api_view(["GET"])
@permission_classes([AllowAny])
def leaderboard(request, code):
    code = code.upper()
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return HttpResponseBadRequest("Room not found")
    subs = Submission.objects.filter(player__room=room).select_related("player")
    data = [{
        "name": s.player.name,
        "roll": s.player.roll_number,
        "className": s.player.class_name,
        "score": s.score,
        "timeMs": s.time_ms,
        "when": int(s.submitted_at.timestamp()*1000),
    } for s in subs]
    data.sort(key=lambda x: (-x["score"], x["timeMs"] if x["timeMs"] is not None else 1e18))
    return JsonResponse({"leaderboard": data})
