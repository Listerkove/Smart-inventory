from mysql.connector import MySQLConnection
from typing import List, Dict, Optional
from datetime import date, timedelta

def get_sales_report(
    conn: MySQLConnection,
    from_date: date,
    to_date: date,
    group_by: str = "day"
) -> List[Dict]:
    """Get sales data grouped by day/week/month."""
    cursor = conn.cursor(dictionary=True)
    
    # Determine SQL grouping
    if group_by == "day":
        group_expr = "transaction_date"
        order = "transaction_date"
    elif group_by == "week":
        group_expr = "DATE_SUB(transaction_date, INTERVAL WEEKDAY(transaction_date) DAY)"
        order = "week_start"
    else:  # month
        group_expr = "DATE_FORMAT(transaction_date, '%Y-%m-01')"
        order = "month_start"
    
    query = f"""
        SELECT
            {group_expr} AS period,
            COUNT(DISTINCT id) AS transaction_count,
            COALESCE(SUM(total_items_sold), 0) AS items_sold,
            COALESCE(SUM(total_revenue), 0) AS revenue
        FROM daily_sales_summary
        WHERE transaction_date BETWEEN %s AND %s
        GROUP BY period
        ORDER BY {order}
    """
    cursor.execute(query, (from_date, to_date))
    results = cursor.fetchall()
    cursor.close()
    return results

def get_stock_movement_report(
    conn: MySQLConnection,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    product_sku: Optional[str] = None,
    movement_type: Optional[str] = None,
    limit: int = 1000
) -> List[Dict]:
    """Get stock movements with optional filters."""
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT
            sm.id,
            sm.created_at AS datetime,
            p.sku AS product_sku,
            p.name AS product_name,
            mt.name AS movement_type,
            sm.quantity,
            sm.previous_quantity,
            sm.new_quantity,
            sm.reason,
            u.username AS performed_by
        FROM stock_movements sm
        JOIN products p ON sm.product_sku = p.sku
        JOIN movement_types mt ON sm.movement_type_id = mt.id
        LEFT JOIN users u ON sm.created_by = u.id
        WHERE 1=1
    """
    params = []
    if from_date:
        query += " AND DATE(sm.created_at) >= %s"
        params.append(from_date)
    if to_date:
        query += " AND DATE(sm.created_at) <= %s"
        params.append(to_date)
    if product_sku:
        query += " AND p.sku = %s"
        params.append(product_sku)
    if movement_type:
        query += " AND mt.name = %s"
        params.append(movement_type)
    query += " ORDER BY sm.created_at DESC LIMIT %s"
    params.append(limit)
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    cursor.close()
    return results

def get_product_performance_report(
    conn: MySQLConnection,
    sort_by: str = "total_sold_30d",
    limit: int = 50
) -> List[Dict]:
    """Get product performance from the product_performance view."""
    cursor = conn.cursor(dictionary=True)
    
    # Map sort_by to column
    sort_col = {
        "total_sold_30d": "total_sold_30d DESC",
        "avg_daily_sales": "avg_daily_sales DESC",
        "stock": "quantity_in_stock DESC",
        "slow_movers": "total_sold_30d ASC",
        "name": "name"
    }.get(sort_by, "total_sold_30d DESC")
    
    query = f"""
        SELECT
            sku,
            name,
            category_name AS category,
            quantity_in_stock AS current_stock,
            total_sold_30d,
            avg_daily_sales,
            CASE
                WHEN quantity_in_stock > 0 THEN ROUND(total_sold_30d / quantity_in_stock, 2)
                ELSE NULL
            END AS turnover_rate,
            status
        FROM product_performance
        ORDER BY {sort_col}
        LIMIT %s
    """
    cursor.execute(query, (limit,))
    results = cursor.fetchall()
    cursor.close()
    return results

def get_distinct_movement_types(conn: MySQLConnection) -> List[str]:
    """Get all distinct movement type names for filter dropdown."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM movement_types ORDER BY name")
    results = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return results

def get_distinct_product_skus(conn: MySQLConnection) -> List[Dict]:
    """Get product SKUs and names for filter dropdown."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT sku, name FROM products WHERE is_active = TRUE ORDER BY name")
    results = cursor.fetchall()
    cursor.close()
    return results