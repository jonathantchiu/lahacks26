import { useCallback, useEffect, useRef, useState } from 'react';
import CameraCard from '../components/CameraCard';
import type { Camera } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CLIP_NOTES = [
  {
    title: 'Fridge clip (funny)',
    url: 'https://www.youtube.com/watch?v=0nojVYjH8U8',
    pitch: 'Fred is stealing your cookies (demo voice + event card).',
  },
  {
    title: 'Pool safety clip (serious)',
    url: 'https://www.youtube.com/watch?v=cICz7GKsGwU',
    pitch: 'High-stakes “missed moment” scenario: seconds matter.',
  },
];

export default function DemoLab() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [frames, setFrames] = useState<Record<string, { image: string; caption?: string }>>({});

  const fetchCameras = useCallback(() => {
    fetch(`${API_BASE}/cameras`)
      .then((r) => r.json())
      .then(setCameras)
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchCameras();
  }, [fetchCameras]);

  const connectionsRef = useRef(new Map<string, WebSocket>());

  useEffect(() => {
    const connections = connectionsRef.current;
    cameras.forEach((cam) => {
      if (connections.has(cam.id)) return;
      const ws = new WebSocket(`${API_BASE.replace('http', 'ws')}/ws/stream/${cam.id}`);
      ws.onmessage = (msg) => {
        const data = JSON.parse(msg.data);
        setFrames((prev) => ({
          ...prev,
          [cam.id]: {
            image: `data:image/jpeg;base64,${data.jpeg_b64 ?? data.frame}`,
            caption: typeof data.caption === 'string' ? data.caption : undefined,
          },
        }));
      };
      connections.set(cam.id, ws);
    });

    return () => {
      connections.forEach((ws) => ws.close());
      connections.clear();
    };
  }, [cameras]);

  return (
    <div style={{ padding: 16, display: 'grid', gap: 16 }}>
      <div>
        <h1 style={{ margin: 0 }}>Demo lab</h1>
        <p style={{ margin: '8px 0 0', opacity: 0.85 }}>
          Live tiles use the same websocket feed as the dashboard. Boxes are burned into the JPEG on the server (YOLOv8n, person class).
        </p>
      </div>

      <div style={{ display: 'grid', gap: 10 }}>
        <div style={{ fontWeight: 600 }}>Hard-coded story clips (source)</div>
        <ul style={{ margin: 0, paddingLeft: 18, opacity: 0.9 }}>
          {CLIP_NOTES.map((c) => (
            <li key={c.title} style={{ marginBottom: 8 }}>
              <div style={{ fontWeight: 600 }}>{c.title}</div>
              <div style={{ fontSize: 12, opacity: 0.85 }}>{c.pitch}</div>
              <div style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 12 }}>
                {c.url}
              </div>
            </li>
          ))}
        </ul>
        <div style={{ fontSize: 12, opacity: 0.85 }}>
          Practical note: YouTube URLs are not great as direct OpenCV inputs. For the hackathon demo, download each clip once on the server and point a camera at{' '}
          <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>/root/clips/*.mp4</span>.
        </div>
      </div>

      <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>
        {cameras.map((cam) => (
          <CameraCard
            key={cam.id}
            id={cam.id}
            name={cam.name}
            context={cam.context}
            status={cam.status}
            streamUrl={cam.stream_url}
            frame={frames[cam.id]?.image || null}
            caption={frames[cam.id]?.caption}
          />
        ))}
      </div>
    </div>
  );
}
