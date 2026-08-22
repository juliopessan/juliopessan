"""
Estado operacional do bot: volume das últimas 24 h e fila de transferência humana.

O snapshot() produz exatamente o contrato `orbita.whatsapp/1` que o Órbita OS lê
pelo Google Drive. Números de telefone ficam mascarados no snapshot — o número
cru nunca sai deste processo.
"""
import hashlib
import json
import logging
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger("whatsapp-chatbot.stats")

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "stats.json"
WINDOW_HOURS = 24
SCHEMA = "orbita.whatsapp/1"
TZ_NAME = "America/Sao_Paulo"

_lock = threading.Lock()
_state: dict = {"events": [], "handoffs": {}, "last_error": None}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mask_contact(phone: str) -> str:
    """5511987654321 -> '•••• 4321'. O número cru nunca é exportado."""
    digits = "".join(c for c in str(phone or "") if c.isdigit())
    return "•••• " + digits[-4:] if len(digits) >= 4 else "••••"


def _load() -> None:
    if not DATA_FILE.exists():
        return
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            _state.update({k: loaded.get(k, _state[k]) for k in _state})
    except Exception as exc:                                  # arquivo corrompido não derruba o bot
        log.warning("Não consegui ler %s: %s", DATA_FILE.name, exc)


def _persist() -> None:
    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = DATA_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_state, f, ensure_ascii=False)
        tmp.replace(DATA_FILE)                                 # troca atômica
    except Exception as exc:
        log.warning("Não consegui gravar %s: %s", DATA_FILE.name, exc)


def _prune(now: datetime) -> None:
    cutoff = (now - timedelta(hours=WINDOW_HOURS)).timestamp()
    _state["events"] = [e for e in _state["events"] if e["ts"] >= cutoff]


def _record(kind: str, company: dict, contact: str = "") -> None:
    now = _now()
    with _lock:
        _state["events"].append({
            "ts": now.timestamp(),
            "kind": kind,
            "company_id": company.get("company_id", "desconhecida"),
            "company_name": company.get("name", company.get("company_id", "desconhecida")),
            "contact": mask_contact(contact),
        })
        _prune(now)
        _persist()


def record_inbound(company: dict, contact: str) -> None:
    _record("in", company, contact)


def record_outbound(company: dict, contact: str) -> None:
    _record("out", company, contact)


def record_ai_reply(company: dict, contact: str) -> None:
    _record("ai", company, contact)


def record_error(company: dict, message: str) -> None:
    _record("error", company)
    with _lock:
        _state["last_error"] = {"at": _iso(_now()), "message": str(message)[:200]}
        _persist()


def open_handoff(company: dict, contact: str, last_message: str, reason: str = "keyword") -> None:
    """Entra na fila de atendimento humano. Reabrir não zera a espera original."""
    company_id = company.get("company_id", "desconhecida")
    key = f"{company_id}:{contact}"
    with _lock:
        existing = _state["handoffs"].get(key)
        _state["handoffs"][key] = {
            "id": handoff_id(company_id, contact),
            "company_id": company_id,
            "company_name": company.get("name", company_id),
            "contact": mask_contact(contact),
            "since": existing["since"] if existing else _iso(_now()),
            "reason": reason,
            "last_message": str(last_message or "")[:120],
        }
        _persist()


def handoff_id(company_id: str, contact: str) -> str:
    """Id opaco e estável — permite resolver a fila sem expor o número."""
    return hashlib.sha1(f"{company_id}:{contact}".encode("utf-8")).hexdigest()[:12]


def resolve_handoff(company_id: str, contact: str) -> bool:
    return resolve_handoff_by_id(handoff_id(company_id, contact))


def resolve_handoff_by_id(hid: str) -> bool:
    with _lock:
        for key, h in list(_state["handoffs"].items()):
            if h.get("id") == hid:
                _state["handoffs"].pop(key, None)
                _persist()
                return True
    return False


def open_handoff_keys() -> list[str]:
    with _lock:
        return list(_state["handoffs"].keys())


def snapshot(bot_version: str = "2.0.0") -> dict:
    """Contrato orbita.whatsapp/1 — o que o Órbita OS lê do Drive."""
    now = _now()
    with _lock:
        _prune(now)
        events = list(_state["events"])
        handoffs = list(_state["handoffs"].values())
        last_error = _state["last_error"]

    per_company: dict[str, dict] = {}
    conversations: set[tuple[str, str]] = set()
    totals = {"conversations": 0, "messages_in": 0, "messages_out": 0, "ai_replies": 0, "errors": 0}

    for e in events:
        cid = e["company_id"]
        c = per_company.setdefault(cid, {
            "name": e["company_name"], "conversations": 0, "messages": 0, "open_handoffs": 0,
        })
        if e["kind"] == "in":
            totals["messages_in"] += 1
            c["messages"] += 1
            conversations.add((cid, e["contact"]))
        elif e["kind"] == "out":
            totals["messages_out"] += 1
            c["messages"] += 1
        elif e["kind"] == "ai":
            totals["ai_replies"] += 1
        elif e["kind"] == "error":
            totals["errors"] += 1

    for cid, contact in conversations:
        per_company.setdefault(cid, {"name": cid, "conversations": 0, "messages": 0, "open_handoffs": 0})
        per_company[cid]["conversations"] += 1
    totals["conversations"] = len(conversations)

    queue = []
    for h in handoffs:
        since = datetime.fromisoformat(h["since"].replace("Z", "+00:00"))
        waiting = max(0, int((now - since).total_seconds() // 60))
        per_company.setdefault(h["company_id"], {
            "name": h["company_name"], "conversations": 0, "messages": 0, "open_handoffs": 0,
        })
        per_company[h["company_id"]]["open_handoffs"] += 1
        queue.append({
            "id": h.get("id", handoff_id(h["company_id"], h["contact"])),
            "company": h["company_name"],
            "contact": h["contact"],
            "waiting_minutes": waiting,
            "reason": h["reason"],
            "last_message": h["last_message"],
        })
    queue.sort(key=lambda q: q["waiting_minutes"], reverse=True)

    return {
        "schema": SCHEMA,
        "generated_at": _iso(now),
        "timezone": TZ_NAME,
        "window_hours": WINDOW_HOURS,
        "bot": {"status": "online", "version": bot_version, "last_error": last_error},
        "totals": totals,
        "companies": sorted(per_company.values(), key=lambda c: -c["messages"]),
        "handoff_queue": queue,
    }


_load()
