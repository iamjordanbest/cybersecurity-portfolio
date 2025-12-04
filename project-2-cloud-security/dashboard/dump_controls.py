import sqlite3
import pandas as pd

DB_PATH = "../data/cspm.db"
conn = sqlite3.connect(DB_PATH)

df = pd.read_sql_query("SELECT control_id, title, category FROM controls ORDER BY control_id", conn)
print(df.to_string())

conn.close()
