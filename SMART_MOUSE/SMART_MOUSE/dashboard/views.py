from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
import json, threading, sys, os, cv2, time, numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import virtual_mouse as vm
    from virtual_mouse import gesture_state, run_gesture
    from voice_assistant import voice_state, start_voice_thread
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] {e}")
    MODULES_AVAILABLE = False
    gesture_state = {"current_gesture":"None","fps":0,"camera":"disconnected","gesture_active":False}
    voice_state   = {"voice_active":False,"last_command":""}

gesture_thread   = None
voice_thread_ref = None
streaming_active = False  # ← stream control

def generate_frames():
    global streaming_active
    streaming_active = True
    while streaming_active:
        try:
            frame = vm.latest_frame if MODULES_AVAILABLE else None
            if frame is not None:
                _, buffer = cv2.imencode('.jpg', frame,
                                         [cv2.IMWRITE_JPEG_QUALITY, 75])
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                       + buffer.tobytes() + b'\r\n')
            else:
                blank = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(blank, "Click Start System",
                            (150, 240), cv2.FONT_HERSHEY_SIMPLEX,
                            0.9, (0, 255, 180), 2)
                _, buffer = cv2.imencode('.jpg', blank)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                       + buffer.tobytes() + b'\r\n')
        except Exception as e:
            print(f"[STREAM] {e}")
        time.sleep(0.033)

def video_feed(request):
    return StreamingHttpResponse(
        generate_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

def home(request):
    return render(request, 'dashboard/index.html')

def get_status(request):
    return JsonResponse({
        "gesture_active":    vm.gesture_state.get("gesture_active", False) if MODULES_AVAILABLE else False,
        "voice_active":      voice_state.get("voice_active", False),
        "camera":            vm.gesture_state.get("camera", "disconnected") if MODULES_AVAILABLE else "disconnected",
        "fps":               vm.gesture_state.get("fps", 0) if MODULES_AVAILABLE else 0,
        "current_gesture":   vm.gesture_state.get("current_gesture", "None") if MODULES_AVAILABLE else "None",
        "last_command":      voice_state.get("last_command", ""),
        "modules_available": MODULES_AVAILABLE,
    })

def start_system(request):
    global gesture_thread, voice_thread_ref

    if not MODULES_AVAILABLE:
        return JsonResponse({"status":"error","message":"Modules not installed"}, status=500)

    # gesture_active True ആക്കൂ
    vm.gesture_state["gesture_active"] = True

    # Gesture thread start — stream തുടങ്ങുന്നതിന് മുമ്പ്
    if gesture_thread is None or not gesture_thread.is_alive():
        gesture_thread = threading.Thread(target=run_gesture, daemon=True)
        gesture_thread.start()
        print("[DJANGO] Gesture thread started!")
        time.sleep(2)  # ← camera open ആകാൻ 2 seconds wait
        print(f"[DJANGO] Thread alive: {gesture_thread.is_alive()}")
        print(f"[DJANGO] Camera: {vm.gesture_state.get('camera')}")

    if voice_thread_ref is None or not voice_thread_ref.is_alive():
        voice_thread_ref = start_voice_thread()

    return JsonResponse({"status": "started"})

def stop_system(request):
    global streaming_active
    streaming_active = False
    if MODULES_AVAILABLE:
        vm.gesture_state["gesture_active"] = False
    voice_state["voice_active"] = False
    return JsonResponse({"status": "stopped"})

def update_settings(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if MODULES_AVAILABLE:
            if "gesture_active" in data:
                vm.gesture_state["gesture_active"] = data["gesture_active"]
        if "voice_active" in data:
            voice_state["voice_active"] = data["voice_active"]
        return JsonResponse({"status": "ok", "saved": data})
    return JsonResponse({"error": "POST only"}, status=405)