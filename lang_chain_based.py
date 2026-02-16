from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.agents import create_sql_agent
from langchain.agents.agent_types import AgentType

# -----------------------------
# 1. SQLite Connection
# -----------------------------
DB_PATH = "local_database_attendance.db"

engine = create_engine(f"sqlite:///{DB_PATH}")
db = SQLDatabase(engine)

print("Tables detected:", db.get_usable_table_names())

# -----------------------------
# 2. Gemini LLM
# -----------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0
)

# -----------------------------
# 3. SQL Query Chain (NL → SQL)
# -----------------------------
sql_chain = create_sql_query_chain(llm, db)

# -----------------------------
# 4. SQL Execution Tool
# -----------------------------
execute_tool = QuerySQLDataBaseTool(db=db)

# -----------------------------
# 5. Simple pipeline (manual)
# -----------------------------
def ask_db_manual(question: str):
    print("\nQuestion:", question)

    # Generate SQL
    sql_query = sql_chain.invoke({"question": question})
    print("\nGenerated SQL:\n", sql_query)

    # Execute SQL
    result = execute_tool.invoke(sql_query)
    print("\nResult:\n", result)
    return result

# -----------------------------
# 6. SQL Agent (auto repair, retry, reasoning)
# -----------------------------
agent = create_sql_agent(
    llm=llm,
    db=db,
    agent_type=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

# def ask_db_agent(question: str):
#     print("\nAgent Question:", question)
#     response = agent.invoke(question)
#     print("\nAgent Response:\n", response)
#     return response

# -----------------------------
def ask_db_agent_raw(question: str):
    response = agent.invoke(question)
    return response["output"]  # raw DB text


def format_output(question: str, raw_data: str):
    format_prompt = f"""
You are a data presentation assistant.

User Question:
{question}

Raw Database Result:
{raw_data}

Format this into a clean, professional, easy-to-read report.
Use tables if appropriate.
Do NOT change any values.
"""

    formatted = llm.invoke(format_prompt)
    return formatted.content


def ask_db_agent(question: str):
    raw = ask_db_agent_raw(question)
    clean = format_output(question, raw)

    print("\n========== FINAL OUTPUT ==========\n")
    print("\nAgent Response:\n",clean)
# 7. Run
# -----------------------------
if __name__ == "__main__":
    question = "Give me attendance summary of Aadam Vanker"

    # print("\n========= MANUAL CHAIN =========")
    # ask_db_manual(question)

    print("\n========= SQL AGENT =========")
    ask_db_agent(question)
