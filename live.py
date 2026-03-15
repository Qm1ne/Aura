from google.adk.agents import LlmAgent, SequentialAgent
from google.genai import types

# Shared no-thinking config for all live agents
_NO_THINK = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0)
)

# TRIAGE
triage = LlmAgent(
    name="Triage",
    instruction="Analyze the user's voice and biometrics. If they sound tired or stressed, decide if they need the Stress Coach.",
    generate_content_config=_NO_THINK,
    model="gemini-2.5-flash-native-audio-latest"
)

# STRESS_COACH
stress_coach = LlmAgent(
    name="Stress_Coach",
    instruction="Conduct live guided breathing exercises. Use an affective, calm tone.",
    generate_content_config=_NO_THINK,
    model="gemini-2.5-flash-native-audio-latest"
)

# 03_WELLNESS_LIFECYCLE (SequentialAgent)
# Replaced LoopAgent with SequentialAgent for compatibility with Voice/Live mode
wellness_lifecycle = SequentialAgent(
    name="Wellness_Lifecycle",
    description="Real-time wellness monitoring and stress management.",
    sub_agents=[triage, stress_coach]
)
