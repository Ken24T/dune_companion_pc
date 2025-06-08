#!/usr/bin/env python3

import sqlite3

conn = sqlite3.connect(':memory:')
cur = conn.cursor()

# Test the format strings
space_format_query = "SELECT strftime('%Y-%m-%d %H:%M:%f', 'now', 'utc')"
iso_format_query = "SELECT strftime('%Y-%m-%dT%H:%M:%f', 'now', 'utc')"

result = cur.execute(space_format_query).fetchone()
print('Space format result:', result[0])

result = cur.execute(iso_format_query).fetchone()
print('ISO format result:', result[0])

# Test what our database is actually using
db_format = "'%Y-%m-%d %H:%M:%f'"
test_query = f"SELECT strftime({db_format}, 'now', 'utc')"
print('Query:', test_query)
result = cur.execute(test_query).fetchone()
print('Current database format result:', result[0])

conn.close()
