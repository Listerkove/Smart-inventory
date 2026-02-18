# app/models/integration.py
import json
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from mysql.connector import MySQLConnection

# ----------------------------------------------------------------------
# API Keys
# ----------------------------------------------------------------------

def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)

def create_api_key(
    conn: MySQLConnection,
    name: str,
    created_by: int,
    expires_in_days: Optional[int] = None
) -> Dict:
    """Create a new API key and return the full record."""
    cursor = conn.cursor(dictionary=True)
    api_key = generate_api_key()
    expires_at = None
    if expires_in_days:
        expires_at = datetime.now() + timedelta(days=expires_in_days)
    
    query = """
        INSERT INTO api_keys (name, api_key, expires_at, created_by)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (name, api_key, expires_at, created_by))
    conn.commit()
    key_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM api_keys WHERE id = %s", (key_id,))
    result = cursor.fetchone()
    cursor.close()
    return result

def get_api_keys(conn: MySQLConnection) -> List[Dict]:
    """Get all API keys."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM api_keys ORDER BY created_at DESC")
    results = cursor.fetchall()
    cursor.close()
    return results

def get_api_key_by_id(conn: MySQLConnection, key_id: int) -> Optional[Dict]:
    """Get a specific API key by ID."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM api_keys WHERE id = %s", (key_id,))
    result = cursor.fetchone()
    cursor.close()
    return result

def revoke_api_key(conn: MySQLConnection, key_id: int) -> bool:
    """Soft delete (deactivate) an API key."""
    cursor = conn.cursor()
    cursor.execute("UPDATE api_keys SET is_active = FALSE WHERE id = %s", (key_id,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    return affected > 0

def regenerate_api_key(conn: MySQLConnection, key_id: int) -> Optional[Dict]:
    """Generate a new key for an existing entry."""
    cursor = conn.cursor(dictionary=True)
    new_key = generate_api_key()
    cursor.execute(
        "UPDATE api_keys SET api_key = %s, last_used_at = NULL WHERE id = %s",
        (new_key, key_id)
    )
    conn.commit()
    cursor.execute("SELECT * FROM api_keys WHERE id = %s", (key_id,))
    result = cursor.fetchone()
    cursor.close()
    return result

def validate_api_key(conn: MySQLConnection, api_key: str) -> Optional[Dict]:
    """Check if API key is valid and not expired. Update last_used_at."""
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT * FROM api_keys
        WHERE api_key = %s AND is_active = TRUE
        AND (expires_at IS NULL OR expires_at > NOW())
    """
    cursor.execute(query, (api_key,))
    key = cursor.fetchone()
    if key:
        # Update last used
        cursor.execute("UPDATE api_keys SET last_used_at = NOW() WHERE id = %s", (key['id'],))
        conn.commit()
    cursor.close()
    return key

# ----------------------------------------------------------------------
# Webhooks
# ----------------------------------------------------------------------

def create_webhook(
    conn: MySQLConnection,
    data: Dict,
    created_by: int
) -> int:
    """Create a new webhook and return its ID."""
    cursor = conn.cursor()
    query = """
        INSERT INTO webhooks (name, url, events, secret, created_by)
        VALUES (%s, %s, %s, %s, %s)
    """
    events_json = json.dumps(data['events'])
    cursor.execute(query, (
        data['name'],
        str(data['url']),
        events_json,
        data.get('secret'),
        created_by
    ))
    conn.commit()
    webhook_id = cursor.lastrowid
    cursor.close()
    return webhook_id

def get_webhooks(conn: MySQLConnection) -> List[Dict]:
    """Get all webhooks with parsed events."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM webhooks ORDER BY created_at DESC")
    results = cursor.fetchall()
    for w in results:
        w['events'] = json.loads(w['events'])
    cursor.close()
    return results

def get_webhook_by_id(conn: MySQLConnection, webhook_id: int) -> Optional[Dict]:
    """Get a specific webhook by ID."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM webhooks WHERE id = %s", (webhook_id,))
    webhook = cursor.fetchone()
    if webhook:
        webhook['events'] = json.loads(webhook['events'])
    cursor.close()
    return webhook

