import json, os, sys, urllib.error, urllib.request
from typing import List

TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
    "2mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
)
WELL_KNOWN = ["gpt-4o", "gpt-4o-mini", "gpt-4-vision-preview", "o4-mini", "claude-3-haiku-20240307"]


def get_config(base_url: str, api_key: str) -> tuple:
    base = (base_url or os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_KEY_BASE_URL") or "").strip()
    key = (api_key or os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_SECRET_KEY") or "").strip()
    return base, key


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
        if exc.code in (400, 404, 415, 422):
            try:
                body = json.loads(exc.read().decode("utf-8"))
                msg = ((body.get("error") or {}).get("message") or "").lower()
                if any(k in msg for k in ["image", "vision", "multimodal", "does not exist", "not found"]):
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


def score_model(m: str) -> int:
    ml = m.lower()
    s = 0
    if "4o" in ml:
        s += 4
    if "4-vision" in ml:
        s += 4
    if "vision" in ml:
        s += 3
    if "omni" in ml:
        s += 2
    if "multimodal" in ml:
        s += 2
    return s


def choose_candidates(model_ids: List[str]) -> List[str]:
    present = [m for m in model_ids if m.lower() in [w.lower() for w in WELL_KNOWN]]
    rest = [m for m in model_ids if m not in present]
    preferred = [m for m in rest if any(k in m.lower() for k in ["4o", "4-vision", "vision", "omni", "multimodal"])]
    preferred.sort(key=score_model, reverse=True)
    ordered = present + preferred
    if ordered:
        return ordered
    return model_ids


def main() -> int:
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: python detect_multimodal.py <base_url> [<api_key> [<model_id|auto>]]")
        return 2

    base_url = sys.argv[1] if len(sys.argv) >= 2 else ""
    api_key = sys.argv[2] if len(sys.argv) >= 3 else ""
    explicit = sys.argv[3] if len(sys.argv) == 4 else ""

    base_url, api_key = get_config(base_url, api_key)
    if not base_url or not api_key:
        print(json.dumps({"mode": "env", "status": "UNKNOWN", "reason": "missing OPENAI_BASE_URL or OPENAI_API_KEY"}))
        return 2

    if explicit and explicit.lower() != "auto":
        try:
            result = check(base_url, api_key, explicit)
            print(json.dumps({"mode": "explicit", "selected": explicit, "multimodal": result, "status": "MULTIMODAL" if result else "NOT_MULTIMODAL"}))
            return 0 if result else 1
        except Exception as exc:
            print(json.dumps({"mode": "explicit", "selected": explicit, "error": str(exc), "status": "UNKNOWN"}), file=sys.stderr)
            return 2

    try:
        model_ids = list_models(base_url, api_key)
    except Exception as exc:
        print(json.dumps({"mode": "auto", "selected": None, "status": "UNKNOWN", "reason": f"list models failed: {exc}"}))
        return 2

    candidates = choose_candidates(model_ids)

    # also ensure well-known ids are probed even if not in /models
    for m in WELL_KNOWN:
        if m not in candidates:
            candidates.append(m)

    # additionally include all remaining listed models so unknown models are tested too
    for m in model_ids:
        if m not in candidates:
            candidates.append(m)

    tested: List[str] = []
    for m in candidates:
        try:
            ok = check(base_url, api_key, m)
            tested.append(m)
            if ok:
                print(json.dumps({"mode": "auto", "selected": m, "tested": tested, "status": "MULTIMODAL"}))
                return 0
        except Exception:
            tested.append(m)
            continue

    print(json.dumps({"mode": "auto", "selected": None, "tested": tested, "status": "NOT_MULTIMODAL"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
