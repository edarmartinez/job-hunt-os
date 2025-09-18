from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import os

# ✅ import from app/database.py and app/models.py
from ..database import get_db, Base, engine
from .. import models

router = APIRouter()

@router.post("/dev/seed", tags=["dev"])
def seed_data(db: Session = Depends(get_db)):
    if os.getenv("ENV") != "dev":
        return {"error": "Seeding is disabled outside dev"}

    # adjust fields to match your Application model
    rows = [
        models.Application(name="Alice", email="alice@example.com"),
        models.Application(name="Bob", email="bob@example.com"),
        models.Application(name="Charlie", email="charlie@example.com"),
        models.Application(name="Diana", email="diana@example.com"),
        models.Application(name="Evan", email="evan@example.com"),
    ]
    db.add_all(rows)
    db.commit()
    return {"inserted": len(rows)}
