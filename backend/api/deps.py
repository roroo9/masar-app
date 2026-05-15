from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_current_student_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
) -> int:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return decode_token(credentials.credentials)
    except (JWTError, Exception):
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_same_student(
    student_id: int,
    current_id: int = Depends(get_current_student_id),
) -> int:
    if student_id != current_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return student_id
