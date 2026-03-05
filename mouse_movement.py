import cv2
import mediapipe as mp
import pyautogui
import math
import time

# Screen size
screen_width, screen_height = pyautogui.size()

# MediaPipe setup (CORRECT FORMAT)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# Webcam
cap = cv2.VideoCapture(0)

# Control variables
click_delay = 0.5
last_click_time = 0
dragging = False

# Smoothing
prev_x, prev_y = 0, 0
smoothening = 7

# Scroll
prev_scroll_y = 0
scroll_threshold = 20

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:

            # Landmarks
            index = hand_landmarks.landmark[8]
            thumb = hand_landmarks.landmark[4]
            middle = hand_landmarks.landmark[12]

            ix, iy = int(index.x * w), int(index.y * h)
            tx, ty = int(thumb.x * w), int(thumb.y * h)
            mx, my = int(middle.x * w), int(middle.y * h)

            # Draw points
            cv2.circle(frame, (ix, iy), 10, (0, 255, 0), -1)
            cv2.circle(frame, (tx, ty), 10, (255, 0, 0), -1)
            cv2.circle(frame, (mx, my), 10, (255, 255, 0), -1)

            # ---------------- Cursor Movement ----------------
            screen_x = int(index.x * screen_width)
            screen_y = int(index.y * screen_height)

            curr_x = prev_x + (screen_x - prev_x) / smoothening
            curr_y = prev_y + (screen_y - prev_y) / smoothening

            pyautogui.moveTo(curr_x, curr_y)
            prev_x, prev_y = curr_x, curr_y

            # ---------------- Distance Calculations ----------------
            distance_left = math.hypot(ix - tx, iy - ty)
            distance_right = math.hypot(mx - tx, my - ty)

            current_time = time.time()

            # ---------------- Drag & Left Click ----------------
            if distance_left < 30:
                if not dragging:
                    pyautogui.mouseDown()
                    dragging = True
                    cv2.putText(frame, "DRAGGING", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (0, 0, 255), 2)
            else:
                if dragging:
                    pyautogui.mouseUp()
                    dragging = False

            # ---------------- Right Click ----------------
            if distance_right < 30 and current_time - last_click_time > click_delay:
                pyautogui.rightClick()
                last_click_time = current_time
                cv2.putText(frame, "RIGHT CLICK", (50, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (255, 0, 0), 2)

            # ---------------- Scroll ----------------
            if prev_scroll_y != 0:
                diff = iy - prev_scroll_y
                if abs(diff) > scroll_threshold:
                    if diff < 0:
                        pyautogui.scroll(40)  # Scroll Up
                        cv2.putText(frame, "SCROLL UP", (50, 130),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                                    (0, 255, 0), 2)
                    else:
                        pyautogui.scroll(-40)  # Scroll Down
                        cv2.putText(frame, "SCROLL DOWN", (50, 170),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                                    (0, 255, 255), 2)

            prev_scroll_y = iy

            # Draw hand structure
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    cv2.imshow("Virtual Mouse", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()