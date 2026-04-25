import logging
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from database import cameras_collection
from routers import cameras, events, websocket
from services.event_pipeline import pipeline
from services.stream_manager import stream_manager


async def _init_solana():
    try:
        from services.solana_logger import SolanaLogger
        logger = SolanaLogger()
        await logger.fund_wallet()

        async def solana_adapter(event_hash: str, camera_id: str, ts: int) -> Optional[str]:
            return await logger.log_event(camera_id, float(ts), event_hash)

        pipeline.set_solana_logger(solana_adapter)
        logging.info("Solana logger wired — wallet %s", logger.payer.pubkey())
    except Exception:
        logging.exception("Solana logger failed to init — events will have no on-chain proof")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _init_solana()
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
