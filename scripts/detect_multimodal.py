from __future__ import annotations
import json, sys, urllib.error, urllib.request
from typing import List

TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
    "2mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
)


def check(base_url: str, api_key: str, model: str, timeout: int = 20) -> bool:
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "user", "content": [
                {"type": "text", "text": "ok"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{TINY_PNG_B64}"}},
            ]}
        ],
        "max_tokens": 1,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as exc:
        if exc.code in (400, 404, 415):
            try:
                body = json.loads(exc.read().decode("utf-8"))
                msg = ((body.get("error") or {}).get("message") or "").lower()
                if "image" in msg or "vision" in msg or "multimodal" in msg:
                    return False
            except Exception:
                pass
            return False
        raise
    except Exception:
        raise


def list_models(base_url: str, api_key: str, timeout: int = 20) -> List[str]:
    url = f"{base_url.rstrip('/')}/models"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    items = data.get("data") or []
    return [str((it.get("id") or "")).strip() for it in items if it.get("id")]


def choose_candidates(model_ids: List[str]) -> List[str]:
    preferred = [m for m in model_ids if any(k in m.lower() for k in ["4o", "4-vision", "vision", "omni", "multimodal"])]
    if preferred:
        return preferred
    return model_ids


def main() -> int:
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python detect_multimodal.py <base_url> <api_key> [model_id|auto]")
        return 2

    base_url, api_key = sys.argv[1], sys.argv[2]
    explicit = sys.argv[3] if len(sys.argv) == 4 else ""

    if explicit and explicit.lower() != "auto":
        try:
            result = check(base_url, api_key, explicit)
            print(json.dumps({"mode": "explicit", "model": explicit, "multimodal": result}))
            return 0 if result else 1
        except Exception as exc:
            print(json.dumps({"mode": "explicit", "model": explicit, "error": str(exc)}), file=sys.stderr)
            return 2

    try:
        model_ids = list_models(base_url, api_key)
    except Exception as exc:
        print(json.dumps({"mode": "auto", "model": None, "status": "UNKNOWN", "reason": f"list models failed: {exc}"}))
        return 2

    candidates = choose_candidates(model_ids)
    tested = []
    for m in candidates:
        try:
            ok = check(base_url, api_key, m)
            tested.append({"model": m, "multimodal": ok})
            if ok:
                print(json.dumps({"mode": "auto", "selected": m, "tested": tested, "status": "MULTIMODAL"}))
                return 0
        except Exception as exc:
            tested.append({"model": m, "error": str(exc)})
            continue

    print(json.dumps({"mode": "auto", "selected": None, "tested": tested, "status": "NOT_MULTIMODAL"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
