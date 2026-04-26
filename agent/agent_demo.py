"""
SentinelAI — Demo Agent (hardcoded data, no backend required)

Use this if your backend isn't reachable during Agentverse registration/demo.
Swap to agent.py once backend is live.
"""

import os
from dotenv import load_dotenv

from uagents import Context, Field, Model, Protocol
from uagents.experimental.chat_agent import ChatAgent

load_dotenv()

# ---------------------------------------------------------------------------
# Hardcoded demo data
# ---------------------------------------------------------------------------

DEMO_CAMERAS = [
    {"name": "Office Lobby", "status": "active", "context": "Watch for unauthorized entry after hours"},
    {"name": "Parking Lot B", "status": "active", "context": "Monitor for suspicious vehicles or loitering"},
    {"name": "Server Room", "status": "active", "context": "Detect unauthorized access to equipment"},
]

DEMO_EVENTS = [
    {
        "timestamp": "2026-04-25T02:34:12Z",
        "camera_name": "Parking Lot B",
        "description": "Unrecognized individual loitering near south entrance for 4+ minutes",
        "confidence": 0.92,
        "solana_tx": "5xKj9mR3vN8pQw2tYhL6bCdFeGaH7iJkMnOpQrStUvWx",
    },
    {
        "timestamp": "2026-04-25T01:17:45Z",
        "camera_name": "Server Room",
        "description": "Door opened outside scheduled maintenance window",
        "confidence": 0.88,
        "solana_tx": "3yBn7kL5wM9rTs4vXhJ2cDdAeGfH6iKjMnOpQrStUvWx",
    },
    {
        "timestamp": "2026-04-24T23:52:03Z",
        "camera_name": "Office Lobby",
        "description": "Motion detected in lobby after building closure at 11pm",
        "confidence": 0.85,
        "solana_tx": "7zCm8jK4xN6qUr3wYiH1bEdBfGgI5hLjMnOpQrStUvWx",
    },
    {
        "timestamp": "2026-04-24T22:08:31Z",
        "camera_name": "Parking Lot B",
        "description": "Vehicle circling lot 3 times without parking — flagged as suspicious",
        "confidence": 0.79,
        "solana_tx": "2wAo6iJ3yO5pVs2xZjG0aDcCeHhF4gKkMnOpQrStUvWx",
    },
]

# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------

camera_proto = Protocol(name="CameraMonitor", version="0.1.0")
event_proto = Protocol(name="EventQuery", version="0.1.0")
status_proto = Protocol(name="SystemStatus", version="0.1.0")


class ListCamerasRequest(Model):
    """Request to list all active security cameras."""
    dummy: str = Field(default="", description="No input needed")


class ListCamerasResponse(Model):
    summary: str = Field(..., description="Summary of active cameras")


@camera_proto.on_message(ListCamerasRequest)
async def handle_list_cameras(ctx: Context, sender: str, msg: ListCamerasRequest):
    lines = [f"📡 **{len(DEMO_CAMERAS)} camera(s) active:**"]
    for cam in DEMO_CAMERAS:
        lines.append(f"  • **{cam['name']}** — {cam['context']} (status: {cam['status']})")
    await ctx.send(sender, ListCamerasResponse(summary="\n".join(lines)))


class GetRecentEventsRequest(Model):
    """Request to get recent security events detected by AI."""
    camera_name: str = Field(
        default="",
        description="Optional camera name to filter events. Leave empty for all.",
    )
    limit: int = Field(default=5, description="Number of recent events to return")


class GetRecentEventsResponse(Model):
    summary: str = Field(..., description="Summary of recent security events")


@event_proto.on_message(GetRecentEventsRequest)
async def handle_recent_events(ctx: Context, sender: str, msg: GetRecentEventsRequest):
    events = DEMO_EVENTS
    if msg.camera_name:
        events = [e for e in events if msg.camera_name.lower() in e["camera_name"].lower()]
    events = events[:msg.limit]

    if not events:
        summary = "No security events detected recently."
    else:
        lines = [f"🚨 **{len(events)} recent event(s):**"]
        for ev in events:
            line = f"  • [{ev['timestamp']}] **{ev['camera_name']}** — {ev['description']} (confidence: {ev['confidence']:.0%})"
            line += f"\n    Solana TX: `{ev['solana_tx'][:16]}...`"
            lines.append(line)
        summary = "\n".join(lines)

    await ctx.send(sender, GetRecentEventsResponse(summary=summary))


class SystemStatusRequest(Model):
    """Request to check the health and status of the SentinelAI system."""
    dummy: str = Field(default="", description="No input needed")


class SystemStatusResponse(Model):
    summary: str = Field(..., description="System health status")


@status_proto.on_message(SystemStatusRequest)
async def handle_system_status(ctx: Context, sender: str, msg: SystemStatusRequest):
    summary = (
        "🟢 **SentinelAI Status:** operational\n"
        "  • Active camera streams: 3\n"
        "  • AI pipeline: ResNet-18 → Gemma 4 → ElevenLabs TTS\n"
        "  • Blockchain: Solana devnet (tamper-proof logging)\n"
        "  • Storage: MongoDB Atlas + Cloudinary CDN\n"
        "  • Last event detected: 32 minutes ago"
    )
    await ctx.send(sender, SystemStatusResponse(summary=summary))


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

agent = ChatAgent(
    name="SentinelAI",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
    instructions=(
        "You are SentinelAI, an AI-powered security camera monitoring assistant. "
        "You help users check on their security cameras, review recent events "
        "detected by AI (motion, people, anomalies), and check system status. "
        "When users ask about what's happening, use the event query tool. "
        "When they ask about cameras, use the camera list tool. "
        "When they ask about system health, use the status tool. "
        "Be concise, security-focused, and helpful."
    ),
)

agent.include(camera_proto, publish_manifest=True)
agent.include(event_proto, publish_manifest=True)
agent.include(status_proto, publish_manifest=True)


if __name__ == "__main__":
    agent.run()
