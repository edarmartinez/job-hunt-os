import os
from fastapi import Header, HTTPException

API_KEY = os.getenv("API_KEY")

def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if API_KEY is None or API_KEY.strip() == "":
        # Server misconfigured
        raise HTTPException(status_code=500, detail="Server missing API_KEY")
    if x_api_key is None or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True
