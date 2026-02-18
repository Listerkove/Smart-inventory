from fastapi import APIRouter, Depends, HTTPException, Query, status
from mysql.connector import MySQLConnection
from typing import List, Optional

from ...schemas.inventory import (
    StockReceiptCreate,
    StockAdjustmentCreate,
    StockMovementResponse,
    MovementTypeResponse,
    StockLevelResponse
)
from ...models import stock_movement as movement_model
from ...models import product as product_model
from ...core.database import get_db
from ...api.dependencies import get_current_user, get_current_active_manager

router = APIRouter(prefix="/inventory", tags=["Inventory"])

# ---------- PUBLIC (any authenticated user) ----------
@router.get("/movement-types", response_model=List[MovementTypeResponse])
def get_movement_types(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)  # any auth user
):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, description, sign FROM movement_types ORDER BY name")
    types = cursor.fetchall()
    cursor.close()
    return types

@router.get("/movements", response_model=List[StockMovementResponse])
def get_movements(
    product_sku: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)  # any auth user
):
    movements = movement_model.get_stock_movements(conn, product_sku, limit, offset)
    return movements

@router.get("/stock/{sku}", response_model=StockLevelResponse)
def get_stock_level(
    sku: str,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)  # any auth user
):
    product = product_model.get_product_by_sku(conn, sku)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    status_label = "Low Stock" if product["quantity_in_stock"] <= product["reorder_threshold"] else "OK"
    return {
        "sku": sku,
        "name": product["name"],
        "quantity_in_stock": product["quantity_in_stock"],
        "reorder_threshold": product["reorder_threshold"],
        "status": status_label
    }

# ---------- PROTECTED (manager/admin only) ----------
@router.post("/receipt", status_code=status.HTTP_201_CREATED)
def receive_stock(
    receipt: StockReceiptCreate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)  # 🔒 MANAGER/ADMIN ONLY
):
    product = product_model.get_product_by_sku(conn, receipt.product_sku)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not product["is_active"]:
        raise HTTPException(status_code=400, detail="Cannot receive stock for inactive product")

    try:
        movement_id = movement_model.create_stock_receipt(
            conn,
            receipt.product_sku,
            receipt.quantity,
            receipt.reference_id,
            current_user["id"]
        )
        new_qty = movement_model.get_product_stock_level(conn, receipt.product_sku)
        return {
            "message": "Stock received successfully",
            "movement_id": movement_id,
            "new_quantity": new_qty
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record receipt: {str(e)}")

@router.post("/adjust", status_code=status.HTTP_201_CREATED)
def adjust_stock(
    adjustment: StockAdjustmentCreate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)  # 🔒 MANAGER/ADMIN ONLY
):
    product = product_model.get_product_by_sku(conn, adjustment.product_sku)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    valid_types = ["adjustment", "damage", "return"]
    if adjustment.movement_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Movement type must be one of: {valid_types}")

    # Check stock for decrease operations
    movement_type_id = movement_model.get_movement_type_id(conn, adjustment.movement_type)
    cursor = conn.cursor()
    cursor.execute("SELECT sign FROM movement_types WHERE id = %s", (movement_type_id,))
    sign = cursor.fetchone()[0]
    cursor.close()

    if sign == -1:
        current_stock = movement_model.get_product_stock_level(conn, adjustment.product_sku)
        if current_stock is not None and adjustment.quantity > current_stock:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {current_stock}, tried to remove: {adjustment.quantity}"
            )

    try:
        movement_id = movement_model.create_stock_adjustment(
            conn,
            adjustment.product_sku,
            adjustment.quantity,
            adjustment.movement_type,
            adjustment.reason,
            current_user["id"]
        )
        new_qty = movement_model.get_product_stock_level(conn, adjustment.product_sku)
        return {
            "message": f"Stock {adjustment.movement_type} recorded successfully",
            "movement_id": movement_id,
            "new_quantity": new_qty
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record adjustment: {str(e)}")