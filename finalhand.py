import cv2
import mediapipe as mp
import time
import pyautogui

# Initialize MediaPipe Hand Tracking
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Open Webcam
cap = cv2.VideoCapture(0)

# Variables for tracking hand movements
prev_x = None
gesture_cooldown = time.time()

print(" Script started! Move your hand to control music.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print(" Webcam not accessible.")
        break

    # Flip frame for mirror effect
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process hand detection
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Detect Swipe Gestures
            x_wrist = hand_landmarks.landmark[0].x  # X-coordinate of the wrist

            if prev_x is not None:
                movement = x_wrist - prev_x
                if movement > 0.2 and time.time() - gesture_cooldown > 1:
                    print("➡️ Swiped Right - Next Song")
                    pyautogui.press("nexttrack")
                    gesture_cooldown = time.time()
                elif movement < -0.2 and time.time() - gesture_cooldown > 1:
                    print("⬅️ Swiped Left - Previous Song")
                    pyautogui.press("prevtrack")
                    gesture_cooldown = time.time()

            prev_x = x_wrist  # Update previous x-coordinate

            # Detect Open Palm (Play/Pause)
            finger_tips = [hand_landmarks.landmark[i] for i in [8, 12, 16, 20]]  # Index, Middle, Ring, Pinky
            palm_open = all(finger.y < hand_landmarks.landmark[0].y for finger in finger_tips)

            if palm_open and time.time() - gesture_cooldown > 1:
                print("🛑 Play/Pause")
                pyautogui.press("playpause")
                gesture_cooldown = time.time()

            # Detect Thumbs Up (Like Song)
            thumb_tip = hand_landmarks.landmark[4]  # Thumb tip
            thumb_base = hand_landmarks.landmark[2]  # Thumb base

            if thumb_tip.y < thumb_base.y and time.time() - gesture_cooldown > 1:
                print("👍 Liked Song")
                pyautogui.hotkey("ctrl", "l")  # Spotify like shortcut
                gesture_cooldown = time.time()

    # Show Webcam Feed
    cv2.imshow("Hand Gesture Music Control", frame)

    #  Quit if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
print("Script stopped.")
