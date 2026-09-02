import os
import subprocess
import ollama
from PIL import Image

def capture_screen(filename="screen.png"):
    """Takes a quick screenshot on macOS."""
    subprocess.run(["screencapture", "-x", filename])
    return filename

def analyze_screen(prompt="What is currently on my screen, sir?"):
    """Captures desktop screenshot and uses local vision model to analyze it."""
    image_path = capture_screen()
    
    try:
        print("\n👁️ JARVIS is inspecting your screen...")
        # Uses local lightweight vision model via Ollama
        response = ollama.chat(
            model="moondream",  # Or 'llava', 'qwen2.5-vl'
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_path]
            }]
        )
        
        # Cleanup screenshot after analysis
        if os.path.exists(image_path):
            os.remove(image_path)
            
        return response['message']['content']
    except Exception as e:
        if os.path.exists(image_path):
            os.remove(image_path)
        return f"Vision system note: Make sure you have pulled 'moondream' via 'ollama pull moondream'. Error: {e}"