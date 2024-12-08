import sqlite3
import os
import sys
from dotenv import load_dotenv

load_dotenv()

SQLITE_DATABASE_PATH = os.getenv("DB_PATH")

# Make sure the file exists
if (not os.path.exists(SQLITE_DATABASE_PATH)):
    print(f"Error: SQLite file not found at {SQLITE_DATABASE_PATH}")
    sys.exit(1)

# Connect to your SQLite database file.
conn = sqlite3.connect(SQLITE_DATABASE_PATH)

# Get a cursor object
cur = conn.cursor()

# Add a dummy record to the api_responses table
cur.execute("INSERT INTO api_responses (response_json) VALUES ('{\"example\": \"data\"}');")

# Fetch the record
cur.execute("SELECT * FROM api_responses;")
print(cur.fetchall())

# Remove the dummy record
cur.execute("DELETE FROM api_responses WHERE response_json = '{\"example\": \"data\"}';")

print("Test complete")

# Close the connection
conn.close()