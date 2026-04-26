import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { DemoProvider } from './lib/DemoContext';
import { useDemo } from './lib/useDemo';
import Sidebar from './components/Sidebar';
import StatusBar from './components/StatusBar';
import DiscoBg from './components/DiscoBg';
import Footer from './components/Footer';
import Dashboard from './pages/Dashboard';
import CameraSetup from './pages/CameraSetup';
import EventHistory from './pages/EventHistory';
import StreamView from './pages/StreamView';

function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { sparkleMode } = useDemo();

  return (
    <div className={`app-layout ${sparkleMode ? 'sparkle-mode' : ''}`}>
      {sparkleMode && <DiscoBg />}
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}
      <div className="app-body">
        <StatusBar onMenuClick={() => setSidebarOpen(true)} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/cameras/new" element={<CameraSetup />} />
            <Route path="/stream/:id" element={<StreamView />} />
            <Route path="/events" element={<EventHistory />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <DemoProvider>
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    </DemoProvider>
  );
}
