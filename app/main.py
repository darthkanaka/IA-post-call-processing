import logging

from fastapi import FastAPI

from app.routers.retell_webhook import router as retell_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title="Invisible Arts Post-Call Processor", version="1.0.0")
app.include_router(retell_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "post-call-processor"}
