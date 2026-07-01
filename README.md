# OMS AI - Multi-Agent System

Horus is a multi-agent AI ecosystem built with **CrewAI** designed for the extraction, analysis of specifich fields, statistical counting and criminal data.

## Tech Stack

* **Agent Framework:** [CrewAI](https://crewai.com)
* **Local LLM:** [Ollama](https://ollama.com) (Llama 3.1 8B)
* **API Framework:** [FastAPI](https://fastapi.tiangolo.com/)
* **Database Integration:** SQL Server via `pyodbc`
* **Data Validation:** Pydantic (args_schema)

## Project Structure

```text
horus/
├── src/
│   └── horus_agents/
│       ├── config/                 # YAML configurations for Agents and Tasks
│       │   ├── agents.yaml         # Agent persona and constraint definitions
│       │   ├── tasks.yaml          # Agent tasks
│       ├── tools/                  # Custom Python Tools for Database API interaction
│       │   ├── custom_tool.yaml    # Agent tools
│       ├── crew.py                 # Single-task logic for local execution
│       ├── tests/                  # Folder for testing purposing
├── main_api.py                     # Entry point for the Agentic API
├── db_api.py                       # Database abstraction layer (Middleware)
├── requirements.txt                # Project dependencies
└── pyproject.toml                  # Modern Python build configuration
```

## Usage Guide

Follow these steps to configure and run Horus on your machine.

### 1. previous requirements
* **Python 3.10+** insatlled.
* **Ollama** installed and running.
* **SQL Server** accessible (or the active database API endpoint).

### 2. Installation
Clone the repository and install the dependencies:

```bash
# Clone the project
git clone(https://github.com/HULTIG/Management-Agent)
cd horus

# Create and activate the virtual enviroment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install the necessary libraries.
pip install -r requirements.txt
```

### 3. LLM configuration

If everything is running locally, donwload the model:

```bash
ollama pull qwen2.5:7b
```

### 4. Project execution

You must open 2 terminals at the same time

### Step A: Inicialize the database API
This service creates the bridge between the agents and SQL Server

```bash
python db_api.py
Local url: http://127.0.0.1:8000/docs
```

### Step B: Iniciate Horus API (agents)
```bash
python main_api.py
Local url: http://127.0.0.1:8001/docs
```

### 5. Test the agents
You can now send POST requests to officers. Example of how to check an inmate's criminal record:

```bash
{
  "query": "What is the criminal history of offender ID 6?"
}
```


# Universal OMS AI Gateway

Horus is an Agentic API ecosystem built with **CrewAI** and **FastAPI**, designed for the extraction, analytical reasoning, and statistical formatting of demographic and criminal data. 

Transitioning from a multi-agent framework to a **Universal Agent Architecture**, Horus acts as an intelligent bridge between natural language queries and structured SQL Server databases. It is optimized to run seamlessly on local hardware (e.g., Ubuntu Linux environments using Ollama) with strict enforcement of JSON structured outputs.

The system is architected for flexibility, allowing it to run seamlessly on local hardware (smaller LLMs) or high-performance environments (Larger LLMs).

## Dual-Architecture Strategy

The project implements a "Hybrid Prompting" strategy to handle different hardware constraints:

* **Local Mode:** Dispite also having two tasks, the local mode **tasks_local.yaml** prompts are optimized for small LLMs running via **Ollama**.
* **Server Mode:** Designed for larger models, the server mode **tasks_server.yaml** also uses a dual-task architecture but the pormpts are optimized for larger LLMs running via **Ollama**.


## Tech Stack

* **Agent Framework:** [CrewAI](https://crewai.com)
* **Local LLM Engine:** [Ollama](https://ollama.com) (Optimized for `qwen:35b` or `qwen2.5-coder:7b` with 8K+ context windows)
* **API Framework:** [FastAPI](https://fastapi.tiangolo.com/) & Uvicorn
* **Database Integration:** SQL Server via `pyodbc`
* **Data Validation:** Pydantic V2

## Project Structure

```text
horus/
├── src/
│   └── horus_agents/
│       ├── config/
│       │   ├── agents.yaml               # Agent persona and constraint definitions
│       │   └── tasks_agent_local.yaml    # Universal routing and structured formatting tasks for local mode
│       │   └── tasks_agent_server.yaml   # Universal routing and structured formatting tasks for server mode
│       ├── tools/
│       │   └── tools_agent.py            # Pydantic-shielded SQL tools (Search, Profile, Stats)
│       └── crew_agent.py                 # Core CrewAI execution engine and LLM configuration
│       ├── tests/                        # Folder for testing purposing
├── db_api_agent.py                       # FastAPI entry point, endpoint routing, and Regex JSON parser for connection to the artificial database
├── main_api_agent.py                     # FastAPI entry point, endpoint routing, and Regex JSON parser
├── requirements.txt                      # Project dependencies
└── pyproject.toml                        # Modern Python build configuration
