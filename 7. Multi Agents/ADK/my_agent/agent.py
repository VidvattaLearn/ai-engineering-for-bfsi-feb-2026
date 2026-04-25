from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm

import os

# RESOURCE_NAME = "ai-engineering-vidvatta1"
# DEPLOYMENT = "gpt-5.4-mini-2"

AZURE_OPENAI_ENDPOINT = f"https://{os.environ['RESOURCE_NAME']}.openai.azure.com"
# AZURE_OPENAI_API_KEY = os.environ['AZURE_OPENAI_KEY']
AZURE_API_BASE = f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/v1/"

# os.environ["AZURE_DEPLOYMENT"] = os.environ['DEPLOYMENT_NAME']
# os.environ["OPENAI_API_KEY"] = AZURE_OPENAI_API_KEY
os.environ["AZURE_API_BASE"] = AZURE_API_BASE

# Mock tool implementation
def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    return {"status": "success", "city": city, "time": "10:30 AM"}

root_agent = Agent(
    model=LiteLlm(model=f"openai/{os.environ['DEPLOYMENT_NAME']}", api_key=os.environ['AZURE_OPENAI_KEY'], api_base=AZURE_API_BASE),
    name='root_agent',
    description="Tells the current time in a specified city.",
    instruction="You are a helpful assistant that tells the current time in cities. Use the 'get_current_time' tool for this purpose.",
    tools=[get_current_time],
)