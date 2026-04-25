import type { ToastEvent } from '../types';
import CldImage from './CldImage';
import './EventToast.css';

interface EventToastProps {
  events: ToastEvent[];
}

export default function EventToast({ events }: EventToastProps) {
  if (events.length === 0) return null;

  return (
    <div className="toast-container" aria-live="polite" role="log">
      {events.map((event) => (
        <div key={event.id} className="event-toast">
          <CldImage src={event.thumbnail} alt="" className="toast-thumb" thumbnail />
          <div className="toast-content">
            <span className="toast-camera">{event.camera_name}</span>
            <p className="toast-desc">{event.description}</p>
            <span className="toast-time mono-data">
              {new Date(event.timestamp).toLocaleTimeString()}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
