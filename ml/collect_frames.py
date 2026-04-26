import argparse
import json
import subprocess
from pathlib import Path

import cv2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download videos and extract frames.")
    parser.add_argument("--manifest", default="ml/video_manifest.json")
    parser.add_argument("--out-dir", default="ml/data")
    parser.add_argument("--fps", type=float, default=1.0)
    parser.add_argument("--max-videos", type=int, default=0)
    return parser.parse_args()


def download_video(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "yt-dlp",
        "--no-check-certificate",
        "-f",
        "best[height<=720]",
        "-o",
        str(out_path),
        url,
    ]
    subprocess.run(cmd, check=True)


def extract_frames(video_path: Path, frames_dir: Path, fps: float) -> int:
    frames_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    interval = max(1, int(round(src_fps / fps)))

    idx = 0
    saved = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % interval == 0:
            frame_path = frames_dir / f"frame_{saved:06d}.jpg"
            cv2.imwrite(str(frame_path), frame)
            saved += 1
        idx += 1
    cap.release()
    return saved


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest)
    out_dir = Path(args.out_dir)
    videos_dir = out_dir / "videos"
    frames_root = out_dir / "frames"

    manifest = json.loads(manifest_path.read_text())
    if args.max_videos > 0:
        manifest = manifest[: args.max_videos]

    total = 0
    for i, item in enumerate(manifest):
        video_id = item.get("id", f"video_{i}")
        url = item.get("url")
        local_path = item.get("local_path")
        video_path = videos_dir / f"{video_id}.mp4"
        frames_dir = frames_root / video_id

        if local_path:
            src = Path(local_path)
            if not src.exists():
                raise FileNotFoundError(f"Local video not found: {src}")
            video_path = src
            print(f"Using local video {video_id}: {video_path}")
        else:
            if not url:
                raise ValueError(f"Manifest entry {video_id} must include url or local_path")
            if not video_path.exists():
                print(f"Downloading {video_id}")
                try:
                    download_video(url, video_path)
                except subprocess.CalledProcessError as e:
                    print(f"Skipping {video_id}: download failed ({e})")
                    continue
            else:
                print(f"Reusing existing video {video_id}")

        count = extract_frames(video_path, frames_dir, args.fps)
        total += count
        print(f"Extracted {count} frames -> {frames_dir}")

    print(f"Done. Total extracted frames: {total}")


if __name__ == "__main__":
    main()
