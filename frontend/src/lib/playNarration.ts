const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const cache = new Map<string, string>();

export async function playNarration(audioUrl: string | undefined | null, description: string): Promise<void> {
  if (audioUrl && !audioUrl.includes('stub.local')) {
    new Audio(audioUrl).play().catch(() => {});
    return;
  }

  if (!description) return;

  const cached = cache.get(description);
  if (cached) {
    new Audio(cached).play().catch(() => {});
    return;
  }

  const res = await fetch(`${API_BASE}/events/narrate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: description }),
  });

  if (!res.ok) return;

  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  cache.set(description, blobUrl);
  new Audio(blobUrl).play().catch(() => {});
}
