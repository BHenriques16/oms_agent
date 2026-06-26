from fastapi import FastAPI, HTTPException
import pyodbc
import uvicorn

app = FastAPI(title="HORUS Swagger UI")

# SQL Server Connection Details
SERVER = r'BERNARDO\SQLEXPRESS'
DATABASE = 'Horus_test'

CONN_STR = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    rf'SERVER={SERVER};'
    rf'DATABASE={DATABASE};'
    r'Trusted_Connection=yes;'
)

def get_db_connection():
    try:
        conn = pyodbc.connect(CONN_STR)
        return conn
    except Exception as e:
        print(f"Erro ao ligar à Base de Dados: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed.")

# Auxiliar function to convert SQL rows to dictionaries
def row_to_dict(cursor, row):
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))

# API Endpoints
@app.get("/api/demographics/{offender_id}")
def get_demographics(offender_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Offenders WHERE Offender_ID = ?", offender_id)
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="No records found.")
    return row_to_dict(cursor, row)

@app.get("/api/incarcerations/{offender_id}")
def get_incarcerations(offender_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Incarcerations WHERE Offender_ID = ?", offender_id)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No records found.")
    return [row_to_dict(cursor, row) for row in rows]

@app.get("/api/criminal_history/{offender_id}")
def get_criminal_history(offender_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Criminal_History WHERE Offender_ID = ?", offender_id)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No records found.")
    return [row_to_dict(cursor, row) for row in rows]

@app.get("/api/supervision/{offender_id}")
def get_supervision(offender_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Supervision_Conduct WHERE Incarceration_ID = ?", offender_id)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No records found.")
    return [row_to_dict(cursor, row) for row in rows]

@app.get("/api/outcomes/{offender_id}")
def get_outcomes(offender_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Outcomes WHERE Offender_ID = ?", offender_id)
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="No records found.")
    return row_to_dict(cursor, row)

@app.get("/api/count_offenders")
def count_offenders(race: str = None, gang_affiliated: str = None, education_level: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT COUNT(*) as TotalCount FROM Offenders WHERE 1=1"
    params = []
    
    if race:
        query += " AND Race = ?"
        params.append(race)
    if gang_affiliated:
        query += " AND Gang_Affiliated = ?"
        params.append(True if gang_affiliated.lower() in ['true', '1', 'yes'] else False)
    if education_level:
        query += " AND Education_level LIKE ?"
        
        search_term = education_level.replace("Diploma", "").strip()
        params.append(f"%{search_term}%")
        
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    
    return {"TotalCount": row[0]}

if __name__ == "__main__":
    uvicorn.run("db_api:app", host="127.0.0.1", port=8000)