"""
SentinelAI — Fetch.ai Agentverse Agent

Following the official ASI:One example pattern:
https://uagents.fetch.ai/docs/examples/asi-1
"""

import os
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv
from openai import OpenAI
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

load_dotenv()

# ---------------------------------------------------------------------------
# Demo data — swap with live API calls once backend is deployed
# ---------------------------------------------------------------------------

DEMO_CAMERAS = [
    {"name": "Office Lobby", "status": "active", "context": "Watch for unauthorized entry after hours"},
    {"name": "Parking Lot B", "status": "active", "context": "Monitor for suspicious vehicles or loitering"},
    {"name": "Server Room", "status": "active", "context": "Detect unauthorized access to equipment"},
]

DEMO_EVENTS = [
    {
        "timestamp": "2026-04-25 02:34 AM",
        "camera": "Parking Lot B",
        "description": "Unrecognized individual loitering near south entrance for 4+ minutes",
        "confidence": "92%",
        "solana_tx": "5xKj9mR3vN8pQw2t",
    },
    {
        "timestamp": "2026-04-25 01:17 AM",
        "camera": "Server Room",
        "description": "Door opened outside scheduled maintenance window",
        "confidence": "88%",
        "solana_tx": "3yBn7kL5wM9rTs4v",
    },
    {
        "timestamp": "2026-04-24 11:52 PM",
        "camera": "Office Lobby",
        "description": "Motion detected in lobby after building closure at 11pm",
        "confidence": "85%",
        "solana_tx": "7zCm8jK4xN6qUr3w",
    },
]

SYSTEM_CONTEXT = f"""You are SentinelAI, an AI-powered security camera monitoring assistant.

You have access to the following live system data:

CAMERAS:
{chr(10).join(f"- {c['name']} ({c['status']}): {c['context']}" for c in DEMO_CAMERAS)}

RECENT EVENTS:
{chr(10).join(f"- [{e['timestamp']}] {e['camera']}: {e['description']} (confidence: {e['confidence']}, solana tx: {e['solana_tx']})" for e in DEMO_EVENTS)}

SYSTEM STATUS:
- 3 active camera streams
- AI pipeline: Custom ResNet-18 (event detection) → Gemma 4 (reasoning) → ElevenLabs (narration)
- Blockchain: Solana devnet — every event is hashed and logged on-chain for tamper-proof records
- Storage: MongoDB Atlas (events DB) + Cloudinary CDN (frames & audio)
- Infrastructure: Vultr GPU cloud for real-time inference

Answer user questions about camera status, security events, and system health using the data above.
Be concise, professional, and security-focused. If asked about something outside your scope, say so politely.
"""

# ---------------------------------------------------------------------------
# ASI:One LLM client
# ---------------------------------------------------------------------------

client = OpenAI(
    base_url="https://api.asi1.ai/v1",
    api_key=os.getenv("ASI1_API_KEY"),
)

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

agent = Agent(
    name="SentinelAI",
    seed="sentinelai-lahacks-2026-security-monitor",
    port=8001,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )

    text = ""
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text

    response = "Something went wrong — I'm unable to answer right now."
    try:
        r = client.chat.completions.create(
            model="asi1",
            messages=[
                {"role": "system", "content": SYSTEM_CONTEXT},
                {"role": "user", "content": text},
            ],
            max_tokens=2048,
        )
        response = str(r.choices[0].message.content)
    except Exception:
        ctx.logger.exception("Error querying ASI:One model")

    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=response),
                EndSessionContent(type="end-session"),
            ],
        ),
    )


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
