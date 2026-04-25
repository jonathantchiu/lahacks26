import type { Camera, ToastEvent, EventRecord } from '../types';

const img = (id: number, w = 640, h = 360) =>
  `https://picsum.photos/id/${id}/${w}/${h}`;

export const MOCK_CAMERAS: Camera[] = [
  {
    id: 'cam-1',
    name: 'Main Entrance A',
    stream_url: '',
    context: 'Watching for people taking food',
    status: 'active',
    threshold: 0.7,
  },
  {
    id: 'cam-2',
    name: 'Lower Parking',
    stream_url: '',
    context: 'Watching for unauthorized vehicle entry',
    status: 'active',
    threshold: 0.75,
  },
  {
    id: 'cam-3',
    name: 'Cafeteria Lounge',
    stream_url: '',
    context: 'Watching for restricted area access',
    status: 'active',
    threshold: 0.8,
  },
  {
    id: 'cam-4',
    name: 'Main Server Hub',
    stream_url: '',
    context: 'Watching for movement after hours',
    status: 'inactive',
    threshold: 0.65,
  },
];

export const MOCK_FRAMES: Record<string, string> = {
  'cam-1': img(1067),
  'cam-2': img(1078),
  'cam-3': img(1076),
  'cam-4': '',
};

const now = new Date();
const ago = (mins: number) => new Date(now.getTime() - mins * 60000).toISOString();

export const MOCK_EVENTS: EventRecord[] = [
  {
    id: 'evt-1',
    camera_id: 'cam-1',
    camera_name: 'PERIMETER NORTH',
    timestamp: ago(3),
    confidence: 0.94,
    description: 'Unidentified Motion Detected. Multiple frame variance detected in high-security zone. AI classifier: "humanoid signature". Subject bypassed sector 4 gating mechanism.',
    frames: [img(1067, 320, 180), img(1059, 320, 180), img(1061, 320, 180), img(1062, 320, 180)],
    thumbnail: img(1067, 320, 180),
    audio_url: '',
    solana_tx: '5xK9mN2vR7pQ3wE8yH4jL6bF1cD9aG0kT',
    context_used: 'Verification context: System triggered high-density burst capture during ingress event.',
  },
  {
    id: 'evt-2',
    camera_id: 'cam-2',
    camera_name: 'MAIN LOBBY',
    timestamp: ago(12),
    confidence: 0.89,
    description: 'Deliverable Drop-off. Courier signature verified. Package placed in secure staging zone. No threat detected.',
    frames: [img(1074, 320, 180), img(1071, 320, 180), img(1072, 320, 180)],
    thumbnail: img(1074, 320, 180),
    audio_url: '',
    solana_tx: '8aB3cD5eF7gH9iJ1kL3mN5oP7qR9sT1u',
    context_used: 'Watch for unauthorized vehicle access or loitering after hours.',
  },
  {
    id: 'evt-3',
    camera_id: 'cam-3',
    camera_name: 'SECURE SERVER ROOM',
    timestamp: ago(28),
    confidence: 0.92,
    description: 'Thermal Threshold Warning. Cabinet 7B reporting irregular heat signature. Hardware failure likely. Recommend immediate site inspection.',
    frames: [img(1084, 320, 180), img(1080, 320, 180)],
    thumbnail: img(1084, 320, 180),
    audio_url: '',
    solana_tx: '2wX4yZ6aB8cD0eF2gH4iJ6kL8mN0oP2q',
    context_used: 'Monitor server room for temperature anomalies and unauthorized access.',
  },
];

export const MOCK_TOASTS: ToastEvent[] = [
  {
    id: 'toast-1',
    camera_name: 'Main Entrance A',
    description: 'Person detected in restricted zone near east corridor.',
    thumbnail: img(1067, 160, 120),
    timestamp: ago(0.5),
  },
  {
    id: 'toast-2',
    camera_name: 'Lower Parking',
    description: 'Vehicle recognized. Plate XY2-9B2. Logging entry.',
    thumbnail: img(1078, 160, 120),
    timestamp: ago(1),
  },
];
