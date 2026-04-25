import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from database import cameras_collection
from routers import cameras, events, websocket
from services.stream_manager import stream_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Resume streams for cameras already in the DB.
    async for doc in cameras_collection.find({"status": "active"}):
        try:
            await stream_manager.start_camera(str(doc["_id"]), doc["stream_url"])
        except Exception:
            logging.exception("failed to resume stream for %s", doc["_id"])
    yield
    await stream_manager.stop_all()


app = FastAPI(title="SentinelAI", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cameras.router)
app.include_router(events.router)
app.include_router(websocket.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "active_streams": list(stream_manager.streams.keys()),
    }
