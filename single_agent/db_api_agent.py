from typing import Optional

import pyodbc
import uvicorn
from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="HORUS OMS Swagger UI",
)

# Database config
SERVER = r"BERNARDO\SQLEXPRESS"
DATABASE = "Horus_oms"
CONN_STR = (
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    rf"SERVER={SERVER};"
    rf"DATABASE={DATABASE};"
    r"Trusted_Connection=yes;"
)


def get_db_connection():
    try:
        return pyodbc.connect(CONN_STR)
    except Exception as e:
        print(f"Critical error connecting to database: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed.")


def row_to_dict(cursor, row):
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def rows_to_dict_list(cursor):
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


@app.get("/api/inmates/search")
def search_inmates(
    block: Optional[str] = None,
    security_level: Optional[str] = None,
    min_risk: Optional[float] = None,
    max_risk: Optional[float] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    primary_offense: Optional[str] = None,
    is_parole_eligible: Optional[str] = None,
    gang_affiliation: Optional[str] = None,
    gender: Optional[str] = None,
    ethnicity: Optional[str] = None,
    health_status: Optional[str] = None,
    education_level: Optional[str] = None,
    offense_keyword: Optional[str] = None,
    behavioral_keyword: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "DESC",
):

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Base query targeting essential columns only
            base_select = (
                "SELECT OffenderID, Name, CellBlock, SecurityLevel, PrimaryOffense, "
                "RiskAssessmentScore, IsParoleEligible, Age, CommissaryBalance, "
                "DisciplinaryIncidents, Gender, Ethnicity, HealthStatus, EducationLevel"
            )
            query = f"{base_select} FROM Offenders WHERE 1=1"
            params = []

            # Dynamic filtering logic
            if block:
                query += " AND CellBlock = ?"
                params.append(block)
            if security_level:
                query += " AND SecurityLevel = ?"
                params.append(security_level)
            if min_risk is not None:
                query += " AND RiskAssessmentScore >= ?"
                params.append(min_risk)
            if max_risk is not None:
                query += " AND RiskAssessmentScore <= ?"
                params.append(max_risk)
            if min_age is not None:
                query += " AND CAST(Age as INT) >= ?"
                params.append(min_age)
            if max_age is not None:
                query += " AND CAST(Age as INT) <= ?"
                params.append(max_age)

            # Rich-Text and Categorical matching
            if primary_offense:
                query += " AND PrimaryOffense LIKE ?"
                params.append(f"%{primary_offense}%")
            if is_parole_eligible:
                # Standardizing boolean check across different potential DB formats
                if is_parole_eligible.lower() in ["true", "1"]:
                    query += " AND (IsParoleEligible = 1 OR IsParoleEligible = 'True')"
                else:
                    query += " AND (IsParoleEligible = 0 OR IsParoleEligible = 'False')"
            if gang_affiliation:
                query += " AND GangAffiliation = ?"
                params.append(gang_affiliation)
            if gender:
                query += " AND Gender = ?"
                params.append(gender)
            if ethnicity:
                query += " AND Ethnicity = ?"
                params.append(ethnicity)
            if health_status:
                query += " AND HealthStatus = ?"
                params.append(health_status)
            if education_level:
                query += " AND EducationLevel = ?"
                params.append(education_level)

            # Full-Text keyword sub-string matching
            if offense_keyword:
                query += " AND OffenseDescription LIKE ?"
                params.append(f"%{offense_keyword}%")
            if behavioral_keyword:
                query += " AND BehavioralNotes LIKE ?"
                params.append(f"%{behavioral_keyword}%")

            valid_sort_columns = [
                "Age",
                "RiskAssessmentScore",
                "SentenceLengthMonths",
                "CommissaryBalance",
                "DisciplinaryIncidents",
            ]
            if sort_by and sort_by in valid_sort_columns:
                safe_order = "ASC" if sort_order.upper() == "ASC" else "DESC"
                query += f" ORDER BY {sort_by} {safe_order}"
            else:
                query += " ORDER BY OffenderID"

            query += " OFFSET 0 ROWS FETCH NEXT 100 ROWS ONLY"

            cursor.execute(query, params)
            results = rows_to_dict_list(cursor)

            # Execute an independent COUNT query to provide macro context to the AI
            count_query = query.replace(base_select, "SELECT COUNT(*) as Total")
            count_query = count_query.split(" ORDER BY ")[0]
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]

            return {
                "filters_used": {
                    "block": block,
                    "security_level": security_level,
                    "min_risk": min_risk,
                    "max_risk": max_risk,
                    "min_age": min_age,
                    "max_age": max_age,
                    "primary_offense": primary_offense,
                    "is_parole_eligible": is_parole_eligible,
                    "gang_affiliation": gang_affiliation,
                    "gender": gender,
                    "ethnicity": ethnicity,
                    "health_status": health_status,
                    "education_level": education_level,
                    "offense_keyword": offense_keyword,
                    "behavioral_keyword": behavioral_keyword,
                    "sort_by": sort_by,
                    "sort_order": sort_order,
                },
                "total_found_in_db": total_count,
                "records_returned": len(results),
                "results": results,
            }

    except pyodbc.Error as db_err:
        print(f"[SQL Server Error in Search]: {db_err}")
        raise HTTPException(
            status_code=500, detail="Database execution error during search."
        )


