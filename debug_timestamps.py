#!/usr/bin/env python3

import sqlite3
import os
from datetime import datetime, timezone

# Create a test database
test_db_path = "debug_timestamps.db"

# Delete if exists
if os.path.exists(test_db_path):
    os.remove(test_db_path)

# Create and test
conn = sqlite3.connect(test_db_path)
cursor = conn.cursor()

# Test different timestamp formats
cursor.execute("""
    CREATE TABLE test_timestamps (
        id INTEGER PRIMARY KEY,
        space_format TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'utc')),
        iso_format TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now', 'utc')),
        seconds_format TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now', 'utc'))
    )
""")

# Insert a record
cursor.execute("INSERT INTO test_timestamps (id) VALUES (1)")

# Read back the values
cursor.execute("SELECT * FROM test_timestamps WHERE id = 1")
row = cursor.fetchone()

print("Database timestamp formats:")
print(f"Space format UTC: {row[1]}")
print(f"ISO format UTC: {row[2]}")
print(f"Seconds format UTC: {row[3]}")

print(f"\nPython current time (UTC): {datetime.now(timezone.utc).isoformat()}")
print(f"Python current time (local): {datetime.now().isoformat()}")

# Test parsing the space format
try:
    parsed = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f')
    print(f"Successfully parsed space format: {parsed}")
except ValueError as e:
    print(f"Failed to parse space format: {e}")

# Test parsing the ISO format
try:
    parsed = datetime.strptime(row[2], '%Y-%m-%dT%H:%M:%S.%f')
    print(f"Successfully parsed ISO format: {parsed}")
except ValueError as e:
    print(f"Failed to parse ISO format: {e}")

conn.close()
os.remove(test_db_path)
