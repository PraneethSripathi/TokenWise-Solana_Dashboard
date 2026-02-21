
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from core.logger import logger
from bson import ObjectId
from datetime import datetime

def custom_json_encoder(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

if not settings.MONGO_URL:
    raise RuntimeError("MONGO_URL is not set in environment")

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DB_NAME]

logger.info("MongoDB client initialized.")