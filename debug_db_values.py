#!/usr/bin/env python3

import sqlite3
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# from app.data.database import get_db_connection

test_db = r'C:\repos\dune_companion_pc\tests\test_data\test_dune_companion.db'

if os.path.exists(test_db):
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    
    # Check if there are any resources
    result = cur.execute("SELECT name, created_at, updated_at FROM resource LIMIT 3").fetchall()
    print("Current database values:")
    for row in result:
        print(f"  Name: {row[0]}, Created: '{row[1]}', Updated: '{row[2]}'")
    
    # Check what the schema is for table creation
    result = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='resource'").fetchone()
    if result:
        print("\nCurrent resource table schema:")
        print(result[0])
    
    conn.close()
else:
    print(f"Test database not found at: {test_db}")
