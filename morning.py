from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.tools.tool_context import ToolContext
from data_generator import generator

async def fetch_sleep_data(tool_context: ToolContext):
    """Retrieves sleep metrics."""
    data = await generator.get_sleep_data()
    tool_context.state["last_sleep_data"] = data
    return data

async def fetch_vitals(tool_context: ToolContext):
    """Retrieves vitals."""
    data = await generator.get_vitals()
    tool_context.state["vitals"] = data
    return data

async def fetch_calendar(tool_context: ToolContext):
    """Retrieves meetings."""
    data = await generator.get_calendar()
    tool_context.state["calendar"] = data
    return data

# Agents (Parallel for high-speed harvesting)
sleep_agent = LlmAgent(name="Sleep_Harvester", instruction="Extract quality metrics.", tools=[fetch_sleep_data], model="gemini-2.5-flash")
vitals_agent = LlmAgent(name="Vitals_Harvester", instruction="Extract current biomarkers.", tools=[fetch_vitals], model="gemini-2.5-flash")
calendar_agent = LlmAgent(name="Calendar_Harvester", instruction="Extract agenda.", tools=[fetch_calendar], model="gemini-2.5-flash")

# The Parallel Harvester (Out of Live Flow)
morning_harvester = ParallelAgent(
    name="Morning_Data_Harvester",
    sub_agents=[sleep_agent, vitals_agent, calendar_agent]
)
