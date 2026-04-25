# Ved — Personal Execution Plan (SentinelAI)

**Role:** Person B — API / Infrastructure
**Window:** Friday 7 PM → Sunday 8 AM PDT (~36 hours, ~16 hours active dev + buffer)
**Owns:** FastAPI backend, MongoDB, WebSockets, event pipeline, Cloudinary upload glue, deployment, domain.
**Does NOT own:** ML training (Sartaj), frontend pages (Jonny), Solana on-chain code (Jonny — but I expose the hook).

Reference: [`docs/superpowers/plans/sentinelai.md`](sentinelai.md) for full code scaffolds. This file is my checklist + decision log.

---

## North Star

By Sunday 7 AM I need: a deployed FastAPI service on Vultr behind a GoDaddy domain that
1. Accepts camera CRUD,
2. Streams frames over WS to the frontend,
3. Receives "notable" flags from Sartaj's classifier and runs the full pipeline (Gemma → ElevenLabs → Cloudinary → MongoDB → Solana hook → WS push to frontend),
4. Survives the demo without crashing.

Everything else is gravy.

---

## Pre-Hack Checklist (Do BEFORE Friday 7 PM)

- [ ] Create accounts: MongoDB Atlas, Cloudinary, Vultr, GoDaddy, Google AI Studio (Gemma), ElevenLabs.
- [ ] Apply for hackathon credits (Vultr, MongoDB, GoDaddy domain coupon).
- [ ] Generate API keys, store in a private gist or 1Password — DO NOT commit.
- [ ] Install locally: Python 3.11, `uv` or `venv`, MongoDB Compass (GUI), Postman/Insomnia.
- [ ] Clone repo, confirm I can `git push` to my branch.
- [ ] Skim FastAPI WebSocket docs + `motor` async MongoDB driver — these are my main tools.
- [ ] Decide: deploy via `uvicorn` + `nginx` reverse proxy on Vultr (simplest). No Docker unless time allows.

---

## Hour-by-Hour Plan

### Phase 1 — Foundation (Hours 0–3, Fri 7–10 PM)

**Goal:** A working FastAPI server with MongoDB connected and `/cameras` CRUD endpoints live locally.

- [ ] **H0 (15 min):** Repo setup — create `backend/` directory, `requirements.txt`, `.env.example`, `.gitignore` for `.env` and `__pycache__/`.
- [ ] **H0–1:** Scaffold `backend/main.py`, `backend/database.py`, `backend/models.py` per Task 5 in main plan.
- [ ] **H1:** Spin up MongoDB Atlas free cluster, get connection string, test ping from `database.py`.
- [ ] **H1–2:** Build `backend/routers/cameras.py` — POST, GET, GET/:id, PUT/:id, DELETE/:id.
- [ ] **H2–3:** Test all endpoints with Postman. Commit: `feat(backend): cameras CRUD + Mongo wiring`.

**Deliverable to team:** Backend runs at `http://localhost:8000`, OpenAPI docs at `/docs`. Tell Jonny so he can start hitting it from frontend.

**Integration handoff:** Send Jonny the Pydantic schema for `Camera` so his frontend types match.

---

### Phase 2 — WebSockets (Hours 3–7, Fri 10 PM – Sat 2 AM)

**Goal:** Frontend can subscribe to live frames per camera and a global event stream.

- [ ] **H3–4:** Create `backend/routers/websocket.py`. Two endpoints:
  - `WS /ws/stream/:camera_id` — pushes JPEG frames (base64) at 1 fps.
  - `WS /ws/events` — pushes new event objects when pipeline completes.
- [ ] **H4–5:** Build a `ConnectionManager` class to fan out messages to all subscribers per camera. Stub frame source with a placeholder JPEG until Sartaj's `stream_manager.py` lands.
- [ ] **H5–6:** Test with `websocat` or a tiny HTML page. Confirm reconnect logic works (frontend dropping/rejoining).
- [ ] **H6–7:** Wire Sartaj's `stream_manager` (when ready) into the WS — his service pushes frames into a shared queue, my WS reads from it.

**Deliverable:** Jonny can render a live camera grid pulling from `/ws/stream/:id`.

