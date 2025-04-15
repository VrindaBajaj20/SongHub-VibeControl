import speech_recognition as sr
import pyttsx3
import keyboard
import webbrowser
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

# 🧠 Set your Spotify credentials
SPOTIFY_CLIENT_ID = '#your Spotify credentials'
SPOTIFY_CLIENT_SECRET = '#your Spotify credentials'
SPOTIFY_REDIRECT_URI = 'http://localhost:8080/callback'

# 🟢 Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-read-playback-state user-modify-playback-state user-read-currently-playing"
))

# 🎤 Voice engine setup
engine = pyttsx3.init()
recognizer = sr.Recognizer()

def speak(text):
    print(f"🗣 {text}")
    engine.say(text)
    engine.runAndWait()

def listen_command():
    with sr.Microphone() as source:
        print("🎙 Listening... Speak now!")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"🎤 Recognized text: {text}")
            return text.lower()
        except sr.UnknownValueError:
            print("🤷 Couldn't understand the audio.")
            return ""
        except sr.RequestError:
            print("⚠ Speech recognition service error.")
            return ""

# 🔎 Command mapping
COMMANDS = {
    "play": ["play", "resume", "start"],
    "pause": ["pause", "stop"],
    "next": ["next", "skip", "next song", "play next"],
    "prev": ["previous", "back", "last"],
    "volume up": ["volume up", "increase volume", "raise volume", "louder"],
    "volume down": ["volume down", "decrease volume", "lower volume", "quieter"],
    "search_play": ["play "],  # handled by logic
}

def detect_command(text):
    if text.startswith("play ") and len(text.split()) > 1:
        return "search_play"
    for cmd, keywords in COMMANDS.items():
        if any(keyword in text for keyword in keywords):
            return cmd
    return None

def control_keyboard(cmd):
    key_map = {
        "play": "play/pause media",
        "pause": "play/pause media",
        "next": "next track",
        "prev": "previous track",
        "volume up": "volume up",
        "volume down": "volume down"
    }
    if cmd in key_map:
        keyboard.send(key_map[cmd])

def search_and_play_spotify(song_name):
    result = sp.search(q=song_name, type='track', limit=1)
    tracks = result.get('tracks', {}).get('items', [])
    if not tracks:
        speak(f"Sorry, couldn't find {song_name} on Spotify.")
        return
    uri = tracks[0]['uri']
    devices = sp.devices()
    if not devices['devices']:
        speak("Please start playback in Spotify once so I can detect your device.")
        return
    device_id = devices['devices'][0]['id']
    sp.start_playback(device_id=device_id, uris=[uri])
    speak(f"🎵 Playing {tracks[0]['name']} by {tracks[0]['artists'][0]['name']} on Spotify")

def execute_command(text):
    cmd = detect_command(text)
    if cmd:
        print(f"✅ Detected command: {cmd}")
        if cmd == "search_play":
            song = text.replace("play", "", 1).strip()
            if song:
                search_and_play_spotify(song)
            else:
                speak("Please say the song name after 'play'")
        else:
            speak_response = {
                "play": "▶ Playing",
                "pause": "⏸ Paused",
                "next": "⏭ Skipping",
                "prev": "⏮ Going back",
                "volume up": "🔊 Volume up",
                "volume down": "🔉 Volume down"
            }.get(cmd, "")
            speak(speak_response)
            control_keyboard(cmd)
    else:
        print("🤷 No recognizable command detected.")

# 🏁 MAIN LOOP
if __name__ == "__main__":
    speak("Hello! I am your voice assistant. How can I help with your music?")
    while True:
        print("⏳ Waiting for command...")
        text = listen_command()
        if text:
            execute_command(text)

