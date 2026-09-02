import os
import wave
import pyaudio
from faster_whisper import WhisperModel

# Initialize Faster-Whisper model locally
model = WhisperModel("base", device="cpu", compute_type="int8")

AUDIO_FILENAME = "temp_input.wav"


def listen_local() -> str:
    """Captures microphone input and transcribes it using Faster-Whisper with VAD silence filtering."""
    chunk = 1024
    sample_format = pyaudio.paInt16
    channels = 1
    rate = 16000
    record_seconds = 4

    p = pyaudio.PyAudio()

    print("\n🎤 Listening (Local STT)...")
    stream = p.open(
        format=sample_format,
        channels=channels,
        rate=rate,
        frames_per_buffer=chunk,
        input=True,
    )

    frames = []
    for _ in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk, exception_on_overflow=False)
        frames.append(data)

    stream.stop_stream()
    stream.close()

    # Save audio temporarily (Fixed: get_sample_size with underscores)
    wf = wave.open(AUDIO_FILENAME, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(rate)
    wf.writeframes(b"".join(frames))
    wf.close()

    p.terminate()

    print("🧠 Transcribing on-device...")

    # Transcribe with VAD (Voice Activity Detection) filter to drop background silence
    segments, info = model.transcribe(
        AUDIO_FILENAME,
        beam_size=5,
        vad_filter=True,  # Filters out background static & silence
        vad_parameters=dict(min_silence_duration_ms=500),
        no_speech_threshold=0.6,
    )

    text = " ".join([segment.text for segment in segments]).strip()

    # Clean up temp file
    if os.path.exists(AUDIO_FILENAME):
        os.remove(AUDIO_FILENAME)

    # Filter out common Whisper hallucination loops
    hallucinations = [
        "i'm sorry",
        "you can't let me go",
        "thank you for watching",
        "subtitles by",
        "amara.org",
    ]

    if any(h in text.lower() for h in hallucinations) or len(text) < 2:
        return ""

    print(f"You: '{text}'")
    return text