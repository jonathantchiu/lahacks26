export interface ToastEvent {
  id: string;
  camera_name: string;
  description: string;
  thumbnail: string;
  timestamp: string;
}

export interface Camera {
  id: string;
  name: string;
  stream_url: string;
  context: string;
  status: string;
  threshold: number;
}

export interface EventRecord {
  id: string;
  camera_id: string;
  camera_name: string;
  timestamp: string;
  confidence: number;
  description: string;
  frames: string[];
  thumbnail: string;
  audio_url: string;
  solana_tx: string;
  context_used: string;
}
