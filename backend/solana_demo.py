import asyncio
import hashlib
import json
import sys

sys.path.insert(0, "/opt/sentinelai/backend")
from services.solana_logger import SolanaLogger


async def main():
    logger = SolanaLogger()
    event_data = json.dumps(
        {
            "camera_id": "demo-pool",
            "timestamp": "2026-04-26T09:00:00+00:00",
            "description": "Baby has fallen into pool.",
            "confidence": 0.97,
        },
        sort_keys=True,
    )
    event_hash = hashlib.sha256(event_data.encode()).hexdigest()
    tx = await logger.log_event("demo-pool", 1777500000.0, event_hash)
    print("TX:", tx)


asyncio.run(main())
