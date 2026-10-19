# Second Brain Kit

A second brain that gives you **and your AI agent** a memory. It's built for [Claude Code](https://claude.com/claude-code) and [Obsidian](https://obsidian.md), and it runs locally.

- **The vault** holds what you *think*: your notes in Obsidian, as plain markdown files you own, backed up to a private git repo.
- **The knowledge base** holds what *happened*: every past Claude Code session, your vault notes and (optionally) your Gmail, all in one SQLite file. Keyword search over it takes about a tenth of a second.
- **The agent** searches both before answering questions about your past work, and links back to the original source.

```
sources ──► knowledge base (~/kb) ──► Claude Code ──► vault (~/SecondBrain)
email*        one sqlite file          kb-search        10 Sources   read-only
AI sessions   keyword search           /session-log     20 Notes     yours
your notes    secrets masked           /weekly, /lint   90 Agent Output  AI writes here
              refreshes every 6h                         git backup, graph + canvas map
```
<sub>* Gmail is optional and read-only.</sub>

## Why
AI agents forget everything between sessions, and Claude Code deletes its own session history after 30 days by default. So you re-explain context, re-solve old errors, and lose track of what you promised people. This kit fixes that with as little machinery as possible.

## Design choices (and why)
- **Keyword search, no vector database.** Names, error messages and file paths are what people actually search for. Results are ranked with BM25, combined with rank fusion, and given a small recency boost. Add embeddings only if your own test questions show misses.
- **Raw text is the truth.** Originals are stored verbatim. Optional Claude Haiku summaries are pointers you can rebuild at any time.
- **Secrets are masked** before anything is stored or summarized. Session transcripts often contain API keys.
- **Email is data, never instructions.** The summarizer has no tools, and the agent is told to report any instructions it finds in your content, never to follow them. This blocks the main prompt-injection route.
- **A fenced vault.** The AI can't edit `10 Sources`, must ask before changing `20 Notes`, and writes freely only in `90 Agent Output`. Permission rules enforce this; it doesn't rely on the AI following instructions.
- **Rituals over automation.** `/session-log` at the end of a useful session, `/weekly` once a week, `/lint` once a month. The most common way these systems fail is that people stop maintaining them, so upkeep has to stay cheaper than the value.

## Install (about 15 minutes)
**Easiest:** clone this repo, open Claude Code in the folder, and say:

> set up my second brain

Claude follows [`SETUP.md`](SETUP.md) and asks before anything that needs a login or costs money.

**What you'll need:** Python 3.10+, git, [Obsidian](https://obsidian.md), and [Claude Code](https://claude.com/claude-code). Windows, macOS and Linux all work.

## Daily use
| When | Do |
|---|---|
| End of a useful Claude session | `/session-log` |
| An idea clicks | Write 3–5 lines in `20 Notes`, in your own words |
| Sunday | `/weekly` |
| Monthly | `/lint` |
| Anytime | Ask Claude about your past ("how did I fix…", "what did we decide about…"). It searches automatically. |

## What's in the repo
| Path | What it is |
|---|---|
| `vault/` | The Obsidian vault template: zones, house rules (`CLAUDE.md`), permission rules, `/weekly` and `/lint`, a Home hub, a canvas mind map, and graph colours |
| `kb/` | The knowledge base: `kb.py` (search, ingest, status, eval), `connectors.py` (vault, Claude sessions, Gmail) and `test_kb.py` |
| `claude-skills/` | User-level skills: `kb-search` and `session-log` |
| `SETUP.md` | Step-by-step install instructions, written so Claude Code can follow them |

## License
MIT. Built by [Joseph Dummar](https://josephdummar.com).
