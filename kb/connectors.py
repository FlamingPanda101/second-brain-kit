"""One function per source. Each takes the db, ingests only what changed, and returns the
source_ids it added or changed. Re-running is safe: kb.upsert_item skips unchanged items."""
import base64, html, json, re
from datetime import datetime, timezone
from pathlib import Path

from kb import get_state, set_state, upsert_item, HOME

VAULT = Path.home() / "SecondBrain"
CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"


class NotConfigured(Exception):
    pass


# ---------- Obsidian vault (read-only) ----------
def vault(db):
    changed, seen = [], set()
    for p in VAULT.rglob("*.md"):
        rel = p.relative_to(VAULT).as_posix()
        if rel.split("/")[0] in (".git", ".obsidian", ".trash", ".claude"):
            continue
        seen.add(rel)
        mtime = str(p.stat().st_mtime)
        if get_state(db, "vault", rel) == mtime:
            continue
        ts = datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")
        if upsert_item(db, "vault", rel, ts, p.stem, p.read_text(encoding="utf-8", errors="replace"), {"path": str(p)}):
            changed.append(rel)
        set_state(db, "vault", rel, mtime)
    # notes deleted or renamed in the vault disappear from the KB too
    for (sid,) in db.execute("SELECT DISTINCT source_id FROM docs WHERE source='vault'").fetchall():
        if sid not in seen:
            db.execute("DELETE FROM docs WHERE source='vault' AND source_id=?", (sid,))
            db.execute("DELETE FROM ingest_state WHERE source='vault' AND key=?", (sid,))
    return changed


# ---------- Claude Code sessions ----------
_REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)


def _block_text(b):
    t = b.get("type")
    if t == "text":
        return b.get("text", "")
    if t == "tool_use":
        return f"[tool {b.get('name')}] {json.dumps(b.get('input', {}), ensure_ascii=False)[:400]}"
    if t == "tool_result":
        c = b.get("content")
        if isinstance(c, list):
            c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
        return f"[result{' ERROR' if b.get('is_error') else ''}] {str(c or '')[:800]}"
    return ""  # thinking, images


def parse_session(path):
    lines, title, first_prompt, ts = [], None, None, None
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            try:
                o = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if o.get("type") == "custom-title":
                title = o.get("customTitle") or o.get("title") or title
            if o.get("type") not in ("user", "assistant") or o.get("isMeta"):
                continue
            ts = ts or o.get("timestamp")
            c = o.get("message", {}).get("content")
            text = c if isinstance(c, str) else "\n".join(_block_text(b) for b in c or [] if isinstance(b, dict))
            text = _REMINDER.sub("", text).strip()
            if not text:
                continue
            if o["type"] == "user" and isinstance(c, str) and not first_prompt:
                first_prompt = text
            lines.append(f"{o['type'].upper()}: {text}")
    return "\n\n".join(lines), (title or (first_prompt or path.stem)[:100]).strip(), ts


def claude(db):
    changed = []
    for p in CLAUDE_PROJECTS.glob("*/*.jsonl"):
        key = str(p)
        mtime = str(p.stat().st_mtime)
        if get_state(db, "claude", key) == mtime:
            continue
        text, title, ts = parse_session(p)
        if text:
            ts = (ts or datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat())[:19]
            meta = {"path": str(p), "project": p.parent.name}
            if upsert_item(db, "claude", p.stem, ts, f"{title} [{p.parent.name}]", text, meta):
                changed.append(p.stem)
        set_state(db, "claude", key, mtime)
        db.commit()
    return changed


# ---------- Gmail (read-only) ----------
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
SKIP_LABELS = {"CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL", "SPAM", "TRASH"}
SKIP_SUBJECT = re.compile(r"(?i)verification code|security code|one[- ]time|\bOTP\b|2-step|two-factor|"
                          r"password reset|reset your password|sign[- ]in code|login code|confirm your (email|account)")
QUOTE_START = re.compile(r"(?m)^(On .{5,200}wrote:|-----Original Message-----|From: .+\nSent: )", re.S)


