from mysql.connector import MySQLConnection
from typing import List, Dict, Optional
from datetime import date

def get_low_stock_alerts(conn: MySQLConnection) -> List[Dict]:
    """Fetch all low stock alerts from the low_stock_alerts view."""
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM low_stock_alerts ORDER BY quantity_in_stock ASC"
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    return results

def get_daily_sales_summary(conn: MySQLConnection, target_date: date) -> Optional[Dict]:
    """Get sales summary for a specific date from the daily_sales_summary view."""
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM daily_sales_summary WHERE transaction_date = %s"
    cursor.execute(query, (target_date,))
    result = cursor.fetchone()
    cursor.close()
    return result

def get_current_inventory(conn: MySQLConnection, active_only: bool = True) -> List[Dict]:
    """Fetch current inventory snapshot from the current_inventory view."""
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM current_inventory"
    params = []
    if active_only:
        query += " WHERE is_active = %s"
        params.append(True)
    query += " ORDER BY name"
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    cursor.close()
    return results

def get_product_performance(conn: MySQLConnection, days: int = 30) -> List[Dict]:
    """Fetch product performance (last 30 days sales) from the product_performance view."""
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM product_performance ORDER BY total_sold_30d DESC"
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    return results

def get_total_products_count(conn: MySQLConnection) -> int:
    """Get count of active products."""
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM products WHERE is_active = TRUE"
    cursor.execute(query)
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def get_total_stock_value(conn: MySQLConnection) -> float:
    """Calculate total value of current stock (cost price * quantity)."""
    cursor = conn.cursor()
    query = "SELECT SUM(cost_price * quantity_in_stock) FROM products WHERE is_active = TRUE"
    cursor.execute(query)
    value = cursor.fetchone()[0] or 0.0
    cursor.close()
    return value

def get_low_stock_count(conn: MySQLConnection) -> int:
    """Count of products with stock <= reorder_threshold."""
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM products WHERE quantity_in_stock <= reorder_threshold AND is_active = TRUE"
    cursor.execute(query)
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def get_out_of_stock_count(conn: MySQLConnection) -> int:
    """Count of products with zero stock."""
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM products WHERE quantity_in_stock = 0 AND is_active = TRUE"
    cursor.execute(query)
    count = cursor.fetchone()[0]
    cursor.close()
    return count