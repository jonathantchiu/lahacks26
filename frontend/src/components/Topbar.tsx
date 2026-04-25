import { NavLink } from 'react-router-dom';
import { Bell, UserCircle, Menu } from 'lucide-react';
import './Topbar.css';

interface TopbarProps {
  onMenuClick: () => void;
}

export default function Topbar({ onMenuClick }: TopbarProps) {
  return (
    <header className="topbar">
      <button className="topbar-menu-btn" onClick={onMenuClick} aria-label="Open menu">
        <Menu size={18} />
      </button>
      <nav className="topbar-nav">
        <NavLink to="/" end>Dashboard</NavLink>
        <NavLink to="/cameras/new">Add Camera</NavLink>
        <NavLink to="/events">Event History</NavLink>
      </nav>
      <div className="topbar-actions">
        <button className="topbar-icon-btn">
          <Bell size={18} />
        </button>
        <button className="topbar-icon-btn">
          <UserCircle size={18} />
        </button>
      </div>
    </header>
  );
}
