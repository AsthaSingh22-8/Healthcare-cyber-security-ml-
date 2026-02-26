import sqlite3
import os

# Check if database exists
if os.path.exists('users.db'):
    print("Database exists")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Check if tables exist
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    print(f"Tables: {tables}")
    
    # Check users
    try:
        c.execute("SELECT id, username, email FROM users")
        users = c.fetchall()
        print(f"Users in database: {users}")
    except Exception as e:
        print(f"Error reading users: {e}")
    
    conn.close()
else:
    print("Database doesn't exist")