from mysql.connector import MySQLConnection
from typing import List, Dict, Optional
from datetime import datetime
from ..core.security import hash_password

# ---------- User Management ----------
def get_all_users(conn: MySQLConnection) -> List[Dict]:
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT u.id, u.username, u.email, u.is_active, u.created_at, u.updated_at,
               GROUP_CONCAT(r.name) as roles
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    return results

def get_user_by_id_admin(conn: MySQLConnection, user_id: int) -> Optional[Dict]:
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT u.id, u.username, u.email, u.is_active, u.created_at, u.updated_at,
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

def create_user_admin(conn: MySQLConnection, user_data: Dict) -> int:
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
            user_data.get("is_active", True)
        ))
        user_id = cursor.lastrowid

        # Assign role
        role_name = user_data.get("role", "clerk").strip().lower()
        role_query = "SELECT id FROM roles WHERE LOWER(name) = %s"
        cursor.execute(role_query, (role_name,))
        role_row = cursor.fetchone()
        if role_row:
            assign_query = "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)"
            cursor.execute(assign_query, (user_id, role_row[0]))
        else:
            # fallback to clerk
            cursor.execute("SELECT id FROM roles WHERE LOWER(name) = 'clerk'")
            clerk_row = cursor.fetchone()
            if clerk_row:
                assign_query = "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)"
                cursor.execute(assign_query, (user_id, clerk_row[0]))

        conn.commit()
        return user_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()

def update_user_admin(conn: MySQLConnection, user_id: int, update_data: Dict) -> bool:
    cursor = conn.cursor()
    fields = []
    values = []
    if "username" in update_data and update_data["username"]:
        fields.append("username = %s")
        values.append(update_data["username"])
    if "email" in update_data and update_data["email"]:
        fields.append("email = %s")
        values.append(update_data["email"])
    if "password" in update_data and update_data["password"]:
        fields.append("password_hash = %s")
        values.append(hash_password(update_data["password"]))
    if "is_active" in update_data:
        fields.append("is_active = %s")
        values.append(update_data["is_active"])
    
    if fields:
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
        cursor.execute(query, tuple(values))
        conn.commit()
    
    # Update role if provided
    if "role" in update_data and update_data["role"]:
        # First delete existing roles
        cursor.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))
        # Insert new role
        role_name = update_data["role"].strip().lower()
        cursor.execute("SELECT id FROM roles WHERE LOWER(name) = %s", (role_name,))
        role_row = cursor.fetchone()
        if role_row:
            cursor.execute("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", (user_id, role_row[0]))
        conn.commit()
    
    affected = cursor.rowcount
    cursor.close()
    return affected > 0 or "role" in update_data

def delete_user_admin(conn: MySQLConnection, user_id: int) -> bool:
    # Soft delete: set is_active = FALSE
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active = FALSE WHERE id = %s", (user_id,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    return affected > 0

# ---------- System Settings ----------
def get_all_settings(conn: MySQLConnection) -> List[Dict]:
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.*, u.username as updated_by_username
        FROM system_settings s
        LEFT JOIN users u ON s.updated_by = u.id
        ORDER BY s.setting_key
    """)
    results = cursor.fetchall()
    cursor.close()
    return results

def get_setting(conn: MySQLConnection, key: str) -> Optional[str]:
    cursor = conn.cursor()
    cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = %s", (key,))
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else None

def create_setting(conn: MySQLConnection, key: str, value: str, description: str = None, updated_by: int = None) -> int:
    cursor = conn.cursor()
    query = """
        INSERT INTO system_settings (setting_key, setting_value, description, updated_by)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (key, value, description, updated_by))
    conn.commit()
    setting_id = cursor.lastrowid
    cursor.close()
    return setting_id

def update_setting(conn: MySQLConnection, key: str, value: str = None, description: str = None, updated_by: int = None) -> bool:
    cursor = conn.cursor()
    fields = []
    values = []
    if value is not None:
        fields.append("setting_value = %s")
        values.append(value)
    if description is not None:
        fields.append("description = %s")
        values.append(description)
    if updated_by is not None:
        fields.append("updated_by = %s")
        values.append(updated_by)
    if not fields:
        return False
    values.append(key)
    query = f"UPDATE system_settings SET {', '.join(fields)} WHERE setting_key = %s"
    cursor.execute(query, tuple(values))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    return affected > 0

def delete_setting(conn: MySQLConnection, key: str) -> bool:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM system_settings WHERE setting_key = %s", (key,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    return affected > 0

# ---------- Audit Log ----------
def get_audit_logs(
    conn: MySQLConnection,
    table_name: Optional[str] = None,
    user_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    operation: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT al.*, u.username as changed_by_username
        FROM audit_log al
        LEFT JOIN users u ON al.changed_by = u.id
        WHERE 1=1
    """
    params = []
    if table_name:
        query += " AND al.table_name = %s"
        params.append(table_name)
    if user_id:
        query += " AND al.changed_by = %s"
        params.append(user_id)
    if from_date:
        query += " AND al.changed_at >= %s"
        params.append(from_date)
    if to_date:
        query += " AND al.changed_at <= %s"
        params.append(to_date)
    if operation:
        query += " AND al.operation = %s"
        params.append(operation)
    query += " ORDER BY al.changed_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    for r in results:
        if r['old_data']:
            r['old_data'] = json.loads(r['old_data'])
        if r['new_data']:
            r['new_data'] = json.loads(r['new_data'])
    cursor.close()
    return results