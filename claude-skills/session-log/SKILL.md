---
name: session-log
description: Write a short log of the current Claude session into the user's Obsidian vault. Use when the user says "/session-log", "log this session", "save this to my second brain", or "done for today".
---

Write `~/SecondBrain/90 Agent Output/Sessions/YYYY-MM-DD-<project-slug>.md`. If that file already exists, append `-2`, `-3` and so on. Never write anywhere else in the vault.

```markdown
---
source: ai
created: YYYY-MM-DD
project: "[[<Hub name>]]"
tags: [session]
---
# <one-line title of what this session was about>
Part of [[<Hub name>]].

## Outcome
2-3 sentences: what is now true or done.

## Decisions
- Decision, then *why* (one line each).

## Errors and fixes
- `exact error text` → what fixed it.

## Commands and paths worth remembering
- `command or path`: what it's for.

## Follow-ups
- [ ] Next step, owner, and date if one is known.
```

Hub (this is what builds the mind map in Graph view):
- Choose `<Hub name>` from the Areas links in `~/SecondBrain/Home.md` (for example `Work`, `Finances` or a project name). If none fits, pick a short new name and add it to the right Areas line in Home.md.
- If `90 Agent Output/Projects/<Hub name>.md` doesn't exist yet, create it with frontmatter `source: ai`, `created:`, a one-line description, and a `## Sessions` heading.
- Append `- [[YYYY-MM-DD-<slug>]]: <title>` under `## Sessions` in the hub.

Rules:
- Use exact strings (error text, flags, file paths) so keyword search can find them later.
- Leave out any section that would be empty. Keep the whole note under about 40 lines.
- Never include passwords, API keys or tokens.
- When finished, run `git -C ~/SecondBrain add "90 Agent Output" Home.md && git -C ~/SecondBrain commit -m "session log: <title>"`.
