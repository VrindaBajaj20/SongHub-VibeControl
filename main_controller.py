import cv2
import mediapipe as mp
import time
import math
import pyautogui
import speech_recognition as sr
import pyttsx3
import webbrowser
import urllib.parse
import threading

# Initialize MediaPipe
cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Swipe Detection History
swipe_history = []
max_history = 5
swipe_threshold = 0.15  # Lower = more sensitive

# Cooldown management for gestures
last_gesture_time = 0
gesture_cooldown = 1.2  # seconds
last_action = 0

# Gesture state
prev_gesture = "Pause"

# Speech Engine
engine = pyttsx3.init()

def speak(text):
    print(f"🗣 {text}")
    engine.say(text)
    engine.runAndWait()

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙 Listening... Speak now!")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio).lower()
        print(f"🎤 Recognized text: {text}")
        return text
    except sr.UnknownValueError:
        print("🤷 Couldn't understand the audio.")
        return ""
    except sr.RequestError:
        print("⚠ Speech Recognition API unavailable.")
        return ""

def get_intent(text):
    # Priority match for control commands first
    play_words = ["play", "resume", "start"]
    pause_words = ["pause", "stop", "halt"]
    next_words = ["next", "skip"]
    prev_words = ["previous", "back"]
    repeat_words = ["repeat", "again"]
    vol_up = ["volume up", "increase", "louder"]
    vol_down = ["volume down", "decrease", "softer"]
    mute_words = ["mute"]
    unmute_words = ["unmute"]

    if any(word in text for word in pause_words): return "pause"
    if any(word in text for word in next_words): return "next"
    if any(word in text for word in prev_words): return "previous"
    if any(word in text for word in repeat_words): return "repeat"
    if any(word in text for word in vol_up): return "volume up"
    if any(word in text for word in vol_down): return "volume down"
    if any(word in text for word in mute_words): return "mute"
    if any(word in text for word in unmute_words): return "unmute"
    if text.strip() in play_words: return "play"

    if text.startswith("play "):
        return "search_play"

    return None

def execute_command(cmd, text=""):
    if cmd == "play":
        pyautogui.press("playpause")
        speak("▶ Playing")
    elif cmd == "pause":
        pyautogui.press("playpause")
        speak("⏸ Paused")
    elif cmd == "next":
        pyautogui.press("nexttrack")
        speak("⏭ Skipping")
    elif cmd == "previous":
        pyautogui.press("prevtrack")
        speak("⏮ Going back")
    elif cmd == "repeat":
        pyautogui.press("prevtrack")
        speak("🔁 Repeating")
    elif cmd == "volume up":
        pyautogui.press("volumeup")
        speak("🔊 Volume up")
    elif cmd == "volume down":
        pyautogui.press("volumedown")
        speak("🔉 Volume down")
    elif cmd == "mute":
        pyautogui.press("volumemute")
        speak("🔇 Muted")
    elif cmd == "unmute":
        pyautogui.press("volumemute")
        speak("🔊 Unmuted")
    elif cmd == "search_play":
        song = text.replace("play", "", 1).strip()
        if song:
            query = urllib.parse.quote(song)
            #youtube open 
            # webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            #spotify open
            webbrowser.open(f"https://open.spotify.com/search/{query}")
            speak(f"🎵 Searching and playing {song} on Spotify")
        else:
            speak("Please say the song name after 'play'")

