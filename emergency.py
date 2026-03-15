from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.tool_context import ToolContext
from google.genai import types

# No-thinking config — emergency responses must be instant
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

# VERIFIER (LlmAgent)
verifier = LlmAgent(
    name="Verifier",
    instruction="""You are an emergency verifier. The user or their biometrics have flagged a CRITICAL emergency.
    YOUR ONLY JOB: Confirm the situation is real. Ask ONE quick question like:
    'Are you or someone near you in danger right now?'
    If they say YES or don't respond clearly, immediately escalate.
    Trigger the watch vibration to alert the user. Be calm but urgent.""",
    tools=[send_watch_vibration],
    generate_content_config=_NO_THINK,
    model="gemini-2.5-flash-native-audio-latest"
)

# RESPONDER (LlmAgent)
responder = LlmAgent(
    name="Responder",
    instruction="""You are an emergency responder agent. A confirmed emergency is in progress.
    ACTION: Call notify_emergency_services immediately using the location and vitals from session state.
    Then clearly tell the user: 'Emergency services have been notified. Help is on the way. Stay calm.'
    Be direct and speak only what is necessary.""",
    tools=[notify_emergency_services],
    generate_content_config=_NO_THINK,
    model="gemini-2.5-flash-native-audio-latest"
)

# 01_EMERGENCY_BRANCH (SequentialAgent)
emergency_branch = SequentialAgent(
    name="Emergency_Branch",
    description="Handles critical health alerts and emergency response coordination.",
    sub_agents=[verifier, responder]
)
