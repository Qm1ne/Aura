from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
from google.genai import types

# Standard no-thinking config
_NO_THINK = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0)
)

async def send_watch_vibration(tool_context: ToolContext):
    """Triggers a physical vibration on the user's wearable to get immediate attention."""
    print("   [WATCH] Buzzing wearer's wrist...")
    tool_context.state["last_vibration"] = "triggered"
    return "Vibration triggered"

async def notify_emergency_services(tool_context: ToolContext):
    """Sends current location and vitals from state to local emergency response units."""
    vitals = tool_context.state.get("vitals", {})
    location = vitals.get("location") if isinstance(vitals, dict) else tool_context.state.get("location")
    if not location:
        location = "Unknown Location"
    print(f"   [911] ALERT: Sending {vitals} to {location}")
    return f"EMS Notified at {location}"

def create_emergency_agent():
    """Factory to create unique instances of the emergency agent."""
    return LlmAgent(
        name="Emergency_Branch",
        description="Handles critical health alerts and emergency response coordination.",
        instruction="""You are Aura's emergency responder.
        The user or their sub-agents have flagged an EMERGENCY.

        ## PROTOCOL:
        1. If the user is yelling 'help', 'heart attack', or sounding clearly distressed:
           - IMMEDIATELY call `notify_emergency_services`.
           - Trigger `send_watch_vibration`.
           - Say: 'Emergency services have been notified. I am buzzing your watch. Help is on the way. Stay with me.'

        2. If the user's situation is unclear:
           - Ask ONE very fast question: 'Are you in danger right now?'
           - Trigger `send_watch_vibration` regardless (safety first).
           - If they say yes or don't respond, proceed to notify services.

        Speak urgently but calmly. Use short sentences.""",
        tools=[send_watch_vibration, notify_emergency_services],
        generate_content_config=_NO_THINK,
        model="gemini-2.5-flash-native-audio-latest"
    )

emergency_branch = create_emergency_agent()
