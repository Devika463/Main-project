import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

# ── Windows only: Volume & Brightness ──
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    vol_range = volume.GetVolumeRange()  # (-65.25, 0.0)
    VOLUME_AVAILABLE = True
except:
    VOLUME_AVAILABLE = False
    print("[WARNING] Volume control not available")

try:
    import screen_brightness_control as sbc
    BRIGHTNESS_AVAILABLE = True
except:
    BRIGHTNESS_AVAILABLE = False
    print("[WARNING] Brightness control not available")

# ── Setup ──────────────────────────────
pyautogui.FAILSAFE = False
screen_w, screen_h = pyautogui.size()

mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils
hands    = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.85,
    min_tracking_confidence=0.8
)

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)
cam_w, cam_h = 640, 480

# ── Shared state (Django API reads this) ──
gesture_state = {
    "current_gesture": "None",
    "fps": 0,
    "camera": "connected",
    "gesture_active": True,
}

# ── State variables ────────────────────
prev_x, prev_y     = 0, 0
drag_active        = False
last_click_time    = 0
scroll_prev_y      = None
pinch_prev_x       = None
pinch_prev_y       = None
fps_counter        = 0
fps_start_time     = time.time()

# ── Helpers ────────────────────────────
def get_lm_list(hand_landmarks):
    lm = []
    for id, landmark in enumerate(hand_landmarks.landmark):
        cx = int(landmark.x * cam_w)
        cy = int(landmark.y * cam_h)
        lm.append([id, cx, cy])
    return lm

def fingers_up(lm):
    """Returns [Thumb, Index, Middle, Ring, Pinky] — 1=up, 0=down"""
    f = []
    f.append(1 if lm[4][1] < lm[3][1] else 0)   # Thumb (x-axis)
    for tip in [8, 12, 16, 20]:                    # 4 fingers (y-axis)
        f.append(1 if lm[tip][2] < lm[tip-2][2] else 0)
    return f

def dist(p1, p2):
    return np.hypot(p2[0]-p1[0], p2[1]-p1[1])

def map_to_screen(x, y):
    mx = int(np.interp(x, [50, cam_w-50], [0, screen_w]))
    my = int(np.interp(y, [50, cam_h-50], [0, screen_h]))
    return mx, my

