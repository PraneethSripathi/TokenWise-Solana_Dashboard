

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from core.config import settings
from core.database import client, db
from core.logger import logger
from api.routers import realtime, analytics
from api.websocket_manager import manager

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.PROJECT_DESCRIPTION,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(realtime.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")


app.websocket("/ws/transactions")(manager.websocket_endpoint)

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")
    
    await manager.load_tracked_wallets()
    await manager.start_monitoring() 
    

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")
    await manager.stop_monitoring()
    client.close() # Close MongoDB connection
    logger.info("MongoDB connection closed.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)