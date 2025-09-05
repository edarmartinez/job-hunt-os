from fastapi import FastAPI
from .routers import applications

app = FastAPI(title="Job Hunt OS")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(applications.router)
