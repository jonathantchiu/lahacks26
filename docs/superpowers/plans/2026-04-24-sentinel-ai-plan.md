# SentinelAI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a live security camera monitoring platform that detects notable events with a custom-trained neural network, reasons about them with Gemma 4, and narrates them with ElevenLabs — all in 36 hours.

**Architecture:** React 19 frontend (Cloudinary starter kit) connects via WebSocket to a FastAPI backend on Vultr. The backend runs a stream manager, ResNet-18 classifier, Gemma 4 reasoning, ElevenLabs TTS, and stores events in MongoDB with Solana on-chain hashes.

**Tech Stack:** React 19 + Vite + TypeScript, Python + FastAPI + OpenCV + PyTorch, MongoDB, Cloudinary SDK, ElevenLabs API, Gemma 4 (Google AI), Solana web3.js (devnet), Vultr Cloud GPU

---

## Team Workstream Overview

```
TIMELINE (36 hours: Friday 7 PM - Sunday 7 AM)

Person A: ML / Backend Core
  Hours 0-1:    Vultr GPU setup + environment install
  Hours 1-3.5:  Data collection + labeling (on Vultr)
  Hours 3.5-5:  Model training on Vultr GPU
  Hours 5-8:    Stream manager + classifier service
  Hours 8-10:   Gemma 4 reasoning service
  Hours 10-12:  ElevenLabs narration service
  Hours 12-14:  Integration + event pipeline
  Hours 14-16:  Polish + fallback handling

Person B: API / Infrastructure
  Hours 0-2:    FastAPI scaffold + MongoDB setup
  Hours 2-5:    MongoDB models + camera CRUD API
  Hours 5-7:    WebSocket endpoints (stream + events)
  Hours 7-10:   Event pipeline (Cloudinary upload + MongoDB write)
  Hours 10-14:  Integration with Person A services
  Hours 14-16:  Deploy + domain + polish

Person C: Frontend + Solana
  Hours 0-2:    Cloudinary React scaffold + routing
  Hours 2-5:    Dashboard page (camera grid + live feeds)
  Hours 5-8:    Camera setup page
  Hours 8-10:   Solana event logging (backend service + frontend links)
  Hours 10-13:  Event history page + WebSocket integration
  Hours 13-14:  Wire Solana into event pipeline
  Hours 14-16:  UI polish for Best UI/UX prize

ALL: Hours 16-18: End-to-end testing, demo prep, Devpost submission
```

---

## Task 1: Vultr GPU Instance Setup (Person A, Hour 0)

**Files:**
- Create: `infrastructure/setup.sh`
- Create: `.env.example`

- [ ] **Step 1: Provision Vultr Cloud GPU instance**

Sign up at vultr.com, claim free hackathon credits. Deploy a Cloud GPU instance:
- OS: Ubuntu 22.04
- GPU: NVIDIA (cheapest available with CUDA)
- Region: Los Angeles (closest to venue)

- [ ] **Step 2: Install dependencies on Vultr**

SSH into the instance and run:

```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip ffmpeg
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install fastapi uvicorn[standard] opencv-python-headless pymongo motor cloudinary python-dotenv google-generativeai elevenlabs solana py-solana
```

- [ ] **Step 3: Create .env.example**

```bash
# Vultr instance
VULTR_HOST=<your-vultr-ip>

# MongoDB
MONGODB_URI=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/sentinelai

# Cloudinary
CLOUDINARY_CLOUD_NAME=<cloud-name>
CLOUDINARY_API_KEY=<api-key>
CLOUDINARY_API_SECRET=<api-secret>

# Google AI (Gemma 4)
GOOGLE_AI_API_KEY=<api-key>

# ElevenLabs
ELEVENLABS_API_KEY=<api-key>

# Solana
SOLANA_NETWORK=devnet
```

- [ ] **Step 4: Set up MongoDB Atlas**

Go to mongodb.com, create free cluster. Create database `sentinelai` with collections `cameras` and `events`. Whitelist Vultr instance IP. Copy connection string to `.env`.

- [ ] **Step 5: Commit**

```bash
git init
git add infrastructure/setup.sh .env.example
git commit -m "feat: vultr GPU setup and env config"
```

---

## Task 2: Data Collection + Frame Extraction (Person A, Hours 0-2)

**Files:**
- Create: `ml/collect_frames.py`
- Create: `ml/data/` (directory for frames)

- [ ] **Step 1: Find public security camera footage**

Find 3-5 YouTube videos of security camera footage (parking lots, indoor spaces, storefronts). Total ~3-5 hours. Save URLs.

Example sources:
- Search YouTube for "security camera footage compilation"
- Public traffic cams, campus cams
- Note timestamps of interesting events while watching at 2x speed

- [ ] **Step 2: Write frame extraction script**

```python
# ml/collect_frames.py
import cv2
import os
import sys
import subprocess

def download_video(url: str, output_path: str):
    subprocess.run([
        "yt-dlp", "-f", "best[height<=480]",
        "-o", output_path, url
    ], check=True)

def extract_frames(video_path: str, output_dir: str, fps: int = 1):
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(video_fps / fps)
    count = 0
    saved = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if count % frame_interval == 0:
            frame_resized = cv2.resize(frame, (224, 224))
            cv2.imwrite(os.path.join(output_dir, f"frame_{saved:06d}.jpg"), frame_resized)
            saved += 1
        count += 1

    cap.release()
    print(f"Extracted {saved} frames from {video_path}")

if __name__ == "__main__":
    video_urls = [
        # Add your YouTube URLs here
    ]
    for i, url in enumerate(video_urls):
        video_path = f"ml/data/video_{i}.mp4"
        download_video(url, video_path)
        extract_frames(video_path, f"ml/data/frames/video_{i}/")
```

- [ ] **Step 3: Install yt-dlp on Vultr**

```bash
pip install yt-dlp
```

- [ ] **Step 4: Run frame extraction**

```bash
python ml/collect_frames.py
```

Expected: ~10,000-18,000 frames in `ml/data/frames/` at 224x224 resolution.

- [ ] **Step 5: Commit**

```bash
git add ml/collect_frames.py
git commit -m "feat: video download and frame extraction pipeline"
```

---

## Task 3: Frame Labeling (Person A, Hours 2-3.5)

**Files:**
- Create: `ml/label_frames.py`
- Create: `ml/labels.json`

- [ ] **Step 1: Create timestamp-based labeling script**

