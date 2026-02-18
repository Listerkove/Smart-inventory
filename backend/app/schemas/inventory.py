from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MovementTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    sign: int

class StockMovementBase(BaseModel):
    product_sku: str
    quantity: int = Field(..., gt=0)
    reference_id: Optional[str] = None
    reason: Optional[str] = None

class StockReceiptCreate(StockMovementBase):
    pass

class StockAdjustmentCreate(StockMovementBase):
    movement_type: str = "adjustment"  # or "damage", "return"

class StockMovementResponse(BaseModel):
    id: int
    product_name: Optional[str]
    product_sku: str
    movement_type: str
    quantity: int
    previous_quantity: int
    new_quantity: int
    reference_id: Optional[str]
    reason: Optional[str]
    performed_by: Optional[str]
    created_at: datetime

class StockLevelResponse(BaseModel):
    sku: str
    name: str
    quantity_in_stock: int
    reorder_threshold: int
    status: str