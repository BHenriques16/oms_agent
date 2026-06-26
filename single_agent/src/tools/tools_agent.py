from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional
import requests
import json


# Search tool
class InmateSearchInput(BaseModel):
    block: Optional[str] = Field(None, description="The prison cell block (e.g., 'A-1', 'D-4').")
    security_level: Optional[str] = Field(None, description="The security level (e.g., 'Maximum', 'Medium', 'Minimum').")
    min_risk: Optional[float] = Field(None, description="Minimum risk assessment score (0.0 to 10.0).")
    max_risk: Optional[float] = Field(None, description="Maximum risk assessment score (0.0 to 10.0).")
    min_age: Optional[int] = Field(None, description="Minimum age filter.")
    max_age: Optional[int] = Field(None, description="Maximum age filter.")
    primary_offense: Optional[str] = Field(None, description="The broad categorization of offense (e.g., 'Kidnapping', 'Assault').")
    is_parole_eligible: Optional[str] = Field(None, description="Parole eligibility status ('True' or 'False').")
    gang_affiliation: Optional[str] = Field(None, description="Specific gang name or affiliation status.")
    gender: Optional[str] = Field(None, description="Gender classification ('Male' or 'Female').")
    ethnicity: Optional[str] = Field(None, description="Ethnicity categories (e.g., 'Hispanic', 'African American', 'Caucasian').")
    health_status: Optional[str] = Field(None, description="General health condition description (e.g., 'Good', 'Fair', 'Poor').")
    education_level: Optional[str] = Field(None, description="Highest educational level achieved (e.g., 'Some High School', 'Some College').")
    offense_keyword: Optional[str] = Field(None, description="Substring search keywords inside the long detailed offense descriptions.")
    behavioral_keyword: Optional[str] = Field(None, description="Substring search keywords inside detailed guard and behavioral notes.")
    sort_by: Optional[str] = Field(None, description="Column to sort by. Valid options ONLY: 'Age', 'RiskAssessmentScore', 'CommissaryBalance', 'DisciplinaryIncidents'.")
    sort_order: Optional[str] = Field(None, description="'DESC' for highest/most, 'ASC' for lowest/least.")

class InmateSearchTool(BaseTool):
    name: str = "Search Inmates Database"
    description: str = (
        "WHEN TO USE: Always use this tool FIRST when the user asks to find, filter, list, or locate inmates. "
        "CRITICAL RULE: If the user asks for extremes like 'oldest', 'youngest', 'highest', or 'most', you MUST use the 'sort_by' and 'sort_order' parameters! "
        "ANTI-MATH RULE: NEVER use this tool to calculate averages, totals, or sums. It only returns a preview of 3 inmates, so doing math on this output will be WRONG. "
        "This tool is smart and will automatically retrieve 'BehavioralNotes' and 'OffenseDescription' for the top results. You DO NOT need to call the Profile Tool."
    )
    args_schema: type[BaseModel] = InmateSearchInput

    def _run(self, **kwargs) -> str:
        # Filter out None values to keep the API request clean
        params = {k: v for k, v in kwargs.items() if v is not None}
        url = "http://localhost:8002/api/inmates/search"
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            total_found = data.get("total_found_in_db", 0)
            results = data.get("results", [])
            
            # Fast-fail if database is empty for this criteria
            if total_found == 0:
                return "Search completed: 0 inmates match the requested filters. Inform the user that no results were found."
            
            summary = f"Search completed: A total of {total_found} inmates match the criteria.\n"
            summary += "Notice: Auto-fetched full profile details (BehavioralNotes, etc.) for the top results shown below. You DO NOT need to use the Profile Tool.\n\n"
            
            preview_limit = 3
            extracted_previews = []
            
            # Python will fetch the long-form text for the top 3 results.
            # This ensures the LLM never receives contradictory instructions to use the Profile Tool.
            for inmate in results[:preview_limit]:
                offender_id = inmate.get("OffenderID")
                
                # Silent fetch for the specific profile
                try:
                    prof_resp = requests.get(f"http://localhost:8002/api/inmates/{offender_id}/profile")
                    if prof_resp.status_code == 200:
                        prof_data = prof_resp.json()
                        inmate["BehavioralNotes"] = prof_data.get("BehavioralNotes", "No behavioral notes available.")
                        inmate["OffenseDescription"] = prof_data.get("OffenseDescription", "No offense description available.")
                except Exception:
                    # Fallback in case the individual profile API fails
                    inmate["BehavioralNotes"] = "System Error fetching notes."
                    inmate["OffenseDescription"] = "System Error fetching description."
                    
                extracted_previews.append(inmate)
            
            # Append the enriched JSON to the final string sent back to the LLM
            summary += f"Preview of top {len(extracted_previews)} results:\n{json.dumps(extracted_previews, ensure_ascii=False, indent=2)}"
            
            return summary
            
        except Exception as e:
            return f"API Error: The database is unreachable or the query failed. Details: {str(e)}"


