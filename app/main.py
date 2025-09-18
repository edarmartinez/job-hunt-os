import os
import time
from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from .routers import applications, dev
from .database import Base, engine   # ✅ from app/database.py

app = FastAPI(title="Job Hunt OS")

@app.get("/health")
def health():
    return {"status": "ok"}

# main app routes
app.include_router(applications.router)

# create tables on startup (with small retry for Dockerized PG)
@app.on_event("startup")
def on_startup():
    for _ in range(10):
        try:
            Base.metadata.create_all(bind=engine)
            break
        except OperationalError:
            time.sleep(1)

# dev-only routes
if os.getenv("ENV") == "dev":
    app.include_router(dev.router)
