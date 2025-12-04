import sqlite3

DB_PATH = "../data/cspm.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("SELECT control_id FROM controls ORDER BY control_id")
ids = [row[0] for row in c.fetchall()]

print(f"DB Controls ({len(ids)}):")
print(", ".join(ids))

conn.close()
