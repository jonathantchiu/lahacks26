import { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { Volume2, VolumeX } from 'lucide-react';
import CameraCard from '../components/CameraCard';
import ConnectCard from '../components/ConnectCard';
import EventToast from '../components/EventToast';
import { useDemo } from '../lib/useDemo';
import { playNarration } from '../lib/playNarration';
import { DEMO_POOL_CAMERA, DEMO_POOL_TOAST } from '../lib/mockData';
import type { ToastEvent, Camera } from '../types';
import './Dashboard.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Dashboard() {
  const { demoActive } = useDemo();
  const [liveCameras, setLiveCameras] = useState<Camera[]>([]);
  const [toasts, setToasts] = useState<ToastEvent[]>([]);
  const location = useLocation();

  const [frames, setFrames] = useState<Record<string, string>>({});
  const [muted, setMuted] = useState(true);
  const pendingEvent = useRef<{ audio_url?: string; description?: string } | null>(null);

  const cameras = demoActive ? [DEMO_POOL_CAMERA, ...liveCameras] : liveCameras;
  const displayFrames = frames;
  const displayToasts = demoActive ? [DEMO_POOL_TOAST, ...toasts] : toasts;

  const toggleMute = useCallback(() => {
    setMuted((prev) => {
      if (prev && pendingEvent.current) {
        playNarration(pendingEvent.current.audio_url, pendingEvent.current.description || '');
        pendingEvent.current = null;
      }
      return !prev;
    });
  }, []);

  const fetchCameras = useCallback(() => {
    fetch(`${API_BASE}/cameras`)
      .then((r) => r.json())
      .then(setLiveCameras)
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchCameras();
  }, [fetchCameras, location.key]);

  useEffect(() => {
    const connections: WebSocket[] = [];

    liveCameras.forEach((cam) => {
      const ws = new WebSocket(`${API_BASE.replace('http', 'ws')}/ws/stream/${cam.id}`);
      ws.onmessage = (msg) => {
        const data = JSON.parse(msg.data);
        setFrames((prev) => ({
          ...prev,
          [data.camera_id]: `data:image/jpeg;base64,${data.jpeg_b64 ?? data.frame}`,
        }));
      };
      connections.push(ws);
    });

    return () => connections.forEach((ws) => ws.close());
  }, [liveCameras]);

  useEffect(() => {
    const ws = new WebSocket(`${API_BASE.replace('http', 'ws')}/ws/events`);

    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      if (data.type === 'event' || data.type === 'notable_event') {
        const event = data.data ?? data.event;
        setToasts((prev) => [event, ...prev].slice(0, 5));

        if (!muted) {
          playNarration(event.audio_url, event.description || '');
        } else {
          pendingEvent.current = { audio_url: event.audio_url, description: event.description };
        }

        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== event.id));
        }, 8000);
      }
    };

    return () => ws.close();
  }, [muted]);

  return (
    <div className="dashboard">
      <button className="unmute-banner" onClick={toggleMute}>
        {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
        {muted ? 'Click to enable alert narration' : 'Narration enabled — click to mute'}
      </button>
      <div className="camera-grid">
        {cameras.map((cam) => (
          <CameraCard
            key={cam.id}
            id={cam.id}
            name={cam.name}
            context={cam.context}
            status={cam.status}
            streamUrl={cam.stream_url}
            frame={displayFrames[cam.id] || null}
          />
        ))}
        <ConnectCard />
      </div>

      <EventToast events={displayToasts} />
    </div>
  );
}
