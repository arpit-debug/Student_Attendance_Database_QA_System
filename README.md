# 🎓 Student Attendance Database QA System

Natural Language → Guardrailed SQL Assistant

A structured, safe, and deterministic Question Answering system that converts natural language into validated SQL queries.

Built with:

Streamlit (UI)

LangChain + Ollama (LLM reasoning layer)

SQLite (Local database)

Multi-layer guardrailed SQL pipeline

# 📌 System Daigram
![Demo of the app](Diagram.png)

# 📌 System Overview

User Question
→ Query Classification (LLM)
→ Structured Plan Extraction (LLM → JSON)
→ Validation & Guardrails (Deterministic)
→ SQL Builder (Deterministic)
→ SQLite Execution
→ Natural Language Answer (LLM)

The LLM is never allowed to execute SQL directly.
All SQL is validated, parameterized, and deterministic.


🧠 Architecture
```text
USER (Streamlit UI)
        │
        ▼
run_query(user_input)
        │
        ▼
LAYER 1 — classify_query()      ✅ LLM
→ Detects intent (aggregate | list | lookup)

        ▼
LAYER 2 — extract_plan()        ✅ LLM
→ Generates structured JSON:
  {
    table,
    select_column,
    aggregation,
    filters
  }

        ▼
LAYER 3 — validate_plan()       ❌ No LLM
→ Table whitelist
→ Column whitelist
→ Type enforcement
→ Date normalization
→ Range → BETWEEN conversion
→ Operator correction
→ LIKE removal for date fields

        ▼
LAYER 4 — build_sql()           ❌ No LLM
→ Deterministic SQL builder
→ Parameterized queries
→ Safe JOIN handling

        ▼
EXECUTE (SQLite)                ❌ No LLM

        ▼
LAYER 5 — generate_answer()     ✅ LLM
→ Converts result rows into natural language
```

# 🗄 Database Tables
## 1️⃣ detailed_attendance

Session-level attendance records.

Key columns:

Student

SIMS_ID

DOB

DOA

Gender

Mark

Mark_date

AM_PM

Year_taught_in_Code

Key_Stage

Reg

## 2️⃣ attendance_summary

Year-level aggregated totals per student.

Includes:

Present

Illness

Authorised absence

Late

Unauthorised absence

Grand_Total

## 3️⃣ attendance_mark_description

Reference table for attendance codes.

Columns:

Reg_Codes

Description

Statistical_Meaning

Physical_Meaning

Status

## ❓ Supported Question Types
🔹 Record Lookup

What is the date of birth of Arjan Jha Crasto?

What is the admission date of SIMS ID 12345?

🔹 Aggregate Queries

How many students were born in March 2016?

Count illness marks.

How many students are in Year 3?

🔹 Attribute Lookup

What does mark code C mean?

🔹 List Queries

List students in Year 4.

Show students admitted in 2022.

Below is properly formatted **Markdown**.
You can copy this directly into `README.md` — headings and code blocks will render correctly.

---

# 🚀 Setup & Run Instructions

## 1️⃣ Install Ollama

Download and install Ollama:

👉 [https://ollama.com](https://ollama.com)

Verify installation:

```bash
ollama --version
```

Pull the required model (example: llama3):

```bash
ollama pull llama3
```

Test the model:

```bash
ollama run llama3
```

---

## 2️⃣ Clone the Project

```bash
git clone <your-repo-url>
cd student-attendance-qa
```

---

## 3️⃣ Create Virtual Environment (Recommended)

Create environment:

```bash
python -m venv venv
```

Activate environment:

### Windows

```bash
venv\Scripts\activate
```

### Mac / Linux

```bash
source venv/bin/activate
```

---

## 4️⃣ Install Dependencies

Ensure `requirements.txt` exists, then run:

```bash
pip install -r requirements.txt
```

---

## 5️⃣ Run the Application

### ▶ If using Streamlit UI

```bash
streamlit run app.py
```

### ▶ If using CLI version

```bash
python main.py
```

---

# 📁 Example `requirements.txt`

```text
streamlit
langchain
langchain-community
ollama
pydantic
```

> **Note:** `sqlite3` is included with Python by default and does not need installation.

---

# 🔒 Security Design

This system is designed with strict guardrails:

* ❌ No raw SQL generation from LLM
* ✅ Strict table whitelist validation
* ✅ Strict column whitelist validation
* ✅ Deterministic SQL builder
* ✅ Parameterized queries (prevents SQL injection)
* ✅ Date normalization
* ✅ Operator correction
* ✅ Plan validation before execution

The LLM is used only for reasoning and structured planning — never for direct SQL execution.

---

# 🧪 Example Query

### User Question

```
How many students were born in March 2016?
```

### Generated SQL

```sql
SELECT COUNT(DISTINCT DOB)
FROM detailed_attendance
WHERE DOB BETWEEN ? AND ?;
```

---

# 📌 Key Principles

* LLM for reasoning only
* Deterministic SQL execution
* Guardrailed architecture
* Safe parameter binding
* Modular multi-layer pipeline

---

# 📜 License

MIT License

---

If you want to extend the system (range logic, joins, advanced filters, multi-table queries), enhance the **validation layer** and **SQL builder layer** without modifying the LLM reasoning layer.
