"""Verify Cloudinary, Gemma, and ElevenLabs credentials."""
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()


def check_cloudinary() -> bool:
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
        secure=True,
    )
    # Tiny 1x1 PNG
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000a49444154789c6300010000000500010d0a2db40000000049454e44ae426082"
    )
    result = cloudinary.uploader.upload(
        png, resource_type="image", folder="sentinelai_keytest"
    )
    print(f"  Cloudinary OK: {result['secure_url']}")
    cloudinary.uploader.destroy(result["public_id"])
    return True


def check_gemini() -> bool:
    key = os.environ["GEMINI_API_KEY"]
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models"
        f"?key={key}"
    )
    r = httpx.get(url, timeout=15.0)
    r.raise_for_status()
    models = [m["name"] for m in r.json().get("models", [])]
    has_gemini = any("gemini" in m.lower() for m in models)
    print(f"  Gemini OK: {len(models)} models available, gemini present: {has_gemini}")
    return True


def check_elevenlabs() -> bool:
    key = os.environ["ELEVENLABS_API_KEY"]
    r = httpx.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": key},
        timeout=15.0,
    )
    r.raise_for_status()
    voices = r.json().get("voices", [])
    print(f"  ElevenLabs OK: {len(voices)} voices available")
    return True


def main() -> int:
    checks = [
        ("Cloudinary", check_cloudinary),
        ("Gemini", check_gemini),
        ("ElevenLabs", check_elevenlabs),
    ]
    failed = []
    for name, fn in checks:
        print(f"checking {name}...")
        try:
            fn()
        except Exception as e:
            print(f"  {name} FAILED: {e}")
            failed.append(name)
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1
    print("OK: all credentials valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
