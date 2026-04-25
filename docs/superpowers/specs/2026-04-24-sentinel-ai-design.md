# SentinelAI — Design Spec

**Date:** 2026-04-24
**Team size:** 3
**Hackathon:** LA Hacks 2026 (April 25-26, 36 hours)
**Hacking window:** Friday 7 PM — Sunday 7 AM PDT
**Submission deadline:** Sunday 8 AM PDT

## One-Liner

A live security camera monitoring platform that uses a custom-trained neural network to detect notable events, Gemma to reason about what happened, and ElevenLabs to narrate it to you in real-time.

## Target Challenges

| # | Challenge | Prize |
|---|-----------|-------|
| 1 | Arista — Connect the Dots | Claude Pro 12mo + Bose QC Headphones |
| 2 | Cloudinary Challenge | $500 Amazon gift card per member |
| 3 | Flicker to Flow (main track) | Keurig K-Mini |
| 4 | MLH x GoDaddy — Best Domain | Digital gift card |
| 5 | MLH x Solana | Solana Ledger |
| 6 | MLH x Vultr | Portable screens |
| 7 | MLH x MongoDB | MongoDB Atlas kit |
| 8 | MLH x ElevenLabs | ElevenLabs earbuds |
| 9 | Best UI/UX | Wacom Intuos Tablet |
| 10 | Best Social Impact | JBL Flip 5 |
| 11 | Sponsormaxxing | Amazon Echo Show |

## Core Flow

```
Public camera streams (RTSP/MJPEG)
  -> Frame extraction (1 fps)
  -> Circular buffer (keeps last 60s per camera, fallback on stream drop)
  -> Custom-trained ResNet-18 classifier on Vultr GPU
  -> Frame flagged notable?
      -> NO: discard, continue
      -> YES: grab 10s before + 5s after from buffer (~16 frames)
          -> Gemma analyzes frame sequence with camera's custom context
          -> ElevenLabs narrates the event description
          -> Event stored in MongoDB (metadata + frames via Cloudinary)
          -> Event hash logged on Solana (tamper-proof record)
          -> Dashboard updates live (WebSocket)
          -> Audio narration plays in browser
```

## Frontend Architecture

**Stack:** React 19 + Vite + TypeScript via `create-cloudinary-react`

### Pages

**1. Dashboard (main view)**
- Grid of live camera feeds, each showing the stream in real-time
- Each camera card shows: stream, name, custom context label ("Watching for: people taking food")
- Notable event toast pops up with narration audio when detected
- Global event counter and status indicators per camera

**2. Camera Setup**
- Add a camera: paste a public stream URL, give it a name
- Set custom context: text field for what to watch for ("alert me when someone approaches the car")
- Preview the stream before saving

**3. Event History**
- Timeline of all notable events across all cameras
- Each event: timestamp, camera name, Cloudinary-hosted thumbnail/clip, Gemma's description, audio playback button
- Filterable by camera, date range, severity
- Solana transaction link per event (proof of tamper-proof logging)

**4. Training Dashboard (stretch goal / demo talking point)**
- Model training stats: accuracy, loss curves
- "We trained this on X frames from Y hours of footage on Vultr GPUs"

**Real-time updates:** WebSocket connection from backend pushes new events instantly.

**Cloudinary usage:**
- All event thumbnails/frames uploaded via Cloudinary SDK
- Image transformations for thumbnail grids (auto-resize, optimization)
- Upload widget for any manual footage uploads

## Backend Architecture

**Stack:** Python (FastAPI) deployed on Vultr

### Services

**1. Stream Manager**
- Connects to camera RTSP/MJPEG URLs via OpenCV
- Extracts 1 frame per second from each active camera
- Maintains 60-second circular buffer per camera (fallback + event context)
- If stream drops, replays buffer on loop until reconnection
- Pushes frames to frontend via WebSocket for live display

**2. Classifier Service**
- Loads fine-tuned ResNet-18 model
- Runs inference on each extracted frame
- Returns confidence score (0-1) for "notable"
- Threshold configurable per camera (default 0.7)
- Runs on Vultr GPU for fast inference (~10-20ms per frame)

**3. Reasoning Service (Gemma 4)**
- Triggered when classifier flags a frame above threshold
- Waits 5 seconds to capture post-event frames
- Grabs 10s before + flagged frame + 5s after = ~16 frames
- Sends to Gemma with camera's custom context prompt
- Returns natural language event description

**4. Narration Service (ElevenLabs)**
- Takes Gemma's event description text
- Sends to ElevenLabs TTS API
- Returns audio file, stored in Cloudinary
- Streams to frontend for immediate playback

