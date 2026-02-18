import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
cursor = conn.cursor()

# Insert roles
roles = [
    ('admin', 'Full system access'),
    ('manager', 'Can manage inventory and view reports'),
    ('clerk', 'Can process sales and view stock')
]
cursor.executemany(
    "INSERT IGNORE INTO roles (name, description) VALUES (%s, %s)",
    roles
)

# Also insert movement types (needed for Module 3)
movement_types = [
    ('sale', 'Stock sold to customer', -1),
    ('receipt', 'Stock received from supplier', 1),
    ('adjustment', 'Manual stock adjustment', 1),
    ('return', 'Customer return', 1),
    ('damage', 'Damaged or expired stock', -1)
]
cursor.executemany(
    "INSERT IGNORE INTO movement_types (name, description, sign) VALUES (%s, %s, %s)",
    movement_types
)

conn.commit()
cursor.close()
conn.close()
print("✅ Roles and movement types inserted successfully.")