from mysql.connector import MySQLConnection
from typing import Optional, Dict, Any
from ..core.security import hash_password

def create_user(conn: MySQLConnection, user_data: Dict[str, Any]) -> int:
    cursor = conn.cursor()
    try:
        # Insert user
        query = """
            INSERT INTO users (username, email, password_hash, is_active)
            VALUES (%s, %s, %s, %s)
        """
        password_hash = hash_password(user_data["password"])
        cursor.execute(query, (
            user_data["username"],
            user_data["email"],
            password_hash,
            True
        ))
        user_id = cursor.lastrowid

        # --- FIXED: Case-insensitive role lookup + fallback ---
        role_name = user_data.get("role", "clerk").strip().lower()
        
        # Lookup role ID (case-insensitive)
        role_query = "SELECT id FROM roles WHERE LOWER(name) = %s"
        cursor.execute(role_query, (role_name,))
        role_row = cursor.fetchone()
        
        if role_row:
            role_id = role_row[0]
            assign_query = "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)"
            cursor.execute(assign_query, (user_id, role_id))
        else:
            # Fallback: assign 'clerk' if role not found
            cursor.execute("SELECT id FROM roles WHERE LOWER(name) = 'clerk'")
            clerk_row = cursor.fetchone()
            if clerk_row:
                assign_query = "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)"
                cursor.execute(assign_query, (user_id, clerk_row[0]))
        # -------------------------------------------------------

        conn.commit()
        return user_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()

def get_user_by_username(conn: MySQLConnection, username: str) -> Optional[Dict]:
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT u.id, u.username, u.email, u.password_hash, u.is_active,
               GROUP_CONCAT(r.name) as roles
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        WHERE u.username = %s
        GROUP BY u.id
    """
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    cursor.close()
    return user

def get_user_by_id(conn: MySQLConnection, user_id: int) -> Optional[Dict]:
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT u.id, u.username, u.email, u.is_active,
               GROUP_CONCAT(r.name) as roles
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        WHERE u.id = %s
        GROUP BY u.id
    """
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return user