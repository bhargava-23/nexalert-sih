"""NexAlert Backend Service

FastAPI modular monolith backend for NexAlert.
"""

from fastapi import FastAPI

app = FastAPI(title="NexAlert Backend", version="0.1.0")


@app.get("/")
async def root():
    return {"message": "NexAlert Backend", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Phase 3: Structure only - no business logic modules imported yet
# Module imports and routes will be added in Phase 4+