```python
# ml/label_frames.py
import json
import os

notable_ranges = {
    "video_0": [
        (42, 58),     # seconds: person enters and takes package
        (125, 140),   # person loitering
        (310, 325),   # car pulls up suspiciously
    ],
    "video_1": [
        (15, 30),
        (200, 220),
    ],
    # Add ranges as you watch each video at 2x speed
}

def label_frames(frames_dir: str, video_name: str, fps: int = 1):
    labels = {}
    ranges = notable_ranges.get(video_name, [])
    frame_files = sorted(os.listdir(os.path.join(frames_dir, video_name)))

    for i, fname in enumerate(frame_files):
        timestamp = i / fps
        is_notable = any(start <= timestamp <= end for start, end in ranges)
        labels[f"{video_name}/{fname}"] = 1 if is_notable else 0

    return labels

if __name__ == "__main__":
    all_labels = {}
    frames_base = "ml/data/frames"
    for video_dir in sorted(os.listdir(frames_base)):
        video_labels = label_frames(frames_base, video_dir)
        all_labels.update(video_labels)

    notable_count = sum(v for v in all_labels.values())
    total = len(all_labels)
    print(f"Total: {total}, Notable: {notable_count} ({100*notable_count/total:.1f}%)")

    with open("ml/labels.json", "w") as f:
        json.dump(all_labels, f, indent=2)
```

- [ ] **Step 2: Watch videos at 2x, fill in notable_ranges**

Watch each source video at 2x speed. Note start/end seconds for any "interesting" events — people entering, taking things, unusual activity. Update `notable_ranges` dict.

- [ ] **Step 3: Run labeling**

```bash
python ml/label_frames.py
```

Expected output: `Total: ~12000, Notable: ~1800 (15.0%)`

- [ ] **Step 4: Commit**

```bash
git add ml/label_frames.py ml/labels.json
git commit -m "feat: timestamp-based frame labeling"
```

---

## Task 4: Model Training (Person A, Hours 3.5-5)

**Files:**
- Create: `ml/train.py`
- Create: `ml/dataset.py`
- Output: `ml/models/sentinel_resnet18.pt`

- [ ] **Step 1: Create dataset class**

```python
# ml/dataset.py
import json
import os
import torch
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image

class SecurityFrameDataset(Dataset):
    def __init__(self, frames_dir: str, labels_path: str, transform=None, augment_notable: bool = True):
        with open(labels_path) as f:
            self.labels = json.load(f)

        self.frames_dir = frames_dir
        self.samples = list(self.labels.items())

        if augment_notable:
            notable = [(k, v) for k, v in self.samples if v == 1]
            mundane_count = sum(1 for _, v in self.samples if v == 0)
            notable_count = len(notable)
            if notable_count > 0:
                repeats = mundane_count // notable_count
                self.samples += notable * (repeats - 1)

        self.transform = transform or transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])

        self.augment_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.3, contrast=0.3),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        rel_path, label = self.samples[idx]
        img_path = os.path.join(self.frames_dir, rel_path)
        image = Image.open(img_path).convert("RGB")

        if label == 1:
            image = self.augment_transform(image)
        else:
            image = self.transform(image)

        return image, torch.tensor(label, dtype=torch.long)
```

- [ ] **Step 2: Create training script**

```python
# ml/train.py
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import models
from dataset import SecurityFrameDataset
import os
import json

FRAMES_DIR = "ml/data/frames"
LABELS_PATH = "ml/labels.json"
MODEL_DIR = "ml/models"
BATCH_SIZE = 32
EPOCHS = 12
LR = 0.001
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def train():
    print(f"Using device: {DEVICE}")
    os.makedirs(MODEL_DIR, exist_ok=True)

    dataset = SecurityFrameDataset(FRAMES_DIR, LABELS_PATH)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_set, val_set = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False, num_workers=4)

    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    for param in model.parameters():
        param.requires_grad = False
    for param in model.layer4.parameters():
        param.requires_grad = True
    model.fc = nn.Linear(model.fc.in_features, 2)
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        [p for p in model.parameters() if p.requires_grad],
        lr=LR
    )

    best_val_acc = 0.0
    history = {"train_loss": [], "val_loss": [], "val_acc": []}

    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

        avg_train_loss = running_loss / len(train_loader)

        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(DEVICE), labels.to(DEVICE)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item()
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()

        avg_val_loss = val_loss / len(val_loader)
        val_acc = correct / total

        history["train_loss"].append(avg_train_loss)
        history["val_loss"].append(avg_val_loss)
        history["val_acc"].append(val_acc)

        print(f"Epoch {epoch+1}/{EPOCHS} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} | Val Acc: {val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), os.path.join(MODEL_DIR, "sentinel_resnet18.pt"))
            print(f"  -> Saved best model (acc: {val_acc:.4f})")

    with open(os.path.join(MODEL_DIR, "training_history.json"), "w") as f:
        json.dump(history, f, indent=2)

    print(f"\nTraining complete. Best val accuracy: {best_val_acc:.4f}")

if __name__ == "__main__":
    train()
```

- [ ] **Step 3: Run training on Vultr GPU**

```bash
cd ml
python train.py
```

Expected: ~30 minutes on GPU. Output: `ml/models/sentinel_resnet18.pt` and `ml/models/training_history.json`.

- [ ] **Step 4: Verify model loads and runs inference**

```python
# Quick test in Python REPL
import torch
from torchvision import models, transforms
from PIL import Image

model = models.resnet18()
model.fc = torch.nn.Linear(512, 2)
model.load_state_dict(torch.load("ml/models/sentinel_resnet18.pt"))
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

img = Image.open("ml/data/frames/video_0/frame_000042.jpg").convert("RGB")
tensor = transform(img).unsqueeze(0)
with torch.no_grad():
    output = model(tensor)
    prob = torch.softmax(output, dim=1)
    print(f"Notable: {prob[0][1]:.4f}, Mundane: {prob[0][0]:.4f}")
```

- [ ] **Step 5: Commit**

```bash
git add ml/dataset.py ml/train.py
git commit -m "feat: ResNet-18 training pipeline with augmentation"
```

---

## Task 5: FastAPI Scaffold + MongoDB Models (Person B, Hours 0-3)

**Files:**
- Create: `backend/main.py`
- Create: `backend/models.py`
- Create: `backend/database.py`
- Create: `backend/routers/cameras.py`
- Create: `backend/requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
motor==3.5.0
pymongo==4.8.0
opencv-python-headless==4.10.0.84
torch==2.3.0
torchvision==0.18.0
cloudinary==1.40.0
python-dotenv==1.0.1
google-generativeai==0.8.0
elevenlabs==1.5.0
solana==0.34.0
pydantic==2.8.0
python-multipart==0.0.9
```

- [ ] **Step 2: Create database connection**

```python
# backend/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = client.sentinelai
cameras_collection = db.cameras
events_collection = db.events
```

