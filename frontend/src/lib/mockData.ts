import type { Camera, ToastEvent, EventRecord } from '../types';

export const DEMO_POOL_CAMERA: Camera = {
  id: 'demo-pool',
  name: 'Pool',
  stream_url: '/demo/pool.jpg',
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
  solana_tx: '2TN9oBFqhX362m3y7gG2Vq5ms7B5MDUEcctApg3K2kHx6eVohsQBG372y6wqieY36gZtvWYu7xn4kGHq6R2TuHJE',
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
