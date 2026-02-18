from fastapi import APIRouter, Depends, HTTPException, Query
from mysql.connector import MySQLConnection
from typing import List, Optional
from datetime import date

from ...schemas.report import (
    SalesReportFilter, SalesReportItem,
    StockMovementFilter, StockMovementReportItem,
    ProductPerformanceFilter, ProductPerformanceItem
)
from ...models import report as report_model
from ...core.database import get_db
from ...api.dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/sales", response_model=List[SalesReportItem])
def get_sales_report(
    from_date: date,
    to_date: date,
    group_by: str = Query("day", pattern="^(day|week|month)$"),
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)  # any authenticated user
):
    """Get sales report grouped by day/week/month within date range."""
    if from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date must be before to_date")
    return report_model.get_sales_report(conn, from_date, to_date, group_by)

@router.get("/stock-movements", response_model=List[StockMovementReportItem])
def get_stock_movement_report(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    product_sku: Optional[str] = None,
    movement_type: Optional[str] = None,
    limit: int = Query(1000, ge=1, le=10000),
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get stock movement report with optional filters."""
    return report_model.get_stock_movement_report(
        conn, from_date, to_date, product_sku, movement_type, limit
    )

@router.get("/product-performance", response_model=List[ProductPerformanceItem])
def get_product_performance(
    sort_by: str = Query("total_sold_30d", pattern="^(total_sold_30d|avg_daily_sales|stock|slow_movers|name)$"),
    limit: int = Query(50, ge=1, le=500),
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get product performance report (top sellers, slow movers, etc.)."""
    return report_model.get_product_performance_report(conn, sort_by, limit)

@router.get("/filter-options/movement-types")
def get_movement_types(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get list of movement types for filter dropdown."""
    return report_model.get_distinct_movement_types(conn)

@router.get("/filter-options/products")
def get_products(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get list of products (sku + name) for filter dropdown."""
    return report_model.get_distinct_product_skus(conn)