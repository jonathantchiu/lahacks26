import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Info } from 'lucide-react';
import './CameraSetup.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function CameraSetup() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [streamUrl, setStreamUrl] = useState('');
  const [context, setContext] = useState('');
  const [threshold, setThreshold] = useState(0.75);
  const [previewActive, setPreviewActive] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePreview = () => {
    if (streamUrl) setPreviewActive(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/cameras`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          stream_url: streamUrl,
          context,
          threshold,
        }),
      });

      if (!res.ok) throw new Error('Failed to add camera');
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="camera-setup">
      <div className="setup-header">
        <h1>Add New Camera</h1>
        <p>Configure a new RTSP or hardware stream for tactical monitoring.</p>
      </div>

      <form onSubmit={handleSubmit} className="setup-form">
        <div className="form-group">
          <label htmlFor="cam-name" className="label-caps">Camera Name</label>
          <input
            id="cam-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Perimeter North Gate"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="cam-url" className="label-caps">Stream URL</label>
          <div className="input-with-btn">
            <input
              id="cam-url"
              type="url"
              value={streamUrl}
              onChange={(e) => setStreamUrl(e.target.value)}
              placeholder="rtsp://admin:password@192.168.1.100:554/live"
              required
            />
            <button type="button" className="btn-secondary" onClick={handlePreview}>
              Preview
            </button>
          </div>
        </div>

        <div className="form-group">
          <span className="label-caps" id="preview-label">Stream Preview</span>
          <div className="stream-preview" role="img" aria-labelledby="preview-label">
            {previewActive ? (
              <img src={streamUrl} alt="Stream preview" />
            ) : (
              <div className="preview-placeholder">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
                  <path d="M15.6 11.7c0-.7-.4-1.2-1-1.2H9.4c-.6 0-1 .5-1 1.2v4.6c0 .7.4 1.2 1 1.2h5.2c.6 0 1-.5 1-1.2v-4.6z" />
                  <path d="M18 12.5l3-2v7l-3-2" />
                </svg>
                <span>Waiting for stream connection...</span>
              </div>
            )}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="cam-context" className="label-caps">What to Watch For</label>
          <textarea
            id="cam-context"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Identify unauthorized vehicle access or loitering after hours in the secure zone..."
            rows={3}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="cam-threshold" className="label-caps">
            Detection Sensitivity
            <span className="threshold-value mono-data">{Math.round(threshold * 100)}%</span>
          </label>
          <input
            id="cam-threshold"
            type="range"
            min="0.3"
            max="0.95"
            step="0.05"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
            className="range-input"
          />
          <div className="threshold-labels">
            <span>30% LOW</span>
            <span>DEFAULT</span>
            <span>95% HIGH</span>
          </div>
        </div>

        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        <button type="submit" disabled={submitting} className="btn-primary">
          {submitting ? 'Adding...' : 'Add Camera'}
        </button>

        <div className="pro-tip">
          <Info size={14} aria-hidden="true" />
          <p>
            <strong>Pro Tip:</strong> Higher sensitivity reduces false negatives but may increase
            alerts from environmental motion like shadows or swaying trees.
          </p>
        </div>
      </form>
    </div>
  );
}
