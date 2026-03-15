# Aura Voice OS — Reproducible Testing Guide

Aura is a high-performance, live-audio health assistant. This guide ensures anyone can reproduce and verify its core features: **Morning Briefings**, **Stress Management**, and **Emergency Response**.

## 🚀 Quick Start
1. **Activate Environment**: `.\venv\Scripts\activate`
2. **Run Main App**: `python audio_main.py`

---

## 🧪 Reproducible Testing Scenarios

### 1. Morning Briefing & Data Harvesting
Aura automatically "harvests" sleep, vitals, and calendar data on startup.
*   **Trigger**: Just say "Hi Aura" or "What's my status today?"
*   **Expected Behavior**: Aura reads data from the session state (populated by `data_generator.py`).
*   **Validation**: Look for `[HARVESTER] Data Saved` in the console before speaking.

### 2. High Stress & Wellness Flow
Test the non-blocking wellness coaching and 4-7-8 breathing exercise.
*   **Trigger (Voice)**: Say "I'm feeling very stressed" or "Can we do a breathing exercise?"
*   **Expected Behavior**: Aura transfers you to the **Wellness Coach**. You should hear a calm, unhurried voice (Kore) guiding you through inhales and exhales.
*   **Interrupt Test**: While Aura is counting breaths, yell "Help, I'm having a heart attack!"
*   **Expected Behavior**: Aura must immediately stop the breathing exercise and transfer to the **Emergency Responder**.

### 3. Emergency Response (Voice Trigger)
*   **Trigger**: Say "Help!", "Emergency!", or "I think I'm having a heart attack."
*   **Expected Behavior**: 
    1. Aura transfers to **Emergency_Branch**.
    2. You see `[WATCH] Buzzing wearer's wrist...` in the console.
    3. You see `[911] ALERT: Sending vitals...` in the console.
    4. Aura tells you: "Emergency services have been notified... Help is on the way."

### 4. Emergency Response (Scripted/Data Trigger)
To test how the system handles critical biometric spikes without using your voice.
*   **Command**: `python test_emergency.py`
*   **Expected Behavior**: This script simulates a "CRITICAL_SPIKE" (Heart Rate 195, SpO2 82) and forces the Emergency_Branch to process it. It will trigger the vibration and notify 911 automatically.

---

## 🛠️ Technical Testing Tools

### Mock Data Control
You can modify `data_generator.py` to change what Aura "knows" about you:
*   Modify `base_hr` or `base_stress` to see how Aura's tone changes when you ask for a briefing.

### Voice Quality Verification
If the voice sounds "demonic" or deep:
*   Ensure `OUTPUT_RATE = 24000` is set in `audio_main.py`. 
*   Gemini HD voices (Kore/Aoede) require 24kHz. Playing them at 16kHz makes them sound slow and male.

### Connection Stability (1006 Fix)
*   The `AudioInterface` in `audio_main.py` uses threaded background playback. 
*   **Verification**: Start a long breathing exercise. The connection should stay alive for the full 2-minute duration without dropping. If it drops with a `1006` error, the background thread isn't heartbeating correctly.

---

## 📁 Key Files
*   `audio_main.py`: Main OS & Voice logic.
*   `emergency.py`: Emergency Responder logic.
*   `live.py`: Wellness & Breathing logic.
*   `data_generator.py`: The "Source of Truth" for your simulated health.
*   `test_emergency.py`: Direct script for testing critical alerts.
