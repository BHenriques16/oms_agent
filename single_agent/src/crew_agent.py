import os

import yaml
from crewai import LLM, Agent, Crew, Task

os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

# Tools imports
from src.tools.tools_agent import (
    GlobalStatsTool,
    InmateProfileTool,
    InmateSearchTool,
)

# Local LLM configuration using Ollama
llm_local = LLM(
    # model="ollama/qwen2.5:7b",
    # model="ollama/qwen2.5:14b",
    # model="ollama/gemma4:e4b",
    model="ollama/llama3.1",
    base_url="http://127.0.0.1:11434",
    api_key="NA",
    temperature=0.0,
    timeout=600,
    max_tokens=4096,
)

"""
# Server LLM configuration using Ollama
llm_local = LLM(
    model="ollama/qwen3.6:35b",
    base_url="http://192.168.65.6:11434",
    api_key="NA",
    temperature=0.3,
    timeout=600,
    max_tokens=16384,
)
"""

# Path configuration for YAML files
current_dir = os.path.dirname(os.path.abspath(__file__))
agents_path = os.path.join(current_dir, "config", "agent.yaml")
# tasks_path = os.path.join(current_dir, "config", "tasks_agent_server.yaml")
tasks_path = os.path.join(current_dir, "config", "tasks_agent_local.yaml")

# Load YAML configurations
with open(agents_path, "r", encoding="utf-8") as f:
    AGENTS_CFG = yaml.safe_load(f)
with open(tasks_path, "r", encoding="utf-8") as f:
    TASKS_CFG = yaml.safe_load(f)


class UniversalOMSCrew:
    def crew(self) -> Crew:
        # Initialize the single agent that will perform both tasks
        agent = Agent(
            config=AGENTS_CFG["oms_agent"],
            tools=[InmateSearchTool(), InmateProfileTool(), GlobalStatsTool()],
            llm=llm_local,
            verbose=True,
            max_iter=10,
        )

        # The agent uses tools here to gather data and writes a natural text response
        task_research = Task(config=TASKS_CFG["research_and_draft_task"], agent=agent)

        # Initialize the validation and formatting Task
        task_format = Task(
            config=TASKS_CFG["validate_and_format_task"],
            agent=agent,
            context=[task_research],
        )

        # Assemble the sequential pipeline
        # The order in the tasks array dictates the execution flow
        return Crew(agents=[agent], tasks=[task_research, task_format], verbose=True)
