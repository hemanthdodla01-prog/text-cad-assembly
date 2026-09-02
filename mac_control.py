import os
import webbrowser
from voice import speak


def handle_mac_command(command):

    command = command.lower()

    # ==========================
    # OPEN APPS
    # ==========================

    if "open safari" in command:
        os.system("open -a Safari")
        speak("Opening Safari, sir.")
        return True

    if "open notes" in command:
        os.system("open -a Notes")
        speak("Opening Notes, sir.")
        return True

    if "open calculator" in command:
        os.system("open -a Calculator")
        speak("Opening Calculator, sir.")
        return True

    if "open terminal" in command:
        os.system("open -a Terminal")
        speak("Opening Terminal, sir.")
        return True

    # ==========================
    # FOLDERS
    # ==========================

    if "open downloads" in command:
        os.system("open ~/Downloads")
        speak("Opening Downloads, sir.")
        return True

    if "open desktop" in command:
        os.system("open ~/Desktop")
        speak("Opening Desktop, sir.")
        return True

    # ==========================
    # WEBSITES
    # ==========================

    

    if "open google" in command:
        webbrowser.open("https://google.com")
        speak("Opening Google, sir.")
        return True

    # ==========================
    # VOLUME
    # ==========================

    if "mute volume" in command:
        os.system("osascript -e 'set volume output volume 0'")
        speak("Volume muted.")
        return True

    if "max volume" in command:
        os.system("osascript -e 'set volume output volume 100'")
        speak("Volume set to maximum.")
        return True

    # ==========================
    # LOCK
    # ==========================

    if "lock screen" in command:
        os.system("pmset displaysleepnow")
        return True

    return False