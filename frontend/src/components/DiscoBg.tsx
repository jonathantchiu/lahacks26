import { useMemo } from 'react';

const COLORS = ['#ff6bc1', '#c56cf0', '#7c5cfc', '#18dcff', '#fff', '#ffd700', '#ff9ff3', '#a29bfe'];

export default function DiscoBg() {
  const diamonds = useMemo(() =>
    Array.from({ length: 50 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 96 + 2}%`,
      top: `${Math.random() * 96 + 2}%`,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      size: `${4 + Math.random() * 6}px`,
      dur: `${2 + Math.random() * 5}s`,
      delay: `${Math.random() * 5}s`,
    })), []);

  return (
    <div className="sparkle-bg">
      {diamonds.map((d) => (
        <div
          key={d.id}
          className="disco-diamond"
          style={{
            left: d.left,
            top: d.top,
            width: d.size,
            height: d.size,
            background: d.color,
            '--dur': d.dur,
            '--delay': d.delay,
          } as React.CSSProperties}
        />
      ))}
    </div>
  );
}
