import asyncio
import os
import pyaudio
from datetime import datetime
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.sessions.database_session_service import DatabaseSessionService
from google.genai import types

# Import our agents
from emergency import emergency_branch
from morning import morning_harvester
from live import wellness_lifecycle
from night import night_strategist

load_dotenv()

# --- CONFIG ---
MODEL_ID = "gemini-2.5-flash-native-audio-latest"
# 16kHz × 16-bit mono = 32000 bytes/sec
# 960 bytes = exactly 30ms per chunk — optimal for low-latency live streaming
CHUNK_SIZE = 960
FORMAT = pyaudio.paInt16   # 16-bit PCM — native hardware, no conversion
CHANNELS = 1               # Mono
RATE = 16000               # Native 16kHz — no downsampling CPU cost

class AudioInterface:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        self.is_running = False

    def start(self, request_queue: LiveRequestQueue):
        self.is_running = True
        self.input_stream = self.p.open(
            format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
            frames_per_buffer=CHUNK_SIZE,
            stream_callback=self._input_callback(request_queue)
        )
        self.output_stream = self.p.open(
            format=FORMAT, channels=CHANNELS, rate=RATE, output=True
        )

    def _input_callback(self, queue):
        def callback(in_data, frame_count, time_info, status):
            if self.is_running:
                queue.send_realtime(types.Blob(data=in_data, mime_type="audio/pcm"))
            return (None, pyaudio.paContinue)
        return callback

    def play(self, audio_data):
        if self.output_stream:
            self.output_stream.write(audio_data)

    def stop(self):
        self.is_running = False
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        self.p.terminate()

# No-thinking config — skips deep reasoning loops, goes straight to response
_NO_THINK = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0)
)

# --- THE VOICE PERSONA (Live-Aware Orchestrator) ---
aura_voice = LlmAgent(
    name="Aura",
    instruction=f"""You are Aura, a warm and concise AI health voice assistant.
    Current Time: {datetime.now().strftime('%H:%M')}

    ## ROUTING RULES (STRICT - Follow exactly):

    1. EMERGENCY: If the user says ANYTHING suggesting a medical emergency, heart attack, stroke, 
       chest pain, 'help', 'emergency', 'call 911', or confirms an emergency is happening —
       you MUST transfer to the 'Emergency_Branch' agent. Do NOT handle it yourself. TRANSFER IMMEDIATELY.

    2. STRESS/WELLNESS: If the user mentions feeling stressed, anxious, overwhelmed, or asks for 
       a breathing exercise — transfer to the 'Wellness_Lifecycle' agent.

    3. MORNING BRIEFING: If the user asks for their daily stats, morning routine, schedule, 
       vitals, or sleep data — summarize the data from session state in 2-3 sentences.

    4. GENERAL: For all other conversations, be warm and concise. Max 2 sentences.

    ## CRITICAL: You have sub-agents available. USE THEM. Do not try to handle emergencies yourself.
    """,
    sub_agents=[emergency_branch, wellness_lifecycle],
    generate_content_config=_NO_THINK,
    model=MODEL_ID
)

# Disk-based Session Service (SQLite) — persists across restarts, zero RAM lag
session_service = DatabaseSessionService(db_url="sqlite+aiosqlite:///./aura_sessions.db")

async def harvest_initial_data(runner: Runner, user_id, session_id):
    """Step 1 & 2: Run Parallel Harvester to populate state."""
    print(">>> [HARVESTER] Gathering Morning Data (Parallel Mode)...")
    # We use a separate runner or the same one but in standard mode
    harvester_runner = Runner(
        app_name="Aura_Harvester",
        agent=morning_harvester,
        session_service=session_service,
        auto_create_session=True
    )
    events = harvester_runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(parts=[types.Part(text="Harvest all morning metrics.")])
    )
    # Drain events to ensure tools finish writing to state
    for _ in events: pass
    print(">>> [HARVESTER] Data Saved to Session State.")

async def run_voice_aura():
    user_id = "lewis"
    session_id = "aura_voice_session"
    
    # Initialize Main Runner
    runner = Runner(
        app_name="Aura_Voice_OS",
        agent=aura_voice,
        session_service=session_service,
        auto_create_session=True
    )

    # --- EAGER SESSION: START HARVESTING IN BACKGROUND ---
    # Don't block Aura's connection; start gathering data while Aura is waking up.
    asyncio.create_task(harvest_initial_data(runner, user_id, session_id))

    # Fix: use Modality enum instead of string to avoid Pydantic warning
    run_config = RunConfig(
        response_modalities=[types.Modality.AUDIO],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
            )
        ),
        # Prevent 1011 context overload: compress at 25k tokens, keep 10k
        context_window_compression=types.ContextWindowCompressionConfig(
            trigger_tokens=25000,
            sliding_window=types.SlidingWindow(target_tokens=10000),
        )
    )

    request_queue = LiveRequestQueue()
    audio = AudioInterface()
    audio.start(request_queue)
    
    print("\n>>> Aura Voice OS Active. Aura is informed and ready. (Ctrl+C to quit)")

    # Auto-restart loop — recovers from transient 1011 server-side errors
    while True:
        try:
            async for event in runner.run_live(
                user_id=user_id,
                session_id=session_id,
                live_request_queue=request_queue,
                run_config=run_config
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.inline_data and part.inline_data.mime_type and part.inline_data.mime_type.startswith("audio/"):
                            audio.play(part.inline_data.data)

                if event.input_transcription and not event.partial:
                    print(f"[You]: {event.input_transcription.text}")
                if event.output_transcription and not event.partial:
                    print(f"[Aura]: {event.output_transcription.text}")

        except KeyboardInterrupt:
            print("\n>>> Goodbye.")
            break
        except Exception as e:
            err = str(e)
            if "1011" in err:
                print(f"\n[WARN] Server hiccup (1011), reconnecting...")
                await asyncio.sleep(1)
                # Re-create queue for fresh connection
                request_queue = LiveRequestQueue()
                audio.stop()
                audio = AudioInterface()
                audio.start(request_queue)
                continue
            else:
                print(f"\n[ERROR] {e}")
                break

    audio.stop()

if __name__ == "__main__":
    asyncio.run(run_voice_aura())
