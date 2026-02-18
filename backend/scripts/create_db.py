import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    cursor = conn.cursor()
    
    # Read and execute schema file
    with open('scripts/smart_inventory_schema.sql', 'r') as f:
        sql_script = f.read()
    
    # Split by semicolon and execute each statement
    for statement in sql_script.split(';'):
        if statement.strip():
            cursor.execute(statement)
    
    cursor.close()
    conn.close()
    print("✅ Database schema created successfully.")

if __name__ == "__main__":
    create_database()