# Profile tool for fetching detailed inmate information
class InmateProfileInput(BaseModel):
    offender_id: int = Field(..., description="The exact integer ID of the inmate (OffenderID).")

class InmateProfileTool(BaseTool):
    name: str = "Get Full Inmate Profile"
    description: str = (
        "WHEN TO USE: Use ONLY when you have a specific, known OffenderID and the Search tool DID NOT already provide the BehavioralNotes. "
        "CRITICAL RULE: Never call this in parallel with the Search tool."
    )
    args_schema: type[BaseModel] = InmateProfileInput

    def _run(self, offender_id: int) -> str:
        url = f"http://localhost:8002/api/inmates/{offender_id}/profile"
        try:
            response = requests.get(url)
            if response.status_code == 404:
                return f"No inmate found with OffenderID {offender_id}."
            response.raise_for_status()
            return json.dumps(response.json(), ensure_ascii=False, indent=2)
        except Exception as e:
            return f"API Error in Profile Tool: {str(e)}"


# Global stats tool for math and aggregation of inmate data
class GlobalStatsInput(BaseModel):
    block: Optional[str] = Field(None, description="Filter macro facility metrics down to a single cell block.")
    security_level: Optional[str] = Field(None, description="Filter macro facility metrics down to a single security level.")
    health_status: Optional[str] = Field(None, description="Filter metrics by health status (e.g., 'Poor', 'Good').")
    ethnicity: Optional[str] = Field(None, description="Filter metrics by ethnicity (e.g., 'African American', 'Hispanic').")
    gender: Optional[str] = Field(None, description="Filter metrics by gender.")
    primary_offense: Optional[str] = Field(None, description="Filter metrics by the primary offense category.")
    is_parole_eligible: Optional[str] = Field(None, description="Filter metrics by parole eligibility.")
    min_age: Optional[int] = Field(None, description="Minimum age filter.")
    max_age: Optional[int] = Field(None, description="Maximum age filter.")

class GlobalStatsTool(BaseTool):
    name: str = "Get Global Prison Statistics"
    description: str = (
        "CRITICAL: You MUST use this tool whenever the user asks for ANY math, 'average', 'total', 'sum', or 'count'. "
        "This tool SUPPORTS calculating averages directly! It returns EXACT math for any demographic group (e.g., Poor health, African American, etc.). "
        "Do not hesitate, just call it with the appropriate filters to get the exact math."
    )
    args_schema: type[BaseModel] = GlobalStatsInput

    def _run(self, **kwargs) -> str:
        # Securely pass dynamic arguments to the Analytics API
        params = {k: v for k, v in kwargs.items() if v is not None}
        url = "http://localhost:8002/api/analytics/global-stats"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return json.dumps(response.json(), ensure_ascii=False, indent=2)
        except Exception as e:
            return f"API Error in Analytics Tool: {str(e)}"