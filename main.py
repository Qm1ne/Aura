import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.genai import types
from dotenv import load_dotenv
from data_generator import generator

# Import our protocol sub-agents
from emergency import emergency_branch
from morning import morning_pipeline
from live import wellness_lifecycle
from night import night_strategist

load_dotenv()

# Global session service for background access
session_service = InMemorySessionService()

async def update_session_state(user_id, session_id, delta):
    """Helper to update session state without triggering a model turn."""
    session = await session_service.get_session(
        app_name="Aura_OS", 
        user_id=user_id, 
        session_id=session_id
    )
    if session:
        event = Event(
            author="SYSTEM_INGESTION",
            actions=EventActions(state_delta=delta)
        )
        await session_service.append_event(session, event)

# --- 00_INGESTION_SYSTEM (Service Layer) ---
async def ingestion_system(user_id, session_id):
    """Background task to simulate streaming data ingestion into shared state."""
    print("[INIT] Ingestion System started.")
    while True:
        try:
            vitals = generator.get_vitals()
            await update_session_state(user_id, session_id, {"vitals": vitals})
        except Exception as e:
            print(f"[INGESTION ERROR] {e}")
        await asyncio.sleep(5)

# --- EMERGENCY MONITORING SYSTEM ---
async def monitor_and_trigger_emergency(runner, user_id, session_id):
    """Polls the state and forces an emergency run if critical data is detected."""
    print("[INIT] Emergency Monitor started.")
    while True:
        try:
            session = await session_service.get_session(
                app_name="Aura_OS", 
                user_id=user_id, 
                session_id=session_id
            )
            if session and "vitals" in session.state:
                vitals = session.state["vitals"]
                if vitals.get("status") == "CRITICAL_SPIKE":
                    print("\n" + "!"*60)
                    print("!!! MONITOR DETECTED CRITICAL SPIKE !!!")
                    print(f"Data: {vitals}")
                    print("!"*60)
                    
                    msg = types.Content(role="user", parts=[types.Part(text="CRITICAL_ALARM: Biometric spike detected. Trigger Emergency response.")])
                    events = runner.run(
                        user_id=user_id,
                        session_id=session_id,
                        new_message=msg
                    )
                    for event in events:
                        if event.content:
                            text = "".join(p.text for p in event.content.parts if p.text)
                            if text: print(f"[{event.author}]: {text}")
                    
                    # Mark as handled to prevent infinite loops
                    await update_session_state(user_id, session_id, {"vitals": {"status": "HANDLED"}})
        except Exception as e:
            print(f"[MONITOR ERROR] {e}")
        await asyncio.sleep(2)

# --- Aura (SupervisorAgent) ---
aura_supervisor = LlmAgent(
    name="Aura",
    instruction="""You are Aura, the master health supervisor. 
    You have access to a shared state via tools and system events.
    Route requests:
    - If there is a CRITICAL_ALARM or emergency alert, use Emergency_Branch immediately.
    - For morning routines, use Morning_Pipeline.
    - Otherwise, help the user with health coaching.""",
    sub_agents=[emergency_branch, morning_pipeline, wellness_lifecycle, night_strategist],
    model="gemini-3.1-pro-preview"
)

# Initialize Runner
runner = Runner(
    app_name="Aura_OS",
    agent=aura_supervisor,
    session_service=session_service,
    auto_create_session=True
)

async def main():
    user_id = "lewis"
    session_id = "live_aura_session"

    # Pre-create session
    await session_service.create_session(app_name="Aura_OS", user_id=user_id, session_id=session_id)

    # Start background tasks
    asyncio.create_task(ingestion_system(user_id, session_id))
    asyncio.create_task(monitor_and_trigger_emergency(runner, user_id, session_id))
    
    print("Aura OS Initialized. Waiting for data...")
    await asyncio.sleep(2) # Give background tasks a moment

    # Normal interaction
    print("\n[User]: Hello Aura.")
    msg = types.Content(role="user", parts=[types.Part(text="Hello Aura.")])
    events = runner.run(user_id=user_id, session_id=session_id, new_message=msg)
    for event in events:
        if event.content:
            text = "".join(p.text for p in event.content.parts if p.text)
            if text: print(f"[{event.author}]: {text}")

    # Now SIMULATE the heartstroke by updating the state correctly
    print("\n--- INJECTING CRITICAL BIOMETRICS INTO SYSTEM STATE ---")
    await update_session_state(user_id, session_id, {"vitals": generator.get_emergency_vitals()})
    
    # Observe the monitor triggering the emergency
    await asyncio.sleep(20)

if __name__ == "__main__":
    asyncio.run(main())
