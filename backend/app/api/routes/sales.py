from fastapi import APIRouter, Depends, HTTPException, Query, status
from mysql.connector import MySQLConnection
from typing import List, Optional
from datetime import datetime, date

from ...schemas.sale import (
    SaleCreate, SaleTransactionResponse, SaleItemResponse, SaleSummaryResponse
)
from ...models import sale as sale_model
from ...core.database import get_db
from ...api.dependencies import get_current_user

router = APIRouter(prefix="/sales", tags=["Sales"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=SaleTransactionResponse)
def create_sale(
    sale: SaleCreate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)  # any authenticated user (clerk, manager, admin)
):
    """Process a sale transaction."""
    # Validate that all SKUs exist (optional – the procedure will also validate)
    # But we can do quick existence check
    from ...models.product import get_product_by_sku
    for item in sale.items:
        product = get_product_by_sku(conn, item.sku)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with SKU '{item.sku}' not found"
            )
        if not product["is_active"]:
            raise HTTPException(
                status_code=400,
                detail=f"Product '{item.sku}' is inactive and cannot be sold"
            )

    try:
        # Prepare items list for the stored procedure
        items_data = [
            {
                "sku": item.sku,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price)  # convert Decimal to float for JSON
            }
            for item in sale.items
        ]
        
        transaction_id = sale_model.create_sale(
            conn,
            sale.transaction_number,
            current_user["id"],
            sale.transaction_date,
            items_data
        )
        
        # Fetch the complete transaction with items
        transaction = sale_model.get_transaction_by_id(conn, transaction_id)
        items = sale_model.get_transaction_items(conn, transaction_id)
        transaction["items"] = items
        return transaction
        
    except Exception as e:
        # Check for specific error messages from the stored procedure
        error_msg = str(e)
        if "Insufficient stock" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        raise HTTPException(status_code=500, detail=f"Failed to process sale: {error_msg}")

@router.get("/transactions", response_model=List[SaleTransactionResponse])
def get_transactions(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get sales transactions (paginated, optionally filtered by date)."""
    transactions = sale_model.get_transactions(conn, from_date, to_date, limit, offset)
    
    # Fetch items for each transaction
    for t in transactions:
        t["items"] = sale_model.get_transaction_items(conn, t["id"])
    
    return transactions

@router.get("/transactions/{transaction_id}", response_model=SaleTransactionResponse)
def get_transaction(
    transaction_id: int,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a single transaction by ID."""
    transaction = sale_model.get_transaction_by_id(conn, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    transaction["items"] = sale_model.get_transaction_items(conn, transaction_id)
    return transaction

@router.get("/summary/daily", response_model=SaleSummaryResponse)
def get_daily_summary(
    transaction_date: date = Query(default_factory=lambda: datetime.now().date()),
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get sales summary for a specific day."""
    summary = sale_model.get_daily_summary(conn, transaction_date)
    if not summary:
        summary = {"total_transactions": 0, "total_revenue": 0, "total_items_sold": 0}
    return summary