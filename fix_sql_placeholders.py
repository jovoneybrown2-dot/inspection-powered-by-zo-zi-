#!/usr/bin/env python3
"""
Fix SQL placeholders from SQLite (?) to PostgreSQL (%s) syntax
"""
import re

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace ? with %s in SQL statements
# This regex finds SQL query strings and replaces ? with %s
# We need to be careful to only replace in SQL contexts

# Pattern 1: VALUES (...?) patterns
content = re.sub(r'VALUES\s*\(([^)]*\?[^)]*)\)',
                 lambda m: 'VALUES (' + m.group(1).replace('?', '%s') + ')',
                 content, flags=re.IGNORECASE)

# Pattern 2: INSERT OR IGNORE (SQLite specific)
content = re.sub(r'INSERT OR IGNORE', 'INSERT', content, flags=re.IGNORECASE)

# Pattern 3: Standalone ? in WHERE clauses, SET clauses, etc.
# Match patterns like "WHERE id = ?" or "SET name = ?"
content = re.sub(r'=\s*\?(?=\s|,|\))', '= %s', content)
content = re.sub(r'>\s*\?(?=\s|,|\))', '> %s', content)
content = re.sub(r'<\s*\?(?=\s|,|\))', '< %s', content)
content = re.sub(r'IN\s*\(\s*\?\s*\)', 'IN (%s)', content, flags=re.IGNORECASE)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed SQL placeholders in app.py")
print("Changed ? to %s for PostgreSQL compatibility")
