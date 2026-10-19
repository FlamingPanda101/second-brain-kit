"""Smallest checks that fail if redaction, de-duplication or ranking break. Run: python test_kb.py"""
from datetime import datetime
import kb

# redaction
s = kb.redact('key sk-ant-api03-abcdefghijklmnopqrstuvwxyz and "API_KEY": "0f9e8d7c6b5a4f3e2d1c" token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ12')
assert "sk-ant" not in s and "0f9e8d7c" not in s and "ghp_" not in s, s
assert "ponytail" not in kb.redact(r'{\\"API_KEY\\": \\"ponytail123\\"}')  # JSON-escaped quotes
assert "commit 973e58f" == kb.redact("commit 973e58f")  # ordinary text untouched

db = kb.connect(":memory:")
# idempotent upsert
assert kb.upsert_item(db, "t", "a", "2026-10-01T00:00:00", "Landlord deposit", "The deposit refund is due Nov 1.", {})
assert not kb.upsert_item(db, "t", "a", "2026-10-01T00:00:00", "Landlord deposit", "The deposit refund is due Nov 1.", {})
assert db.execute("SELECT count(*) FROM docs WHERE source_id='a'").fetchone()[0] == 2  # item + 1 raw chunk

# ranking: exact phrase beats scattered words; recency breaks ties
kb.upsert_item(db, "t", "b", "2024-01-01T00:00:00", "Notes", "path here. later on, the error was about something else", {})
kb.upsert_item(db, "t", "c", "2026-10-01T00:00:00", "Fix", "Fixed the PATH error by reinstalling Python", {})
kb.upsert_item(db, "t", "d", "2023-01-01T00:00:00", "Fix", "Fixed the PATH error by reinstalling Python", {})
res = kb.search(db, "PATH error", now=datetime(2026, 10, 19))
assert [r[3] for _, r in res][:2] == ["c", "d"], [r[3] for _, r in res]
assert kb.search(db, "deposit", after="2026-01-01")[0][1][3] == "a"
assert kb.search(db, "deposit", source="nope") == []
print("ok")
