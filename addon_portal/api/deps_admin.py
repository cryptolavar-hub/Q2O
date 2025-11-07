from fastapi import Request, HTTPException

def require_admin(request: Request):
    user = getattr(request, "session", {}).get("user") if hasattr(request, "session") else None
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user