@app.get("/api/inmates/{offender_id}/profile")
def get_full_profile(offender_id: int):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Secure parameterized query to prevent SQL Injection
            cursor.execute("SELECT * FROM Offenders WHERE OffenderID = ?", offender_id)
            row = cursor.fetchone()

            if not row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Inmate with ID {offender_id} not found in database.",
                )

            return row_to_dict(cursor, row)

    except pyodbc.Error as db_err:
        print(f"[SQL Server Error in Profile]: {db_err}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching inmate profile.",
        )


@app.get("/api/analytics/global-stats")
def get_global_stats(
    block: Optional[str] = None,
    security_level: Optional[str] = None,
    health_status: Optional[str] = None,
    ethnicity: Optional[str] = None,
    gender: Optional[str] = None,
    primary_offense: Optional[str] = None,
    is_parole_eligible: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            stats = {}
            where_clause = " WHERE 1=1"
            params = []

            # Dynamic Filters mirroring the Search capability
            if block:
                where_clause += " AND CellBlock = ?"
                params.append(block)
            if security_level:
                where_clause += " AND SecurityLevel = ?"
                params.append(security_level)
            if health_status:
                where_clause += " AND HealthStatus = ?"
                params.append(health_status)
            if ethnicity:
                where_clause += " AND Ethnicity = ?"
                params.append(ethnicity)
            if gender:
                where_clause += " AND Gender = ?"
                params.append(gender)
            if primary_offense:
                where_clause += " AND PrimaryOffense LIKE ?"
                params.append(f"%{primary_offense}%")
            if is_parole_eligible:
                if is_parole_eligible.lower() in ["true", "1"]:
                    where_clause += (
                        " AND (IsParoleEligible = 1 OR IsParoleEligible = 'True')"
                    )
                else:
                    where_clause += (
                        " AND (IsParoleEligible = 0 OR IsParoleEligible = 'False')"
                    )
            if min_age is not None:
                where_clause += " AND CAST(Age as INT) >= ?"
                params.append(min_age)
            if max_age is not None:
                where_clause += " AND CAST(Age as INT) <= ?"
                params.append(max_age)

            # Execute core macro-metrics calculation
            cursor.execute(
                f"""
                SELECT 
                    COUNT(*) as TotalInmates, 
                    AVG(CAST(Age as FLOAT)) as AvgAge, 
                    AVG(RiskAssessmentScore) as AvgRiskScore,
                    AVG(CAST(SentenceLengthMonths as FLOAT)) as AvgSentenceMonths,
                    SUM(CAST(DisciplinaryIncidents as INT)) as TotalIncidents,
                    SUM(CommissaryBalance) as TotalCommissary,
                    AVG(CommissaryBalance) as AvgCommissaryBalance
                FROM Offenders
                {where_clause}
            """,
                params,
            )

            general_row = cursor.fetchone()
            columns = [col[0] for col in cursor.description]

            # Validate if database returned actionable numerical data
            if general_row and general_row[0] > 0:
                stats["general_metrics"] = dict(zip(columns, general_row))
            else:
                stats["general_metrics"] = {
                    "TotalInmates": 0,
                    "Message": "No inmates match the specified demographic filters.",
                }

            # Fetch ONLY the top 10 most populated cell blocks
            if not block and general_row and general_row[0] > 0:
                cursor.execute(
                    f"SELECT TOP 10 CellBlock, COUNT(*) as Qty FROM Offenders {where_clause} GROUP BY CellBlock ORDER BY Qty DESC",
                    params,
                )
                stats["top_10_populated_blocks"] = {
                    row[0]: row[1] for row in cursor.fetchall()
                }

            if not security_level and general_row and general_row[0] > 0:
                cursor.execute(
                    f"SELECT TOP 10 SecurityLevel, COUNT(*) as Qty FROM Offenders {where_clause} GROUP BY SecurityLevel ORDER BY Qty DESC",
                    params,
                )
                stats["by_security_level"] = {
                    row[0]: row[1] for row in cursor.fetchall()
                }

            return stats

    except pyodbc.Error as db_err:
        print(f"[SQL Server Error in Stats]: {db_err}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while computing global statistics.",
        )


if __name__ == "__main__":
    uvicorn.run("db_api_agent:app", host="127.0.0.1", port=8002, reload=True)
