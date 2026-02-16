import sqlite3
import json
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime

from langchain_community.chat_models import ChatOllama
from langchain.schema import SystemMessage, HumanMessage


# ==========================================================
# CONFIG
# ==========================================================

DB_PATH = "local_database_attendance.db"
llm = ChatOllama(model="qwen2.5", temperature=0)


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


# ==========================================================
# FULL SCHEMA REGISTRY (AUTHORITATIVE)
# ==========================================================

SCHEMA = {
    "detailed_attendance": {
        "description": "Raw session-level attendance records (one row per student per session)",
        "columns": {
            "External_Id": "Unique internal identifier for student",
            "SIMS_ID": "School system unique student ID",
            "Mark": "Attendance code for the session",
            "Mark_date": "Date of attendance session (format: DD-Mon-YY, example: 11-Nov-24)",
            "AM/PM": "Session type",
            "Student": "Full student name including class",
            "DOB": "Date of birth (format: D/M/YYYY)",
            "DOA": "Date of admission (format: D/M/YYYY)",
            "Gender": "M or F",
            "Key_Stage": "Educational key stage",
            "Year_taught_in_Code": "Numeric year group (e.g., 3 = 3rd standard)",
            "Reg": "Registration group"
        }
    },
    "attendance_summary": {
        "description": "Aggregated yearly attendance totals per student",
        "columns": {
            "Student": "Full student name including class",
            "nan": "Missing marks",
            "-": "Not required",
            "#": "Planned absence",
            "/": "Present AM count",
            "\\": "Present PM count",
            "B": "Educated off site",
            "C": "Authorised absence",
            "D": "Dual registration",
            "E": "Excluded",
            "H": "Holiday",
            "I": "Illness",
            "L": "Late",
            "M": "Medical",
            "N": "No reason yet provided",
            "O": "Unauthorised absence",
            "P": "Approved sporting activity",
            "R": "Religious observance",
            "S": "Study leave",
            "T": "Traveller absence",
            "V": "Educational visit",
            "W": "Work experience",
            "X": "Non compulsory school age",
            "Z": "Closed to pupils",
            "Grand_Total": "Total sessions recorded"
        }
    },
    "attendance_mark_description": {
        "description": "Reference table explaining mark codes",
        "columns": {
            "Reg_Codes": "Attendance code",
            "Description": "Human readable explanation",
            "Lesson_Codes": "Session code",
            "Statistical_Meaning": "Statistical category",
            "Physical_Meaning": "Physical attendance meaning",
            "Status": "Present or Absence classification"
        }
    }
}

JOIN_RELATIONS = {
    ("detailed_attendance", "attendance_mark_description"):
        "detailed_attendance.Mark = attendance_mark_description.Reg_Codes"
}


# ==========================================================
# DATE NORMALIZATION
# ==========================================================

def build_date_range(value: str):
    """
    Detect if value represents:
    - Year only (2016)
    - Month + Year (March 2016)
    - Full date
    Returns:
        ("between", start, end) OR ("exact", value)
    """

    value = value.strip()

    # Year only
    if re.fullmatch(r"\d{4}", value):
        year = int(value)
        start = f"1/1/{year}"
        end = f"31/12/{year}"
        return "between", start, end

    # Month + Year (e.g., March 2016)
    try:
        parsed = datetime.strptime(value, "%B %Y")
        month = parsed.month
        year = parsed.year

        start = datetime(year, month, 1)

        if month == 12:
            end = datetime(year, 12, 31)
        else:
            next_month = datetime(year, month + 1, 1)
            end = next_month - timedelta(days=1)

        return "between", f"{start.day}/{start.month}/{start.year}", \
                          f"{end.day}/{end.month}/{end.year}"
    except:
        pass

    return "exact", value

def normalize_date(value: str, column: str) -> str:

    if not value:
        return value

    value = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', value.lower())

    formats = [
        "%d %B %Y",
        "%d %b %Y",
        "%Y-%m-%d",
        "%d/%m/%Y"
    ]

    parsed = None
    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt)
            break
        except:
            continue

    if not parsed:
        return value

    if column == "Mark_date":
        return parsed.strftime("%d-%b-%y")

    if column in ["DOB", "DOA"]:
        return f"{parsed.day}/{parsed.month}/{parsed.year}"

    return value


# ==========================================================
# LAYER 1 — CLASSIFICATION
# ==========================================================

def classify_query(question: str) -> str:

    prompt = """
Classify the query into one of:

- aggregate
- attribute_lookup
- record_lookup
- list

Return only one word.
"""

    response = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=question)
    ])

    return response.content.strip().lower()


# ==========================================================
# LAYER 2 — STRUCTURED PLAN EXTRACTION
# ==========================================================

