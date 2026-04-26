import { useState, useEffect } from 'react';
import { Menu } from 'lucide-react';
import { useDemo } from '../lib/useDemo';
import { MOCK_CAMERAS } from '../lib/mockData';
import type { Camera } from '../types';
import './StatusBar.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface StatusBarProps {
  onMenuClick?: () => void;
}

export default function StatusBar({ onMenuClick }: StatusBarProps) {
  const { demoActive } = useDemo();
  const [liveCameras, setLiveCameras] = useState<Camera[]>([]);

  useEffect(() => {
    if (demoActive) return;
    fetch(`${API_BASE}/cameras`)
      .then((r) => r.json())
      .then(setLiveCameras)
      .catch(() => {});
  }, [demoActive]);

  const cams = demoActive ? MOCK_CAMERAS : liveCameras;
  const cameras = cams.length;
  const online = cams.filter((c) => c.status === 'active').length;
  const offline = cameras - online;

  return (
    <div className="status-bar" role="status">
      <button className="menu-toggle" onClick={onMenuClick} aria-label="Open menu">
        <Menu size={18} />
      </button>
      <div className="status-item">
        <span className={`status-indicator ${online > 0 ? 'ok' : 'down'}`} aria-hidden="true" />
        <span className="status-label">CAMERAS</span>
        <span className="status-value">{online}/{cameras}</span>
        {offline > 0 && <span className="status-warn">{offline} offline</span>}
      </div>

      <div className="status-sep" aria-hidden="true" />

      <div className="status-item">
        <span className="status-label">EVENTS / HR</span>
        <span className="status-value">{demoActive ? '12' : '--'}</span>
      </div>

      <div className="status-sep" aria-hidden="true" />

      <div className="status-item">
        <span className="status-label">INFERENCE</span>
        <span className="status-value">{demoActive ? '18' : '--'}ms</span>
      </div>

      <div className="status-sep" aria-hidden="true" />

      <div className="status-item">
        <span className="status-label">UPTIME</span>
        <span className="status-value">{demoActive ? '99.7' : '--'}%</span>
      </div>
    </div>
  );
}
