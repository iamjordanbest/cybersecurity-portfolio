import sqlite3

DB_PATH = "../data/cspm.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

ids = ['CIS-1.12', 'CIS-1.20', 'CIS-4.2']
for i in ids:
    c.execute("SELECT title FROM controls WHERE control_id = ?", (i,))
    row = c.fetchone()
    print(f"{i}: {row[0] if row else 'NOT FOUND'}")

conn.close()
