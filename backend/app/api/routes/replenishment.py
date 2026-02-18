from fastapi import APIRouter, Depends, HTTPException, Query, status
from mysql.connector import MySQLConnection
from typing import List

from ...schemas.replenishment import (
    ReplenishmentSuggestionCreate,
    ReplenishmentSuggestionResponse,
    ReplenishmentAction
)
from ...models import replenishment as replenishment_model
from ...core.database import get_db
from ...api.dependencies import get_current_active_manager  # manager/admin only

router = APIRouter(prefix="/replenishment", tags=["Replenishment"])

@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_suggestions(
    params: ReplenishmentSuggestionCreate = Depends(),  # query params
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)  # 🔒 manager/admin only
):
    """Generate replenishment suggestions using predictive algorithm."""
    try:
        replenishment_model.generate_suggestions(
            conn,
            params.lookback_days,
            params.forecast_days,
            params.safety_stock_factor
        )
        return {"message": "Replenishment suggestions generated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.get("/suggestions", response_model=List[ReplenishmentSuggestionResponse])
def get_suggestions(
    active_only: bool = True,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)  # 🔒 manager/admin only
):
    """Get list of replenishment suggestions."""
    return replenishment_model.get_suggestions(conn, active_only, limit, offset)

@router.post("/actions")
def take_action(
    action: ReplenishmentAction,
    conn: MySQLConnection = Depends(get_db),
    current_user = Depends(get_current_active_manager)  # 🔒 manager/admin only
):
    """Accept (mark as acted upon) or ignore/delete a suggestion."""
    if action.action == "accept":
        success = replenishment_model.mark_as_acted_upon(conn, action.suggestion_id)
        message = "Suggestion marked as acted upon"
    elif action.action == "ignore":
        success = replenishment_model.ignore_suggestion(conn, action.suggestion_id)
        message = "Suggestion ignored and removed"
    else:
        raise HTTPException(status_code=400, detail="Action must be 'accept' or 'ignore'")
    
    if not success:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"message": message}