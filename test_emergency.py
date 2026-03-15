from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from dotenv import load_dotenv
from emergency import emergency_branch
from data_generator import generator

load_dotenv()

# Create a local runner for just the emergency branch
runner = Runner(
    app_name="EmergencyTest",
    agent=emergency_branch,
    session_service=InMemorySessionService(),
    auto_create_session=True
)

def run_test():
    critical_data = generator.get_emergency_vitals()
    print(f"\n[SYSTEM] Triggering Emergency with data: {critical_data}")
    
    # Send the critical data directly to the Emergency Branch
    events = runner.run(
        user_id="test_user",
        session_id="emer_test_123",
        new_message=types.Content(parts=[types.Part(text=f"CRITICAL BIOMETRIC DATA: {critical_data}. Execute emergency response protocol.")])
    )
    
    for event in events:
        if event.get_function_calls():
            for fc in event.get_function_calls():
                print(f"\n[ACTION] {event.author} is calling {fc.name}...")
        
        if event.content:
            text = "".join(p.text for p in event.content.parts if p.text)
            if text:
                print(f"[{event.author}]: {text}")

if __name__ == "__main__":
    run_test()
