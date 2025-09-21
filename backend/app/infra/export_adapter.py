import os
import json
import hmac
import hashlib
from datetime import datetime
from typing import Any, Dict
from cryptography.fernet import Fernet
from app.infra.event_bus import event_bus

EXPORT_DIR = os.environ.get("EUMENIDES_EXPORT_DIR", "/app/secure_exports")
EXPORT_KEY = os.environ.get("EXPORT_KEY")
HMAC_KEY = os.environ.get("EXPORT_HMAC_KEY", "change-me-hmac-key")

os.makedirs(EXPORT_DIR, exist_ok=True)

def _get_fernet() -> Fernet:
    if not EXPORT_KEY:
        raise RuntimeError("EXPORT_KEY env var not set. Generate via Fernet.generate_key().")
    return Fernet(EXPORT_KEY.encode())

def _hmac_of_handle(handle: str) -> str:
    return hmac.new(HMAC_KEY.encode(), handle.encode(), hashlib.sha256).hexdigest()

def _make_export_payload(event_payload: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.utcnow().isoformat() + "Z"
    payload = {
        "exported_at": now,
        "source": "eumenides_metadata_monitor",
        "version": "1.0",
        "platform": event_payload.get("platform"),
        "handle": event_payload.get("handle"),
        "display_name": event_payload.get("display_name"),
        "description": event_payload.get("description"),
        "risk_score": event_payload.get("risk_score"),
        "reasons": event_payload.get("reasons"),
        "first_seen": event_payload.get("first_seen"),
        "last_seen": event_payload.get("last_seen"),
        "crawl_log": event_payload.get("crawl_log", []),
        "producer": {"name": "Eumenides", "contact": event_payload.get("producer_contact", "")}
    }
    return payload

def _write_encrypted_file(payload: Dict[str, Any], handle_normalized: str) -> str:
    f = _get_fernet()
    raw = json.dumps(payload, ensure_ascii=False, indent=2).encode()
    token = f.encrypt(raw)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_handle = handle_normalized.replace("/", "_")[:60] if handle_normalized else "unknown"
    filename = f"{timestamp}_{safe_handle}.json.enc"
    path = os.path.join(EXPORT_DIR, filename)
    with open(path, "wb") as fh:
        fh.write(token)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass
    return path

def _append_index_record(encrypted_path: str, handle: str):
    idx_path = os.path.join(EXPORT_DIR, "index.audit.log")
    record = {
        "time": datetime.utcnow().isoformat() + "Z",
        "file": os.path.basename(encrypted_path),
        "handle_hmac": _hmac_of_handle(handle),
    }
    with open(idx_path, "a", encoding="utf-8") as idx:
        idx.write(json.dumps(record, ensure_ascii=False) + "\n")
    try:
        os.chmod(idx_path, 0o600)
    except Exception:
        pass

def handle_account_flagged(payload: dict):
    try:
        export_payload = _make_export_payload(payload)
        handle_norm = payload.get("handle", "unknown")
        encrypted_path = _write_encrypted_file(export_payload, handle_norm)
        _append_index_record(encrypted_path, handle_norm)
        print(f"[export_adapter] wrote export: {encrypted_path}")
    except Exception as e:
        print(f"[export_adapter] export failed: {e}")

def subscribe():
    event_bus.subscribe("AccountFlagged", lambda p: handle_account_flagged(p))
    print("[export_adapter] subscribed to AccountFlagged events")
