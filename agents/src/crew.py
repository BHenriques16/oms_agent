import os

import yaml
from crewai import LLM, Agent, Crew, Task

# Custom tools imports
from src.tools.custom_tool import (
    CountOffendersTool,
    CriminalHistoryTool,
    IncarcerationsTool,
    OffendersTool,
    OutcomesTool,
    SupervisionTool,
)

# local LLm configuration
llm_local = LLM(
    # model="ollama/llama3.1",
    model="ollama/qwen2.5:7b",
    # model ="ollama/qwen2.5:14b",
    # model ="ollama/gemma4:e4b",
    base_url="http://127.0.0.1:11434",
    api_key="NA",
    temperature=0.3,
    timeout=600,
    max_tokens=8192,
)

current_dir = os.path.dirname(os.path.abspath(__file__))
agents_path = os.path.join(current_dir, "config", "agents.yaml")
tasks_path = os.path.join(current_dir, "config", "tasks.yaml")

with open(agents_path, "r", encoding="utf-8") as f:
    AGENTS_CFG = yaml.safe_load(f)
with open(tasks_path, "r", encoding="utf-8") as f:
    TASKS_CFG = yaml.safe_load(f)


# Demographics Crew
class DemographicsCrew:
    def crew(self) -> Crew:
        agent = Agent(
            config=AGENTS_CFG["demographics_specialist"],
            tools=[OffendersTool()],
            llm=llm_local,
            verbose=True,
            max_iter=2,
        )
        task = Task(config=TASKS_CFG["demographics_task"], agent=agent)
        return Crew(agents=[agent], tasks=[task], verbose=True)


# Incarcerations Crew
class IncarcerationsCrew:
    def crew(self) -> Crew:
        agent = Agent(
            config=AGENTS_CFG["incarcerations_specialist"],
            tools=[IncarcerationsTool()],
            llm=llm_local,
            verbose=True,
            max_iter=2,
        )
        task = Task(config=TASKS_CFG["incarcerations_task"], agent=agent)
        return Crew(agents=[agent], tasks=[task], verbose=True)


# Criminal History Crew
class CriminalHistoryCrew:
    def crew(self) -> Crew:
        agent = Agent(
            config=AGENTS_CFG["criminal_history_specialist"],
            tools=[CriminalHistoryTool()],
            llm=llm_local,
            verbose=True,
            max_iter=2,
        )
        task = Task(config=TASKS_CFG["criminal_history_task"], agent=agent)
        return Crew(agents=[agent], tasks=[task], verbose=True)


# Supervision Crew
class SupervisionCrew:
    def crew(self) -> Crew:
        agent = Agent(
            config=AGENTS_CFG["supervision_specialist"],
            tools=[SupervisionTool()],
            llm=llm_local,
            verbose=True,
            max_iter=2,
        )
        task = Task(config=TASKS_CFG["supervision_task"], agent=agent)
        return Crew(agents=[agent], tasks=[task], verbose=True)


# Outcomes Crew
class OutcomesCrew:
    def crew(self) -> Crew:
        agent = Agent(
            config=AGENTS_CFG["outcomes_specialist"],
            tools=[OutcomesTool()],
            llm=llm_local,
            verbose=True,
            max_iter=2,
        )
        task = Task(config=TASKS_CFG["outcomes_task"], agent=agent)
        return Crew(agents=[agent], tasks=[task], verbose=True)


# Count Crew
class CountCrew:
    def crew(self) -> Crew:
        agent = Agent(
            config=AGENTS_CFG["count_specialist"],
            tools=[CountOffendersTool()],
            llm=llm_local,
            verbose=True,
            max_iter=2,
        )
        task = Task(config=TASKS_CFG["count_task"], agent=agent)
        return Crew(agents=[agent], tasks=[task], verbose=True)
