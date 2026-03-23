import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import datetime
import pyautogui
import threading

# ── TTS Engine ─────────────────────────
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

# ── Shared state ───────────────────────
voice_state = {
    "voice_active": False,
    "last_command": "",
}

def speak(text):
    print(f"[ASSISTANT] {text}")
    engine.say(text)
    engine.runAndWait()

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("[VOICE] Listening...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=6)
        except sr.WaitTimeoutError:
            return ""
    try:
        command = r.recognize_google(audio, language='en-IN')
        print(f"[VOICE] You said: {command}")
        voice_state["last_command"] = command
        return command.lower()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        speak("Internet connection error.")
        return ""

def handle_command(command):
    if not command:
        return

    # ── App Control ──
    if "open chrome" in command or "open browser" in command:
        speak("Opening Chrome")
        try:
            os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
        except:
            webbrowser.open("https://www.google.com")

    elif "open notepad" in command:
        speak("Opening Notepad")
        os.system("notepad")

    elif "open calculator" in command:
        speak("Opening Calculator")
        os.system("calc")

    elif "open file manager" in command or "open explorer" in command:
        speak("Opening File Explorer")
        os.system("explorer")

    # ── Web Search ──
    elif "search" in command:
        query = command.replace("search", "").strip()
        if query:
            speak(f"Searching for {query}")
            webbrowser.open(f"https://www.google.com/search?q={query}")
        else:
            speak("What do you want to search?")

    elif "youtube" in command:
        query = command.replace("youtube", "").strip()
        speak(f"Opening YouTube for {query}" if query else "Opening YouTube")
        url = f"https://www.youtube.com/results?search_query={query}" if query else "https://www.youtube.com"
        webbrowser.open(url)

    # ── Time & Date ──
    elif "time" in command:
        t = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"Current time is {t}")

    elif "date" in command:
        d = datetime.datetime.now().strftime("%B %d, %Y")
        speak(f"Today is {d}")

    # ── System Control ──
    elif "screenshot" in command or "take screenshot" in command:
        pyautogui.screenshot("screenshot.png")
        speak("Screenshot saved!")

    elif "volume up" in command:
        pyautogui.press("volumeup")
        pyautogui.press("volumeup")
        pyautogui.press("volumeup")
        speak("Volume increased")

    elif "volume down" in command:
        pyautogui.press("volumedown")
        pyautogui.press("volumedown")
        pyautogui.press("volumedown")
        speak("Volume decreased")

    elif "mute" in command:
        pyautogui.press("volumemute")
        speak("Muted")

    elif "scroll up" in command:
        pyautogui.scroll(5)
        speak("Scrolling up")

    elif "scroll down" in command:
        pyautogui.scroll(-5)
        speak("Scrolling down")

    # ── Smart Mouse control ──
    elif "click" in command:
        pyautogui.click()
        speak("Clicked")

    elif "right click" in command:
        pyautogui.rightClick()
        speak("Right clicked")

    # ── Stop ──
    elif "stop" in command or "exit" in command or "goodbye" in command:
        speak("Goodbye! Stopping voice assistant.")
        voice_state["voice_active"] = False
        return

    else:
        speak(f"Sorry, I didn't understand: {command}")

def run_voice():
    voice_state["voice_active"] = True
    speak("Hello! Smart Mouse voice assistant is ready. How can I help you?")
    while voice_state["voice_active"]:
        command = listen()
        if command:
            handle_command(command)

def start_voice_thread():
    t = threading.Thread(target=run_voice, daemon=True)
    t.start()
    return t

if __name__ == "__main__":
    run_voice()
