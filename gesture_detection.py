import cv2
import mediapipe as mp
import time
import math
import pyautogui

# Initialize MediaPipe
cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Swipe Detection History
swipe_history = []
max_history = 5
swipe_threshold = 0.15  # Lower = more sensitive

# Cooldown management
last_gesture_time = 0
gesture_cooldown = 1.2  # seconds
last_action = 0

# Gesture state
prev_gesture = "Pause"

def get_distance(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

def fingers_up(landmarks):
    fingers = []
    fingers.append(landmarks[4].x < landmarks[3].x)  # Thumb
    for tip, pip in zip([8, 12, 16, 20], [6, 10, 14, 18]):
        fingers.append(landmarks[tip].y < landmarks[pip].y)
    return fingers

while True:
    success, img = cap.read()
    if not success:
        break

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    gesture_info = ""
    now = time.time()

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
            lm = handLms.landmark
            fingers = fingers_up(lm)
            count = fingers.count(True)

            # Debug info
            gesture_info = f"Fingers: {count} → "

            # Play/Pause toggle with open hand
            if count >= 4 and (now - last_gesture_time) > gesture_cooldown:
                gesture = "Play" if prev_gesture == "Pause" else "Pause"
                pyautogui.press('playpause')
                print(f"[Gesture] {gesture}")
                prev_gesture = gesture
                last_gesture_time = now

            # Volume Control (using thumb + index pinch)
            elif count <= 1:
                thumb = lm[4]
                index = lm[8]
                dist = get_distance(thumb, index)

                if dist < 0.05:
                    pyautogui.press('volumedown')
                    gesture_info += "Volume: Low"
                elif dist < 0.1:
                    gesture_info += "Volume: Medium"
                elif dist < 0.2:
                    pyautogui.press('volumeup')
                    gesture_info += "Volume: High"

                last_gesture_time = now

            # Improved Swipe Detection with 2 fingers
            elif count == 2:
                wrist_x = lm[0].x
                swipe_history.append(wrist_x)

                if len(swipe_history) > max_history:
                    swipe_history.pop(0)

                if len(swipe_history) == max_history:
                    movement = swipe_history[-1] - swipe_history[0]
                    gesture_info += f" | Swipe Δ: {movement:.2f}"

                    if abs(movement) > swipe_threshold and (now - last_action) > gesture_cooldown:
                        if movement > 0:
                            pyautogui.press('nexttrack')
                            print("[Gesture] Swipe Right → Next Song")
                            gesture_info += " → Swipe Right"
                        else:
                            pyautogui.press('prevtrack')
                            print("[Gesture] Swipe Left → Prev Song")
                            gesture_info += " → Swipe Left"

                        swipe_history.clear()
                        last_action = now
            else:
                swipe_history.clear()

            # Display gesture info on screen
            cv2.putText(img, gesture_info, (10, 70), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (255, 0, 0), 2)
    else:
        swipe_history.clear()
        cv2.putText(img, "No hand detected", (10, 70), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 0, 255), 2)

    cv2.imshow("Gesture Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()



'''import cv2
import mediapipe as mp
import time
import math

# Setup
cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

last_gesture_time = 0
gesture_cooldown = 1
gesture_mode_lock = None
mode_lock_time = 0
lock_duration = 1.2
prev_x = None
prev_gesture = "Pause"

def get_distance(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

def fingers_up(landmarks):
    fingers = []
    fingers.append(landmarks[4].x < landmarks[3].x)  # Thumb
    for tip, pip in zip([8, 12, 16, 20], [6, 10, 14, 18]):
        fingers.append(landmarks[tip].y < landmarks[pip].y)
    return fingers

while True:
    success, img = cap.read()
    if not success:
        break

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    gesture_detected = None
    gesture_info = ""
    current_time = time.time()

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
            landmarks = handLms.landmark
            wrist = landmarks[0]
            thumb = landmarks[4]
            index = landmarks[8]

            fingers = fingers_up(landmarks)
            finger_count = fingers.count(True)

            # Gesture Debug Text
            gesture_info = f"Fingers Up: {finger_count} → "

            if gesture_mode_lock and (current_time - mode_lock_time < lock_duration):
                gesture_detected = f"Locked ({gesture_mode_lock})"
                gesture_info += gesture_detected
            elif (current_time - last_gesture_time) > gesture_cooldown:
                if finger_count >= 4:
                    gesture_detected = "Play" if prev_gesture == "Pause" else "Pause"
                    prev_gesture = gesture_detected
                    gesture_mode_lock = "playpause"
                    mode_lock_time = current_time

                elif finger_count <= 1:
                    dist = get_distance(thumb, index)
                    if dist < 0.05:
                        gesture_detected = "Volume: Low"
                    elif dist < 0.1:
                        gesture_detected = "Volume: Medium"
                    elif dist < 0.2:
                        gesture_detected = "Volume: High"
                    if gesture_detected:
                        gesture_mode_lock = "volume"
                        mode_lock_time = current_time

                elif finger_count == 2:
                    wrist_x = wrist.x
                    if prev_x is not None:
                        dx = wrist_x - prev_x
                        if dx > 0.15:
                            gesture_detected = "Swipe Right (Next Song)"
                            gesture_mode_lock = "swipe"
                            mode_lock_time = current_time
                        elif dx < -0.15:
                            gesture_detected = "Swipe Left (Prev Song)"
                            gesture_mode_lock = "swipe"
                            mode_lock_time = current_time
                    prev_x = wrist_x

                if gesture_detected:
                    last_gesture_time = current_time
                    gesture_info += gesture_detected
                    print(f"[Gesture] {gesture_info}")
            else:
                gesture_info += "Waiting..."

            # Display Info on Screen
            cv2.putText(img, gesture_info, (10, 70), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (255, 0, 0), 2)

    else:
        cv2.putText(img, "No hand detected", (10, 70), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 0, 255), 2)

    cv2.imshow("Gesture Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
'''