from voice import listen, speak
from ai import ask_ai
from commands import handle_command
from mac_control import handle_mac_command
from config import WAKE_WORD


print("===================================")
print("        JARVIS ONLINE")
print("===================================")
print(f"Say '{WAKE_WORD}' to activate.\n")


sleeping = False


while True:

    command = listen()

    if not command:
        continue

    command = command.lower().strip()


    # ==========================================
    # SLEEPING MODE
    # ==========================================

    if sleeping:

        if command == WAKE_WORD:

            sleeping = False

            speak("I am back online, sir.")

        continue


    # ==========================================
    # WAKE WORD
    # ==========================================

    if not command.startswith(WAKE_WORD):

        continue


    command = command[len(WAKE_WORD):].strip()


    # ==========================================
    # JUST "JARVIS"
    # ==========================================

    if not command:

        speak("Yes, sir?")

        continue


    # ==========================================
    # EXIT COMPLETELY
    # ==========================================

    if command == "exit":

        speak("Goodbye, sir.")

        break


    # ==========================================
    # SLEEP / STOP LISTENING
    # ==========================================

    if command in [
        "stop listening",
        "go to sleep",
        "sleep",
        "standby"
    ]:

        speak("Going into standby, sir.")

        sleeping = True

        continue


    # ==========================================
    # MAC COMMANDS
    # ==========================================

    if handle_mac_command(command):

        continue


    # ==========================================
    # OTHER COMMANDS
    # ==========================================

    if handle_command(command):

        continue


    # ==========================================
    # AI FALLBACK
    # ==========================================

    try:

        answer = ask_ai(command)

        speak(answer)

    except Exception as e:

        print(e)

        speak(
            "I'm having trouble contacting my AI systems."
    