def update_webhook(
    conn: MySQLConnection,
    webhook_id: int,
    update_data: Dict
) -> bool:
    """Update an existing webhook."""
    cursor = conn.cursor()
    fields = []
    values = []
    for key, value in update_data.items():
        if value is not None and key in ['name', 'url', 'secret', 'is_active']:
            fields.append(f"{key} = %s")
            values.append(value)
        elif key == 'events' and value is not None:
            fields.append("events = %s")
            values.append(json.dumps(value))
    if not fields:
        return False
    values.append(webhook_id)
    query = f"UPDATE webhooks SET {', '.join(fields)} WHERE id = %s"
    cursor.execute(query, tuple(values))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    return affected > 0

def delete_webhook(conn: MySQLConnection, webhook_id: int) -> bool:
    """Permanently delete a webhook."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM webhooks WHERE id = %s", (webhook_id,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    return affected > 0

# ----------------------------------------------------------------------
# Webhook Deliveries
# ----------------------------------------------------------------------

def log_webhook_delivery(
    conn: MySQLConnection,
    webhook_id: int,
    event: str,
    payload: Dict,
    response_status: Optional[int],
    response_body: Optional[str],
    success: bool
) -> int:
    """Record a webhook delivery attempt."""
    cursor = conn.cursor()
    query = """
        INSERT INTO webhook_deliveries (webhook_id, event, payload, response_status, response_body, success)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (
        webhook_id,
        event,
        json.dumps(payload),
        response_status,
        response_body,
        success
    ))
    conn.commit()
    log_id = cursor.lastrowid
    cursor.close()
    return log_id

def get_recent_deliveries(
    conn: MySQLConnection,
    limit: int = 20,
    webhook_id: Optional[int] = None
) -> List[Dict]:
    """Get recent webhook deliveries, optionally filtered by webhook."""
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT wd.*, w.name as webhook_name
        FROM webhook_deliveries wd
        JOIN webhooks w ON wd.webhook_id = w.id
    """
    params = []
    if webhook_id:
        query += " WHERE wd.webhook_id = %s"
        params.append(webhook_id)
    query += " ORDER BY wd.attempted_at DESC LIMIT %s"
    params.append(limit)
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    for r in results:
        r['payload'] = json.loads(r['payload'])
    cursor.close()
    return results

# ----------------------------------------------------------------------
# Webhook Trigger (for background use)
# ----------------------------------------------------------------------

def trigger_webhooks(conn: MySQLConnection, event: str, payload: Dict):
    """
    Find all active webhooks subscribed to this event and send notifications.
    This is a stub – actual sending should be done asynchronously (e.g., via background tasks).
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM webhooks WHERE is_active = TRUE")
    webhooks = cursor.fetchall()
    cursor.close()
    
    for w in webhooks:
        events = json.loads(w['events'])
        if event in events:
            # In production, send the webhook asynchronously (e.g., using httpx, aiohttp, or Celery)
            # For now, we just log that it would be sent.
            print(f"🔔 Would send webhook '{w['name']}' for event '{event}' to {w['url']}")
            # Optionally, you can implement synchronous sending here, but be careful not to block.
            # Example using requests (add to requirements):
            # import requests
            # try:
            #     headers = {'Content-Type': 'application/json'}
            #     if w['secret']:
            #         headers['X-Webhook-Secret'] = w['secret']
            #     resp = requests.post(w['url'], json=payload, headers=headers, timeout=5)
            #     success = resp.status_code >= 200 and resp.status_code < 300
            #     log_webhook_delivery(conn, w['id'], event, payload, resp.status_code, resp.text, success)
            # except Exception as e:
            #     log_webhook_delivery(conn, w['id'], event, payload, None, str(e), False)