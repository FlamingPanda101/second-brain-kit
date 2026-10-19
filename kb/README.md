# Knowledge base

One SQLite file that holds your Claude Code sessions, your Obsidian vault and (optionally) Gmail, all searchable by keyword in under a second. Claude searches it through the `kb-search` skill.

| File | What it does |
|---|---|
| `kb.py` | Database, search, summaries and commands (`init`, `ingest`, `search`, `status`, `summarize`, `eval`) |
| `connectors.py` | One function per source: `vault`, `claude`, `gmail` |
| `kb.sqlite` | The data, created on the first ingest. **Never put it in a cloud-synced folder or git**: it can hold your email. |
| `kb.log` | Log of every ingest. Run `python kb.py status` for a summary. |
| `evals.example.tsv` | Example test questions. Copy it to `evals.tsv`, grow it to about 40 real questions, and run `python kb.py eval` after any change. |
| `test_kb.py` | Self-check for secret masking, de-duplication and ranking |
| `.env` | `ANTHROPIC_API_KEY=...` (create this file yourself, only if you want summaries) |
| `credentials.json`, `token.json` | Gmail OAuth files (you create these yourself, only if you want Gmail) |

## Commands
```
python kb.py ingest                 # pull in anything new (safe to run any time)
python kb.py search "words" [--after YYYY-MM-DD] [--source claude|vault|gmail] [--limit N]
python kb.py status                 # per-source health and last sync
python kb.py summarize              # optional AI summaries; shows the cost and asks first
python kb.py eval                   # score your test questions
```

## How search works
- Each query runs as keyword searches (SQLite FTS5 with BM25) over summaries, over raw text, over all the words together and over the exact phrase. The results are merged with reciprocal rank fusion.
- Newer items get a small recency boost.
- Each result shows its date, its source and a pointer to the original.

## Turning on summaries (optional, usually under $1 to backfill)
1. Create an API key at console.anthropic.com, then put `ANTHROPIC_API_KEY=your-key` in `kb/.env`.
2. `pip install anthropic`
3. `python kb.py summarize`. It shows the item count and estimated cost, and asks before spending anything.

After that, each scheduled ingest summarizes new long items automatically, at most 40 per run.

## Connecting Gmail (optional, read-only)
1. `pip install google-api-python-client google-auth-oauthlib`
2. Go to console.cloud.google.com and create a project.
3. **APIs & Services → Library → Gmail API → Enable.**
4. **OAuth consent screen:** choose External. Under Test users, add your own Gmail address. Add the scope `.../auth/gmail.readonly`.
5. **Credentials → Create credentials → OAuth client ID → Desktop app.** Download the JSON and save it as `kb/credentials.json`.
6. `python connectors.py gmail-login`, then approve read-only access in the browser window that opens.
7. `python kb.py ingest`. The first run pulls the last 12 months of email, skipping promotions, social, spam, and 2FA or password-reset emails.

While the app is in Google's "Testing" mode, the sign-in expires after 7 days. Either publish the app (it stays private to you), or re-run step 6 when `status` shows an error.