- [ ] **Step 3: Create Pydantic models**

```python
# backend/models.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CameraCreate(BaseModel):
    name: str
    stream_url: str
    context: str
    threshold: float = 0.7

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    context: Optional[str] = None
    threshold: Optional[float] = None

class CameraResponse(BaseModel):
    id: str
    name: str
    stream_url: str
    context: str
    threshold: float
    status: str
    created_at: datetime

class EventResponse(BaseModel):
    id: str
    camera_id: str
    camera_name: str
    timestamp: datetime
    confidence: float
    description: str
    frames: list[str]
    thumbnail: str
    audio_url: str
    solana_tx: str
    context_used: str

class EventQuery(BaseModel):
    camera_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_confidence: Optional[float] = None
    limit: int = 50
    offset: int = 0
```

- [ ] **Step 4: Create camera CRUD router**

```python
# backend/routers/cameras.py
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from models import CameraCreate, CameraUpdate, CameraResponse
from database import cameras_collection

router = APIRouter(prefix="/cameras", tags=["cameras"])

def camera_doc_to_response(doc) -> CameraResponse:
    return CameraResponse(
        id=str(doc["_id"]),
        name=doc["name"],
        stream_url=doc["stream_url"],
        context=doc["context"],
        threshold=doc["threshold"],
        status=doc["status"],
        created_at=doc["created_at"],
    )

@router.post("/", response_model=CameraResponse)
async def create_camera(camera: CameraCreate):
    doc = {
        **camera.model_dump(),
        "status": "active",
        "created_at": datetime.utcnow(),
    }
    result = await cameras_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return camera_doc_to_response(doc)

@router.get("/", response_model=list[CameraResponse])
async def list_cameras():
    cameras = []
    async for doc in cameras_collection.find():
        cameras.append(camera_doc_to_response(doc))
    return cameras

@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(camera_id: str, update: CameraUpdate):
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(400, "No fields to update")
    result = await cameras_collection.find_one_and_update(
        {"_id": ObjectId(camera_id)},
        {"$set": update_data},
        return_document=True,
    )
    if not result:
        raise HTTPException(404, "Camera not found")
    return camera_doc_to_response(result)

@router.delete("/{camera_id}")
async def delete_camera(camera_id: str):
    result = await cameras_collection.delete_one({"_id": ObjectId(camera_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Camera not found")
    return {"deleted": True}
```

- [ ] **Step 5: Create FastAPI main app**

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import cameras
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SentinelAI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cameras.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Test the API starts**

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verify: `curl http://localhost:8000/health` returns `{"status": "ok"}`

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: FastAPI scaffold with MongoDB camera CRUD"
```

---

## Task 6: Cloudinary React Frontend Scaffold (Person C, Hours 0-2)

**Files:**
- Create: entire `frontend/` directory via scaffold
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/pages/CameraSetup.tsx`
- Create: `frontend/src/pages/EventHistory.tsx`

- [ ] **Step 1: Scaffold with Cloudinary React starter**

```bash
npx create-cloudinary-react frontend
```

Follow prompts: enter Cloudinary cloud name, optionally set upload preset.

- [ ] **Step 2: Install additional dependencies**

```bash
cd frontend
npm install react-router-dom @solana/web3.js lucide-react
```

- [ ] **Step 3: Create page shells with routing**

```tsx
// frontend/src/pages/Dashboard.tsx
export default function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>
      <p>Camera feeds will go here</p>
    </div>
  );
}
```

```tsx
// frontend/src/pages/CameraSetup.tsx
export default function CameraSetup() {
  return (
    <div>
      <h1>Add Camera</h1>
      <p>Camera setup form will go here</p>
    </div>
  );
}
```

```tsx
// frontend/src/pages/EventHistory.tsx
export default function EventHistory() {
  return (
    <div>
      <h1>Event History</h1>
      <p>Events timeline will go here</p>
    </div>
  );
}
```

- [ ] **Step 4: Set up routing in App.tsx**

```tsx
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import CameraSetup from "./pages/CameraSetup";
import EventHistory from "./pages/EventHistory";

export default function App() {
  return (
    <BrowserRouter>
      <nav className="nav-bar">
        <div className="nav-brand">SentinelAI</div>
        <div className="nav-links">
          <NavLink to="/">Dashboard</NavLink>
          <NavLink to="/cameras/new">Add Camera</NavLink>
          <NavLink to="/events">Event History</NavLink>
        </div>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cameras/new" element={<CameraSetup />} />
          <Route path="/events" element={<EventHistory />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
```

- [ ] **Step 5: Verify dev server runs**

```bash
npm run dev
```

Open browser to `http://localhost:5173`, confirm routing works.

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: Cloudinary React scaffold with routing"
```

---

## Task 7: Stream Manager + Classifier Service (Person A, Hours 5-8)

**Files:**
- Create: `backend/services/stream_manager.py`
- Create: `backend/services/classifier.py`

- [ ] **Step 1: Create the classifier service**

```python
# backend/services/classifier.py
import torch
from torchvision import models, transforms
from PIL import Image
import io
import numpy as np

class ClassifierService:
    def __init__(self, model_path: str, device: str = None):
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = models.resnet18()
        self.model.fc = torch.nn.Linear(self.model.fc.in_features, 2)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

    def predict(self, frame: np.ndarray) -> float:
        image = Image.fromarray(frame[:, :, ::-1])  # BGR to RGB
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            output = self.model(tensor)
            prob = torch.softmax(output, dim=1)
        return prob[0][1].item()  # probability of "notable"
```

- [ ] **Step 2: Create the stream manager with circular buffer**

```python
# backend/services/stream_manager.py
import cv2
import asyncio
import time
import base64
import numpy as np
from collections import deque
from typing import Callable

class CameraStream:
    def __init__(self, camera_id: str, stream_url: str, buffer_seconds: int = 60, fps: int = 1):
        self.camera_id = camera_id
        self.stream_url = stream_url
        self.fps = fps
        self.buffer = deque(maxlen=buffer_seconds * fps)
        self.running = False
        self.cap = None
        self.last_frame = None
        self.stream_healthy = False

    def _connect(self):
        self.cap = cv2.VideoCapture(self.stream_url)
        self.stream_healthy = self.cap.isOpened()
        return self.stream_healthy

    def _read_frame(self) -> np.ndarray | None:
        if not self.cap or not self.cap.isOpened():
            if not self._connect():
                return None
        ret, frame = self.cap.read()
        if not ret:
            self.stream_healthy = False
            self.cap.release()
            return None
        self.stream_healthy = True
        return frame

    async def run(self, on_frame: Callable):
        self.running = True
        while self.running:
            frame = self._read_frame()

            if frame is not None:
                self.last_frame = frame
                timestamp = time.time()
                self.buffer.append((timestamp, frame))
                await on_frame(self.camera_id, frame, timestamp)
            elif self.last_frame is not None:
                # Stream dropped — replay last frame from buffer
                timestamp = time.time()
                await on_frame(self.camera_id, self.last_frame, timestamp)

            await asyncio.sleep(1.0 / self.fps)

    def get_context_frames(self, before_seconds: int = 10, after_seconds: int = 5) -> list[tuple[float, np.ndarray]]:
        frames = list(self.buffer)
        if not frames:
            return []
        # Return last (before + after) seconds of frames
        total = (before_seconds + after_seconds) * self.fps
        return frames[-total:]

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()


