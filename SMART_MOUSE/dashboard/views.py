from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
import json
import threading
import sys
import os
import cv2
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from virtual_mouse import gesture_state, run_gesture
    from voice_assistant import voice_state, start_voice_thread
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] Could not import modules: {e}")
    MODULES_AVAILABLE = False
    gesture_state = {"current_gesture": "None", "fps": 0, "camera": "disconnected", "gesture_active": False}
    voice_state   = {"voice_active": False, "last_command": ""}

gesture_thread   = None
voice_thread_ref = None

# ── MJPEG Camera Stream ────────────────
import mediapipe as mp
import numpy as np

mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils

def generate_frames():
    """Yields MJPEG frames with hand landmarks drawn."""
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    gesture_state["camera"] = "connected"

    hands_detector = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.8,
        min_tracking_confidence=0.75
    )

    fps_time = time.time()
    fps_count = 0
    fps_display = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands_detector.process(rgb)

        # FPS
        fps_count += 1
        if time.time() - fps_time >= 1.0:
            fps_display = fps_count
            gesture_state["fps"] = fps_display
            fps_count = 0
            fps_time  = time.time()

        label = gesture_state.get("current_gesture", "No Hand")

        if result.multi_hand_landmarks:
            for hand_lm in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame, hand_lm, mp_hands.HAND_CONNECTIONS,
                    mp_draw.DrawingSpec(color=(0, 255, 180), thickness=2, circle_radius=4),
                    mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2)
                )

        # Overlay — gesture label
        cv2.rectangle(frame, (0, 0), (350, 44), (0, 0, 0), -1)
        cv2.putText(frame, f"Gesture: {label}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 180), 2)

        # Overlay — FPS
        cv2.putText(frame, f"FPS: {fps_display}", (555, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 200), 1)

        # Encode to JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()
    gesture_state["camera"] = "disconnected"


def video_feed(request):
    """MJPEG stream endpoint — /api/video/"""
    return StreamingHttpResponse(
        generate_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


def home(request):
    return render(request, 'dashboard/index.html')


def get_status(request):
    return JsonResponse({
        "gesture_active":    gesture_state.get("gesture_active", False),
        "voice_active":      voice_state.get("voice_active", False),
        "camera":            gesture_state.get("camera", "disconnected"),
        "fps":               gesture_state.get("fps", 0),
        "current_gesture":   gesture_state.get("current_gesture", "None"),
        "last_command":      voice_state.get("last_command", ""),
        "modules_available": MODULES_AVAILABLE,
    })


def start_system(request):
    global gesture_thread, voice_thread_ref
    if not MODULES_AVAILABLE:
        return JsonResponse({"status": "error", "message": "Modules not installed"}, status=500)
    if gesture_thread is None or not gesture_thread.is_alive():
        gesture_thread = threading.Thread(target=run_gesture, daemon=True)
        gesture_thread.start()
    if voice_thread_ref is None or not voice_thread_ref.is_alive():
        voice_thread_ref = start_voice_thread()
    return JsonResponse({"status": "started"})


def stop_system(request):
    voice_state["voice_active"]     = False
    gesture_state["gesture_active"] = False
    return JsonResponse({"status": "stopped"})


def update_settings(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if "gesture_active" in data:
            gesture_state["gesture_active"] = data["gesture_active"]
        if "voice_active" in data:
            voice_state["voice_active"] = data["voice_active"]
        return JsonResponse({"status": "ok", "saved": data})
    return JsonResponse({"error": "POST only"}, status=405)
