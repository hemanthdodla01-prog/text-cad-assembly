import os
import asyncio
import threading
import pygame
import edge_tts
import ollama

# Local voice & command tools
from local_voice import listen_local
from tools import JARVIS_TOOLS, execute_user_command

SYSTEM_PROMPT = """
You are JARVIS, a highly intelligent, calm, and sophisticated AI assistant.
Address the user as 'Sir'. Keep responses brief, direct, and precise (1-2 sentences).
When the user asks to perform an action (open an app/website, play YouTube video, manage memory, look at screen, volume control), ALWAYS call the 'execute_user_command' tool.
"""


def speak(text: str):
    """Neural British AI voice output using edge-tts (Safe Thread Isolation)."""
    clean_text = text.replace("*", "").replace("`", "")
    print(f"\nJARVIS: {clean_text}\n")

    async def generate_audio():
        communicate = edge_tts.Communicate(clean_text, "en-GB-RyanNeural")
        await communicate.save("jarvis_speech.mp3")

    def run_async_speak():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate_audio())
        loop.close()

    try:
        # Run audio generation in a separate thread to avoid event loop collisions
        thread = threading.Thread(target=run_async_speak)
        thread.start()
        thread.join()

        pygame.mixer.init()
        pygame.mixer.music.load("jarvis_speech.mp3")
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.quit()
        if os.path.exists("jarvis_speech.mp3"):
            os.remove("jarvis_speech.mp3")
    except Exception as e:
        print(f"Speech warning: {e}")


class JarvisBrain:
    def __init__(self, model_name: str = "qwen2.5:7b"):
        self.model_name = model_name
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    def execute_tool(self, name: str, args: dict) -> str:
        if name == "execute_user_command":
            return execute_user_command(args.get("command", ""))
        return f"Unknown tool: {name}"

    def process_command(self, text: str) -> str:
        self.history.append({"role": "user", "content": text})
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=self.history,
                tools=JARVIS_TOOLS,
            )
            msg = response["message"]

            # Check if Qwen decided to execute a tool call
            if msg.get("tool_calls"):
                self.history.append(msg)
                for tool in msg["tool_calls"]:
                    fn = tool["function"]["name"]
                    args = tool["function"]["arguments"]
                    tool_result = self.execute_tool(fn, args)
                    self.history.append(
                        {"role": "tool", "content": tool_result}
                    )

                final_res = ollama.chat(
                    model=self.model_name, messages=self.history
                )
                reply = final_res["message"]["content"]
            else:
                reply = msg["content"]

            self.history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            return f"An operational error occurred, sir: {e}"


if __name__ == "__main__":
    brain = JarvisBrain()
    speak("JARVIS systems active and operational, sir.")

    print("\n==========================================")
    print("      JARVIS INTERFACE MODE SELECTION     ")
    print("==========================================")
    print("1. Text Mode (Type commands)")
    print("2. Voice Mode (Microphone)")
    mode = input("\nSelect mode (1/2, default is 1): ").strip()

    while True:
        if mode == "2":
            # Voice Mode via Local Whisper / Mic
            speech = listen_local()

            # Ignore empty noise or filtered Whisper hallucinations
            if not speech or len(speech.strip()) == 0:
                continue

            lowered = speech.lower()

            if "jarvis" not in lowered:
                continue

            if lowered in ["jarvis exit", "exit", "quit", "goodbye"]:
                speak("Powering down. Good day, sir.")
                break

            if lowered.strip() == "jarvis":
                speak("Yes, sir?")
                continue

            command = lowered.replace("jarvis", "").strip()
            if not command:
                continue
        else:
            # Text Mode Input
            command = input("\nYou > ").strip()
            if not command:
                continue

            if command.lower() in ["exit", "quit", "goodbye", "jarvis exit"]:
                speak("Powering down. Good day, sir.")
                break

        # Process command through brain & execute tools
        response = brain.process_command(command)
        speak(response)
        if mode == "2":
            # Voice Mode via Local Whisper / Mic
            speech = listen_local()

            # Ignore empty noise or filtered Whisper hallucinations
            if not speech or len(speech.strip()) == 0:
                continue

            lowered = speech.lower()

            # Variations Whisper often produces for "Jarvis"
            wake_words = ["jarvis", "jarris", "jarrus", "javis", "jarvs", "service", "travis"]

            # Check if any wake word variation is in the transcribed speech
            detected_wake_word = next((word for word in wake_words if word in lowered), None)

            if not detected_wake_word:
                continue

            if any(exit_cmd in lowered for exit_cmd in ["exit", "quit", "goodbye"]):
                speak("Powering down. Good day, sir.")
                break

            # Strip out whichever wake word variation was caught
            command = lowered.replace(detected_wake_word, "").strip()

            # If you ONLY said "Jarvis" (or "Jarris"), acknowledge it
            if not command:
                speak("Yes, sir?")
                continue