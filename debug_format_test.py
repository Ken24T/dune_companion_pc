#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, '.')
from app.data.crud import create_resource
from app.data.database import initialize_database
import sqlite3

test_db = r'tests\test_data\test_dune_companion.db'
os.makedirs(os.path.dirname(test_db), exist_ok=True)

# Initialize the database first
initialize_database(test_db)

# Create a resource to see the timestamp format
resource = create_resource(
    db_path=test_db,
    name='Test Resource',
    description='Test'
)

# Check the actual timestamps
conn = sqlite3.connect(test_db)
cur = conn.cursor()
result = cur.execute('SELECT name, created_at, updated_at FROM resource LIMIT 1').fetchone()
if result:
    print(f'Name: {result[0]}')
    print(f'Created: \'{result[1]}\'')
    print(f'Updated: \'{result[2]}\'')
    print(f'Created format matches ISO (T): {"T" in result[1]}')
    print(f'Created format matches space: {" " in result[1] and "T" not in result[1]}')
conn.close()
