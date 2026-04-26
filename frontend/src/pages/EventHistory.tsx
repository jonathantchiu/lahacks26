import { useState, useEffect } from 'react';
import { Play, ExternalLink, ChevronDown } from 'lucide-react';
import type { EventRecord, Camera } from '../types';
import CldImage from '../components/CldImage';
import { useDemo } from '../lib/useDemo';
import { playNarration } from '../lib/playNarration';
import { DEMO_POOL_CAMERA, DEMO_POOL_EVENT } from '../lib/mockData';
import './EventHistory.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const SOLANA_EXPLORER = 'https://explorer.solana.com/tx';

export default function EventHistory() {
  const { demoActive } = useDemo();
  const [liveEvents, setLiveEvents] = useState<EventRecord[]>([]);
  const [liveCameras, setLiveCameras] = useState<Camera[]>([]);
  const [filterCamera, setFilterCamera] = useState('');
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);

  const events = demoActive ? [DEMO_POOL_EVENT, ...liveEvents] : liveEvents;
  const cameras = demoActive ? [DEMO_POOL_CAMERA, ...liveCameras] : liveCameras;

  useEffect(() => {
    fetch(`${API_BASE}/cameras`)
      .then((r) => r.json())
      .then(setLiveCameras)
      .catch(() => {});
  }, []);

  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams();
    if (filterCamera) params.set('camera_id', filterCamera);

    fetch(`${API_BASE}/events?${params}`)
      .then((r) => r.json())
      .then((data) => { if (!cancelled) setLiveEvents(data); })
      .catch(() => { if (!cancelled) setLiveEvents([]); });

    return () => { cancelled = true; };
  }, [filterCamera]);

  const toggleEvent = (id: string) => {
    setExpandedEvent(expandedEvent === id ? null : id);
  };

  const getConfidenceClass = (confidence: number) => {
    if (confidence >= 0.9) return 'confidence-high';
    if (confidence >= 0.7) return 'confidence-medium';
    return 'confidence-low';
  };

  return (
    <div className="event-history">
      <div className="history-header">
        <div className="history-title-row">
          <h1>System Logs</h1>
          <span className="event-total mono-data">{events.length} events</span>
        </div>
        <select
          value={filterCamera}
          onChange={(e) => setFilterCamera(e.target.value)}
          className="camera-filter"
          aria-label="Filter by camera"
        >
          <option value="">All Cameras</option>
          {cameras.map((cam) => (
            <option key={cam.id} value={cam.id}>
              {cam.name}
            </option>
          ))}
        </select>
      </div>

      {events.length === 0 ? (
        <div className="empty-state">No events recorded yet.</div>
      ) : (
        <div className="events-list">
          {events.map((event) => {
            const isExpanded = expandedEvent === event.id;
            return (
              <div
                key={event.id}
                className={`event-card ${isExpanded ? 'expanded' : ''}`}
              >
                <div
                  className="event-main"
                  role="button"
                  tabIndex={0}
                  aria-expanded={isExpanded}
                  onClick={() => toggleEvent(event.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      toggleEvent(event.id);
                    }
                  }}
                >
                  <div className="event-thumb-wrap">
                    <CldImage src={event.thumbnail} alt="" className="event-thumb" thumbnail />
                    {event.frames.length > 1 && (
                      <span className="frame-count mono-data">+{event.frames.length - 1}</span>
                    )}
                  </div>

                  <div className="event-details">
                    <div className="event-top-row">
                      <span className="event-camera">{event.camera_name}</span>
                      <span className="event-time mono-data">
                        {new Date(event.timestamp).toLocaleString('en-US', {
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                          hour12: false,
                        })}{' '}
                        UTC
                      </span>
                    </div>

                    <h3 className="event-title">
                      {event.description.split('.')[0]}
                    </h3>

                    <span className={`confidence-badge ${getConfidenceClass(event.confidence)}`}>
                      {Math.round(event.confidence * 100)}% Confidence
                    </span>

                    <p className="event-desc">{event.description}</p>

                    <div className="event-actions">
                      <button
                        className="action-btn play-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          playNarration(event.audio_url, event.description);
                        }}
                        aria-label={`Play narration for ${event.camera_name} event`}
                      >
                        <Play size={12} />
                        Play Narration
                      </button>
                      <a
                        href={`${SOLANA_EXPLORER}/${event.solana_tx}?cluster=devnet`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="action-btn solana-btn"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink size={12} />
                        Solana Proof
                      </a>
                    </div>
                  </div>

                  <ChevronDown
                    size={14}
                    className={`expand-icon ${isExpanded ? 'rotated' : ''}`}
                    aria-hidden="true"
                  />
                </div>

                {isExpanded && (
                  <div className="event-expanded">
                    <div className="expanded-section">
                      <span className="label-caps">Verification context</span>
                      <p>{event.context_used}</p>
                    </div>
                    <div className="expanded-section">
                      <span className="label-caps">Captured frames</span>
                      <div className="expanded-frames">
                        {event.frames.map((url, i) => (
                          <CldImage key={i} src={url} alt={`Captured frame ${i + 1}`} width={400} />
                        ))}
                      </div>
                    </div>
                    <div className="expanded-meta">
                      <span className="label-caps mono-data">
                        BUFFER: 1000ms POST-TRIGGER
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
