import sqlite3

# ===== CONFIG =====
db_path = r"local_database_attendance.db"   # <-- change this
output_file = r"Tables.txt"
# ==================

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all user tables (skip internal sqlite_ tables)
cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table' AND name NOT LIKE 'sqlite_%';
""")
tables = [t[0] for t in cursor.fetchall()]

with open(output_file, "w", encoding="utf-8") as f:
    for table in tables:
        f.write(f"\n\n{'='*80}\n")
        f.write(f"TABLE: {table}\n")
        f.write(f"{'='*80}\n\n")

        # Fetch column names
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [col[1] for col in cursor.fetchall()]
        f.write(" | ".join(columns) + "\n")
        f.write("-" * 120 + "\n")

        # Fetch rows
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()

        for row in rows:
            row_text = " | ".join(str(item) for item in row)
            f.write(row_text + "\n")

        if not rows:
            f.write("(No rows)\n")

print(f"Done! All tables exported to: {output_file}")

conn.close()
