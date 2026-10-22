"""
gemini/audio.py — audio format constants + small PCM helpers shared by
audio/microphone.py and audio/playback.py.

Per the current Gemini Live API docs: input audio is sent as raw 16-bit PCM,
16kHz, little-endian (mime type "audio/pcm;rate=16000"); output audio comes
back as raw 16-bit PCM, 24kHz. Keep these as named constants so a future
API change only has to be fixed in one place.
"""
from __future__ import annotations

INPUT_SAMPLE_RATE = 16_000
OUTPUT_SAMPLE_RATE = 24_000
CHANNELS = 1
SAMPLE_WIDTH_BYTES = 2  # 16-bit
INPUT_MIME_TYPE = f"audio/pcm;rate={INPUT_SAMPLE_RATE}"


def bytes_to_int16_count(data: bytes) -> int:
    return len(data) // SAMPLE_WIDTH_BYTES


def chunk_duration_seconds(data: bytes, sample_rate: int = INPUT_SAMPLE_RATE) -> float:
    return bytes_to_int16_count(data) / float(sample_rate)
