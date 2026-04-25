# Jonny — Personal Execution Plan (SentinelAI)

**Role:** Person C — Frontend + Solana
**Window:** Friday 7 PM → Sunday 7 AM PDT (~36 hours, ~16 hours active dev)
**Owns:** All frontend pages, routing/layout shell, Solana on-chain logging service, UI polish for Best UI/UX prize.
**Does NOT own:** FastAPI backend (Ved), ML training/classifier/Gemma/ElevenLabs (Sartaj).

Reference: [`sentinelai.md`](sentinelai.md) for full code scaffolds and API contracts.

---

## North Star

By Sunday 7 AM I need: a polished React app on a custom domain that
1. Shows a live camera grid with WebSocket frame streaming,
2. Lets users add cameras with context + threshold config,
3. Displays event history with narration playback and Solana proof links,
4. Logs events on Solana devnet (backend service consumed by Ved's pipeline),
5. Looks good enough to win Best UI/UX.

Everything else is gravy.

---

## Current State (as of plan creation)

### Done
| Component | File | Status |
|-----------|------|--------|
| Dashboard page | `pages/Dashboard.tsx` + `.css` | Complete — camera grid, WS frames, event toasts, audio playback |
| CameraCard | `components/CameraCard.tsx` + `.css` | Complete — feed display, status badge, placeholder |
| ConnectCard | `components/ConnectCard.tsx` + `.css` | Complete — "Add camera" link card |
| EventToast | `components/EventToast.tsx` + `.css` | Complete — toast notifications |
| CameraSetup page | `pages/CameraSetup.tsx` + `.css` | Complete — form, preview, threshold slider, API POST |
| Sidebar | `components/Sidebar.tsx` + `.css` | Complete — nav links, branding |
| Topbar | `components/Topbar.tsx` + `.css` | Complete — nav + action buttons |
| Global CSS | `styles/global.css` | Complete — "Obsidian Protocol" design system, layout classes |
| EventHistory CSS | `pages/EventHistory.css` | Complete — all styles ready |

### Not Done
| Task | Blocked by? |
|------|------------|
| ~~Wire App.tsx~~ | DONE |
| ~~Import global.css in main.tsx~~ | DONE |
| ~~Build EventHistory.tsx page~~ | DONE |
| ~~Adopt Cloudinary React components~~ | DONE |
| ~~Solana logger backend service~~ | DONE |
| ~~UI polish pass~~ | DONE |
| Integration + smoke test | Ved's backend + Sartaj's ML on Vultr |

---

## Execution Order

### Phase 1: Wire the App Shell (30 min)

App.tsx is still the Cloudinary starter template. Sidebar, Topbar, and all pages exist but aren't connected.

- [ ] **1a. Update `main.tsx`** — import `styles/global.css` before `index.css`
- [ ] **1b. Rewrite `App.tsx`** — replace entire contents with:
  - `BrowserRouter` wrapping the app
  - `.app-layout` flex container with `<Sidebar />` + main content area
  - `<Topbar />` above `<Routes>`
  - Routes: `/` → Dashboard, `/cameras/new` → CameraSetup, `/events` → EventHistory
  - `.main-content` wrapper around the routed content (matches `global.css` layout)
- [ ] **1c. Remove dead imports** — delete the `reactLogo`, `viteLogo`, `heroImg` imports and `App.css` if unused
- [ ] **1d. Verify** — `npm run dev`, confirm sidebar renders, all 3 routes work, no console errors

**Files touched:** `src/main.tsx`, `src/App.tsx`
**Depends on:** Nothing

---

### Phase 2: Build EventHistory Page (1.5 hours)

CSS is already written in `pages/EventHistory.css`. Build the TSX to match.

- [ ] **2a. Create `pages/EventHistory.tsx`** with:
  - State: `events`, `cameras` (for filter dropdown), `loading`, `expandedEvent`, `filterCamera`
  - Fetch cameras from `GET /cameras/` on mount (for dropdown)
  - Fetch events from `GET /events/?camera_id=X` when `filterCamera` changes
  - Each event card shows: thumbnail + stacked frames, camera name, timestamp, confidence badge (high/medium/low based on thresholds), description, "Play Narration" button, "Solana Proof" link
  - Clicking a card toggles expanded view: full frame grid, context used, metadata
  - Loading spinner and empty state
- [ ] **2b. Wire confidence badge logic:**
  - `>=0.85` → `confidence-high` (red)
  - `>=0.6` → `confidence-medium` (amber)
  - `<0.6` → `confidence-low` (green)
- [ ] **2c. Narration playback** — "Play Narration" button creates `new Audio(event.audio_url).play()`
- [ ] **2d. Solana proof link** — `https://explorer.solana.com/tx/${event.solana_tx}?cluster=devnet`, opens in new tab
- [ ] **2e. Verify** — page renders at `/events`, filter dropdown works, expand/collapse works. No real data yet (that's fine — empty state should show).

**Expected API contract** (from Ved's `GET /events/`):
```json
{
  "id": "string",
  "camera_id": "string",
  "camera_name": "string",
  "timestamp": "ISO datetime",
  "confidence": 0.0-1.0,
  "description": "string",
  "frames": ["url", "url"],
  "thumbnail": "url",
  "audio_url": "url",
  "solana_tx": "string",
  "context_used": "string"
}
```

**Files touched:** `src/pages/EventHistory.tsx`
**Depends on:** Phase 1 (needs routing). Data depends on Ved's events router (Task 11), but page builds fine without it.

---

### Phase 3: Solana Logger Service (1 hour)

Standalone backend Python service. Gets imported by Ved's event pipeline — no dependency on his code to write it.

- [ ] **3a. Create `backend/services/solana_logger.py`** with `SolanaLogger` class:
  - `__init__`: connect to `https://api.devnet.solana.com`, generate a `Keypair`
  - `fund_wallet()`: request airdrop of 1 SOL on devnet for tx fees
  - `hash_event(camera_id, timestamp, description)`: SHA-256 hash of JSON-serialized event data (sorted keys)
  - `log_event(camera_id, timestamp, description) -> str`: hash the event, create a 0-lamport self-transfer transaction (memo-style), return the tx signature string
- [ ] **3b. Verify imports resolve** — needs `solana`, `solders` packages. Check that Ved's `requirements.txt` includes them; if not, add them.
- [ ] **3c. Quick sanity test** — if Python env is available, test that `SolanaLogger()` initializes and `hash_event()` returns a hex string. Full `log_event()` test requires devnet airdrop (can wait for integration).

**Files touched:** `backend/services/solana_logger.py`
**Depends on:** Nothing. Consumed by Ved's event pipeline (Task 11).

---

### Phase 4: Cloudinary React Components (1 hour)

The project uses the Cloudinary React SDK (`@cloudinary/react`, `@cloudinary/url-gen`) — we should actually use their components instead of raw `<img>` tags for any media served from Cloudinary. This is a sponsor integration and judges will check for it.

**Context:** The backend (Ved's pipeline) uploads event thumbnails, frames, and audio to Cloudinary and stores the resulting URLs in MongoDB. Those URLs come back to the frontend via the API. We need to extract the Cloudinary public ID from those URLs and render via `<AdvancedImage>` / `<AdvancedVideo>`.

- [ ] **4a. Create a helper** `lib/cloudinaryHelpers.ts`:
  - `extractPublicId(cloudinaryUrl: string) -> string` — parse the public ID from a full Cloudinary URL (everything after `/upload/v.../`)
  - `getEventImage(publicId: string)` — returns a `CloudinaryImage` from `cld.image(publicId)` with relevant transforms (auto format, auto quality, resize)
  - `getEventAudio(publicId: string)` — returns a `CloudinaryVideo` from `cld.video(publicId)`
- [ ] **4b. Update `EventToast.tsx`** — replace `<img src={event.thumbnail}>` with `<AdvancedImage cldImg={getEventImage(publicId)}>`
- [ ] **4c. Update `EventHistory.tsx`** — replace all `<img>` tags for thumbnails and expanded frames with `<AdvancedImage>`. Use Cloudinary transforms for responsive sizing (thumbnail: `w_200,c_fill`, expanded: `w_400,c_fill`)
- [ ] **4d. Audio narration** — if using Cloudinary-hosted audio, consider using `<AdvancedVideo>` for narration playback instead of raw `new Audio()`. If the audio URLs aren't Cloudinary-hosted, leave as-is.
- [ ] **4e. Fallback** — if a URL isn't a Cloudinary URL (e.g. during local dev with mock data), fall back to plain `<img src={url}>`. The helper should handle this gracefully.
- [ ] **4f. Verify** — images still render, no broken sources, Cloudinary transforms apply (check network tab for optimized image URLs)

**Files touched:** `lib/cloudinaryHelpers.ts` (new), `components/EventToast.tsx`, `pages/EventHistory.tsx`
**Depends on:** Phase 2 (EventHistory exists). Can run parallel with Phase 3.

**Note:** CameraCard live feed frames come via WebSocket as base64 — these are NOT Cloudinary images, so they stay as raw `<img>` tags. Only media that was uploaded to Cloudinary by the backend pipeline should use Cloudinary components.

---

### Phase 5: UI Polish Pass (2 hours)

Target: Best UI/UX prize. The design system ("Obsidian Protocol") is solid. This phase is about consistency and the small details judges notice.

- [ ] **5a. Audit all pages in browser at 1440px and 768px widths**
  - Dashboard camera grid should collapse gracefully
  - CameraSetup form should stay readable on narrow screens
  - EventHistory cards should stack on mobile
- [ ] **5b. Add responsive breakpoints** where missing:
  - Sidebar: collapse to icon-only or hamburger below 768px
  - `.camera-grid`: switch to single column below 600px
  - `.main-content`: reduce padding on small screens
- [ ] **5c. Interaction polish:**
  - Focus states on all interactive elements (already in CameraSetup, check Dashboard and EventHistory)
  - Hover transitions on event cards (already in CSS, verify they feel smooth)
  - Toast slide-in animation (already in plan CSS — may need to add to EventToast.css if not present)
- [ ] **5d. Empty states** — make sure Dashboard (no cameras) and EventHistory (no events) both have clean, helpful empty states with CTAs
- [ ] **5e. Loading states** — verify loading spinner shows on EventHistory while fetching
- [ ] **5f. Clean up index.css and App.css** — remove any Cloudinary starter CSS that conflicts with global.css

**Files touched:** Various CSS files, possibly `App.css`/`index.css` cleanup
**Depends on:** Phases 1-2, 4

---

### Phase 6: Integration + Smoke Test (1 hour)

Once Ved's backend and Sartaj's ML services are running on Vultr:

- [ ] **5a. Set `VITE_API_URL`** in `.env` to point to Vultr backend
- [ ] **5b. Test camera CRUD flow** — add camera via CameraSetup, verify it appears on Dashboard
- [ ] **5c. Test live frame streaming** — verify WebSocket connects and frames render in CameraCard
- [ ] **5d. Test event pipeline end-to-end:**
  - Wait for classifier to flag a frame
  - Verify toast appears on Dashboard with narration audio
  - Verify event appears in EventHistory
  - Click "Play Narration" — audio plays
  - Click "Solana Proof" — opens Solana Explorer with valid tx
- [ ] **5e. Test with 2-3 cameras simultaneously** — verify grid layout handles it, no WebSocket conflicts
- [ ] **5f. Fix any integration bugs** — mismatched field names, CORS issues, WS URL format, etc.

**Depends on:** Ved (Task 5, 11) + Sartaj (Tasks 1-4, 7-9) running on Vultr

---

## Dependency Map

```
Phase 1 (App Shell)          ──> no blockers
Phase 2 (EventHistory)       ──> Phase 1
Phase 3 (Solana Logger)      ──> no blockers (parallel with 1 & 2)
Phase 4 (Cloudinary React)   ──> Phase 2 (parallel with 3)
Phase 5 (UI Polish)          ──> Phases 1, 2, 4
Phase 6 (Integration)        ──> Ved's backend + Sartaj's ML running on Vultr
```

Phases 1 and 3 can start immediately in parallel. Phase 2 needs 1 done (routing). Phase 4 needs 2 done (EventHistory exists). Phase 5 is the final polish once all pages + Cloudinary are in. Phase 6 is the integration gate.

---

## Time Budget

| Phase | Estimated | Cumulative |
|-------|-----------|------------|
| 1. App Shell | 30 min | 0:30 |
| 2. EventHistory | 1.5 hr | 2:00 |
| 3. Solana Logger | 1 hr | 3:00 |
| 4. Cloudinary React | 1 hr | 4:00 |
| 5. UI Polish | 2 hr | 6:00 |
| 6. Integration | 1 hr | 7:00 |
| Buffer | 2 hr | 9:00 |

**Total: ~7 hours active work + 2 hours buffer for integration surprises.**

---

## What Ved Needs From Me

- **Solana logger** (`backend/services/solana_logger.py`) — he imports `SolanaLogger` in his event pipeline. Get this done in Phase 3 so it's ready when he reaches Task 11.

## What I Need From Ved

- **`GET /cameras/`** endpoint — Dashboard and EventHistory fetch camera list. (Task 5)
- **`POST /cameras/`** endpoint — CameraSetup posts to this. (Task 5)
- **`GET /events/`** endpoint with `?camera_id=` filter — EventHistory fetches from this. (Task 11)
- **WebSocket `/ws/stream/{camera_id}`** — Dashboard subscribes for live frames. (Task 11)
- **WebSocket `/ws/events`** — Dashboard subscribes for event toasts. (Task 11)
- **CORS enabled** — `allow_origins=["*"]` on FastAPI. (Task 5)

## What I Need From Sartaj

- Nothing directly. His services (classifier, Gemma, ElevenLabs) are consumed by Ved's pipeline, not by my frontend.

---

## Commit Strategy

One commit per phase:
1. `feat: wire app shell with sidebar routing`
2. `feat: event history page with filters and Solana proof links`
3. `feat: Solana devnet event logging service`
4. `feat: adopt Cloudinary React components for media rendering`
5. `feat: responsive UI polish`
6. `fix: integration tweaks` (if needed)
