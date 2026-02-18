from fastapi import APIRouter, Depends, Query
from mysql.connector import MySQLConnection
from datetime import date
from typing import List, Optional

from ...schemas.dashboard import (
    LowStockAlert,
    DailySalesSummary,
    CurrentInventoryItem,
    ProductPerformance,
    DashboardSummary
)
from ...models import dashboard as dashboard_model
from ...core.database import get_db
from ...api.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/low-stock", response_model=List[LowStockAlert])
def get_low_stock_alerts(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)  # any authenticated user, but UI will hide for clerk
):
    """Get all products with stock below reorder threshold."""
    return dashboard_model.get_low_stock_alerts(conn)

@router.get("/daily-sales", response_model=Optional[DailySalesSummary])
def get_daily_sales(
    transaction_date: date = Query(default_factory=lambda: date.today()),
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get sales summary for a specific date."""
    return dashboard_model.get_daily_sales_summary(conn, transaction_date)

@router.get("/inventory", response_model=List[CurrentInventoryItem])
def get_current_inventory(
    active_only: bool = True,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current inventory snapshot."""
    return dashboard_model.get_current_inventory(conn, active_only)

@router.get("/product-performance", response_model=List[ProductPerformance])
def get_product_performance(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get product sales performance for last 30 days."""
    return dashboard_model.get_product_performance(conn)

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get summary metrics for the dashboard."""
    today = date.today()
    return {
        "total_products": dashboard_model.get_total_products_count(conn),
        "total_stock_value": dashboard_model.get_total_stock_value(conn),
        "low_stock_count": dashboard_model.get_low_stock_count(conn),
        "out_of_stock_count": dashboard_model.get_out_of_stock_count(conn),
        "today_sales": dashboard_model.get_daily_sales_summary(conn, today)
    }