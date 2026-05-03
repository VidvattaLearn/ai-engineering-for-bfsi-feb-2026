import os

RESOURCE_NAME = "ai-engineering-vidvatta1"
DEPLOYMENT = "gpt-5.4-mini-2"

AZURE_OPENAI_ENDPOINT = f"https://{RESOURCE_NAME}.openai.azure.com"
AZURE_OPENAI_API_KEY = "<key>"
AZURE_API_BASE = f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/v1/"

os.environ["AZURE_DEPLOYMENT"] = DEPLOYMENT
os.environ["AZURE_OPENAI_API_KEY"] = AZURE_OPENAI_API_KEY
os.environ["AZURE_API_BASE"] = AZURE_API_BASE
deployment = os.environ["AZURE_DEPLOYMENT"]

from crewai import Agent, LLM, Task, Crew

llm = LLM(
    model=f"openai/{deployment}",
    base_url=os.environ["AZURE_API_BASE"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"]
)