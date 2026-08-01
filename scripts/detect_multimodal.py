import json, os, sys, urllib.error, urllib.request
from typing import List

TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
    "2mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
)
WELL_KNOWN = ["mimo-v2.5", "gpt-4o", "gpt-4o-mini", "gpt-4-vision-preview", "o4-mini", "claude-3-haiku-20240307"]
PROVIDER_ENDPOINTS = ["https://api.xiaomimimo.com/v1"]


def get_config(base_url: str, api_key: str) -> tuple:
    base = (base_url or os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_KEY_BASE_URL") or "").strip()
    key = (api_key or os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_SECRET_KEY") or "").strip()
    return base, key


def looks_like_html(text: str) -> bool:
    t = text.lstrip().lower()
    return t.startswith("<!doctype") or t.startswith("<html")


def is_api_like(base_url: str, timeout: int = 20) -> bool:
    try:
        req = urllib.request.Request(f"{base_url.rstrip('/')}/models", method="GET")
        req.add_header("User-Agent", "CodexCLI")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
            if looks_like_html(raw):
                return False
            data = json.loads(raw)
            return isinstance(data.get("data"), list)
    except urllib.error.HTTPError as exc:
        # 401/403 likely means API exists but needs auth; still treat as API-like
        return exc.code in (401, 403)
    except Exception:
        return False


def try_resolve_base(base_url: str) -> str:
    if base_url and is_api_like(base_url):
        return base_url
    for ep in PROVIDER_ENDPOINTS:
        if is_api_like(ep):
            return ep
    return base_url


def _post_chat(base_url: str, api_key: str, model: str, payload: dict, timeout: int):
    url = f"{base_url.rstrip('/')}/chat/completions"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "CodexCLI")
    return urllib.request.urlopen(req, timeout=timeout)


def check(base_url: str, api_key: str, model: str, timeout: int = 30) -> bool:
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": [
                {"type": "text", "text": "ok"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{TINY_PNG_B64}"}},
            ]}
        ],
        "max_tokens": 1,
    }
    try:
        with _post_chat(base_url, api_key, model, payload, timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as exc:
        body_text = ""
        try:
            body_text = exc.read().decode("utf-8", errors="ignore")
        except Exception:
            pass
        msg = ""
        try:
            msg = ((json.loads(body_text).get("error") or {}).get("message") or "")
        except Exception:
            msg = body_text
        msg_l = msg.lower()

        if exc.code in (400, 404, 415, 422) and any(k in msg_l for k in [
            "image", "vision", "multimodal", "does not exist", "not found",
            "invalid model", "model_not_found", "max_tokens", "unsupported",
        ]):
            return False

        if exc.code in (400, 422) and "max_tokens" in msg_l:
            payload2 = dict(payload)
            payload2.pop("max_tokens", None)
            try:
                with _post_chat(base_url, api_key, model, payload2, timeout) as resp2:
                    return resp2.status == 200
            except Exception:
                return False

        if exc.code in (500, 502, 503, 504):
            return False

        return False
    except Exception:
        return False


def list_models(base_url: str, api_key: str, timeout: int = 30) -> List[str]:
    url = f"{base_url.rstrip('/')}/models"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "CodexCLI")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
            if looks_like_html(raw):
                return []
            try:
                data = json.loads(raw)
            except Exception:
                return []
            items = data.get("data") or []
            return [str((it.get("id") or "")).strip() for it in items if it.get("id")]
    except Exception:
        return []


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
    if not model_ids:
        return []
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

    base_url = try_resolve_base(base_url)

    if explicit and explicit.lower() != "auto":
        try:
            result = check(base_url, api_key, explicit)
            print(json.dumps({"mode": "explicit", "selected": explicit, "multimodal": result, "status": "MULTIMODAL" if result else "NOT_MULTIMODAL"}))
            return 0 if result else 1
        except Exception as exc:
            print(json.dumps({"mode": "explicit", "selected": explicit, "error": str(exc), "status": "UNKNOWN"}), file=sys.stderr)
            return 2

    model_ids = list_models(base_url, api_key)

    candidates = choose_candidates(model_ids)
    for m in model_ids:
        if m not in candidates:
            candidates.append(m)
    for m in WELL_KNOWN:
        if m not in candidates:
            candidates.append(m)

    tested: List[str] = []
    for m in candidates:
        try:
            ok = check(base_url, api_key, m)
            tested.append(m)
            if ok:
                print(json.dumps({"mode": "auto", "selected": m, "listed": bool(model_ids), "tested": tested, "status": "MULTIMODAL"}))
                return 0
        except Exception:
            tested.append(m)
            continue

    print(json.dumps({"mode": "auto", "selected": None, "listed": bool(model_ids), "tested": tested, "status": "NOT_MULTIMODAL"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
