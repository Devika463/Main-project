import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

# ── Volume ──
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    devices   = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume    = cast(interface, POINTER(IAudioEndpointVolume))
    vol_range = volume.GetVolumeRange()
    VOLUME_AVAILABLE = True
except:
    VOLUME_AVAILABLE = False

# ── Brightness ──
try:
    import screen_brightness_control as sbc
    BRIGHTNESS_AVAILABLE = True
except:
    BRIGHTNESS_AVAILABLE = False

pyautogui.FAILSAFE = False
screen_w, screen_h = pyautogui.size()

mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils

gesture_state = {
    "current_gesture": "None",
    "fps": 0,
    "camera": "disconnected",
    "gesture_active": True,
}

latest_frame = None
cap = None

prev_x, prev_y = 0, 0
drag_active     = False
last_click_time = 0
scroll_prev_y   = None
pinch_prev_x    = None
pinch_prev_y    = None

def get_lm_list(hand_landmarks, cam_w, cam_h):
    lm = []
    for id, landmark in enumerate(hand_landmarks.landmark):
        lm.append([id, int(landmark.x * cam_w), int(landmark.y * cam_h)])
    return lm

def fingers_up(lm):
    f = []
    f.append(1 if lm[4][1] < lm[3][1] else 0)
    for tip in [8, 12, 16, 20]:
        f.append(1 if lm[tip][2] < lm[tip-2][2] else 0)
    return f

def dist(p1, p2):
    return np.hypot(p2[0]-p1[0], p2[1]-p1[1])

def map_to_screen(x, y, cam_w, cam_h):
    mx = int(np.interp(x, [50, cam_w-50], [0, screen_w]))
    my = int(np.interp(y, [50, cam_h-50], [0, screen_h]))
    return mx, my

