from google.adk.agents import LlmAgent, SequentialAgent

def sync_smart_home():
    """Adjusts lights to warm spectrum and sets thermostat to optimal sleep temperature."""
    print("   [HOME] Dimmings lights, setting temp to 18°C...")
    return "Environment Optimized"

def get_daily_exertion():
    """Retrieves total activity and heart rate strain for the day."""
    return {"activity": "High", "steps": 12000}

def set_do_not_disturb():
    """Silences all notifications on mobile and watch."""
    print("   [DEVICES] DND Enabled.")
    return "Silence Mode Active"

# Agents
env_tuner = LlmAgent(name="Environment_Tuner", instruction="Prepare the home environment for sleep.", tools=[sync_smart_home], model="gemini-2.5-flash")
biometric_scan = LlmAgent(name="Biometric_Scan", instruction="Analyze daily exertion and suggest recovery tools like magnesium if activity was high.", tools=[get_daily_exertion], model="gemini-2.5-flash")
cognitive_offload = LlmAgent(name="Cognitive_Offload", instruction="Act as a journaling agent. Use 'Affective Dialog' to help the user clear their mind.", model="gemini-2.5-flash")
sleep_hygiene = LlmAgent(name="Sleep_Hygiene", instruction="Give a final sleep instruction and enable silence mode.", tools=[set_do_not_disturb], model="gemini-2.5-flash")

# 04_NIGHT_STRATEGIST (SequentialAgent)
night_strategist = SequentialAgent(
    name="Night_Strategist",
    description="Prepares the body and mind for optimal recovery during the evening hours.",
    sub_agents=[env_tuner, biometric_scan, cognitive_offload, sleep_hygiene]
)
