import { Link } from 'react-router-dom';
import { PlusCircle } from 'lucide-react';
import './ConnectCard.css';

export default function ConnectCard() {
  return (
    <Link to="/cameras/new" className="connect-card">
      <div className="connect-card-inner">
        <PlusCircle size={32} strokeWidth={1.5} />
        <h3>Connect New Stream</h3>
        <p>Link additional AI-powered nodes to your grid.</p>
      </div>
    </Link>
  );
}
