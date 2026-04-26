import { Link } from 'react-router-dom';
import { Video } from 'lucide-react';
import HlsPlayer from './HlsPlayer';
import './CameraCard.css';

interface CameraCardProps {
  id: string;
  name: string;
  context: string;
  status: string;
  streamUrl: string;
  frame: string | null;
  caption?: string | null;
}

function isHls(url: string): boolean {
  return url.includes('.m3u8');
}

export default function CameraCard({ id, name, context, status, streamUrl, frame, caption }: CameraCardProps) {
  return (
    <Link to={`/stream/${id}`} className="camera-card">
      <div className="camera-feed">
        {isHls(streamUrl) ? (
          <HlsPlayer src={streamUrl} className="camera-feed-video" />
        ) : frame ? (
          <img src={frame} alt={`${name} live feed`} />
        ) : (
          <div className="camera-placeholder">
            <Video size={20} strokeWidth={1.5} aria-hidden="true" />
            <span className="placeholder-text mono-data">NO SIGNAL</span>
          </div>
        )}
        <div className="feed-overlay">
          <span className={`status-badge ${status === 'active' ? 'active' : 'inactive'}`}>
            <span className="status-dot" aria-hidden="true" />
            {status === 'active' ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>
      </div>
      <div className="camera-info">
        <h3 className="camera-name">{name}</h3>
        <p className="camera-context">{context}</p>
        {caption ? <p className="camera-caption mono-data">{caption}</p> : null}
      </div>
    </Link>
  );
}