'''
#integrate with spotify/youtube

import speech_recognition as sr
import pyttsx3
import pyautogui
import webbrowser
import urllib.parse

# Init speech
engine = pyttsx3.init()
def speak(text):
    print(f"🗣 {text}")
    engine.say(text)
    engine.runAndWait()

# Recognize voice
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

# Command detection
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

    # Match control commands first
    if any(word in text for word in pause_words): return "pause"
    if any(word in text for word in next_words): return "next"
    if any(word in text for word in prev_words): return "previous"
    if any(word in text for word in repeat_words): return "repeat"
    if any(word in text for word in vol_up): return "volume up"
    if any(word in text for word in vol_down): return "volume down"
    if any(word in text for word in mute_words): return "mute"
    if any(word in text for word in unmute_words): return "unmute"
    if text.strip() in play_words: return "play"

    # Only if not a control command, check if it's "play [song]"
    if text.startswith("play "):
        return "search_play"

    return None


# Execute the recognized command
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
            speak(f"🎵 Searching and playing {song} on YouTube")
        else:
            speak("Please say the song name after 'play'")

# Main loop
def main():
    speak("Hello! I am your voice assistant. How can I help with your music?")
    while True:
        print("⏳ Waiting for command...")
        text = listen()
        if not text: continue
        cmd = get_intent(text)
        if cmd:
            print(f"✅ Detected command: {cmd}")
            execute_command(cmd, text)
        else:
            print("🤷 No recognizable command detected.")

if __name__ == "__main__":
    main()
'''


'''
#plain voice recognition 

import speech_recognition as sr
import pyttsx3
import pyautogui
from fuzzywuzzy import fuzz

# Initialize recognizer and speaker
r = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 150)

def speak(text):
    print(f"🗣 {text}")
    engine.say(text)
    engine.runAndWait()

def recognize_audio():
    with sr.Microphone() as source:
        print("🎙 Listening... Speak now!")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio)
        print(f"🎤 Recognized text: {text}")
        return text.lower()
    except sr.UnknownValueError:
        print("🤷 Couldn't understand the audio.")
        return ""
    except sr.RequestError:
        print("❌ API unavailable.")
        return ""

def get_intent(text):
    commands = {
        "play": ["play", "resume", "start"],
        "pause": ["pause", "stop"],
        "next": ["next", "skip"],
        "repeat": ["repeat", "again"],
        "volume up": ["volume up", "increase volume", "louder"],
        "volume down": ["volume down", "decrease volume", "lower volume", "quieter"],
        "mute": ["mute", "mute volume"],
        "unmute": ["unmute", "sound on"]
    }

    for intent, phrases in commands.items():
        for phrase in phrases:
            score = fuzz.partial_ratio(text, phrase)
            if score > 75:
                return intent
    return None

def execute_command(cmd):
    if cmd == "play":
        pyautogui.press('playpause')
        speak("▶ Playing")
    elif cmd == "pause":
        pyautogui.press('playpause')
        speak("⏸ Pausing")
    elif cmd == "next":
        pyautogui.press('nexttrack')
        speak("⏭ Skipping to next")
    elif cmd == "repeat":
        pyautogui.press('prevtrack')
        speak("🔁 Repeating")
    elif cmd == "volume up":
        pyautogui.press('volumeup')
        speak("🔊 Volume up")
    elif cmd == "volume down":
        pyautogui.press('volumedown')
        speak("🔉 Volume down")
    elif cmd == "mute":
        pyautogui.press('volumemute')
        speak("🔇 Muted")
    elif cmd == "unmute":
        pyautogui.press('volumemute')
        speak("🔊 Unmuted")
    else:
        speak("Sorry, I didn't get that.")

def listen_for_commands():
    while True:
        print("⏳ Waiting for command...")
        text = recognize_audio()
        if not text:
            continue
        intent = get_intent(text)
        if intent:
            print(f"✅ Detected command: {intent}")
            execute_command(intent)
        else:
            print("🤷 No recognizable command detected.")

if __name__ == "__main__":
    speak("Hello! I am your voice assistant. How can I help with your music?")
    listen_for_commands()
'''