def run_gesture():
    global prev_x, prev_y, drag_active, last_click_time
    global scroll_prev_y, pinch_prev_x, pinch_prev_y
    global latest_frame, cap

    print("[GESTURE] Starting Virtual Mouse...")

    cam_w, cam_h = 640, 480

    # ── Camera open ──
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(3, cam_w)
        cap.set(4, cam_h)
        print(f"[GESTURE] Camera opened: {cap.isOpened()}")
    except Exception as e:
        print(f"[GESTURE] Camera exception: {e}")
        gesture_state["camera"] = "disconnected"
        return

    if not cap.isOpened():
        print("[GESTURE] ERROR: Cannot open camera!")
        gesture_state["camera"] = "disconnected"
        return

    gesture_state["camera"] = "connected"
    gesture_state["gesture_active"] = True

    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.85,
        min_tracking_confidence=0.8
    )

    fps_count = 0
    fps_time  = time.time()

    while gesture_state.get("gesture_active", True):
        ret, frame = cap.read()

        if not ret:
            print("[GESTURE] Camera read failed, retrying...")
            time.sleep(0.05)
            continue

        frame  = cv2.flip(frame, 1)
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        fps_count += 1
        if time.time() - fps_time >= 1.0:
            gesture_state["fps"] = fps_count
            fps_count = 0
            fps_time  = time.time()

        label = "No Hand"

        if result.multi_hand_landmarks:
            for hand_lm in result.multi_hand_landmarks:
                lm = get_lm_list(hand_lm, cam_w, cam_h)
                mp_draw.draw_landmarks(
                    frame, hand_lm, mp_hands.HAND_CONNECTIONS,
                    mp_draw.DrawingSpec(color=(0,255,180), thickness=2, circle_radius=4),
                    mp_draw.DrawingSpec(color=(255,255,255), thickness=2)
                )
                f          = fingers_up(lm)
                index_tip  = (lm[8][1],  lm[8][2])
                middle_tip = (lm[12][1], lm[12][2])
                thumb_tip  = (lm[4][1],  lm[4][2])

                if f == [0, 1, 0, 0, 0]:
                    label = "Mouse Move"
                    drag_active = False
                    mx, my = map_to_screen(index_tip[0], index_tip[1], cam_w, cam_h)
                    sx = int(prev_x + (mx - prev_x) / 5)
                    sy = int(prev_y + (my - prev_y) / 5)
                    pyautogui.moveTo(sx, sy)
                    prev_x, prev_y = sx, sy
                    cv2.circle(frame, index_tip, 10, (0,255,0), -1)

                elif f == [0, 0, 1, 0, 0]:
                    label = "Left Click"
                    pyautogui.click()
                    time.sleep(0.3)

                elif f[1] == 1 and f[2] == 0 and lm[12][2] > lm[10][2] and f[0] == 0:
                    label = "Right Click"
                    pyautogui.rightClick()
                    time.sleep(0.4)

                elif f[1] == 1 and f[2] == 1 and f[3] == 0 and f[4] == 0 and f[0] == 0:
                    d = dist(index_tip, middle_tip)
                    if d < 25:
                        now = time.time()
                        if now - last_click_time < 0.5:
                            label = "Double Click"
                            pyautogui.doubleClick()
                            time.sleep(0.4)
                        last_click_time = now
                    else:
                        mid_y = (index_tip[1] + middle_tip[1]) // 2
                        if scroll_prev_y is not None:
                            diff = scroll_prev_y - mid_y
                            if abs(diff) > 5:
                                pyautogui.scroll(int(diff / 5))
                                label = "Scroll Up" if diff > 0 else "Scroll Down"
                        scroll_prev_y = mid_y

                elif f == [0, 0, 0, 0, 0]:
                    label = "Drag & Drop"
                    mx, my = map_to_screen(lm[9][1], lm[9][2], cam_w, cam_h)
                    if not drag_active:
                        pyautogui.mouseDown()
                        drag_active = True
                    pyautogui.moveTo(mx, my, duration=0.05)

                else:
                    if drag_active:
                        pyautogui.mouseUp()
                        drag_active = False
                    scroll_prev_y = None

                if f == [1, 1, 0, 0, 0] and VOLUME_AVAILABLE:
                    if dist(thumb_tip, index_tip) < 40:
                        if pinch_prev_y is not None:
                            diff_y = pinch_prev_y - index_tip[1]
                            if abs(diff_y) > 5:
                                curr = volume.GetMasterVolumeLevel()
                                volume.SetMasterVolumeLevel(
                                    max(vol_range[0], min(vol_range[1], curr + diff_y * 0.3)), None)
                                label = "Volume Up" if diff_y > 0 else "Volume Down"
                        pinch_prev_y = index_tip[1]
                    else:
                        pinch_prev_y = None

                if f == [1, 1, 0, 0, 0] and BRIGHTNESS_AVAILABLE:
                    if dist(thumb_tip, index_tip) < 40:
                        if pinch_prev_x is not None:
                            diff_x = index_tip[0] - pinch_prev_x
                            if abs(diff_x) > 5:
                                curr = sbc.get_brightness(display=0)[0]
                                sbc.set_brightness(
                                    max(0, min(100, curr + int(diff_x/5))), display=0)
                                label = "Brightness Up" if diff_x > 0 else "Brightness Down"
                        pinch_prev_x = index_tip[0]
                    else:
                        pinch_prev_x = None

                gesture_state["current_gesture"] = label

        else:
            gesture_state["current_gesture"] = "No Hand"
            if drag_active:
                pyautogui.mouseUp()
                drag_active = False

        cv2.rectangle(frame, (0,0), (350,44), (0,0,0), -1)
        cv2.putText(frame, f"Gesture: {label}", (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,180), 2)
        cv2.putText(frame, f"FPS: {gesture_state['fps']}", (555,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200,200,200), 1)

        latest_frame = frame.copy()

    if drag_active:
        pyautogui.mouseUp()
    if cap:
        cap.release()
    gesture_state["camera"] = "disconnected"
    latest_frame = None
    print("[GESTURE] Stopped.")

if __name__ == "__main__":
    gesture_state["gesture_active"] = True
    run_gesture()