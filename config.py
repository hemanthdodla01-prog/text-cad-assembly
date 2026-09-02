from groq import Groq

# ==========================
# GROQ API
# ==========================

import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL = "llama-3.3-70b-versatile"

client = Groq(api_key=API_KEY)

# ==========================
# JARVIS SETTINGS
# ==========================

USER_NAME = "Hemanth"

WAKE_WORD = "jarvis"

VOICE_RATE = 180

VOICE_VOLUME = 1.0

# ==========================
# PERSONALITY
# ==========================

SYSTEM_PROMPT = f"""
You are JARVIS from Iron Man.

The user's name is {USER_NAME}.

Speak in a calm, intelligent, concise British manner.

Be elegant, helpful, slightly witty, and efficient.

Never mention you are an AI.

Always address the user respectfully.
"""