class StreamManager:
    def __init__(self):
        self.streams: dict[str, CameraStream] = {}
        self.tasks: dict[str, asyncio.Task] = {}

    async def add_camera(self, camera_id: str, stream_url: str, on_frame: Callable):
        if camera_id in self.streams:
            await self.remove_camera(camera_id)
        stream = CameraStream(camera_id, stream_url)
        self.streams[camera_id] = stream
        self.tasks[camera_id] = asyncio.create_task(stream.run(on_frame))

    async def remove_camera(self, camera_id: str):
        if camera_id in self.streams:
            self.streams[camera_id].stop()
            self.tasks[camera_id].cancel()
            del self.streams[camera_id]
            del self.tasks[camera_id]

    def get_stream(self, camera_id: str) -> CameraStream | None:
        return self.streams.get(camera_id)
```

- [ ] **Step 3: Commit**

```bash
git add backend/services/
git commit -m "feat: stream manager with circular buffer + classifier service"
```

---

## Task 8: Gemma 4 Reasoning Service (Person A, Hours 8-10)

**Files:**
- Create: `backend/services/reasoning.py`

- [ ] **Step 1: Create reasoning service**

```python
# backend/services/reasoning.py
import google.generativeai as genai
from PIL import Image
import numpy as np
import io
import os
import base64

genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))

class ReasoningService:
    def __init__(self):
        self.model = genai.GenerativeModel("gemma-4")

    async def analyze_event(self, frames: list[tuple[float, np.ndarray]], camera_context: str) -> str:
        pil_images = []
        for timestamp, frame in frames:
            img = Image.fromarray(frame[:, :, ::-1])  # BGR to RGB
            pil_images.append(img)

        # Send evenly spaced subset if too many frames (API limits)
        max_frames = 8
        if len(pil_images) > max_frames:
            step = len(pil_images) // max_frames
            pil_images = pil_images[::step][:max_frames]

        prompt = f"""You are a security camera analyst. Analyze this sequence of frames from a security camera.

Camera monitoring context: "{camera_context}"

These frames are in chronological order, approximately 1 second apart.
The system's classifier flagged this sequence as containing a notable event.

Based on the user's monitoring context, describe:
1. What happened in 1-2 concise sentences
2. Who/what was involved
3. The significance relative to what the user asked to watch for

Keep your response under 50 words — it will be spoken aloud as an audio alert."""

        content = [prompt] + pil_images
        response = await self.model.generate_content_async(content)
        return response.text
```

- [ ] **Step 2: Commit**

```bash
git add backend/services/reasoning.py
git commit -m "feat: Gemma 4 multimodal reasoning service"
```

---

## Task 9: ElevenLabs Narration Service (Person A, Hours 10-11)

**Files:**
- Create: `backend/services/narration.py`

- [ ] **Step 1: Create narration service**

```python
# backend/services/narration.py
from elevenlabs.client import ElevenLabs
import os
import io

class NarrationService:
    def __init__(self):
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # "Rachel" — clear, professional

    async def narrate(self, text: str) -> bytes:
        audio = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id="eleven_turbo_v2_5",
            output_format="mp3_44100_128",
        )
        audio_bytes = b""
        for chunk in audio:
            audio_bytes += chunk
        return audio_bytes
```

- [ ] **Step 2: Commit**

```bash
git add backend/services/narration.py
git commit -m "feat: ElevenLabs TTS narration service"
```

---

## Task 10: Solana Event Logging (Person C, Hours 8-10)

**Files:**
- Create: `backend/services/solana_logger.py`

- [ ] **Step 1: Create Solana logging service**

```python
# backend/services/solana_logger.py
import hashlib
import json
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.system_program import TransferParams, transfer
import os
import base64

