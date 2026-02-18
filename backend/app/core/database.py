import mysql.connector.pooling
from .config import settings

db_config = {
    "pool_name": "smart_inventory_pool",
    "pool_size": 5,
    "host": settings.DB_HOST,
    "port": settings.DB_PORT,
    "database": settings.DB_NAME,
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
}

connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)

def get_db():
    """FastAPI dependency: yields a database connection."""
    conn = connection_pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()