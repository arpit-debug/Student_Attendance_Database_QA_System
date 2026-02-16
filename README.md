# 🎓 Student Attendance Database QA System  
Natural Language → SQL Guardrailed Assistant

This project is a **Student Database Question Answering System** built using:

- Streamlit (UI)
- LangChain + Ollama (LLM layer)
- SQLite (local database)
- Guardrailed structured SQL generation pipeline

The system converts natural language questions into validated SQL queries and executes them safely.

---
# 📌 System Daigram
![Demo of the app](Diagram.png)
# 📌 System Architecture

```text
+------------------------------------------------------+
|                    USER (CLI / UI)                   |
+---------------------------+--------------------------+
                            |
                            v
+------------------------------------------------------+
|                run_query(user_input)                 |
+------------------------------------------------------+
                            |
                            v
┌──────────────────────────────────────────────────────┐
│ LAYER 1 — QUERY CLASSIFICATION                       │
│ Function: classify_query()                           │
│                                                      │
│ 🔹 LLM USED HERE                                     │
│ → Determines intent: aggregate | list | lookup       │
└──────────────────────────────────────────────────────┘
                            |
                            v
┌──────────────────────────────────────────────────────┐
│ LAYER 2 — STRUCTURED PLAN EXTRACTION                 │
│ Function: extract_plan()                             │
│                                                      │
│ 🔹 LLM USED HERE                                     │
│ → Generates Structured JSON Plan                     │
│   { table, select_column, aggregation, filters }     │
└──────────────────────────────────────────────────────┘
                            |
                            v
┌──────────────────────────────────────────────────────┐
│ LAYER 3 — VALIDATION & GUARDRAILS                    │
│ Function: validate_plan()                            │
│                                                      │
│ 🚫 NO LLM USED HERE                                 │
│ ✔ Table whitelist validation                        │
│ ✔ Column whitelist validation                       │
│ ✔ Data type enforcement                             │
│ ✔ Date normalization                                │
│ ✔ Range conversion (BETWEEN)                        │
│ ✔ LIKE removal for dates                            │
│ ✔ Operator correction                               │
└──────────────────────────────────────────────────────┘
                            |
                            v
┌──────────────────────────────────────────────────────┐
│ LAYER 4 — SQL BUILDER                                │
│ Function: build_sql()                                │
│                                                      │
│ 🚫 NO LLM USED HERE                                  │
│ → Deterministic SQL generation                       │
│ → Parameterized queries (prevents injection)         │
│ → Controlled JOIN detection                          │
└──────────────────────────────────────────────────────┘
                            |
                            v
┌──────────────────────────────────────────────────────┐
│ EXECUTION LAYER                                      │
│ Function: execute_sql()                              │
│                                                      │
│ 🚫 NO LLM USED HERE                                  │
│ → SQLite execution                                   │
│ → Returns raw rows                                   │
└──────────────────────────────────────────────────────┘
                            |
                            v
┌──────────────────────────────────────────────────────┐
│ LAYER 5 — ANSWER GENERATION                          │
│ Function: generate_answer()                          │
│                                                      │
│ 🔹 LLM USED HERE                                     │
│ → Converts SQL result into natural language          │
└──────────────────────────────────────────────────────┘
                            |
                            v
+------------------------------------------------------+
|                    FINAL RESPONSE                    |
+------------------------------------------------------+
```

User Question  
→ Query Classification  
→ Structured Plan Extraction (JSON)  
→ Validation  
→ Deterministic SQL Builder  
→ Execution  
→ Natural Language Answer  

The LLM is used only for reasoning and planning.  
SQL execution is deterministic and validated.

---

# 🗄 Database Tables

The system contains 3 main tables:

---

## 1️⃣ detailed_attendance

Raw session-level attendance records.  
Each row represents one student for one session.

**Key Columns:**

- Student (Full name)
- SIMS_ID (Student ID)
- DOB (Date of Birth)
- DOA (Date of Admission)
- Gender
- Mark (Attendance code)
- Mark_date (Session date)
- AM/PM (Session type)
- Year_taught_in_Code (Year group)
- Key_Stage
- Reg (Registration group)

---

## 2️⃣ attendance_summary

Aggregated yearly attendance totals per student.

**Includes counts of attendance codes such as:**

- Present (/ and \)
- Illness (I)
- Authorised absence (C)
- Late (L)
- Unauthorised absence (O)
- Grand_Total (Total sessions)

---

## 3️⃣ attendance_mark_description

Reference table describing attendance codes.

**Columns:**

- Reg_Codes
- Description
- Lesson_Codes
- Statistical_Meaning
- Physical_Meaning
- Status (Present / Absence)

---

# ❓ What Type of Questions Can You Ask?

The system supports:

---

## 🔹 1. Record Lookup

Examples:

- What is the date of birth of Arjan Jha Crasto?
- What is the admission date of SIMS ID 12345?
- What year is John Smith in?

---

## 🔹 2. Aggregate Queries

Examples:

- How many students were born in March 2016?
- How many students are in Year 3?
- Count students with illness marks.
- How many authorised absences are recorded?

---

## 🔹 3. Attribute Lookup

Examples:

- What does mark code C mean?
- What is the meaning of attendance code I?

---

## 🔹 4. List Queries

Examples:

- List all students in Year 4.
- Show students in registration group A1.
- List students admitted in 2022.

---

# 🚀 How to Run

---

## Step 1: Install Ollama

Download and install from:

https://ollama.com

Verify installation:

