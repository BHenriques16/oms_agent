import requests
import json
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional

API_BASE_URL = "http://127.0.0.1:8000/api"

# ------------------------------------------------------------------------
# Schemas (Enforcing exact categorical mapping for the LLM)
# ------------------------------------------------------------------------
class StandardSchema(BaseModel):
    offender_id: Optional[str] = Field(default="", description="The unique ID of the offender.")

class SupervisionSchema(BaseModel):
    incarceration_id: Optional[str] = Field(default="", description="The unique ID of the incarceration.")

class OutcomesSchema(BaseModel):
    offender_id: Optional[str] = Field(default="", description="The unique ID of the offender.")
    recidivism: Optional[str] = Field(default="", description="Use '1' for Yes or '0' for No.")

class CountSchema(BaseModel):
    education_level: Optional[str] = Field(
        default="", 
        description="Filters by exact education level. MUST BE EXACTLY ONE OF: 'High School Diploma', 'Less than High School Diploma', 'Some College', 'Bachelors Degree'."
    )
    race: Optional[str] = Field(
        default="", 
        description="Filters by exact race. MUST BE EXACTLY ONE OF: 'White', 'Black', 'Hispanic', 'Asian', 'Other'."
    )
    gang_affiliated: Optional[str] = Field(
        default="", 
        description="Use '1' for Yes or '0' for No."
    )

# ------------------------------------------------------------------------
# Response Formatter
# ------------------------------------------------------------------------
def format_response(response) -> str:
    if response.status_code == 404:
        return "No records found."
    if response.status_code != 200:
        return f"API Error: {response.status_code}"

    try:
        data = response.json()
        if not data:
            return "No records found."

        item = data[0] if isinstance(data, list) and len(data) > 0 else data
        
        # Ensure dictionaries are returned as strict JSON strings to prevent LLM formatting bias
        if isinstance(item, dict):
            return json.dumps(item) 
            
        return str(item)
    except Exception as e:
        return f"Error parsing data: {str(e)}"

# ------------------------------------------------------------------------
# Tools
# ------------------------------------------------------------------------
class OffendersTool(BaseTool):
    name: str = "get_offenders_demographics"
    description: str = (
        "Retrieves demographic data (Gender, Race, Education, Gang status). "
        "Use when the user asks about personal or social characteristics."
    )
    args_schema: type[BaseModel] = StandardSchema
    
    def _run(self, offender_id: str = "") -> str:
        clean_id = str(offender_id).strip()
        res = requests.get(f"{API_BASE_URL}/demographics/{clean_id}")
        return format_response(res)

class IncarcerationsTool(BaseTool):
    name: str = "get_incarcerations_data"
    description: str = (
        "Accesses prison sentence details (Offense type, years served). "
        "Use for questions about time spent in prison or current offenses."
    )
    args_schema: type[BaseModel] = StandardSchema
    
    def _run(self, offender_id: str = "") -> str:
        clean_id = str(offender_id).strip()
        res = requests.get(f"{API_BASE_URL}/incarcerations/{clean_id}")
        return format_response(res)

class CriminalHistoryTool(BaseTool):
    name: str = "get_criminal_history"
    description: str = (
        "Lists previous criminal background (prior arrests, past violent convictions). "
        "Use to check the history of crime prior to the current sentence."
    )
    args_schema: type[BaseModel] = StandardSchema
    
    def _run(self, offender_id: str = "") -> str:
        clean_id = str(offender_id).strip()
        res = requests.get(f"{API_BASE_URL}/criminal_history/{clean_id}")
        return format_response(res)

class SupervisionTool(BaseTool):
    name: str = "get_supervision_conduct"
    description: str = (
        "Monitors post-release behavior and supervision conduct. "
        "Use to evaluate the conduct of an offender while on parole."
    )
    args_schema: type[BaseModel] = SupervisionSchema
    
    def _run(self, incarceration_id: str = "") -> str:
        clean_id = str(incarceration_id).strip()
        res = requests.get(f"{API_BASE_URL}/supervision/{clean_id}")
        return format_response(res)

class OutcomesTool(BaseTool):
    name: str = "get_outcomes_recidivism"
    description: str = (
        "Confirms if the offender committed new crimes (recidivism). "
        "Use to answer if an individual returned to crime."
    )
    args_schema: type[BaseModel] = OutcomesSchema

    def _run(self, offender_id: str = "", recidivism: str = "") -> str:
        clean_id = str(offender_id).strip()
        res = requests.get(f"{API_BASE_URL}/outcomes/{clean_id}")
        return format_response(res)

class CountOffendersTool(BaseTool):
    name: str = "count_offenders"
    description: str = (
        "Returns the total count of offenders based on specific filters. "
        "Use ONLY for quantitative questions (e.g., 'How many...')."
    )
    args_schema: type[BaseModel] = CountSchema
    
    def _run(self, education_level: str = "", race: str = "", gang_affiliated: str = "") -> str:
        params = {}
        
        # General defensive cleanup
        ed_lvl = str(education_level).strip() if education_level and str(education_level).lower() != "none" else ""
        rce = str(race).strip() if race and str(race).lower() != "none" else ""
        gang = str(gang_affiliated).strip() if gang_affiliated and str(gang_affiliated).lower() != "none" else ""

        if ed_lvl: params["education_level"] = ed_lvl
        if rce: params["race"] = rce
        
        # Standardized boolean mapping
        if gang:
            if gang.lower() in ["1", "yes", "true", "y"]:
                params["gang_affiliated"] = "1"
            elif gang.lower() in ["0", "no", "false", "n"]:
                params["gang_affiliated"] = "0"

        res = requests.get(f"{API_BASE_URL}/count_offenders", params=params)
        return format_response(res)