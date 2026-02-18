from mysql.connector import MySQLConnection
from typing import List, Dict, Optional

def get_movement_type_id(conn: MySQLConnection, movement_name: str) -> Optional[int]:
    """Get movement_type_id by name (sale, receipt, adjustment, return, damage)."""
    cursor = conn.cursor()
    query = "SELECT id FROM movement_types WHERE name = %s"
    cursor.execute(query, (movement_name,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

def create_stock_receipt(
    conn: MySQLConnection,
    sku: str,
    quantity: int,
    reference_id: Optional[str],
    user_id: int
) -> int:
    """Call the stored procedure AddStockReceipt()."""
    cursor = conn.cursor()
    cursor.callproc("AddStockReceipt", (sku, quantity, reference_id, user_id))
    conn.commit()
    # Fetch the last inserted movement ID
    cursor.execute("SELECT LAST_INSERT_ID()")
    movement_id = cursor.fetchone()[0]
    cursor.close()
    return movement_id

def create_stock_adjustment(
    conn: MySQLConnection,
    sku: str,
    quantity: int,
    movement_type: str,  # 'adjustment', 'damage', 'return'
    reason: Optional[str],
    user_id: int
) -> int:
    """Manual stock adjustment – insert directly into stock_movements.
       The trigger `before_stock_movement_insert` will handle stock update.
    """
    movement_type_id = get_movement_type_id(conn, movement_type)
    if not movement_type_id:
        raise ValueError(f"Invalid movement type: {movement_type}")

    cursor = conn.cursor()
    query = """
        INSERT INTO stock_movements
            (product_sku, movement_type_id, quantity, reason, created_by)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (sku, movement_type_id, quantity, reason, user_id))
    conn.commit()
    movement_id = cursor.lastrowid
    cursor.close()
    return movement_id

def get_stock_movements(
    conn: MySQLConnection,
    product_sku: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """Get stock movement history, optionally filtered by product."""
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT 
            sm.id,
            p.name as product_name,
            p.sku as product_sku,
            mt.name as movement_type,
            sm.quantity,
            sm.previous_quantity,
            sm.new_quantity,
            sm.reference_id,
            sm.reason,
            u.username as performed_by,
            sm.created_at
        FROM stock_movements sm
        JOIN products p ON sm.product_sku = p.sku
        JOIN movement_types mt ON sm.movement_type_id = mt.id
        LEFT JOIN users u ON sm.created_by = u.id
        WHERE 1=1
    """
    params = []
    if product_sku:
        query += " AND sm.product_sku = %s"
        params.append(product_sku)
    query += " ORDER BY sm.created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    cursor.close()
    return results

def get_product_stock_level(conn: MySQLConnection, sku: str) -> Optional[int]:
    """Get current quantity in stock for a product."""
    cursor = conn.cursor()
    query = "SELECT quantity_in_stock FROM products WHERE sku = %s"
    cursor.execute(query, (sku,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None