**5. Event Pipeline (storage + chain)**
- Uploads event frames/thumbnail to Cloudinary
- Writes event record to MongoDB (timestamp, camera ID, description, Cloudinary URLs, audio URL, confidence score)
- Hashes event data and writes to Solana as tamper-proof log
- Pushes event to frontend via WebSocket

### API Endpoints

```
POST   /cameras          — add a camera stream
GET    /cameras          — list all cameras
PUT    /cameras/:id      — update camera context/settings
DELETE /cameras/:id      — remove a camera
GET    /events           — query event history (filterable)
GET    /events/:id       — single event detail
WS     /ws/stream/:id    — live frames for a camera
WS     /ws/events        — real-time event notifications
```

## Data Models

### MongoDB: cameras

```json
{
  "_id": "ObjectId",
  "name": "Office Fridge",
  "stream_url": "http://public-cam-url/stream",
  "context": "Watch for people taking food",
  "threshold": 0.7,
  "status": "active",
  "created_at": "timestamp"
}
```

### MongoDB: events

```json
{
  "_id": "ObjectId",
  "camera_id": "ObjectId",
  "timestamp": "2026-04-25T03:42:15Z",
  "confidence": 0.92,
  "description": "Person in blue hoodie opened fridge, removed a container, walked away",
  "frames": [
    "https://res.cloudinary.com/xxx/frame_01.jpg",
    "https://res.cloudinary.com/xxx/frame_02.jpg"
  ],
  "thumbnail": "https://res.cloudinary.com/xxx/thumb.jpg",
  "audio_url": "https://res.cloudinary.com/xxx/narration.mp3",
  "solana_tx": "5xK9...transaction_hash",
  "context_used": "Watch for people taking food"
}
```

### Solana On-Chain (per event)

```json
{
  "event_hash": "sha256 of event data",
  "camera_id": "string",
  "timestamp": "unix timestamp",
  "description_hash": "sha256 of description"
}
```

Lightweight hashes only on-chain. Full data lives in MongoDB. Uses `@solana/web3.js` on devnet — no real SOL required.

## Model Training Pipeline

**Runs on Vultr Cloud GPU during hacking window.**

**Step 1: Data Collection (~2 hours)**
- Pull public security camera footage from YouTube
- Target: 3-5 hours of raw footage across camera types (parking lots, indoor, storefronts)
- Extract frames at 1fps = ~10,000-18,000 frames

**Step 2: Labeling (~1.5 hours)**
- Watch source videos at 2x speed, note timestamps of notable events
- Script auto-labels: frames in event ranges = "notable", rest = "mundane"
- Expected split: ~85% mundane, ~15% notable
- Data augmentation (flips, brightness) to balance classes

**Step 3: Training (~30 min on GPU)**
- Model: ResNet-18, pretrained on ImageNet
- Freeze all layers except last block + new classification head (2 classes)
- Fine-tune on labeled dataset
- Hyperparameters: lr=0.001, batch_size=32, epochs=10-15
- Validation split: 80/20

**Step 4: Export + Deploy**
- Export to ONNX or TorchScript for fast inference
- Deploy on same Vultr GPU instance as backend
- Inference: ~10-20ms per frame, handles multiple cameras at 1fps easily

## Sponsor Integration Map

| Sponsor | Integration | Role |
|---------|-------------|------|
| Cloudinary | React starter kit, all media storage + transformations | Core |
| Vultr | GPU training + backend hosting | Core |
| MongoDB | Camera configs + event history | Core |
| Gemma 4 | LLM reasoning over frame sequences with custom context | Core |
| ElevenLabs | TTS narration of notable events | Core feature |
| Solana | Tamper-proof on-chain event log | Adds security value |
| GoDaddy | Domain registration, point to deployed app | 5 min effort |
| Arista | Entire project is "routing camera data to users" | It IS the project |
| Figma | Design UI in Figma before building | Figma Make plushies |

**9 sponsor integrations. 11 prize category submissions.**

## Social Impact Angle

Audio narration makes security monitoring accessible to visually impaired users. Instead of watching screens, they hear what's happening. Frame it as: "Security monitoring shouldn't require constant screen-watching."

## Key Demo Moments

1. Add a public camera stream live in front of judges
2. Type custom context: "Watch for people walking near the entrance"
3. System detects an event, narrates it out loud in real-time
4. Show event history with Cloudinary thumbnails and Solana proof links
5. Show training dashboard: "We trained our own model on X hours of footage"
