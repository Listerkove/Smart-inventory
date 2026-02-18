from mysql.connector import MySQLConnection
from typing import List, Optional, Dict, Any

# -------------------- CATEGORIES --------------------
def create_category(conn: MySQLConnection, name: str, description: str = None) -> int:
    cursor = conn.cursor()
    query = "INSERT INTO categories (name, description) VALUES (%s, %s)"
    cursor.execute(query, (name, description))
    conn.commit()
    category_id = cursor.lastrowid
    cursor.close()
    return category_id

def get_all_categories(conn: MySQLConnection) -> List[Dict]:
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id, name, description, created_at FROM categories ORDER BY name"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result

def get_category_by_id(conn: MySQLConnection, category_id: int) -> Optional[Dict]:
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id, name, description, created_at FROM categories WHERE id = %s"
    cursor.execute(query, (category_id,))
    result = cursor.fetchone()
    cursor.close()
    return result

# -------------------- SUPPLIERS --------------------
def create_supplier(conn: MySQLConnection, supplier_data: Dict) -> int:
    cursor = conn.cursor()
    query = """
        INSERT INTO suppliers (name, contact_person, phone, email, address)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (
        supplier_data["name"],
        supplier_data.get("contact_person"),
        supplier_data.get("phone"),
        supplier_data.get("email"),
        supplier_data.get("address")
    ))
    conn.commit()
    supplier_id = cursor.lastrowid
    cursor.close()
    return supplier_id

def get_all_suppliers(conn: MySQLConnection) -> List[Dict]:
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id, name, contact_person, phone, email, address, created_at FROM suppliers ORDER BY name"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result

def get_supplier_by_id(conn: MySQLConnection, supplier_id: int) -> Optional[Dict]:
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM suppliers WHERE id = %s"
    cursor.execute(query, (supplier_id,))
    result = cursor.fetchone()
    cursor.close()
    return result

# -------------------- PRODUCTS --------------------
def create_product(conn: MySQLConnection, product_data: Dict) -> str:
    cursor = conn.cursor()
    query = """
        INSERT INTO products (sku, barcode, name, category_id, supplier_id,
                              cost_price, selling_price, quantity_in_stock, reorder_threshold, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (
        product_data["sku"],
        product_data["barcode"],
        product_data["name"],
        product_data.get("category_id"),
        product_data.get("supplier_id"),
        product_data["cost_price"],
        product_data["selling_price"],
        product_data.get("quantity_in_stock", 0),
        product_data.get("reorder_threshold", 5),
        product_data.get("is_active", True)
    ))
    conn.commit()
    cursor.close()
    return product_data["sku"]

def get_product_by_sku(conn: MySQLConnection, sku: str) -> Optional[Dict]:
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT p.*, 
               c.name as category_name, 
               s.name as supplier_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.sku = %s
    """
    cursor.execute(query, (sku,))
    product = cursor.fetchone()
    cursor.close()
    return product

def get_product_by_barcode(conn: MySQLConnection, barcode: str) -> Optional[Dict]:
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM products WHERE barcode = %s"
    cursor.execute(query, (barcode,))
    product = cursor.fetchone()
    cursor.close()
    return product

def get_all_products(
    conn: MySQLConnection, 
    skip: int = 0, 
    limit: int = 100,
    active_only: bool = True
) -> List[Dict]:
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT p.*, 
               c.name as category_name, 
               s.name as supplier_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE 1=1
    """
    params = []
    if active_only:
        query += " AND p.is_active = %s"
        params.append(True)
    query += " ORDER BY p.name LIMIT %s OFFSET %s"
    params.extend([limit, skip])
    cursor.execute(query, tuple(params))
    products = cursor.fetchall()
    cursor.close()
    return products

def update_product(conn: MySQLConnection, sku: str, update_data: Dict) -> bool:
    cursor = conn.cursor()
    fields = []
    values = []
    for key, value in update_data.items():
        if value is not None and key in ['name', 'barcode', 'category_id', 'supplier_id', 
                                         'cost_price', 'selling_price', 'reorder_threshold', 'is_active']:
            fields.append(f"{key} = %s")
            values.append(value)
    if not fields:
        return False
    values.append(sku)
    query = f"UPDATE products SET {', '.join(fields)} WHERE sku = %s"
    cursor.execute(query, tuple(values))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    return affected > 0

def delete_product(conn: MySQLConnection, sku: str) -> bool:
    # Soft delete: set is_active = FALSE
    cursor = conn.cursor()
    query = "UPDATE products SET is_active = FALSE WHERE sku = %s"
    cursor.execute(query, (sku,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    return affected > 0