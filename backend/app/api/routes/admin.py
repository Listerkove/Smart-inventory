from fastapi import APIRouter, Depends, HTTPException, Query, status
from mysql.connector import MySQLConnection
from typing import List, Optional
from datetime import datetime, date 

from ...schemas.admin import (
    UserAdminCreate, UserAdminUpdate, UserAdminResponse,
    SettingCreate, SettingUpdate, SettingResponse,
    AuditLogEntry, AuditLogFilter
)
from ...schemas.product import CategoryResponse, CategoryCreate
from ...schemas.inventory import MovementTypeResponse
from ...models import admin as admin_model
from ...models import product as product_model
from ...models import stock_movement as movement_model
from ...core.database import get_db
from ...api.dependencies import get_current_active_manager  # managers can also access admin? We'll use admin-only for now, but you can change.

# For stricter admin-only, define:
async def get_current_admin(current_user = Depends(get_current_active_manager)):
    roles = current_user.get("roles", "")
    if "admin" not in roles:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

router = APIRouter(prefix="/admin", tags=["Admin"])

# ---------- User Management ----------
@router.get("/users", response_model=List[UserAdminResponse])
def get_users(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    return admin_model.get_all_users(conn)

@router.get("/users/{user_id}", response_model=UserAdminResponse)
def get_user(
    user_id: int,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    user = admin_model.get_user_by_id_admin(conn, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/users", response_model=UserAdminResponse, status_code=201)
def create_user(
    user_data: UserAdminCreate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    # Check if username exists
    from ...models.user import get_user_by_username
    if get_user_by_username(conn, user_data.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    user_id = admin_model.create_user_admin(conn, user_data.model_dump())
    return admin_model.get_user_by_id_admin(conn, user_id)

@router.put("/users/{user_id}", response_model=UserAdminResponse)
def update_user(
    user_id: int,
    user_update: UserAdminUpdate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    existing = admin_model.get_user_by_id_admin(conn, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    success = admin_model.update_user_admin(conn, user_id, user_update.dict(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=500, detail="Update failed")
    return admin_model.get_user_by_id_admin(conn, user_id)

@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    existing = admin_model.get_user_by_id_admin(conn, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    if existing['username'] == current_user['username']:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    success = admin_model.delete_user_admin(conn, user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Delete failed")
    return None

# ---------- System Settings ----------
@router.get("/settings", response_model=List[SettingResponse])
def get_settings(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    return admin_model.get_all_settings(conn)

@router.get("/settings/{key}", response_model=SettingResponse)
def get_setting(
    key: str,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    settings = admin_model.get_all_settings(conn)
    setting = next((s for s in settings if s['setting_key'] == key), None)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@router.post("/settings", response_model=SettingResponse, status_code=201)
def create_setting(
    setting: SettingCreate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    # Check if exists
    existing = admin_model.get_setting(conn, setting.key)
    if existing is not None:
        raise HTTPException(status_code=400, detail="Setting key already exists")
    setting_id = admin_model.create_setting(conn, setting.key, setting.value, setting.description, current_user['id'])
    # Return full setting
    settings = admin_model.get_all_settings(conn)
    return next(s for s in settings if s['id'] == setting_id)

@router.put("/settings/{key}", response_model=SettingResponse)
def update_setting(
    key: str,
    setting_update: SettingUpdate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    success = admin_model.update_setting(
        conn, key,
        value=setting_update.value,
        description=setting_update.description,
        updated_by=current_user['id']
    )
    if not success:
        raise HTTPException(status_code=404, detail="Setting not found or no changes")
    settings = admin_model.get_all_settings(conn)
    setting = next((s for s in settings if s['setting_key'] == key), None)
    return setting

@router.delete("/settings/{key}", status_code=204)
def delete_setting(
    key: str,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    success = admin_model.delete_setting(conn, key)
    if not success:
        raise HTTPException(status_code=404, detail="Setting not found")
    return None

# ---------- Category Management (from product module) ----------
@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    return product_model.get_all_categories(conn)

@router.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(
    category: CategoryCreate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    cat_id = product_model.create_category(conn, category.name, category.description)
    return product_model.get_category_by_id(conn, cat_id)

@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category: CategoryCreate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    existing = product_model.get_category_by_id(conn, category_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Category not found")
    # We need an update function in product model – add if not present
    # For now, we'll assume product_model has update_category
    # If not, implement similarly to supplier update
    cursor = conn.cursor()
    cursor.execute("UPDATE categories SET name=%s, description=%s WHERE id=%s",
                   (category.name, category.description, category_id))
    conn.commit()
    cursor.close()
    return product_model.get_category_by_id(conn, category_id)

@router.delete("/categories/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    # Check if any product uses this category
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products WHERE category_id = %s", (category_id,))
    count = cursor.fetchone()[0]
    if count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete category with existing products")
    cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    if not affected:
        raise HTTPException(status_code=404, detail="Category not found")
    return None

# ---------- Movement Type Management ----------
@router.get("/movement-types", response_model=List[MovementTypeResponse])
def get_movement_types(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, description, sign FROM movement_types ORDER BY name")
    types = cursor.fetchall()
    cursor.close()
    return types

@router.post("/movement-types", response_model=MovementTypeResponse, status_code=201)
def create_movement_type(
    mt: MovementTypeResponse,  # reuse schema
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO movement_types (name, description, sign) VALUES (%s, %s, %s)",
                   (mt.name, mt.description, mt.sign))
    conn.commit()
    type_id = cursor.lastrowid
    cursor.close()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, description, sign FROM movement_types WHERE id = %s", (type_id,))
    result = cursor.fetchone()
    cursor.close()
    return result

@router.put("/movement-types/{type_id}", response_model=MovementTypeResponse)
def update_movement_type(
    type_id: int,
    mt: MovementTypeResponse,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    cursor = conn.cursor()
    cursor.execute("UPDATE movement_types SET name=%s, description=%s, sign=%s WHERE id=%s",
                   (mt.name, mt.description, mt.sign, type_id))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    if not affected:
        raise HTTPException(status_code=404, detail="Movement type not found")
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, description, sign FROM movement_types WHERE id = %s", (type_id,))
    result = cursor.fetchone()
    cursor.close()
    return result

@router.delete("/movement-types/{type_id}", status_code=204)
def delete_movement_type(
    type_id: int,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    # Check if used in stock_movements
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stock_movements WHERE movement_type_id = %s", (type_id,))
    count = cursor.fetchone()[0]
    if count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete movement type with existing movements")
    cursor.execute("DELETE FROM movement_types WHERE id = %s", (type_id,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    if not affected:
        raise HTTPException(status_code=404, detail="Movement type not found")
    return None

# ---------- Audit Log ----------
@router.get("/audit-logs", response_model=List[AuditLogEntry])
def get_audit_logs(
    table_name: Optional[str] = None,
    user_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    operation: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    return admin_model.get_audit_logs(conn, table_name, user_id, from_date, to_date, operation, limit, offset)