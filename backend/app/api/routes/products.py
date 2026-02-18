from fastapi import APIRouter, Depends, HTTPException, Query, status
from mysql.connector import MySQLConnection
from typing import List, Optional

from ...schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    CategoryCreate, CategoryResponse,
    SupplierCreate, SupplierResponse
)
from ...models import product as product_model
from ...core.database import get_db
from ...api.dependencies import get_current_user, get_current_active_manager

router = APIRouter(prefix="/products", tags=["Products"])

# -------------------- CATEGORY ENDPOINTS --------------------
@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return product_model.get_all_categories(conn)

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)
):
    category_id = product_model.create_category(conn, category.name, category.description)
    return product_model.get_category_by_id(conn, category_id)

# -------------------- SUPPLIER ENDPOINTS --------------------
@router.get("/suppliers", response_model=List[SupplierResponse])
def get_suppliers(
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return product_model.get_all_suppliers(conn)

@router.post("/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    supplier: SupplierCreate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)
):
    supplier_id = product_model.create_supplier(conn, supplier.dict())
    return product_model.get_supplier_by_id(conn, supplier_id)

# -------------------- PRODUCT ENDPOINTS --------------------
@router.get("", response_model=List[ProductResponse])
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = True,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return product_model.get_all_products(conn, skip, limit, active_only)

@router.get("/{sku}", response_model=ProductResponse)
def get_product(
    sku: str,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    product = product_model.get_product_by_sku(conn, sku)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)
):
    # Check if SKU or barcode already exists
    existing = product_model.get_product_by_sku(conn, product.sku)
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    existing = product_model.get_product_by_barcode(conn, product.barcode)
    if existing:
        raise HTTPException(status_code=400, detail="Barcode already exists")
    
    try:
        sku = product_model.create_product(conn, product.model_dump())
        return product_model.get_product_by_sku(conn, sku)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

@router.put("/{sku}", response_model=ProductResponse)
def update_product(
    sku: str,
    product_update: ProductUpdate,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)
):
    # Verify product exists
    existing = product_model.get_product_by_sku(conn, sku)
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # If barcode is being updated, check it's not taken by another product
    if product_update.barcode and product_update.barcode != existing["barcode"]:
        barcode_exists = product_model.get_product_by_barcode(conn, product_update.barcode)
        if barcode_exists and barcode_exists["sku"] != sku:
            raise HTTPException(status_code=400, detail="Barcode already in use by another product")
    
    success = product_model.update_product(conn, sku, product_update.model_dump(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update product")
    return product_model.get_product_by_sku(conn, sku)

@router.delete("/{sku}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    sku: str,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)
):
    existing = product_model.get_product_by_sku(conn, sku)
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    success = product_model.delete_product(conn, sku)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete product")
    return None