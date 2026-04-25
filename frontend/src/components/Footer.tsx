import { useDemo } from '../lib/useDemo';
import './Footer.css';

export default function Footer() {
  const year = new Date().getFullYear();
  const { demoActive, toggleDemo } = useDemo();

  return (
    <footer className="app-footer">
      <div className="footer-row">
        <span className="footer-copy">&copy; {year} SentinelAI</span>
        <span className="footer-sep" aria-hidden="true" />
        <a href="#privacy">Privacy</a>
        <a href="#terms">Terms</a>
        <a href="#security">Security</a>
        <a href="#docs">Docs</a>
        <span className="footer-sep" aria-hidden="true" />
        <button
          className={`demo-toggle ${demoActive ? 'active' : ''}`}
          onClick={toggleDemo}
          aria-label={demoActive ? 'Disable demo data' : 'Load demo data'}
        >
          <span className="demo-toggle-dot" aria-hidden="true" />
          {demoActive ? 'Demo Active' : 'Load Demo'}
        </button>
        <span className="footer-version mono-data">v0.1.0</span>
      </div>
    </footer>
  );
}
