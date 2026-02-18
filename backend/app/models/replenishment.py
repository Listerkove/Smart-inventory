from mysql.connector import MySQLConnection
from typing import List, Dict, Optional
from datetime import datetime

def generate_suggestions(
    conn: MySQLConnection,
    lookback_days: int = 30,
    forecast_days: int = 7,
    safety_stock_factor: float = 1.5
) -> None:
    """Call the stored procedure to generate replenishment suggestions."""
    cursor = conn.cursor()
    cursor.callproc(
        "GenerateReplenishmentSuggestions",
        (lookback_days, forecast_days, safety_stock_factor)
    )
    conn.commit()
    cursor.close()

def get_suggestions(
    conn: MySQLConnection,
    active_only: bool = True,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """Fetch replenishment suggestions with product details."""
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT 
            rs.*,
            p.name AS product_name,
            p.barcode AS product_barcode
        FROM replenishment_suggestions rs
        JOIN products p ON rs.product_sku = p.sku
        WHERE 1=1
    """
    params = []
    if active_only:
        query += " AND rs.is_acted_upon = FALSE"
    query += " ORDER BY rs.date_generated DESC, rs.suggested_quantity DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    cursor.close()
    return results

def mark_as_acted_upon(conn: MySQLConnection, suggestion_id: int) -> bool:
    """Mark a suggestion as acted upon (accepted)."""
    cursor = conn.cursor()
    query = """
        UPDATE replenishment_suggestions
        SET is_acted_upon = TRUE, acted_upon_at = %s
        WHERE id = %s
    """
    cursor.execute(query, (datetime.now(), suggestion_id))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    return affected > 0

def ignore_suggestion(conn: MySQLConnection, suggestion_id: int) -> bool:
    """Delete or mark as ignored (we'll just delete for simplicity)."""
    cursor = conn.cursor()
    query = "DELETE FROM replenishment_suggestions WHERE id = %s"
    cursor.execute(query, (suggestion_id,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    return affected > 0