# SentinelAI Fetch.ai Agent

Agentverse agent for the Fetch.ai challenge. Exposes SentinelAI's security monitoring through ASI:One chat.

## Setup

```bash
pip install "uagents[all]"
```

Set environment variables in `.env`:
```
ASI1_API_KEY=<your-asi1-api-key>
SENTINEL_API_URL=http://localhost:8000  # or your deployed Vultr URL
```

## Run locally

```bash
python agent.py
```

## Register on Agentverse

1. Run the agent locally — it auto-registers with Agentverse
2. Go to https://agentverse.ai and find your agent
3. Test via ASI:One at https://asi1.ai
