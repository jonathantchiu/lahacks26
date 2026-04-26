import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Label frames from notable time ranges.")
    parser.add_argument("--ranges", default="ml/notable_ranges.json")
    parser.add_argument("--frames-dir", default="ml/data/frames")
    parser.add_argument("--out", default="ml/labels.json")
    parser.add_argument("--fps", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frames_root = Path(args.frames_dir)
    ranges = json.loads(Path(args.ranges).read_text())
    labels: dict[str, int] = {}

    for video_dir in sorted(frames_root.iterdir()):
        if not video_dir.is_dir():
            continue
        vid = video_dir.name
        config = ranges.get(vid, {})
        intervals = config.get("intervals", [])
        periodic_every_s = config.get("periodic_every_s")
        periodic_window_s = config.get("periodic_window_s", 1.0)
        frame_files = sorted(video_dir.glob("*.jpg"))

        for i, frame_path in enumerate(frame_files):
            t = i / args.fps
            notable = any(start <= t <= end for start, end in intervals)
            if periodic_every_s and periodic_every_s > 0:
                k = round(t / periodic_every_s)
                target = k * periodic_every_s
                if abs(t - target) <= periodic_window_s:
                    notable = True
            rel = f"{vid}/{frame_path.name}"
            labels[rel] = 1 if notable else 0

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(labels, indent=2))

    total = len(labels)
    positives = sum(labels.values())
    pct = (positives / total * 100.0) if total else 0.0
    print(f"Wrote {out_path} with {total} labels ({positives} notable, {pct:.1f}%).")


if __name__ == "__main__":
    main()
