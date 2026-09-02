from commands import handle_command


def execute_user_command(command: str) -> str:
    """Passes user intents directly into your existing handle_command pipeline."""
    result = handle_command(command)
    if result:
        if isinstance(result, str):
            return result
        return f"Successfully executed action for: '{command}'."
    return f"No matching command found for: '{command}'."


# --- QWEN TOOL SCHEMAS ---
JARVIS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_user_command",
            "description": (
                "Execute system actions, browser automation, vision tasks, or memory tasks. "
                "Use this tool whenever the user asks to: "
                "1. Search or play YouTube videos (e.g., 'play Interstellar soundtrack', 'play 7.7 magnitude'). "
                "2. Inspect screen (e.g., 'what is on my screen', 'look at my screen', 'check this code'). "
                "3. Open websites (e.g., 'open instagram', 'open chatgpt', 'open gmail', 'go to youtube'). "
                "4. Open Mac apps (e.g., 'open safari', 'open notes', 'open calculator', 'open terminal'). "
                "5. Manage memory (e.g., 'remember favourite car = porsche', 'what is favourite car', 'forget favourite car')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The exact command phrase to execute (e.g. 'look at my screen', 'open youtube', 'play 7.7 magnitude on youtube').",
                    }
                },
                "required": ["command"],
            },
        },
    }
]