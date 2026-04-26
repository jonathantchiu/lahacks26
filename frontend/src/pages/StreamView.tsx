import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Settings, Trash2 } from 'lucide-react';
import HlsPlayer from '../components/HlsPlayer';
import { useDemo } from '../lib/useDemo';
import { DEMO_POOL_CAMERA, DEMO_POOL_EVENT } from '../lib/mockData';
import type { Camera, EventRecord } from '../types';
import './StreamView.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function StreamView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { demoActive } = useDemo();

  const [liveCamera, setLiveCamera] = useState<Camera | undefined>(undefined);
  const [liveEvents, setLiveEvents] = useState<EventRecord[]>([]);
  const [liveFrame, setLiveFrame] = useState<string | null>(null);

  const isDemo = id === 'demo-pool';

  useEffect(() => {
    if (isDemo || !id) return;
    fetch(`${API_BASE}/cameras/${id}`)
      .then((r) => r.ok ? r.json() : undefined)
      .then(setLiveCamera)
      .catch(() => {});
  }, [id, isDemo]);

  useEffect(() => {
    if (isDemo || !id) return;
    fetch(`${API_BASE}/events?camera_id=${id}`)
      .then((r) => r.json())
      .then(setLiveEvents)
      .catch(() => {});
  }, [id, isDemo]);

  useEffect(() => {
    if (isDemo || !id) return;
    const ws = new WebSocket(`${API_BASE.replace('http', 'ws')}/ws/stream/${id}`);
    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      setLiveFrame(`data:image/jpeg;base64,${data.jpeg_b64 ?? data.frame}`);
    };
    return () => ws.close();
  }, [id, isDemo]);

  const camera: Camera | undefined = isDemo
    ? DEMO_POOL_CAMERA
    : liveCamera;

  const frame = liveFrame;

  const events: EventRecord[] = isDemo
    ? [DEMO_POOL_EVENT]
    : liveEvents;

  if (!camera) {
    return (
      <div className="stream-view">
        <div className="stream-empty">
          <p>Camera not found.</p>
          <Link to="/">Back to dashboard</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="stream-view">
      <div className="stream-header">
        <button className="back-btn" onClick={() => navigate('/')} aria-label="Back to dashboard">
          <ArrowLeft size={16} />
        </button>
        <div className="stream-title">
          <h1>{camera.name}</h1>
          <span className={`stream-status ${camera.status}`}>
            <span className="stream-status-dot" />
            {camera.status === 'active' ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>
        <div className="stream-actions">
          <button className="stream-action-btn" aria-label="Camera settings">
            <Settings size={14} />
          </button>
          <button
            className="stream-action-btn danger"
            aria-label="Remove camera"
            onClick={async () => {
              if (!confirm('Remove this camera?')) return;
              await fetch(`${API_BASE}/cameras/${id}`, { method: 'DELETE' });
              navigate('/');
            }}
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <div className="stream-layout">
        <div className="stream-main">
          <div className="stream-feed">
            {camera.stream_url.includes('.m3u8') ? (
              <HlsPlayer src={camera.stream_url} className="stream-feed-video" />
            ) : /\.(jpg|jpeg|png)$/i.test(camera.stream_url) ? (
              <img src={camera.stream_url} alt={`${camera.name} feed`} style={{ objectFit: 'cover', width: '100%', height: '100%' }} />
            ) : frame ? (
              <img src={frame} alt={`${camera.name} live feed`} />
            ) : (
              <div className="stream-no-signal">
                <span className="mono-data">NO SIGNAL</span>
              </div>
            )}
            <div className="stream-feed-overlay">
              <span className="mono-data">{camera.name} — {new Date().toLocaleTimeString()}</span>
            </div>
          </div>

          <div className="stream-context">
            <span className="label-caps">Monitoring Context</span>
            <p>{camera.context}</p>
          </div>
        </div>

        <div className="stream-sidebar">
          <div className="stream-panel">
            <span className="label-caps">Configuration</span>
            <div className="config-rows">
              <div className="config-row">
                <span className="config-label">Threshold</span>
                <span className="config-value mono-data">{Math.round(camera.threshold * 100)}%</span>
              </div>
              <div className="config-row">
                <span className="config-label">Buffer</span>
                <span className="config-value mono-data">60s</span>
              </div>
              <div className="config-row">
                <span className="config-label">Pre-trigger</span>
                <span className="config-value mono-data">10s</span>
              </div>
              <div className="config-row">
                <span className="config-label">Post-trigger</span>
                <span className="config-value mono-data">5s</span>
              </div>
            </div>
          </div>

          <div className="stream-panel">
            <span className="label-caps">Recent Events ({events.length})</span>
            {events.length === 0 ? (
              <p className="no-events">No events yet.</p>
            ) : (
              <div className="stream-events">
                {events.map((evt) => (
                  <div key={evt.id} className="stream-event-item">
                    <span className="stream-event-time mono-data">
                      {new Date(evt.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="stream-event-desc">{evt.description.split('.')[0]}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