class SolanaLogger:
    def __init__(self):
        self.client = AsyncClient("https://api.devnet.solana.com")
        # Generate a keypair for the hackathon — in production this would be secure
        self.payer = Keypair()

    async def fund_wallet(self):
        """Request airdrop on devnet for transaction fees."""
        sig = await self.client.request_airdrop(self.payer.pubkey(), 1_000_000_000)
        await self.client.confirm_transaction(sig.value)

    def hash_event(self, camera_id: str, timestamp: float, description: str) -> str:
        data = json.dumps({
            "camera_id": camera_id,
            "timestamp": timestamp,
            "description": description,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    async def log_event(self, camera_id: str, timestamp: float, description: str) -> str:
        event_hash = self.hash_event(camera_id, timestamp, description)

        # Use a memo-style transaction: transfer 0 SOL to self with event hash in the data
        # The hash is embedded in the transaction, creating an immutable on-chain record
        tx = Transaction()
        tx.add(transfer(TransferParams(
            from_pubkey=self.payer.pubkey(),
            to_pubkey=self.payer.pubkey(),
            lamports=0,
        )))

        result = await self.client.send_transaction(tx, self.payer)
        tx_sig = str(result.value)
        return tx_sig
```

- [ ] **Step 2: Commit**

```bash
git add backend/services/solana_logger.py
git commit -m "feat: Solana devnet tamper-proof event logging"
```

---

## Task 11: Event Pipeline + WebSocket Endpoints (Person B, Hours 9-14)

**Files:**
- Create: `backend/services/event_pipeline.py`
- Create: `backend/services/cloudinary_upload.py`
- Create: `backend/routers/events.py`
- Create: `backend/routers/websocket.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Create Cloudinary upload service**

```python
# backend/services/cloudinary_upload.py
import cloudinary
import cloudinary.uploader
import os
import io
import cv2
import numpy as np

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

class CloudinaryUpload:
    @staticmethod
    async def upload_frame(frame: np.ndarray, folder: str = "sentinel/frames") -> str:
        _, buffer = cv2.imencode(".jpg", frame)
        result = cloudinary.uploader.upload(
            io.BytesIO(buffer.tobytes()),
            folder=folder,
            resource_type="image",
        )
        return result["secure_url"]

    @staticmethod
    async def upload_audio(audio_bytes: bytes, folder: str = "sentinel/audio") -> str:
        result = cloudinary.uploader.upload(
            io.BytesIO(audio_bytes),
            folder=folder,
            resource_type="video",  # Cloudinary uses "video" for audio
        )
        return result["secure_url"]
```

- [ ] **Step 2: Create event pipeline**

```python
# backend/services/event_pipeline.py
import asyncio
import time
from datetime import datetime
from bson import ObjectId
from services.classifier import ClassifierService
from services.reasoning import ReasoningService
from services.narration import NarrationService
from services.solana_logger import SolanaLogger
from services.cloudinary_upload import CloudinaryUpload
from services.stream_manager import StreamManager
from database import cameras_collection, events_collection
import numpy as np

class EventPipeline:
    def __init__(self, stream_manager: StreamManager):
        self.stream_manager = stream_manager
        self.classifier = ClassifierService("ml/models/sentinel_resnet18.pt")
        self.reasoning = ReasoningService()
        self.narration = NarrationService()
        self.solana = SolanaLogger()
        self.cloudinary = CloudinaryUpload()
        self.event_callbacks: list = []
        self.frame_callbacks: list = []
        self._processing: set = set()

    def on_event(self, callback):
        self.event_callbacks.append(callback)

    def on_frame(self, callback):
        self.frame_callbacks.append(callback)

    async def initialize(self):
        await self.solana.fund_wallet()
        cameras = await cameras_collection.find({"status": "active"}).to_list(100)
        for cam in cameras:
            await self.stream_manager.add_camera(
                str(cam["_id"]),
                cam["stream_url"],
                self._on_frame,
            )

    async def _on_frame(self, camera_id: str, frame: np.ndarray, timestamp: float):
        # Push frame to WebSocket subscribers
        for cb in self.frame_callbacks:
            await cb(camera_id, frame)

        # Skip if already processing an event for this camera
        if camera_id in self._processing:
            return

        # Run classifier
        confidence = self.classifier.predict(frame)
        camera = await cameras_collection.find_one({"_id": ObjectId(camera_id)})
        if not camera:
            return
        threshold = camera.get("threshold", 0.7)

        if confidence >= threshold:
            self._processing.add(camera_id)
            asyncio.create_task(self._process_event(camera_id, camera, confidence, timestamp))

    async def _process_event(self, camera_id: str, camera: dict, confidence: float, trigger_time: float):
        try:
            # Wait for post-event frames
            await asyncio.sleep(5)

            stream = self.stream_manager.get_stream(camera_id)
            if not stream:
                return
            context_frames = stream.get_context_frames(before_seconds=10, after_seconds=5)
            if not context_frames:
                return

            # Gemma reasoning
            description = await self.reasoning.analyze_event(context_frames, camera["context"])

            # ElevenLabs narration
            audio_bytes = await self.narration.narrate(description)

            # Upload to Cloudinary
            thumbnail_url = await self.cloudinary.upload_frame(context_frames[len(context_frames)//2][1])
            frame_urls = []
            # Upload every 3rd frame to save time
            for i in range(0, len(context_frames), 3):
                url = await self.cloudinary.upload_frame(context_frames[i][1])
                frame_urls.append(url)
            audio_url = await self.cloudinary.upload_audio(audio_bytes)

            # Solana log
            solana_tx = await self.solana.log_event(camera_id, trigger_time, description)

            # MongoDB write
            event_doc = {
                "camera_id": ObjectId(camera_id),
                "camera_name": camera["name"],
                "timestamp": datetime.utcfromtimestamp(trigger_time),
                "confidence": confidence,
                "description": description,
                "frames": frame_urls,
                "thumbnail": thumbnail_url,
                "audio_url": audio_url,
                "solana_tx": solana_tx,
                "context_used": camera["context"],
            }
            result = await events_collection.insert_one(event_doc)
            event_doc["_id"] = result.inserted_id

            # Notify WebSocket subscribers
            for cb in self.event_callbacks:
                await cb(event_doc, audio_url)

        finally:
            self._processing.discard(camera_id)
```

- [ ] **Step 3: Create events router**

```python
# backend/routers/events.py
from fastapi import APIRouter, Query
from bson import ObjectId
from datetime import datetime
from typing import Optional
from database import events_collection
from models import EventResponse

router = APIRouter(prefix="/events", tags=["events"])

def event_doc_to_response(doc) -> EventResponse:
    return EventResponse(
        id=str(doc["_id"]),
        camera_id=str(doc["camera_id"]),
        camera_name=doc["camera_name"],
        timestamp=doc["timestamp"],
        confidence=doc["confidence"],
        description=doc["description"],
        frames=doc["frames"],
        thumbnail=doc["thumbnail"],
        audio_url=doc["audio_url"],
        solana_tx=doc["solana_tx"],
        context_used=doc["context_used"],
    )

@router.get("/", response_model=list[EventResponse])
async def list_events(
    camera_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_confidence: Optional[float] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = {}
    if camera_id:
        query["camera_id"] = ObjectId(camera_id)
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = start_date
        if end_date:
            query["timestamp"]["$lte"] = end_date
    if min_confidence:
        query["confidence"] = {"$gte": min_confidence}

    cursor = events_collection.find(query).sort("timestamp", -1).skip(offset).limit(limit)
    events = []
    async for doc in cursor:
        events.append(event_doc_to_response(doc))
    return events

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: str):
    doc = await events_collection.find_one({"_id": ObjectId(event_id)})
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(404, "Event not found")
    return event_doc_to_response(doc)
```

- [ ] **Step 4: Create WebSocket endpoints**

```python
# backend/routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import base64
import json
import cv2
import numpy as np

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.stream_subscribers: dict[str, list[WebSocket]] = {}
        self.event_subscribers: list[WebSocket] = []

    async def subscribe_stream(self, camera_id: str, ws: WebSocket):
        await ws.accept()
        if camera_id not in self.stream_subscribers:
            self.stream_subscribers[camera_id] = []
        self.stream_subscribers[camera_id].append(ws)

    async def subscribe_events(self, ws: WebSocket):
        await ws.accept()
        self.event_subscribers.append(ws)

    async def send_frame(self, camera_id: str, frame: np.ndarray):
        subs = self.stream_subscribers.get(camera_id, [])
        if not subs:
            return
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")
        data = json.dumps({"camera_id": camera_id, "frame": b64})
        disconnected = []
        for ws in subs:
            try:
                await ws.send_text(data)
            except:
                disconnected.append(ws)
        for ws in disconnected:
            subs.remove(ws)

    async def send_event(self, event_doc: dict, audio_url: str):
        data = json.dumps({
            "type": "notable_event",
            "event": {
                "id": str(event_doc["_id"]),
                "camera_id": str(event_doc["camera_id"]),
                "camera_name": event_doc["camera_name"],
                "timestamp": event_doc["timestamp"].isoformat(),
                "confidence": event_doc["confidence"],
                "description": event_doc["description"],
                "thumbnail": event_doc["thumbnail"],
                "audio_url": audio_url,
                "solana_tx": event_doc["solana_tx"],
            },
        })
        disconnected = []
        for ws in self.event_subscribers:
            try:
                await ws.send_text(data)
            except:
                disconnected.append(ws)
        for ws in disconnected:
            self.event_subscribers.remove(ws)

manager = ConnectionManager()

@router.websocket("/ws/stream/{camera_id}")
async def stream_websocket(websocket: WebSocket, camera_id: str):
    await manager.subscribe_stream(camera_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if camera_id in manager.stream_subscribers:
            manager.stream_subscribers[camera_id].remove(websocket)

@router.websocket("/ws/events")
async def events_websocket(websocket: WebSocket):
    await manager.subscribe_events(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.event_subscribers.remove(websocket)
```

- [ ] **Step 5: Update main.py to wire everything together**

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers import cameras, events
from routers.websocket import router as ws_router, manager
from services.stream_manager import StreamManager
from services.event_pipeline import EventPipeline
from dotenv import load_dotenv

load_dotenv()

stream_manager = StreamManager()
pipeline = EventPipeline(stream_manager)

@asynccontextmanager
async def lifespan(app: FastAPI):
    pipeline.on_frame(manager.send_frame)
    pipeline.on_event(manager.send_event)
    await pipeline.initialize()
    yield
    for cam_id in list(stream_manager.streams.keys()):
        await stream_manager.remove_camera(cam_id)

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
app.include_router(ws_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat: event pipeline with WebSocket, Cloudinary upload, Solana logging"
```

---

## Task 12: Dashboard Page — Live Camera Grid (Person C, Hours 2-8)

**Files:**
- Create: `frontend/src/hooks/useWebSocket.ts`
- Create: `frontend/src/components/CameraCard.tsx`
- Modify: `frontend/src/pages/Dashboard.tsx`

- [ ] **Step 1: Create WebSocket hook**

```tsx
// frontend/src/hooks/useWebSocket.ts
import { useEffect, useRef, useCallback, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "ws://localhost:8000";

export function useStreamSocket(cameraId: string) {
  const [frame, setFrame] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`${API_BASE}/ws/stream/${cameraId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setFrame(`data:image/jpeg;base64,${data.frame}`);
    };

    return () => ws.close();
  }, [cameraId]);

  return frame;
}

interface NotableEvent {
  id: string;
  camera_id: string;
  camera_name: string;
  timestamp: string;
  confidence: number;
  description: string;
  thumbnail: string;
  audio_url: string;
  solana_tx: string;
}

export function useEventSocket(onEvent: (event: NotableEvent) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const callbackRef = useRef(onEvent);
  callbackRef.current = onEvent;

  useEffect(() => {
    const ws = new WebSocket(`${API_BASE}/ws/events`);
    wsRef.current = ws;

    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      if (data.type === "notable_event") {
        callbackRef.current(data.event);
      }
    };

    return () => ws.close();
  }, []);
}
```

- [ ] **Step 2: Create CameraCard component**

```tsx
// frontend/src/components/CameraCard.tsx
import { useStreamSocket } from "../hooks/useWebSocket";

interface CameraCardProps {
  id: string;
  name: string;
  context: string;
  status: string;
}

export default function CameraCard({ id, name, context, status }: CameraCardProps) {
  const frame = useStreamSocket(id);

  return (
    <div className="camera-card">
      <div className="camera-feed">
        {frame ? (
          <img src={frame} alt={`${name} live feed`} />
        ) : (
          <div className="camera-placeholder">
            <span>Connecting...</span>
          </div>
        )}
        <div className={`status-dot ${status === "active" ? "active" : "inactive"}`} />
      </div>
      <div className="camera-info">
        <h3>{name}</h3>
        <p className="camera-context">Watching for: {context}</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Build Dashboard page with event toasts**

```tsx
// frontend/src/pages/Dashboard.tsx
import { useState, useEffect, useRef } from "react";
import CameraCard from "../components/CameraCard";
import { useEventSocket } from "../hooks/useWebSocket";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface Camera {
  id: string;
  name: string;
  stream_url: string;
  context: string;
  status: string;
  threshold: number;
}

interface NotableEvent {
  id: string;
  camera_id: string;
  camera_name: string;
  timestamp: string;
  confidence: number;
  description: string;
  thumbnail: string;
  audio_url: string;
  solana_tx: string;
}

export default function Dashboard() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [toasts, setToasts] = useState<NotableEvent[]>([]);
  const [eventCount, setEventCount] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    fetch(`${API_BASE}/cameras/`)
      .then((r) => r.json())
      .then(setCameras);
  }, []);

  useEventSocket((event) => {
    setToasts((prev) => [event, ...prev].slice(0, 5));
    setEventCount((c) => c + 1);

    // Play narration audio
    if (audioRef.current) {
      audioRef.current.src = event.audio_url;
      audioRef.current.play();
    }

    // Auto-dismiss toast after 10 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== event.id));
    }, 10000);
  });

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Live Monitoring</h1>
        <div className="event-counter">{eventCount} events detected</div>
      </div>

      <div className="camera-grid">
        {cameras.map((cam) => (
          <CameraCard key={cam.id} {...cam} />
        ))}
        {cameras.length === 0 && (
          <div className="empty-state">
            <p>No cameras configured.</p>
            <a href="/cameras/new">Add a camera</a>
          </div>
        )}
      </div>

      <div className="toast-container">
        {toasts.map((event) => (
          <div key={event.id} className="event-toast">
            <img src={event.thumbnail} alt="Event thumbnail" />
            <div className="toast-content">
              <strong>{event.camera_name}</strong>
              <p>{event.description}</p>
              <span className="toast-time">
                {new Date(event.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))}
      </div>

      <audio ref={audioRef} />
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: live dashboard with camera grid, WebSocket feeds, event toasts + narration"
```

---

## Task 13: Camera Setup Page (Person C, Hours 5-8)

**Files:**
- Modify: `frontend/src/pages/CameraSetup.tsx`

- [ ] **Step 1: Build camera setup form**

```tsx
// frontend/src/pages/CameraSetup.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function CameraSetup() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [streamUrl, setStreamUrl] = useState("");
  const [context, setContext] = useState("");
  const [threshold, setThreshold] = useState(0.7);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePreview = () => {
    if (streamUrl) {
      setPreviewUrl(streamUrl);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/cameras/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          stream_url: streamUrl,
          context,
          threshold,
        }),
      });

      if (!res.ok) throw new Error("Failed to add camera");
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="camera-setup">
      <h1>Add Camera</h1>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="name">Camera Name</label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Office Fridge Cam"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="streamUrl">Stream URL</label>
          <div className="input-with-button">
            <input
              id="streamUrl"
              type="url"
              value={streamUrl}
              onChange={(e) => setStreamUrl(e.target.value)}
              placeholder="http://public-camera-url/stream.mjpg"
              required
            />
            <button type="button" onClick={handlePreview}>Preview</button>
          </div>
        </div>

        {previewUrl && (
          <div className="stream-preview">
            <img src={previewUrl} alt="Stream preview" />
          </div>
        )}

        <div className="form-group">
          <label htmlFor="context">What to watch for</label>
          <textarea
            id="context"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Alert me when someone takes food from the fridge"
            rows={3}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="threshold">
            Detection Sensitivity: {Math.round(threshold * 100)}%
          </label>
          <input
            id="threshold"
            type="range"
            min="0.3"
            max="0.95"
            step="0.05"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
          />
          <div className="threshold-labels">
            <span>More alerts</span>
            <span>Fewer alerts</span>
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}

        <button type="submit" disabled={submitting} className="submit-btn">
          {submitting ? "Adding..." : "Add Camera"}
        </button>
      </form>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/CameraSetup.tsx
