from fastapi import APIRouter, Depends, HTTPException, status, Header
from mysql.connector import MySQLConnection
from typing import List, Optional

from ...schemas.integration import (
    ApiKeyCreate, ApiKeyResponse, ApiKeyRegenerate,
    WebhookCreate, WebhookUpdate, IntegrationStatus, WebhookResponse
)
from ...schemas.integration import IntegrationStatus
from ...models import integration as integration_model
from ...models import product, stock_movement, sale
from ...core.database import get_db
from ..dependencies import get_current_active_manager

router = APIRouter(prefix="/intergration", tags=["intergration"])

# ---------- Public API endpoints (authenticated by API key) ----------
async def verify_api_key(
    x_api_key: str = Header(...),
    conn: MySQLConnection = Depends(get_db)
):
    key = integration_model.validate_api_key(conn, x_api_key)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")
    return key

@router.get("/public/products")
def public_get_products(
    api_key: dict = Depends(verify_api_key),
    conn: MySQLConnection = Depends(get_db)
):
    """Public API endpoint to fetch all products (active)."""
    return product.get_all_products(conn, active_only=True)

@router.get("/public/stock/{sku}")
def public_get_stock(
    sku: str,
    api_key: dict = Depends(verify_api_key),
    conn: MySQLConnection = Depends(get_db)
):
    """Public API endpoint to get current stock for a product."""
    prod = product.get_product_by_sku(conn, sku)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"sku": sku, "quantity_in_stock": prod["quantity_in_stock"]}

@router.get("/public/sales/recent")
def public_get_recent_sales(
    limit: int = 10,
    api_key: dict = Depends(verify_api_key),
    conn: MySQLConnection = Depends(get_db)
):
    """Public API endpoint to get recent sales."""
    return sale.get_transactions(conn, limit=limit)

# ---------- Admin endpoints for managing intergration (manager/admin only) ----------
@router.get("/api-keys", response_model=List[ApiKeyResponse])
def get_api_keys(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)
):
    return integration_model.get_api_keys(conn)

@router.post("/api-keys", response_model=ApiKeyResponse, status_code=201)
def create_api_key(
    key_data: ApiKeyCreate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)
):
    return integration_model.create_api_key(
        conn, key_data.name, current_user['id'], key_data.expires_in_days
    )

@router.delete("/api-keys/{key_id}", status_code=204)
def revoke_api_key(
    key_id: int,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)
):
    success = integration_model.revoke_api_key(conn, key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return None

@router.post("/api-keys/{key_id}/regenerate", response_model=ApiKeyResponse)
def regenerate_api_key(
    key_id: int,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)
):
    key = integration_model.regenerate_api_key(conn, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return key

# ---------- Webhooks ----------
@router.get("/webhooks", response_model=List[WebhookResponse])
def get_webhooks(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)
):
    return integration_model.get_webhooks(conn)

@router.post("/webhooks", response_model=WebhookResponse, status_code=201)
def create_webhook(
    webhook: WebhookCreate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)
):
    webhook_id = integration_model.create_webhook(conn, webhook.dict(), current_user['id'])
    return integration_model.get_webhook_by_id(conn, webhook_id)

@router.put("/webhooks/{webhook_id}", response_model=WebhookResponse)
def update_webhook(
    webhook_id: int,
    webhook_update: WebhookUpdate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)
):
    existing = integration_model.get_webhook_by_id(conn, webhook_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Webhook not found")
    success = integration_model.update_webhook(conn, webhook_id, webhook_update.dict(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=500, detail="Update failed")
    return integration_model.get_webhook_by_id(conn, webhook_id)

@router.delete("/webhooks/{webhook_id}", status_code=204)
def delete_webhook(
    webhook_id: int,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)
):
    success = integration_model.delete_webhook(conn, webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return None

@router.get("/status", response_model=IntegrationStatus)
def get_intergration_status(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)
):
    keys = integration_model.get_api_keys(conn)
    webhooks = integration_model.get_webhooks(conn)
    recent = integration_model.get_recent_deliveries(conn, 10)
    return {
        "total_api_keys": len(keys),
        "active_api_keys": sum(1 for k in keys if k['is_active']),
        "total_webhooks": len(webhooks),
        "active_webhooks": sum(1 for w in webhooks if w['is_active']),
        "recent_deliveries": recent
    }