import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import datetime
import pyautogui
import threading
import subprocess

# ── TTS Engine ─────────────────────────
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

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
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
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

    # ── App Control ──────────────────────
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

    elif "open youtube" in command:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")

    elif "open gmail" in command:
        speak("Opening Gmail")
        webbrowser.open("https://mail.google.com")

    elif "open spotify" in command:
        speak("Opening Spotify")
        try:
            os.startfile("spotify:")
        except:
            webbrowser.open("https://open.spotify.com")

    elif "open settings" in command:
        speak("Opening Settings")
        os.system("start ms-settings:")

    elif "open task manager" in command:
        speak("Opening Task Manager")
        os.system("taskmgr")

    # ── Close Commands ───────────────────
    elif "close chrome" in command or "close browser" in command:
        os.system("taskkill /f /im chrome.exe")
        speak("Chrome closed")

    elif "close notepad" in command:
        os.system("taskkill /f /im notepad.exe")
        speak("Notepad closed")

    elif "close calculator" in command:
        os.system("taskkill /f /im calculator.exe")
        speak("Calculator closed")

    elif "close spotify" in command:
        os.system("taskkill /f /im spotify.exe")
        speak("Spotify closed")

    elif "close explorer" in command or "close file manager" in command:
        os.system("taskkill /f /im explorer.exe")
        speak("File manager closed")

    elif "close task manager" in command:
        os.system("taskkill /f /im taskmgr.exe")
        speak("Task manager closed")

    elif "close window" in command or "close this" in command:
        pyautogui.hotkey('alt', 'f4')
        speak("Window closed")

    elif "close all windows" in command:
        pyautogui.hotkey('win', 'd')
        speak("All windows minimized")

    # ── Web Search ───────────────────────
    elif "search" in command:
        query = command.replace("search", "").strip()
        if query:
            speak(f"Searching for {query}")
            webbrowser.open(f"https://www.google.com/search?q={query}")

    elif "youtube" in command:
        query = command.replace("youtube", "").strip()
        speak(f"Playing {query} on YouTube" if query else "Opening YouTube")
        url = f"https://www.youtube.com/results?search_query={query}" if query else "https://www.youtube.com"
        webbrowser.open(url)

    # ── Time & Date ──────────────────────
    elif "time" in command:
        t = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"Current time is {t}")

    elif "date" in command:
        d = datetime.datetime.now().strftime("%B %d, %Y")
        speak(f"Today is {d}")

    elif "day" in command:
        day = datetime.datetime.now().strftime("%A")
        speak(f"Today is {day}")

    # ── System Control ───────────────────
    elif "screenshot" in command or "take screenshot" in command:
        pyautogui.screenshot("screenshot.png")
        speak("Screenshot saved!")

    elif "volume up" in command or "increase volume" in command:
        for _ in range(5):
            pyautogui.press("volumeup")
        speak("Volume increased")

    elif "volume down" in command or "decrease volume" in command:
        for _ in range(5):
            pyautogui.press("volumedown")
        speak("Volume decreased")

    elif "mute" in command or "unmute" in command:
        pyautogui.press("volumemute")
        speak("Toggled mute")

    elif "scroll up" in command:
        pyautogui.scroll(10)
        speak("Scrolling up")

    elif "scroll down" in command:
        pyautogui.scroll(-10)
        speak("Scrolling down")

    elif "zoom in" in command:
        pyautogui.hotkey('ctrl', '+')
        speak("Zoomed in")

    elif "zoom out" in command:
        pyautogui.hotkey('ctrl', '-')
        speak("Zoomed out")

    elif "lock screen" in command or "lock computer" in command:
        speak("Locking screen")
        os.system("rundll32.exe user32.dll,LockWorkStation")

    elif "shutdown" in command:
        speak("Shutting down in 5 seconds")
        os.system("shutdown /s /t 5")

    elif "restart" in command:
        speak("Restarting in 5 seconds")
        os.system("shutdown /r /t 5")

    elif "sleep" in command:
        speak("Going to sleep")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    elif "cancel shutdown" in command:
        os.system("shutdown /a")
        speak("Shutdown cancelled")

    # ── Mouse & Keyboard ─────────────────
    elif "click" in command and "right" not in command:
        pyautogui.click()
        speak("Clicked")

    elif "right click" in command:
        pyautogui.rightClick()
        speak("Right clicked")

    elif "double click" in command:
        pyautogui.doubleClick()
        speak("Double clicked")

    elif "press enter" in command:
        pyautogui.press("enter")
        speak("Pressed enter")

    elif "press escape" in command or "press esc" in command:
        pyautogui.press("escape")
        speak("Pressed escape")

    elif "copy" in command:
        pyautogui.hotkey('ctrl', 'c')
        speak("Copied")

    elif "paste" in command:
        pyautogui.hotkey('ctrl', 'v')
        speak("Pasted")

    elif "undo" in command:
        pyautogui.hotkey('ctrl', 'z')
        speak("Undone")

    elif "select all" in command:
        pyautogui.hotkey('ctrl', 'a')
        speak("Selected all")

    elif "new tab" in command:
        pyautogui.hotkey('ctrl', 't')
        speak("New tab opened")

    elif "close tab" in command:
        pyautogui.hotkey('ctrl', 'w')
        speak("Tab closed")

    elif "go back" in command:
        pyautogui.hotkey('alt', 'left')
        speak("Going back")

    elif "go forward" in command:
        pyautogui.hotkey('alt', 'right')
        speak("Going forward")

    elif "minimize" in command:
        pyautogui.hotkey('win', 'down')
        speak("Minimized")

    elif "maximize" in command:
        pyautogui.hotkey('win', 'up')
        speak("Maximized")

    elif "switch window" in command:
        pyautogui.hotkey('alt', 'tab')
        speak("Switching window")

    # ── Smart Mouse specific ─────────────
    elif "start gesture" in command:
        speak("Gesture control is already running")

    elif "stop gesture" in command:
        speak("Stopping gesture control")

    elif "help" in command:
        speak("I can open and close apps, search the web, control volume, take screenshots, lock screen, and more. Just tell me what you need!")

    elif "hello" in command or "hi" in command:
        speak("Hello! How can I help you?")

    elif "thank you" in command or "thanks" in command:
        speak("You're welcome!")

    elif "what's your name" in command or "who are you" in command:
        speak("I am Smart Mouse, your AI voice assistant!")

    elif "what can you do" in command:
        speak("I can open and close apps, search Google and YouTube, control system volume, take screenshots, lock your screen, and control your mouse. Just ask!")

    # ── Stop ─────────────────────────────
    elif "stop" in command or "exit" in command or "goodbye" in command or "bye" in command:
        speak("Goodbye! Have a great day!")
        voice_state["voice_active"] = False
        return

    # ── Unknown ───────────────────────────
    else:
        speak(f"I heard you say {command}. I'm still learning. Try saying help to know what I can do!")

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
