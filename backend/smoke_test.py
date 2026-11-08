#!/usr/bin/env python3
"""
End-to-end smoke test for the Sectionist backend.

Requires a running backend on 127.0.0.1:8765 (start it with ./start_server.sh
or ``python server.py``). Generates a short synthetic audio file in memory,
uploads it to ``POST /analyze`` and checks that the response looks like a real
analysis result.

Usage:
    python smoke_test.py

Exits 0 on success, 1 on failure.
"""

import io
import os
import sys
import wave

import numpy as np
import requests

BACKEND_URL = os.environ.get("SECTIONIST_BACKEND_URL", "http://127.0.0.1:8765")
SAMPLE_RATE = 22050


def build_test_audio(seconds_per_part=5.0):
    """Build a two-part synthetic signal as an in-memory WAV file.

    Two distinct two-tone chords, back to back, so a working segmenter has a
    clear boundary in the middle to find.
    """
    t = np.linspace(
        0, seconds_per_part, int(SAMPLE_RATE * seconds_per_part), endpoint=False
    )
    part_one = 0.3 * np.sin(2 * np.pi * 220 * t) + 0.2 * np.sin(2 * np.pi * 330 * t)
    part_two = 0.3 * np.sin(2 * np.pi * 440 * t) + 0.2 * np.sin(2 * np.pi * 554 * t)
    samples = np.concatenate([part_one, part_two])

    pcm = (samples * 32767).astype("<i2")
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm.tobytes())
    buffer.seek(0)
    return buffer


def main():
    print(f"Checking {BACKEND_URL}/health ...")
    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=10)
    except requests.exceptions.ConnectionError:
        print(f"FAIL: cannot reach backend at {BACKEND_URL}")
        return 1

    if health.status_code != 200:
        print(f"FAIL: /health returned {health.status_code}")
        return 1
    print(f"OK: {health.json()}")

    print("Uploading synthetic audio to /analyze ...")
    audio = build_test_audio()
    response = requests.post(
        f"{BACKEND_URL}/analyze",
        files={"audio": ("smoke_test.wav", audio, "audio/wav")},
        timeout=300,
    )

    if response.status_code != 200:
        print(f"FAIL: /analyze returned {response.status_code}: {response.text[:500]}")
        return 1

    payload = response.json()
    if not payload.get("success"):
        print(f"FAIL: analysis reported an error: {payload.get('error')}")
        return 1

    analysis = payload.get("analysis", {})
    problems = []

    if analysis.get("duration", 0) <= 0:
        problems.append("duration is not positive")
    if not analysis.get("sections"):
        problems.append("no sections detected")
    if "key" not in analysis:
        problems.append("no key reported")

    for key in ("sections", "chords", "key_changes", "beats_detected", "tempo"):
        if key not in analysis:
            problems.append(f"missing field: {key}")

    if problems:
        print("FAIL: " + "; ".join(problems))
        return 1

    print(
        "OK: duration={duration}s tempo={tempo} key={key} "
        "sections={sections} chords={chords}".format(
            duration=analysis.get("duration"),
            tempo=analysis.get("tempo"),
            key=analysis.get("key"),
            sections=len(analysis.get("sections", [])),
            chords=len(analysis.get("chords", [])),
        )
    )
    print("Smoke test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