# ── Main loop ──────────────────────────
def run_gesture():
    global prev_x, prev_y, drag_active, last_click_time
    global scroll_prev_y, pinch_prev_x, pinch_prev_y
    global fps_counter, fps_start_time

    print("[GESTURE] Starting Virtual Mouse...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        label = "No Hand"

        # ── FPS calculation ──
        fps_counter += 1
        elapsed = time.time() - fps_start_time
        if elapsed >= 1.0:
            gesture_state["fps"] = fps_counter
            fps_counter = 0
            fps_start_time = time.time()

        if result.multi_hand_landmarks:
            for hand_lm in result.multi_hand_landmarks:
                lm = get_lm_list(hand_lm)
                mp_draw.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)

                f = fingers_up(lm)

                index_tip  = (lm[8][1],  lm[8][2])
                middle_tip = (lm[12][1], lm[12][2])
                thumb_tip  = (lm[4][1],  lm[4][2])

                # ─────────────────────────────────────────
                # 1. MOUSE MOVE — Index only
                # ─────────────────────────────────────────
                if f == [0, 1, 0, 0, 0]:
                    label = "Mouse Move"
                    drag_active = False
                    mx, my = map_to_screen(index_tip[0], index_tip[1])
                    smooth_x = int(prev_x + (mx - prev_x) / 5)
                    smooth_y = int(prev_y + (my - prev_y) / 5)
                    pyautogui.moveTo(smooth_x, smooth_y)
                    prev_x, prev_y = smooth_x, smooth_y
                    cv2.circle(frame, index_tip, 10, (0, 255, 0), -1)

                # ─────────────────────────────────────────
                # 2. LEFT CLICK — Middle finger only (index down)
                # ─────────────────────────────────────────
                elif f == [0, 0, 1, 0, 0]:
                    label = "Left Click"
                    pyautogui.click()
                    time.sleep(0.3)
                    cv2.circle(frame, middle_tip, 12, (255, 0, 0), -1)

                # ─────────────────────────────────────────
                # 3. RIGHT CLICK — Index up + Middle curled
                # ─────────────────────────────────────────
                elif f[1] == 1 and lm[12][2] > lm[10][2] and f[2] == 0 and f[0] == 0:
                    label = "Right Click"
                    pyautogui.rightClick()
                    time.sleep(0.4)
                    cv2.circle(frame, index_tip, 12, (0, 0, 255), -1)

                # ─────────────────────────────────────────
                # 4. DOUBLE CLICK — Index + Middle close together
                # ─────────────────────────────────────────
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
                        # ─────────────────────────────────
                        # 6. SCROLL — Index + Middle up, move up/down
                        # ─────────────────────────────────
                        mid_y = (index_tip[1] + middle_tip[1]) // 2
                        if scroll_prev_y is not None:
                            diff = scroll_prev_y - mid_y
                            if abs(diff) > 5:
                                pyautogui.scroll(int(diff / 5))
                                label = "Scroll Up" if diff > 0 else "Scroll Down"
                        scroll_prev_y = mid_y

                # ─────────────────────────────────────────
                # 5. DRAG & DROP — Fist
                # ─────────────────────────────────────────
                elif f == [0, 0, 0, 0, 0]:
                    label = "Drag & Drop"
                    fx = lm[9][1]
                    fy = lm[9][2]
                    mx, my = map_to_screen(fx, fy)
                    if not drag_active:
                        pyautogui.mouseDown()
                        drag_active = True
                    pyautogui.moveTo(mx, my, duration=0.05)
                    cv2.putText(frame, "DRAGGING", (10, 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                else:
                    # Release drag if fist released
                    if drag_active:
                        pyautogui.mouseUp()
                        drag_active = False
                    scroll_prev_y = None

                # ─────────────────────────────────────────
                # 7. VOLUME — Thumb + Index pinch, vertical
                # ─────────────────────────────────────────
                if f == [1, 1, 0, 0, 0] and VOLUME_AVAILABLE:
                    d = dist(thumb_tip, index_tip)
                    if d < 40:
                        cv2.line(frame, thumb_tip, index_tip, (0, 255, 255), 3)
                        if pinch_prev_y is not None:
                            diff_y = pinch_prev_y - index_tip[1]
                            if abs(diff_y) > 5:
                                curr_vol = volume.GetMasterVolumeLevel()
                                new_vol  = max(vol_range[0], min(vol_range[1], curr_vol + diff_y * 0.3))
                                volume.SetMasterVolumeLevel(new_vol, None)
                                label = "Volume Up" if diff_y > 0 else "Volume Down"
                        pinch_prev_y = index_tip[1]
                    else:
                        pinch_prev_y = None

                # ─────────────────────────────────────────
                # 8. BRIGHTNESS — Thumb + Index pinch, horizontal
                # ─────────────────────────────────────────
                if f == [1, 1, 0, 0, 0] and BRIGHTNESS_AVAILABLE:
                    d = dist(thumb_tip, index_tip)
                    if d < 40:
                        if pinch_prev_x is not None:
                            diff_x = index_tip[0] - pinch_prev_x
                            if abs(diff_x) > 5:
                                curr_b = sbc.get_brightness(display=0)[0]
                                new_b  = max(0, min(100, curr_b + int(diff_x / 5)))
                                sbc.set_brightness(new_b, display=0)
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

        # ── UI Overlay ──
        cv2.rectangle(frame, (0, 0), (320, 40), (0, 0, 0), -1)
        cv2.putText(frame, f"Gesture: {label}", (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 180), 2)
        cv2.putText(frame, f"FPS: {gesture_state['fps']}", (cam_w-100, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 200), 1)

        cv2.imshow("SMART MOUSE — Gesture Control", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    if drag_active:
        pyautogui.mouseUp()
    cap.release()
    cv2.destroyAllWindows()
    gesture_state["camera"] = "disconnected"
    print("[GESTURE] Stopped.")

if __name__ == "__main__":
    run_gesture()
