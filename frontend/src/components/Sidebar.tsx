import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Monitor, ScrollText, BarChart3, Network, HelpCircle, LogOut, Sun, Moon } from 'lucide-react';
import './Sidebar.css';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

function getInitialTheme(): 'dark' | 'light' {
  const stored = localStorage.getItem('theme');
  if (stored === 'light' || stored === 'dark') return stored;
  return 'dark';
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  const [theme, setTheme] = useState<'dark' | 'light'>(getInitialTheme);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark');

  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="sidebar-header">
        <span className="brand">SentinelAI</span>
        <span className="brand-sub">SENTINEL HQ</span>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section">
          <span className="nav-group-label">Monitoring</span>
          <NavLink to="/" className="nav-item" end onClick={onClose}>
            <Monitor size={16} />
            <span>Dashboard</span>
          </NavLink>
          <NavLink to="/events" className="nav-item" onClick={onClose}>
            <ScrollText size={16} />
            <span>System Logs</span>
          </NavLink>
        </div>

        <div className="nav-section">
          <span className="nav-group-label">Analysis</span>
          <NavLink to="/analytics" className="nav-item" onClick={onClose}>
            <BarChart3 size={16} />
            <span>Threat Analytics</span>
          </NavLink>
          <NavLink to="/network" className="nav-item" onClick={onClose}>
            <Network size={16} />
            <span>Network Security</span>
          </NavLink>
        </div>
      </nav>

      <div className="sidebar-footer">
        <button className="theme-toggle" onClick={toggleTheme}>
          {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
          <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
        </button>
        <a href="#" className="nav-item">
          <HelpCircle size={16} />
          <span>Support</span>
        </a>
        <a href="#" className="nav-item">
          <LogOut size={16} />
          <span>Sign Out</span>
        </a>
      </div>
    </aside>
  );
}
