import json
import re
import time
from datetime import datetime, timezone
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from src.crew_agent import UniversalOMSCrew, llm_local

app = FastAPI(
    title="HORUS Gateway API",
)

API_ERROR_RESPONSES = {
    408: {
        "description": "Request Timeout: The query took too long to process. The LLM may be struggling with the context size or the database query is too heavy.",
        "content": {
            "application/json": {"example": {"detail": "Query took too long."}}
        },
    },
    500: {
        "description": "Internal Server Error: Critical parsing error or agent execution failure. The LLM might have hallucinated the JSON format.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Critical Parsing Error: No JSON object was found."
                }
            }
        },
    },
    503: {
        "description": "Service Unavailable: The underlying Database (SQL Server) or the LLM (Ollama) is currently down or unreachable.",
        "content": {
            "application/json": {
                "example": {"detail": "Service Unavailable: Database or LLM is down."}
            }
        },
    },
}


class UserQuery(BaseModel):
    query: str


class QueryUseCase1(BaseModel):
    query: str = "Show me the full identification of inmate number 12345."


class QueryUseCase2(BaseModel):
    query: str = "What incidents has inmate 1032 been involved in?"


# Server handles defaults for metadata to prevent LLM hallucinations
class SourceDocument(BaseModel):
    document_id: str = Field(..., example="1002")
    facility: Optional[str] = Field(
        default=None, example="A-1"
    )  # Tolerância para nulos do LLM
    excerpt: Optional[str] = Field(
        default=None,
        description="Relevant text snippet from the behavioral notes or offense description",
    )
    created_at: str = Field(
        default_factory=lambda: (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
    )
    updated_at: str = Field(
        default_factory=lambda: (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
    )


# Final structured response contract enforced by the gateway
class AgentResponse(BaseModel):
    answer: str = Field(
        ..., description="Synthesized answer based strictly on the retrieved data"
    )
    matched_documents: int = Field(
        ..., description="Number of documents retrieved for this query"
    )
    source_documents: List[SourceDocument]
    query_time_s: Optional[float] = Field(
        None, description="Query execution time in seconds"
    )
    data_sources: List[str] = Field(
        default=[],
        description="Exact database columns used to filter or answer the query",
    )


# Auxiliary function to execute the agent process, handling input mapping, execution, and response parsing.
def execute_agent_process(payload: BaseModel):
    start_time = time.time()

    try:
        # Initialize the consolidated crew execution engine
        oms_crew = UniversalOMSCrew().crew()

        # Mapear os inputs dinamicamente
        agent_inputs = {
            "user_query": payload.query,
        }

        # Execute the agent analytical reasoning process
        raw_response = oms_crew.kickoff(inputs=agent_inputs)

        # Convert raw response to string form
        raw_response_str = str(raw_response).strip()

        # Debugging block
        print("\n================== RAW LLM OUTPUT ==================")
        print(raw_response_str)
        print(llm_local.model)
        print("====================================================\n")

        # Scans the raw string, capturing everything starting from the first '{' up to the last '}'
        json_match = re.search(r"\{.*\}", raw_response_str, re.DOTALL)

        if json_match:
            clean_json_text = json_match.group(0).strip()

            # Remove chavetas duplas no início e no fim, caso o LLM faça "mimic" do YAML
            while clean_json_text.startswith("{{"):
                clean_json_text = clean_json_text[1:]
            while clean_json_text.endswith("}}"):
                clean_json_text = clean_json_text[:-1]

        else:
            raise HTTPException(
                status_code=500,
                detail="Critical Parsing Error: No JSON object was found in the agent's output.",
            )

        # Parse the extracted structured JSON string
        try:
            agent_data = json.loads(clean_json_text, strict=False)
        except json.JSONDecodeError as e:
            print(f"JSON Error Details: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="The extracted content is not structurally valid JSON.",
            )

        execution_time_s = round(time.time() - start_time, 3)

        final_response = AgentResponse(
            answer=agent_data.get("answer", "No answer provided."),
            matched_documents=agent_data.get("matched_documents", 0),
            source_documents=agent_data.get("source_documents", []),
            query_time_s=execution_time_s,
            data_sources=agent_data.get("data_sources", ["General Query"]),
        )

        return final_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Execution Error: {str(e)}")


# Endpoints
@app.post("/agent/ask", response_model=AgentResponse, responses=API_ERROR_RESPONSES)
def management_agent(payload: UserQuery):
    return execute_agent_process(payload)


@app.post(
    "/agent/use_case1", response_model=AgentResponse, responses=API_ERROR_RESPONSES
)
def ai_agent_for_inmate_file(payload: QueryUseCase1):
    return execute_agent_process(payload)


@app.post(
    "/agent/use_case2", response_model=AgentResponse, responses=API_ERROR_RESPONSES
)
def ai_agent_for_incidents_and_events(payload: QueryUseCase2):
    return execute_agent_process(payload)


if __name__ == "__main__":
    uvicorn.run("main_api_agent:app", host="127.0.0.1", port=8003, reload=True)
