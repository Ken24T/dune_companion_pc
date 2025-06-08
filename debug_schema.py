#!/usr/bin/env python3

import sqlite3

conn = sqlite3.connect(r'tests\test_data\test_dune_companion.db')
cur = conn.cursor()
result = cur.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="resource"').fetchone()
if result:
    print('Resource table schema:')
    print(result[0])
    print()
    
    # Check what the default value for created_at actually evaluates to
    test_result = cur.execute('SELECT strftime(\'%Y-%m-%d %H:%M:%f\', \'now\', \'utc\')').fetchone()
    print('Test space format:', test_result[0])
    
    test_result = cur.execute('SELECT datetime(\'now\', \'utc\')').fetchone()
    print('Default datetime(now, utc):', test_result[0])
    
conn.close()