**Risk:** WebSocket auth is YAGNI for the demo. Skip auth, add an env-var "API key" header check at most.

---

### Phase 3 — Event Pipeline (Hours 7–11, Sat 2–6 AM) ⚠️ CRITICAL

**Goal:** When the classifier flags a frame, the full chain runs and the event lands in Mongo + WS push.

- [ ] **H7–8:** Build `backend/services/cloudinary_upload.py` — async function `upload_frames(frames: list[bytes]) -> list[str]` returning Cloudinary URLs. Same for audio.
- [ ] **H8–10:** Build `backend/services/event_pipeline.py` — orchestrator:
  1. Receive `(camera_id, frames, confidence)` from classifier.
  2. Call `reasoning.describe(frames, context)` → text. (Sartaj's module.)
  3. Call `narration.synthesize(text)` → audio bytes. (Sartaj's module.)
  4. Upload frames + audio to Cloudinary (parallel via `asyncio.gather`).
  5. Insert event doc into MongoDB.
  6. Call `solana_logger.log(event_hash)` → tx_id. (Jonny's module — wrap in try/except, never let chain failure break the pipeline.)
  7. Update Mongo doc with `solana_tx`.
  8. Broadcast event over `WS /ws/events`.
- [ ] **H10–11:** Build `backend/routers/events.py` — `GET /events` (filterable by camera_id, date range, limit) + `GET /events/:id`.

**Deliverable:** Trigger pipeline manually with a curl command (`POST /test/trigger-event`) — see full chain execute end-to-end. Show team a working dummy event in Mongo + a WS message arriving in browser console.

**Failure modes to guard:**
- ElevenLabs rate limits → cache audio, fallback to "narration unavailable" text.
- Cloudinary upload failures → still write event to Mongo without media URLs, mark as degraded.
- Gemma timeout → 10s timeout, fallback description "Notable activity detected at <camera>".
- Solana failure → log warning, continue (it's a "nice to have" tamper-proof receipt, not a blocker).

---

### Phase 4 — Integration (Hours 11–14, Sat 6–9 AM)

**Goal:** All three of our work converges. The system runs end-to-end with a real public camera stream.

- [ ] **H11–12:** Pair with Sartaj — wire his `classifier.py` into `stream_manager.py` and confirm it calls into my `event_pipeline.run(...)`.
- [ ] **H12–13:** Pair with Jonny — confirm frontend renders live frames + receives event WS messages + shows toast/audio playback.
- [ ] **H13–14:** Add a public test camera (try one from `insecam.org` or a YouTube live RTSP rebroadcast). Run for 10 minutes, watch for memory leaks / dropped connections.

**Deliverable:** A working demo path — add camera → see it live → trigger event → hear narration. Record a 30-sec screen capture as a backup if live demo fails.

**Buffer block:** If Sartaj's model isn't ready by H13, ship with a stub classifier that flags every 30th frame so the pipeline still demos.

---

### Phase 5 — Deploy + Domain (Hours 14–16, Sat 9–11 AM)

**Goal:** Public URL on a real domain. No more localhost.

- [ ] **H14:** Lock GoDaddy domain (something memorable: `sentinelai.live`, `seenotable.com`, etc.). Point A record to Vultr IP.
- [ ] **H14–15:** On the Vultr GPU box: `git pull`, `pip install -r requirements.txt`, set `.env`, run `uvicorn` under `systemd` so it survives SSH disconnect.
- [ ] **H15:** Install nginx, reverse-proxy `:443` → `:8000`. Use `certbot` for free SSL (Let's Encrypt). HTTPS is required for browser WebSockets in some configs.
- [ ] **H15–16:** Update frontend env to point at `https://<my-domain>`. Smoke test from Jonny's laptop.

**Deliverable:** `https://sentinelai.live` (or whatever) loads a working dashboard.

**Submission requirement:** GoDaddy "Best Domain" prize wants the live deployment on the registered domain — confirm both work before the deadline.

---

### Phase 6 — Demo Prep + Submission (Hours 16–18, Sat 11 AM – 1 PM, then sleep)

- [ ] Write Devpost submission draft (project name, tagline, tech list, sponsor list, problem statement, social impact angle, build process).
- [ ] Record a 2-min demo video as backup.
- [ ] Sleep. Seriously. Sat afternoon → Sun 5 AM.

### Phase 7 — Sunday Buffer (Sun 5–7 AM)

- [ ] Smoke test the deployed site cold.
- [ ] Final Devpost edits.
- [ ] Tag all 11 prize categories.
- [ ] Submit by 8 AM PDT — DO NOT miss the deadline. Aim for 7 AM submission.

---

## Files I Own

```
backend/
├── main.py                       (FastAPI app, CORS, router includes)
├── database.py                   (Mongo client, collections)
├── models.py                     (Pydantic: Camera, Event)
├── requirements.txt
├── routers/
│   ├── cameras.py                (CRUD)
│   ├── events.py                 (history queries)
│   └── websocket.py              (live stream + events)
└── services/
    ├── cloudinary_upload.py      (frame + audio upload)
    └── event_pipeline.py         (orchestrator)
```

## Files I Touch but Don't Own

- `backend/services/classifier.py` (Sartaj) — I call into it
- `backend/services/stream_manager.py` (Sartaj) — I consume frames from its queue
- `backend/services/reasoning.py` (Sartaj) — I call `describe()`
- `backend/services/narration.py` (Sartaj) — I call `synthesize()`
- `backend/services/solana_logger.py` (Jonny) — I call `log()` from pipeline

---

## Integration Contracts (lock these EARLY with team)

**With Sartaj:**
```python
# stream_manager exposes:
async def get_frame_queue(camera_id: str) -> asyncio.Queue[bytes]
async def get_buffer_window(camera_id: str, before_s: int, after_s: int) -> list[bytes]

# classifier exposes:
async def classify(frame: bytes) -> float  # returns 0-1 confidence
on_notable_callback: Callable[[str, list[bytes], float], None]  # I register my pipeline here

# reasoning exposes:
async def describe(frames: list[bytes], context: str) -> str

# narration exposes:
async def synthesize(text: str) -> bytes  # mp3 audio
```

**With Jonny:**
```python
# solana_logger exposes:
async def log(event_hash: str, camera_id: str, ts: int) -> str  # returns tx signature

# Frontend WS message shape (events):
{"type": "event", "data": {<full event doc>}}

# Frontend WS message shape (frames):
{"type": "frame", "camera_id": "...", "jpeg_b64": "...", "ts": 123}
```

**Lock these contracts in a Slack/Discord pin at H1 so nobody is blocked.**

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Mongo Atlas IP allowlist blocks Vultr | High | Set allowlist to 0.0.0.0/0 for hackathon (insecure but fine) |
| ElevenLabs free tier credits run out | Medium | Pre-seed quota, cache narrations, fallback to text |
| WebSocket disconnect storm during demo | Medium | Add reconnect-with-backoff on frontend; server-side keepalive ping |
| Sartaj's model not done by H13 | Medium | Stub classifier that fires every N frames |
| Gemma quota limits | Low | Cache by frame hash; fallback canned description |
| Vultr GPU instance crashes mid-demo | Low | Keep a `tmux` session, `systemd` auto-restart, recorded backup demo |
| Solana devnet RPC down | Low | Wrap in try/except, never block pipeline on chain |
| Forget to submit by 8 AM | Catastrophic | Set 3 alarms. Submit by 7 AM. |

---

## Decision Log (fill as I go)

- [ ] Final domain choice: ___
- [ ] Mongo cluster region: ___
- [ ] Vultr instance public IP: ___
- [ ] Auth strategy for backend: none / API key header (decide H1)
- [ ] Frame transport format: base64 JPEG over WS (default) vs binary frames (faster but more code)

---

## Done = Demo-Ready Checklist

- [ ] Public HTTPS URL works from any laptop
- [ ] Add-camera flow works in <30s
- [ ] Live frames render in <2s of stream connect
- [ ] An event triggers narration audio in <15s of classifier flag
- [ ] Event appears in history page with Cloudinary thumbnail
- [ ] Solana tx link clickable on at least one event
- [ ] Backend has been running for >2h without restart
- [ ] Devpost submitted
- [ ] All 11 prize categories selected on Devpost

🎯 Ship it.