# Initialize hand gesture functions
def get_distance(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

def fingers_up(landmarks):
    fingers = []
    fingers.append(landmarks[4].x < landmarks[3].x)  # Thumb
    for tip, pip in zip([8, 12, 16, 20], [6, 10, 14, 18]):
        fingers.append(landmarks[tip].y < landmarks[pip].y)
    return fingers

def gesture_control():
    global prev_gesture, last_gesture_time, last_action
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

                # Swipe Detection with 2 fingers
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
                cv2.putText(img, gesture_info, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        else:
            swipe_history.clear()
            cv2.putText(img, "No hand detected", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow("Gesture Control", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Voice Command Handling Thread
def voice_control():
    speak("Hello! I am your voice assistant. How can I help with your music?")
    while True:
        print("⏳ Waiting for command...")
        text = listen()
        if not text: continue
        if "song" in text or "songhub" in text:
            cmd = get_intent(text)
            if cmd:
                print(f"✅ Detected command: {cmd}")
                execute_command(cmd, text)
            else:
                print("🤷 No recognizable command detected.")

# Main function to start both voice and gesture threads
if __name__ == "__main__":
    # Start gesture control in a separate thread
    gesture_thread = threading.Thread(target=gesture_control, daemon=True)
    gesture_thread.start()

    # Start voice control in the main thread
    voice_control()

'''import cv2
import mediapipe as mp
import time
import math
import threading
import pyttsx3
import speech_recognition as sr
import pyautogui

# ========== VOICE SETUP ==========
engine = pyttsx3.init()
recognizer = sr.Recognizer()
mic = sr.Microphone()

def speak(text):
    print(f"[Voice Assistant] {text}")
    engine.say(text)
    engine.runAndWait()

def process_voice_command(command):
    command = command.lower()
    if "play" in command:
        speak("Playing")
        pyautogui.press('playpause')

    elif "pause" in command:
        speak("Pausing")
        pyautogui.press('playpause')

    elif "next" in command:
        speak("Next track")
        pyautogui.press('nexttrack')

    elif "previous" in command or "back" in command:
        speak("Previous track")
        pyautogui.press('prevtrack')

    elif "volume up" in command:
        speak("Volume up")
        pyautogui.press('volumeup')

    elif "volume down" in command:
        speak("Volume down")
        pyautogui.press('volumedown')

    elif "stop" in command or "exit" in command:
        speak("Goodbye")
        exit(0)
    else:
        speak("Sorry, I didn't understand that.")

def voice_assistant_loop():
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)

    while True:
        with mic as source:
            print("\n[Listening] Say something (waiting for 'songhub')...")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
                transcript = recognizer.recognize_google(audio)
                print(f"[Heard] {transcript}")

                # Normalize
                normalized_transcript = transcript.replace(" ", "").replace("-", "").lower()
                if "songhub" in normalized_transcript:
                    speak("Yes?")
                    print("[Wake Word Detected]")

                    with mic as source:
                        print("[Listening for command]")
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

                        try:
                            command = recognizer.recognize_google(audio)
                            print(f"[Command] {command}")
                            process_voice_command(command)
                        except sr.UnknownValueError:
                            speak("I didn't catch that. Please try again.")
                        except sr.RequestError:
                            speak("There was an issue with the network.")

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                print("[Unrecognized Speech]")
                continue
            except sr.RequestError:
                speak("Network error.")
                continue

# ========== GESTURE SETUP ==========
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

def gesture_detection_loop():
    global last_gesture_time, gesture_mode_lock, mode_lock_time, prev_x, prev_gesture

    while True:
        success, img = cap.read()
        if not success:
            continue

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

                gesture_info = f"Fingers Up: {finger_count} → "

                if gesture_mode_lock and (current_time - mode_lock_time < lock_duration):
                    gesture_detected = f"Locked ({gesture_mode_lock})"
                    gesture_info += gesture_detected
                elif (current_time - last_gesture_time) > gesture_cooldown:
                    if finger_count >= 4:
                        gesture_detected = "Play" if prev_gesture == "Pause" else "Pause"
                        prev_gesture = gesture_detected
                        pyautogui.press('playpause')
                        gesture_mode_lock = "playpause"
                        mode_lock_time = current_time

                    elif finger_count <= 1:
                        dist = get_distance(thumb, index)
                        if dist < 0.05:
                            pyautogui.press('volumedown')
                            gesture_detected = "Volume: Low"
                        elif dist < 0.1:
                            pyautogui.press('volumedown')
                            pyautogui.press('volumedown')
                            gesture_detected = "Volume: Medium"
                        elif dist < 0.2:
                            pyautogui.press('volumeup')
                            pyautogui.press('volumeup')
                            gesture_detected = "Volume: High"
                        if gesture_detected:
                            gesture_mode_lock = "volume"
                            mode_lock_time = current_time

                    elif finger_count == 2:
                        wrist_x = wrist.x
                        if prev_x is not None:
                            dx = wrist_x - prev_x
                            if dx > 0.15:
                                gesture_detected = "Swipe Right (Next)"
                                pyautogui.press('nexttrack')
                                gesture_mode_lock = "swipe"
                                mode_lock_time = current_time
                            elif dx < -0.15:
                                gesture_detected = "Swipe Left (Prev)"
                                pyautogui.press('prevtrack')
                                gesture_mode_lock = "swipe"
                                mode_lock_time = current_time
                        prev_x = wrist_x

                    if gesture_detected:
                        last_gesture_time = current_time
                        gesture_info += gesture_detected
                        print(f"[Gesture] {gesture_info}")
                else:
                    gesture_info += "Waiting..."

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

# ========== MAIN ==========
if __name__ == "__main__":
    voice_thread = threading.Thread(target=voice_assistant_loop, daemon=True)
    gesture_thread = threading.Thread(target=gesture_detection_loop)

    voice_thread.start()
    gesture_thread.start()

    gesture_thread.join()
'''



'''import threading
import time
import math
import pyttsx3
import pyautogui
import speech_recognition as sr
import cv2
import mediapipe as mp

# --- Voice Assistant Section ---
engine = pyttsx3.init()

def speak(text):
    print(f"[Voice Assistant] {text}")
    engine.say(text)
    engine.runAndWait()

def listen_for_command(recognizer, mic):
    with mic as source:
        print("Listening...")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
        command = recognizer.recognize_google(audio).lower()
        print(f"[Heard] {command}")
        return command

def voice_assistant():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        speak("Voice assistant is running. Say 'SongHub' to start.")

    while True:
        try:
            command = listen_for_command(recognizer, mic)

            if "songhub" in command:
                speak("Yes?")
                time.sleep(0.5)

                for attempt in range(2):
                    try:
                        user_cmd = listen_for_command(recognizer, mic)

                        if "play" in user_cmd:
                            speak("Playing")
                            pyautogui.press('playpause')
                            break

                        elif "pause" in user_cmd:
                            speak("Pausing")
                            pyautogui.press('playpause')
                            break

                        elif "next" in user_cmd:
                            speak("Next track")
                            pyautogui.press('nexttrack')
                            break

                        elif "previous" in user_cmd or "back" in user_cmd:
                            speak("Previous track")
                            pyautogui.press('prevtrack')
                            break

                        elif "volume up" in user_cmd:
                            speak("Volume up")
                            pyautogui.press('volumeup')
                            break

                        elif "volume down" in user_cmd:
                            speak("Volume down")
                            pyautogui.press('volumedown')
                            break

                        elif "stop" in user_cmd or "exit" in user_cmd:
                            speak("Goodbye")
                            return

                        else:
                            speak("Could you repeat that?")
                    except sr.UnknownValueError:
                        speak("Sorry, I didn't get that.")
                    except sr.RequestError as e:
                        print(f"[API Error] {e}")
                        speak("API issue, try again later.")
                        break

        except sr.WaitTimeoutError:
            continue
        except Exception as e:
            print(f"[Voice Error] {e}")


# --- Gesture Detection Section ---
def get_distance(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

def fingers_up(landmarks):
    fingers = []
    fingers.append(landmarks[4].x < landmarks[3].x)  # Thumb
    for tip, pip in zip([8, 12, 16, 20], [6, 10, 14, 18]):
        fingers.append(landmarks[tip].y < landmarks[pip].y)
    return fingers

def gesture_detection():
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

    while True:
        success, img = cap.read()
        if not success:
            continue

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

                if gesture_mode_lock and (current_time - mode_lock_time < lock_duration):
                    gesture_detected = f"Locked ({gesture_mode_lock})"
                elif (current_time - last_gesture_time) > gesture_cooldown:
                    if finger_count >= 4:
                        gesture_detected = "Play" if prev_gesture == "Pause" else "Pause"
                        prev_gesture = gesture_detected
                        pyautogui.press('playpause')
                        gesture_mode_lock = "playpause"
                        mode_lock_time = current_time

                    elif finger_count <= 1:
                        dist = get_distance(thumb, index)
                        if dist < 0.05:
                            pyautogui.press('volumedown')
                        elif dist < 0.1:
                            pass  # medium volume level can be neutral
                        elif dist < 0.2:
                            pyautogui.press('volumeup')
                        gesture_mode_lock = "volume"
                        mode_lock_time = current_time

                    elif finger_count == 2:
                        wrist_x = wrist.x
                        if prev_x is not None:
                            dx = wrist_x - prev_x
                            if dx > 0.15:
                                pyautogui.press('nexttrack')
                                gesture_mode_lock = "swipe"
                                mode_lock_time = current_time
                            elif dx < -0.15:
                                pyautogui.press('prevtrack')
                                gesture_mode_lock = "swipe"
                                mode_lock_time = current_time
                        prev_x = wrist_x

                    if gesture_detected:
                        last_gesture_time = current_time

                cv2.putText(img, f"Gesture: {gesture_detected or 'Detecting...'}", (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        else:
            cv2.putText(img, "No hand detected", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow("Gesture Control", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# --- Run Both in Parallel ---
if __name__ == "__main__":
    voice_thread = threading.Thread(target=voice_assistant)
    gesture_thread = threading.Thread(target=gesture_detection)

    voice_thread.start()
    gesture_thread.start()

    voice_thread.join()
    gesture_thread.join()

'''

'''import threading
import time
import cv2
import mediapipe as mp
import math
import speech_recognition as sr
import pyttsx3
import pyautogui

# ----- VOICE SECTION -----

engine = pyttsx3.init()
def speak(text):
    print(f"[Voice Assistant] {text}")
    engine.say(text)
    engine.runAndWait()

def listen_for_keyword(recognizer, mic):
    with mic as source:
        try:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
            command = recognizer.recognize_google(audio).lower()
            print(f"[Heard] {command}")
            return command
        except:
            return ""

def voice_assistant():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)

    while True:
        command = listen_for_keyword(recognizer, mic)
        if "play" in command:
            speak("Playing")
            pyautogui.press('playpause')
        elif "pause" in command:
            speak("Pausing")
            pyautogui.press('playpause')
        elif "next" in command:
            speak("Next track")
            pyautogui.press('nexttrack')
        elif "previous" in command or "back" in command:
            speak("Previous track")
            pyautogui.press('prevtrack')
        elif "volume up" in command:
            speak("Volume up")
            pyautogui.press('volumeup')
        elif "volume down" in command:
            speak("Volume down")
            pyautogui.press('volumedown')
        elif "exit" in command or "stop" in command:
            speak("Exiting voice assistant")
            return

# ----- GESTURE SECTION -----

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils
prev_x = None
last_gesture_time = 0
gesture_cooldown = 1

def get_distance(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

def gesture_controller():
    global prev_x, last_gesture_time
    cap = cv2.VideoCapture(0)

    while True:
        success, img = cap.read()
        if not success:
            continue

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)
        current_time = time.time()

        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
                landmarks = handLms.landmark
                index = landmarks[8]
                thumb = landmarks[4]
                wrist = landmarks[0]

                if (current_time - last_gesture_time) > gesture_cooldown:
                    # Play/Pause detection
                    if landmarks[8].y < landmarks[6].y and landmarks[12].y < landmarks[10].y:
                        pyautogui.press('playpause')
                        last_gesture_time = current_time
                        print("[Gesture] Play/Pause")

                    # Swipe detection
                    wrist_x = wrist.x
                    if prev_x is not None:
                        dx = wrist_x - prev_x
                        if dx > 0.15:
                            pyautogui.press('nexttrack')
                            print("[Gesture] Next")
                            last_gesture_time = current_time
                        elif dx < -0.15:
                            pyautogui.press('prevtrack')
                            print("[Gesture] Previous")
                            last_gesture_time = current_time
                    prev_x = wrist_x

                    # Volume detection
                    dist = get_distance(thumb, index)
                    if dist < 0.05:
                        pyautogui.press('volumedown')
                        print("[Gesture] Volume Low")
                        last_gesture_time = current_time
                    elif dist > 0.1:
                        pyautogui.press('volumeup')
                        print("[Gesture] Volume High")
                        last_gesture_time = current_time

        cv2.imshow("Gesture Detection", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# ----- MAIN CONTROLLER -----

def main_controller():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
    speak("System is running. Say 'SongHub' or use gestures.")

    while True:
        command = listen_for_keyword(recognizer, mic)

        if "songhub" in command:
            speak("Voice Assistant Activated.")
            voice_thread = threading.Thread(target=voice_assistant)
            voice_thread.start()
            voice_thread.join()  # Wait for voice to end before resuming

        # Gesture is already running in parallel

# ----- RUN BOTH IN PARALLEL -----

if __name__ == "__main__":
    gesture_thread = threading.Thread(target=gesture_controller)
    gesture_thread.daemon = True
    gesture_thread.start()

    main_controller()
'''