from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from mysql.connector import MySQLConnection
from ..core.database import get_db
from ..core.security import decode_access_token
from ..models.user import get_user_by_id

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn: MySQLConnection = Depends(get_db)
):
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = get_user_by_id(conn, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user["is_active"]:
        raise HTTPException(status_code=401, detail="Inactive user")
    
    return user

async def get_current_active_manager(current_user = Depends(get_current_user)):
    roles = current_user.get("roles", "")
    print(f"🔍 DEBUG - User {current_user['username']} has roles: '{roles}'")  
    if "manager" not in roles and "admin" not in roles:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user