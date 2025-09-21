import uvicorn
from fastapi import FastAPI
from app.api.controllers import router as api_router
from app.infra.sql_repository import ensure_tables
import logging

from app.infra import export_adapter

app = FastAPI(title="Eumenides - DDD Metadata Monitor (safe-only)")
app.include_router(api_router)

@app.on_event("startup")
async def startup():
    logging.info("Starting up, creating DB if needed")
    await ensure_tables()
    try:
        from app.infra.telegram_client import start_client
        await start_client()
    except Exception:
        logging.exception("Telegram client init failed; continue for offline dev")
    # subscribe export adapter
    try:
        export_adapter.subscribe()
    except Exception:
        logging.exception("export adapter subscribe failed")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
