import { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import CameraCard from '../components/CameraCard';
import ConnectCard from '../components/ConnectCard';
import EventToast from '../components/EventToast';
import { useDemo } from '../lib/useDemo';
import { DEMO_POOL_CAMERA, DEMO_POOL_TOAST } from '../lib/mockData';
import type { ToastEvent, Camera } from '../types';
import './Dashboard.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Dashboard() {
  const { demoActive } = useDemo();
  const [liveCameras, setLiveCameras] = useState<Camera[]>([]);
  const [toasts, setToasts] = useState<ToastEvent[]>([]);
  const location = useLocation();

  const audioRef = useRef<HTMLAudioElement>(null);
  const [frames, setFrames] = useState<Record<string, string>>({});

  const cameras = demoActive ? [DEMO_POOL_CAMERA, ...liveCameras] : liveCameras;
  const displayFrames = frames;
  const displayToasts = demoActive ? [DEMO_POOL_TOAST, ...toasts] : toasts;

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

        if (audioRef.current && event.audio_url) {
          audioRef.current.src = event.audio_url;
          audioRef.current.play();
        }

        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== event.id));
        }, 8000);
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div className="dashboard">
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
      <audio ref={audioRef} />
    </div>
  );
}
