import streamlit as st
from attendance_system import run_query

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Student Attendance QA System",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Student Attendance Database QA System")
st.markdown("Ask natural language questions about student attendance data.")

# ==========================================================
# SESSION STATE INIT
# ==========================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ==========================================================
# CHAT DISPLAY
# ==========================================================

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================================
# USER INPUT
# ==========================================================

user_input = st.chat_input("Ask a question about students...")

if user_input:

    # Show user message
    st.session_state.chat_history.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    # Process query
    with st.chat_message("assistant"):
        with st.spinner("Processing query..."):

            try:
                sql, result, answer = run_query(user_input)

                # Show answer
                st.markdown("### ✅ Answer")
                st.write(answer)

                # Expandable SQL Debug Section
                with st.expander("🔎 View SQL & Raw Result"):
                    st.markdown("**Generated SQL:**")
                    st.code(sql, language="sql")

                    st.markdown("**Raw Result:**")
                    st.write(result)

                # Save assistant response
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": answer}
                )

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)

                st.session_state.chat_history.append(
                    {"role": "assistant", "content": error_msg}
                )

# ==========================================================
# SIDEBAR INFO
# ==========================================================

st.sidebar.title("📊 Database Info")

st.sidebar.markdown("""
### Available Tables

**1️⃣ detailed_attendance**
- Raw session-level attendance
- DOB, Gender, Standard, Mark, etc.

**2️⃣ attendance_summary**
- Yearly aggregated attendance totals
- Present/Absent codes

**3️⃣ attendance_mark_description**
- Meaning of attendance codes
""")

st.sidebar.markdown("""
### Example Questions

- How many students are in 3rd standard?
- What is the DOB of Arjan Jha Crasto?
- Number of students born in 2016?
- How many students were absent in March 2024?
- What does mark 'O' mean?
""")
