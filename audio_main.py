import asyncio
import os
import pyaudio
import queue
import threading
from datetime import datetime
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

# Import our agents
from emergency import create_emergency_agent
from morning import morning_harvester
from live import wellness_lifecycle

load_dotenv()

# --- CONFIG ---
MODEL_ID = "gemini-2.5-flash-native-audio-latest"
CHUNK_SIZE = 960            # 30ms @ 16kHz
FORMAT = pyaudio.paInt16    # 16-bit PCM
CHANNELS = 1                # Mono
INPUT_RATE = 16000         # Mic input
OUTPUT_RATE = 24000        # AI Voice output (HD voices are 24kHz)

class AudioInterface:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        self.is_running = False
        self.play_queue = queue.Queue()
        self.play_thread = None

    def _play_worker(self):
        """Threaded playback worker for non-blocking local audio."""
        while self.is_running:
            try:
                data = self.play_queue.get(timeout=0.1)
                if self.output_stream:
                    self.output_stream.write(data)
            except queue.Empty:
                continue

    def start(self, request_queue: LiveRequestQueue):
        self.is_running = True
        self.play_thread = threading.Thread(target=self._play_worker, daemon=True)
        self.play_thread.start()

        self.input_stream = self.p.open(
            format=FORMAT, channels=CHANNELS, rate=INPUT_RATE, input=True,
            frames_per_buffer=CHUNK_SIZE,
            stream_callback=self._input_callback(request_queue)
        )
        self.output_stream = self.p.open(
            format=FORMAT, channels=CHANNELS, rate=OUTPUT_RATE, output=True
        )

    def _input_callback(self, queue_obj):
        def callback(in_data, frame_count, time_info, status):
            if self.is_running:
                queue_obj.send_realtime(types.Blob(data=in_data, mime_type="audio/pcm"))
            return (None, pyaudio.paContinue)
        return callback

    def play(self, audio_data):
        self.play_queue.put(audio_data)

    def stop(self):
        self.is_running = False
        if self.play_thread:
            self.play_thread.join(timeout=1.0)
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        self.p.terminate()

# Standard no-thinking config (Voice config is provided in RunConfig)
_NO_THINK = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0)
)

# --- THE VOICE PERSONA ---
aura_voice = LlmAgent(
    name="Aura",
    instruction=f"""You are Aura, a warm and concise AI health voice assistant.
    Current Time: {datetime.now().strftime('%H:%M')}

    ## SESSION STATE (Your data — always read this first):
    Your harvested data is stored in session state under these exact key names:
    - key "vitals"          → contains heart_rate, stress_level, spo2
    - key "last_sleep_data" → contains sleep_score, deep_sleep_hours, efficiency
    - key "calendar"        → contains meetings (list of today's meetings)

    ## ROUTING RULES (STRICT):
    1. EMERGENCY: If user yells help, heart attack, or distressed → EMERGENCY_BRANCH.
    2. STRESS: If user is stressed → WELLNESS_LIFECYCLE.
    3. MORNING/SCHEDULE: Summarize the keys above in 2 sentences.
    4. GENERAL: Be warm and concise. Max 2 sentences.
    """,
    sub_agents=[create_emergency_agent(), wellness_lifecycle],
    generate_content_config=_NO_THINK,
    model=MODEL_ID
)

session_service = InMemorySessionService()

async def harvest_initial_data(runner: Runner, user_id, session_id):
    print(">>> [HARVESTER] Gathering Morning Data...")
    harvester_runner = Runner(
        app_name="Aura_Voice_OS", agent=morning_harvester,
        session_service=session_service, auto_create_session=True
    )
    async for _ in harvester_runner.run_async(
        user_id=user_id, session_id=session_id,
        new_message=types.Content(parts=[types.Part(text="Harvest all morning metrics.")])
    ): pass
    print(">>> [HARVESTER] Data Saved.")

async def run_voice_aura():
    user_id = "lewis"
    session_id = f"aura_voice_session_{int(datetime.now().timestamp())}"
    
    runner = Runner(
        app_name="Aura_Voice_OS", agent=aura_voice,
        session_service=session_service, auto_create_session=True
    )

    await harvest_initial_data(runner, user_id, session_id)

    # Core Voice Configuration (Passed once here to avoid 1007 errors)
    run_config = RunConfig(
        response_modalities=[types.Modality.AUDIO],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
            )
        )
    )

    request_queue = LiveRequestQueue()
    audio = AudioInterface()
    audio.start(request_queue)
    
    print("\n>>> Aura Voice OS Active. Aura is informed and ready. (Ctrl+C to quit)")

    while True:
        try:
            async for event in runner.run_live(
                user_id=user_id, session_id=session_id,
                live_request_queue=request_queue, run_config=run_config
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.inline_data and part.inline_data.data:
                            audio.play(part.inline_data.data)

                if event.input_transcription and not event.partial:
                    print(f"[You]: {event.input_transcription.text}")
                if event.output_transcription and not event.partial:
                    print(f"[Aura]: {event.output_transcription.text}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            err = str(e)
            if any(code in err for code in ["1006", "1011", "1008", "1007"]):
                print(f"\n[WARN] Connection issue, recovering...")
                await asyncio.sleep(0.5)
                request_queue = LiveRequestQueue()
                audio.stop()
                audio = AudioInterface()
                audio.start(request_queue)
                continue
            else:
                print(f"[ERROR] {e}"); break

    audio.stop()

if __name__ == "__main__":
    asyncio.run(run_voice_aura())