def _gmail_service(interactive=False):
    creds_file, token_file = HOME / "credentials.json", HOME / "token.json"
    if not creds_file.exists():
        raise NotConfigured("no credentials.json, see README")
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        raise NotConfigured("Google libraries missing: pip install google-api-python-client google-auth-oauthlib")
    creds = Credentials.from_authorized_user_file(str(token_file), SCOPES) if token_file.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not interactive:
            raise NotConfigured("not signed in: run `python connectors.py gmail-login`")
        creds = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES).run_local_server(port=0)
    token_file.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _body(payload):
    """Prefer text/plain parts; fall back to tag-stripped HTML."""
    plain, htm = [], []
    stack = [payload]
    while stack:
        p = stack.pop()
        stack.extend(p.get("parts", []))
        data = p.get("body", {}).get("data")
        if not data:
            continue
        text = base64.urlsafe_b64decode(data + "==").decode("utf-8", "replace")
        (plain if p.get("mimeType") == "text/plain" else htm if p.get("mimeType") == "text/html" else []).append(text)
    if plain:
        return "\n".join(plain)
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", "\n".join(htm))
    return html.unescape(re.sub(r"<[^>]+>", " ", text))


def _strip_quotes(text):
    m = QUOTE_START.search(text)
    text = text[:m.start()] if m else text
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith(">")).strip()


def _thread_ids(svc, q):
    ids, token = [], None
    while True:
        r = svc.users().threads().list(userId="me", q=q, pageToken=token, maxResults=500).execute()
        ids += [t["id"] for t in r.get("threads", [])]
        token = r.get("nextPageToken")
        if not token:
            return ids


def gmail(db):
    svc = _gmail_service()
    from googleapiclient.errors import HttpError
    new_hist = svc.users().getProfile(userId="me").execute()["historyId"]  # read first so nothing slips between runs
    base_q = "-category:promotions -category:social -in:spam -in:trash"
    hist = get_state(db, "gmail", "historyId")
    if not hist:
        ids = _thread_ids(svc, f"newer_than:365d {base_q}")
    else:
        ids, token = set(), None
        try:
            while True:
                r = svc.users().history().list(userId="me", startHistoryId=hist, pageToken=token,
                                               historyTypes=["messageAdded"]).execute()
                for h in r.get("history", []):
                    ids |= {m["message"]["threadId"] for m in h.get("messagesAdded", [])}
                token = r.get("nextPageToken")
                if not token:
                    break
        except HttpError as e:
            if e.resp.status != 404:
                raise
            ids = set(_thread_ids(svc, f"newer_than:7d {base_q}"))  # history expired: re-scan recent mail
    changed = []
    for tid in ids:
        t = svc.users().threads().get(userId="me", id=tid, format="full").execute()
        msgs = t.get("messages", [])
        labels = {l for m in msgs for l in m.get("labelIds", [])}
        if not msgs or labels & SKIP_LABELS:
            continue
        hdr = lambda m, k: next((h["value"] for h in m["payload"].get("headers", []) if h["name"].lower() == k), "")
        subject = hdr(msgs[0], "subject") or "(no subject)"
        if SKIP_SUBJECT.search(subject):
            continue
        parts = [f"From: {hdr(m, 'from')}\nTo: {hdr(m, 'to')}\nDate: {hdr(m, 'date')}\n\n{_strip_quotes(_body(m['payload']))}"
                 for m in msgs]
        ts = datetime.fromtimestamp(int(msgs[-1]["internalDate"]) / 1000).isoformat(timespec="seconds")
        url = f"https://mail.google.com/mail/u/0/#all/{tid}"
        if upsert_item(db, "gmail", tid, ts, subject, "\n\n---\n\n".join(parts), {"url": url}):
            changed.append(tid)
    set_state(db, "gmail", "historyId", new_hist)
    return changed


CONNECTORS = {"vault": vault, "claude": claude, "gmail": gmail}

if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["gmail-login"]:
        _gmail_service(interactive=True)
        print("Gmail connected (read-only). Run: python kb.py ingest")
