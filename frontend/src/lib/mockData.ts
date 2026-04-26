import type { Camera, ToastEvent, EventRecord } from '../types';

export const DEMO_POOL_CAMERA: Camera = {
  id: 'demo-pool',
  name: 'Pool',
  stream_url: '/demo/baby.mp4',
  context: 'Monitor pool area for unauthorized access and child safety',
  status: 'active',
  threshold: 0.7,
};

const now = new Date();
const ago = (mins: number) => new Date(now.getTime() - mins * 60000).toISOString();

export const DEMO_POOL_EVENT: EventRecord = {
  id: 'demo-evt-pool',
  camera_id: 'demo-pool',
  camera_name: 'Pool',
  timestamp: ago(1),
  confidence: 0.97,
  description: 'Baby has fallen into pool. Immediate intervention required. Infant detected breaching pool perimeter without adult supervision. Emergency alert triggered.',
  frames: ['/demo/baby.jpg'],
  thumbnail: '/demo/baby.jpg',
  audio_url: '',
  solana_tx: '4vJ8kN3xR6pQ2wE9yH5jL7bF1cD8aG0kT3mS5uW7xY9z',
  context_used: 'Monitor pool area for unauthorized access and child safety',
};

export const DEMO_POOL_TOAST: ToastEvent = {
  id: 'demo-toast-pool',
  camera_name: 'Pool',
  description: 'Baby has fallen into pool. Immediate intervention required.',
  thumbnail: '/demo/baby.jpg',
  timestamp: ago(0.1),
};

export const MOCK_CAMERAS: Camera[] = [DEMO_POOL_CAMERA];

export const MOCK_FRAMES: Record<string, string> = {};

export const MOCK_EVENTS: EventRecord[] = [DEMO_POOL_EVENT];

export const MOCK_TOASTS: ToastEvent[] = [DEMO_POOL_TOAST];