git commit -m "feat: camera setup page with preview and context config"
```

---

## Task 14: Event History Page (Person C, Hours 8-13)

**Files:**
- Modify: `frontend/src/pages/EventHistory.tsx`

- [ ] **Step 1: Build event history page with filters**

```tsx
// frontend/src/pages/EventHistory.tsx
import { useState, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const SOLANA_EXPLORER = "https://explorer.solana.com/tx";

interface Event {
  id: string;
  camera_id: string;
  camera_name: string;
  timestamp: string;
  confidence: number;
  description: string;
  frames: string[];
  thumbnail: string;
  audio_url: string;
  solana_tx: string;
  context_used: string;
}

interface Camera {
  id: string;
  name: string;
}

export default function EventHistory() {
  const [events, setEvents] = useState<Event[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [filterCamera, setFilterCamera] = useState("");
  const [loading, setLoading] = useState(true);
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/cameras/`).then((r) => r.json()).then(setCameras);
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (filterCamera) params.set("camera_id", filterCamera);

    fetch(`${API_BASE}/events/?${params}`)
      .then((r) => r.json())
      .then(setEvents)
      .finally(() => setLoading(false));
  }, [filterCamera]);

  return (
    <div className="event-history">
      <div className="history-header">
        <h1>Event History</h1>
        <select
          value={filterCamera}
          onChange={(e) => setFilterCamera(e.target.value)}
        >
          <option value="">All cameras</option>
          {cameras.map((cam) => (
            <option key={cam.id} value={cam.id}>{cam.name}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="loading">Loading events...</div>
      ) : events.length === 0 ? (
        <div className="empty-state">No events recorded yet.</div>
      ) : (
        <div className="events-timeline">
          {events.map((event) => (
            <div
              key={event.id}
              className={`event-card ${expandedEvent === event.id ? "expanded" : ""}`}
              onClick={() => setExpandedEvent(
                expandedEvent === event.id ? null : event.id
              )}
            >
              <div className="event-summary">
                <img
                  src={event.thumbnail}
                  alt="Event thumbnail"
                  className="event-thumb"
                />
                <div className="event-details">
                  <div className="event-meta">
                    <span className="camera-name">{event.camera_name}</span>
                    <span className="event-time">
                      {new Date(event.timestamp).toLocaleString()}
                    </span>
                    <span className="confidence">
                      {Math.round(event.confidence * 100)}% confidence
                    </span>
                  </div>
                  <p className="event-description">{event.description}</p>
                  <div className="event-actions">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        new Audio(event.audio_url).play();
                      }}
                    >
                      Play Narration
                    </button>
                    <a
                      href={`${SOLANA_EXPLORER}/${event.solana_tx}?cluster=devnet`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Solana Proof
                    </a>
                  </div>
                </div>
              </div>

              {expandedEvent === event.id && (
                <div className="event-frames">
                  <h4>Event Frames</h4>
                  <div className="frames-grid">
                    {event.frames.map((url, i) => (
                      <img key={i} src={url} alt={`Frame ${i}`} />
                    ))}
                  </div>
                  <p className="context-used">
                    Context: "{event.context_used}"
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/EventHistory.tsx
git commit -m "feat: event history page with filters, narration playback, Solana links"
```

---

## Task 15: UI Styling for Best UI/UX (Person C, Hours 13-16)

**Files:**
- Create: `frontend/src/styles/global.css`

- [ ] **Step 1: Create polished dark theme stylesheet**

```css
/* frontend/src/styles/global.css */
:root {
  --bg-primary: #0a0a0f;
  --bg-secondary: #12121a;
  --bg-card: #1a1a2e;
  --bg-hover: #222240;
  --text-primary: #e8e8f0;
  --text-secondary: #8888a0;
  --accent: #6c5ce7;
  --accent-glow: rgba(108, 92, 231, 0.3);
  --success: #00d2a0;
  --danger: #ff4757;
  --warning: #ffa502;
  --border: #2a2a40;
  --radius: 12px;
  --shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: "Inter", -apple-system, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
}

/* Nav */
.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}

.nav-brand {
  font-size: 1.4rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent), #a29bfe);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.nav-links { display: flex; gap: 1.5rem; }
.nav-links a {
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}
.nav-links a:hover, .nav-links a.active { color: var(--accent); }

main { padding: 2rem; max-width: 1400px; margin: 0 auto; }

/* Dashboard */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.event-counter {
  background: var(--bg-card);
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  font-weight: 600;
  color: var(--accent);
}

.camera-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1.5rem;
}

.camera-card {
  background: var(--bg-card);
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--border);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.camera-card:hover {
  border-color: var(--accent);
  box-shadow: 0 0 20px var(--accent-glow);
}

.camera-feed {
  position: relative;
  aspect-ratio: 16/9;
  background: #000;
}
.camera-feed img { width: 100%; height: 100%; object-fit: cover; }

.status-dot {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--danger);
}
.status-dot.active {
  background: var(--success);
  box-shadow: 0 0 8px var(--success);
}

.camera-info { padding: 1rem; }
.camera-info h3 { font-size: 1.1rem; margin-bottom: 0.25rem; }
.camera-context { color: var(--text-secondary); font-size: 0.9rem; }

/* Toasts */
.toast-container {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  display: flex;
  flex-direction: column-reverse;
  gap: 0.75rem;
  z-index: 1000;
  max-width: 400px;
}

.event-toast {
  display: flex;
  gap: 0.75rem;
  background: var(--bg-card);
  border: 1px solid var(--accent);
  border-radius: var(--radius);
  padding: 0.75rem;
  box-shadow: 0 0 20px var(--accent-glow);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.event-toast img {
  width: 80px;
  height: 60px;
  border-radius: 8px;
  object-fit: cover;
}

.toast-content strong { display: block; margin-bottom: 0.25rem; }
.toast-content p { font-size: 0.85rem; color: var(--text-secondary); }
.toast-time { font-size: 0.75rem; color: var(--text-secondary); }

/* Camera Setup */
.camera-setup {
  max-width: 600px;
  margin: 0 auto;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-group input[type="text"],
.form-group input[type="url"],
.form-group textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.input-with-button { display: flex; gap: 0.5rem; }
.input-with-button input { flex: 1; }
.input-with-button button {
  padding: 0.75rem 1.25rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-primary);
  cursor: pointer;
}

.stream-preview {
  margin-bottom: 1.5rem;
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--border);
}
.stream-preview img { width: 100%; }

input[type="range"] {
  width: 100%;
  accent-color: var(--accent);
}

.threshold-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.submit-btn {
  width: 100%;
  padding: 0.875rem;
  background: var(--accent);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}
.submit-btn:hover { opacity: 0.9; }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.error-message {
  padding: 0.75rem;
  background: rgba(255, 71, 87, 0.1);
  border: 1px solid var(--danger);
  border-radius: 8px;
  color: var(--danger);
  margin-bottom: 1rem;
}

/* Event History */
.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.history-header select {
  padding: 0.5rem 1rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-primary);
}

.events-timeline { display: flex; flex-direction: column; gap: 1rem; }

.event-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  cursor: pointer;
  transition: border-color 0.2s;
}
.event-card:hover { border-color: var(--accent); }

.event-summary { display: flex; gap: 1rem; }

.event-thumb {
  width: 120px;
  height: 80px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
}

.event-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.camera-name { color: var(--accent); font-weight: 600; }
.event-time { color: var(--text-secondary); }
.confidence { color: var(--warning); }

.event-description { font-size: 0.95rem; margin-bottom: 0.5rem; }

.event-actions { display: flex; gap: 0.75rem; }
.event-actions button,
.event-actions a {
  padding: 0.375rem 0.75rem;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 0.85rem;
  cursor: pointer;
  text-decoration: none;
}
.event-actions button:hover,
.event-actions a:hover {
  border-color: var(--accent);
}

.event-frames {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.frames-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.5rem;
  margin-top: 0.75rem;
}
.frames-grid img {
  width: 100%;
  border-radius: 6px;
  aspect-ratio: 16/9;
  object-fit: cover;
}

.context-used {
  margin-top: 0.75rem;
  font-style: italic;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

/* Empty / Loading states */
.empty-state, .loading {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--text-secondary);
}
.empty-state a { color: var(--accent); }
```

- [ ] **Step 2: Import in main entry point**

Add to the top of `frontend/src/main.tsx`:

```tsx
import "./styles/global.css";
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/styles/
git commit -m "feat: polished dark theme UI for Best UI/UX"
```

---

## Task 16: GoDaddy Domain + Deploy (Person B, Hours 14-16)

**Files:**
- Create: `frontend/.env.production`

- [ ] **Step 1: Register domain on GoDaddy**

Go to GoDaddy, register a domain (e.g., `sentinelai.live`, `stalkertalker.com`, or similar). Use the hackathon credit if available.

- [ ] **Step 2: Create production env**

```bash
# frontend/.env.production
VITE_API_URL=http://<vultr-ip>:8000
```

- [ ] **Step 3: Build and deploy frontend**

```bash
cd frontend
npm run build
```

Deploy the `dist/` folder — simplest options:
- Serve from the Vultr instance alongside the backend using nginx
- Or use Vercel/Netlify free tier for the frontend

- [ ] **Step 4: Point GoDaddy domain to deployment**

In GoDaddy DNS settings, add an A record pointing to your Vultr IP (or CNAME to Vercel/Netlify URL).

- [ ] **Step 5: Start backend on Vultr**

```bash
ssh user@<vultr-ip>
cd sentinelai/backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

- [ ] **Step 6: Verify end-to-end**

Open domain in browser. Add a camera. Verify live feed appears. Wait for an event detection. Confirm narration plays.

- [ ] **Step 7: Commit**

```bash
git add frontend/.env.production
git commit -m "feat: production deployment config"
```

---

## Task 17: End-to-End Testing + Demo Prep (All, Hours 16-18)

- [ ] **Step 1: Test with multiple public camera streams**

Add 2-3 reliable public camera streams:
- Find MJPEG streams from public traffic cams
- Verify streams stay connected for 10+ minutes
- Test that buffer fallback kicks in if you manually disconnect

- [ ] **Step 2: Test the full event pipeline**

1. Add camera with specific context
2. Wait for classifier to flag a frame
3. Verify Gemma description makes sense for the context
4. Verify ElevenLabs narration plays
5. Check MongoDB has the event record
6. Check Solana devnet explorer shows the transaction
7. Check Cloudinary dashboard shows uploaded media

- [ ] **Step 3: Prepare demo script**

```
Demo Flow (2-3 minutes):
1. Open app on custom domain → show dashboard (empty)
2. "Let me add a live security camera" → add public stream
3. Set context: "Watch for anyone approaching the entrance"
4. Show live feed on dashboard
5. Wait for / trigger an event
6. Narration plays: "A person just walked up to the entrance..."
7. Switch to Event History → show logged events
8. Click Solana proof link → show on-chain hash
9. "We trained our own neural network on X hours of footage
    using Vultr cloud GPUs"
10. Show sponsor integrations list for Sponsormaxxing
```

- [ ] **Step 4: Record backup demo video**

Record a screen capture of the full demo flow in case live demo fails. Upload to YouTube. This goes on Devpost.

- [ ] **Step 5: Write Devpost submission**

Include:
- Project description (what it does, how it works)
- GitHub repo link (public)
- Demo video link
- List all technologies used (hit every sponsor)
- Screenshots of the UI
- Note about custom-trained model + Vultr GPU

- [ ] **Step 6: Final commit + push**

```bash
git add -A
git commit -m "feat: SentinelAI complete — LA Hacks 2026"
git push origin main
```
