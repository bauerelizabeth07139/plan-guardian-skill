"""Detect whether a model supports multimodal (image) input.

Strategy: send a minimal 1x1 PNG to the model via the chat completions API.
- 200 response -> multimodal
- 404 with "image" in error message -> not multimodal

Usage:
    python detect_multimodal.py <base_url> <api_key> <model_id>

Exit codes:
    0 = multimodal
    1 = not multimodal
    2 = error (network, auth, etc.)
"""
from __future__ import annotations
import json
import sys
import urllib.error
import urllib.request

# 1x1 transparent PNG (68 bytes)
TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
    "2mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
)


def check(base_url: str, api_key: str, model: str) -> bool:
    """Return True if model accepts image input, False otherwise."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "ok"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{TINY_PNG_B64}"},
                    },
                ],
            }
        ],
        "max_tokens": 1,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            try:
                body = json.loads(exc.read().decode("utf-8"))
                msg = (body.get("error") or {}).get("message", "")
                if "image" in msg.lower():
                    return False
            except Exception:
                pass
        raise
    except Exception:
        raise


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: python detect_multimodal.py <base_url> <api_key> <model_id>")
        return 2

    base_url, api_key, model = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        result = check(base_url, api_key, model)
        print(json.dumps({"model": model, "multimodal": result}))
        return 0 if result else 1
    except Exception as exc:
        print(json.dumps({"model": model, "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())