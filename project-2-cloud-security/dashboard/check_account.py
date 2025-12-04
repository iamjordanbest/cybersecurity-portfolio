import sqlite3

DB_PATH = "../data/cspm.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Check what account_id is in the latest assessment
c.execute('SELECT account_id FROM assessments ORDER BY timestamp DESC LIMIT 1')
result = c.fetchone()

print(f"Current account_id in database: {result[0] if result else 'None'}")

conn.close()
