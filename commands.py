import os

from browser import (
    search_youtube,
    open_youtube,
    open_instagram,
    open_chatgpt,
    open_gmail,
    open_website
)

from vector_memory import (
    store_memory,
    query_memory,
    get_all_vector_memories
)

from vision import analyze_screen


def handle_command(command: str):
    command = command.lower().strip()

    # ==========================================
    # VISION — SCREEN INSPECTION
    # ==========================================
    if any(phrase in command for phrase in ["look at my screen", "what's on my screen", "check this code", "whats on my screen"]):
        result = analyze_screen("Describe what is on the user's screen briefly and concisely.")
        print(f"\n[JARVIS Vision Output]: {result}\n")
        return f"Vision detected: {result}"

    # ==========================================
    # YOUTUBE COMMANDS
    # ==========================================
    if "youtube" in command:
        if any(word in command for word in ["search", "find", "look up", "play"]):
            query = command
            for word in ["jarvis", "open youtube", "search youtube for", "search for", "find", "look up", "play", "on youtube", "youtube", "and", "go to"]:
                query = query.replace(word, "")
            
            query = query.strip()
            search_youtube(query)
            return f"Playing '{query}' on YouTube."
        else:
            open_youtube()
            return "Opened YouTube in browser."

    # ==========================================
    # HARDCODED / QUICK WEBSITES
    # ==========================================
    if "instagram" in command:
        open_instagram()
        return "Opened Instagram."

    if "chatgpt" in command or "chat g p t" in command:
        open_chatgpt()
        return "Opened ChatGPT."

    if "gmail" in command or "mail" in command:
        open_gmail()
        return "Opened Gmail."

    # ==========================================
    # OPEN MAC APPS FIRST
    # ==========================================
    if "open safari" in command:
        os.system("open -a Safari")
        return "Opened Safari."

    if "open notes" in command:
        os.system("open -a Notes")
        return "Opened Notes."

    if "open calculator" in command:
        os.system("open -a Calculator")
        return "Opened Calculator."

    if "open terminal" in command:
        os.system("open -a Terminal")
        return "Opened Terminal."

    # ==========================================
    # CATCH-ALL WEBSITES (ANY SITE / BRAND)
    # ==========================================
    if command.startswith("open "):
        target = command.replace("open ", "", 1).replace("website", "").strip()
        open_website(target)
        return f"Opening {target} in browser."

    # ==========================================
    # VECTOR MEMORY — REMEMBER
    # ==========================================
    if command.startswith("remember "):
        text = command.replace("remember", "", 1).strip()
        if "=" in text:
            key, value = text.split("=", 1)
            store_memory(key.strip(), value.strip())
        elif " equals " in text:
            key, value = text.split(" equals ", 1)
            store_memory(key.strip(), value.strip())
        return "Saved memory."

    # ==========================================
    # VECTOR MEMORY — RECALL
    # ==========================================
    if command.startswith("what is") or command.startswith("recall") or command.startswith("do you know my"):
        result = query_memory(command)
        print(f"\n[RAG Recall]: {result}\n")
        return result

    if "what do you know about me" in command:
        return get_all_vector_memories()

    return False