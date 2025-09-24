"""
Segurança “fingida”:
- Dependência que exige o header `X-Admin-Token: <token>`
- Token é comparado com settings.ADMIN_TOKEN
"""

from fastapi import Header, HTTPException, status, Depends
from .config import settings


def require_admin(x_admin_token: str | None = Header(default=None)):
    if not x_admin_token or x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin token inválido ou ausente."
        )
    return True


AdminDep = Depends(require_admin)
