import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.environ["MONGODB_URI"]
DB_NAME = os.getenv("MONGODB_DB", "sentinelai")

client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]
cameras_collection = db.cameras
events_collection = db.events