def extract_plan(question: str, query_type: str) -> Dict[str, Any]:

    schema_text = json.dumps(SCHEMA, indent=2)

    prompt = f"""
You are generating a structured SQL plan.

Available database schema:
{schema_text}

Rules:
- Only use real column names exactly as shown.
- Choose correct table.
- If counting students, use select_column = "Student".
- If asking date of birth, select_column = "DOB".
- If asking student name by SIMS_ID, select_column = "Student".
- If asking standard, use Year_taught_in_Code.
- If asking about mark meaning, join attendance_mark_description.
- For aggregate queries use aggregation="count".

Return JSON only:

{{
  "query_type": "{query_type}",
  "table": "table_name",
  "select_column": "column",
  "aggregation": "count | none",
  "filters": [
    {{
      "column": "column",
      "operator": "=",
      "value": "value"
    }}
  ]
}}
"""

    response = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=question)
    ])

    return json.loads(response.content)


# ==========================================================
# LAYER 3 — VALIDATION
# ==========================================================

def validate_plan(plan: Dict[str, Any]) -> Dict[str, Any]:

    if plan["table"] not in SCHEMA:
        raise ValueError("Invalid table selected")

    valid_columns = SCHEMA[plan["table"]]["columns"]

    if plan["select_column"] not in valid_columns:
        raise ValueError("Invalid select column")

    for f in plan.get("filters", []):
        if f["column"] not in valid_columns:
            raise ValueError(f"Invalid filter column: {f['column']}")

        col_type = valid_columns[f["column"]]

        if "int" in col_type:
            f["value"] = str(int(f["value"]))

        if "date" in col_type:

            # Remove LIKE for dates
            if f["operator"].lower() == "like":
                f["operator"] = "="
                f["value"] = f["value"].replace("%", "")

            range_type, *range_values = build_date_range(f["value"])

            if range_type == "between":
                f["operator"] = "between"
                f["value"] = range_values  # [start, end]
            else:
                f["operator"] = "="
                f["value"] = normalize_date(range_values[0], f["column"])

    return plan


# ==========================================================
# LAYER 4 — SQL BUILDER
# ==========================================================

def build_sql(plan: Dict[str, Any]) -> Tuple[str, List[Any]]:

    table = plan["table"]
    joins = []
    params = []

    # Join detection
    if table == "attendance_mark_description":
        joins.append(
            "JOIN detailed_attendance ON detailed_attendance.Mark = attendance_mark_description.Reg_Codes"
        )

    # SELECT
    if plan["query_type"] == "aggregate" and plan["aggregation"] == "count":
        select_sql = f"SELECT COUNT(DISTINCT {plan['select_column']})"
    else:
        select_sql = f"SELECT DISTINCT {plan['select_column']}"

    sql = f"{select_sql} FROM {table}"

    if joins:
        sql += " " + " ".join(joins)

    # WHERE
    if plan.get("filters"):
        conditions = []
        for f in plan["filters"]:
            if f["operator"].lower() == "between":
                conditions.append(f"{f['column']} BETWEEN ? AND ?")
                params.extend(f["value"])
            else:
                conditions.append(f"{f['column']} {f['operator']} ?")
                params.append(f["value"])
        sql += " WHERE " + " AND ".join(conditions)

    sql += ";"

    return sql, params


# ==========================================================
# EXECUTION
# ==========================================================

def execute_sql(sql: str, params: List[Any]):

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    return rows


# ==========================================================
# ANSWER GENERATION
# ==========================================================

def generate_answer(question: str, result):

    prompt = f"""
Question:
{question}

SQL Result:
{result}

Generate a clear natural language answer.
"""

    response = llm.invoke(prompt)
    return response.content


# ==========================================================
# MAIN PIPELINE
# ==========================================================

def run_query(user_input: str):

    print("\n--- LAYER 1: CLASSIFICATION ---")
    query_type = classify_query(user_input)
    print("Query Type:", query_type)

    print("\n--- LAYER 2: EXTRACTION ---")
    plan = extract_plan(user_input, query_type)
    print("Extracted Plan:", plan)

    print("\n--- LAYER 3: VALIDATION ---")
    validated_plan = validate_plan(plan)
    print("Validated Plan:", validated_plan)

    print("\n--- LAYER 4: SQL BUILD ---")
    sql, params = build_sql(validated_plan)
    print("SQL:", sql)
    print("Params:", params)

    result = execute_sql(sql, params)

    print("\n--- RESULT ---")
    print(result)

    answer = generate_answer(user_input, result)

    return sql, result, answer


# ==========================================================
# STREAMLIT UI
# ==========================================================

st.set_page_config(page_title="Enterprise NL → SQL Assistant", layout="wide")

st.title("Enterprise NL → SQL Assistant")
st.caption("LLM + Guardrails + SQLite")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if prompt := st.chat_input("Ask a question about attendance data..."):

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("Processing..."):
            sql, result, answer = run_query(prompt)

        # Assistant response
        st.session_state.messages.append({"role": "assistant", "content": answer})

        with st.chat_message("assistant"):
            st.markdown(answer)

            with st.expander("Technical Details"):
                st.markdown("**SQL:**")
                st.code(sql, language="sql")

                st.markdown("**Result:**")
                st.code(str(result))

    except Exception as e:
        st.error(f"Error: {str(e)}")
