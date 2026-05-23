import sqlite3
import os

# Check all possible locations
paths_to_check = [
    'portal.db',
    'instance/portal.db',
]

for path in paths_to_check:
    if os.path.exists(path):
        print(f"\nChecking: {path}")
        conn   = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # List all tables first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables found: {tables}")
        
        if tables:
            print("\n===== USERS =====")
            cursor.execute("SELECT id, username, role FROM users")
            for row in cursor.fetchall():
                print(row)

            print("\n===== MARKS =====")
            cursor.execute("SELECT * FROM marks")
            for row in cursor.fetchall():
                print(row)
        
        conn.close()