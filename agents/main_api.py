from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import time

# Imports from the crew modules for each agent type
from src.horus_agents.crew import (
    DemographicsCrew, 
    IncarcerationsCrew, 
    CriminalHistoryCrew, 
    SupervisionCrew, 
    OutcomesCrew, 
    CountCrew,
    llm_local
)

app = FastAPI(title="HORUS Gateway API")

class UserQuery(BaseModel):
    query: str

# Auxiliar function
def run_with_metrics(crew_instance, query: str, agent_name: str):
    print(f"\nInitializing agent: {agent_name}...")
    start_time = time.time()
    
    response = crew_instance.crew().kickoff(inputs={'query': query})
    
    end_time = time.time()
    tempo_execucao = round(end_time - start_time, 2)
    
    modelo_atual = llm_local.model
    
    print("\n" + "="*60)
    print(f"Final result - {agent_name.upper()}")
    print("="*60)
    print(response)
    print("-" * 60)
    print("Execution Metrics:")
    print(f"Cognitive Engine (LLM) : {modelo_atual}")
    print(f"Inference Time   : {tempo_execucao} seconds")
    print("="*60 + "\n")

    # A MUDANÇA ESTÁ AQUI: Devolvemos o texto e o tempo de execução
    return str(response), tempo_execucao

# API Endpoints
@app.post("/agent/demographics")
def ask_demographics(payload: UserQuery):
    try:
        res_text, exec_time = run_with_metrics(DemographicsCrew(), payload.query, "Demographics")
        return {
            "response": res_text,
            "execution_time_seconds": exec_time,
            "model_used": llm_local.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/incarcerations")
def ask_incarcerations(payload: UserQuery):
    try:
        res_text, exec_time = run_with_metrics(IncarcerationsCrew(), payload.query, "Incarcerations")
        return {
            "response": res_text,
            "execution_time_seconds": exec_time,
            "model_used": llm_local.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/criminal-history")
def ask_criminal_history(payload: UserQuery):
    try:
        res_text, exec_time = run_with_metrics(CriminalHistoryCrew(), payload.query, "Criminal History")
        return {
            "response": res_text,
            "execution_time_seconds": exec_time,
            "model_used": llm_local.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/supervision")
def ask_supervision(payload: UserQuery):
    try:
        res_text, exec_time = run_with_metrics(SupervisionCrew(), payload.query, "Supervision")
        return {
            "response": res_text,
            "execution_time_seconds": exec_time,
            "model_used": llm_local.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/outcomes")
def ask_outcomes(payload: UserQuery):
    try:
        res_text, exec_time = run_with_metrics(OutcomesCrew(), payload.query, "Outcomes")
        return {
            "response": res_text,
            "execution_time_seconds": exec_time,
            "model_used": llm_local.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/count")
def ask_count(payload: UserQuery):
    try:
        res_text, exec_time = run_with_metrics(CountCrew(), payload.query, "Count & Statistics")
        return {
            "response": res_text,
            "execution_time_seconds": exec_time,
            "model_used": llm_local.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main_api:app", host="127.0.0.1", port=8001)