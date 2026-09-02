import pyttsx3
import speech_recognition as sr

# ==========================
# INITIALIZE
# ==========================

engine = pyttsx3.init()

listener = sr.Recognizer()

engine.setProperty("rate", 180)
engine.setProperty("volume", 1.0)

# ==========================
# SPEAK
# ==========================

def speak(text):
    """Make Jarvis speak."""
    print(f"Jarvis: {text}")
    engine.say(text)
    engine.runAndWait()


# ==========================
# LISTEN
# ==========================

def listen():
    """Listen for a voice command."""

    with sr.Microphone() as source:

        print("\n🎤 Listening...")

        listener.adjust_for_ambient_noise(source, duration=0.5)

        audio = listener.listen(source)

    try:

        command = listener.recognize_google(audio)

        print(f"You: {command}")

        return command.lower()

    except sr.UnknownValueError:

        return ""

    except sr.RequestError:

        speak("Speech recognition is currently unavailable.")

        return ""