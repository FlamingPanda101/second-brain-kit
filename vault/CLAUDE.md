# Second Brain vault: house rules

This is my Obsidian vault. Git tracks it, and a private GitHub repo backs it up.

## Zones
- `10 Sources/` holds clippings, imports and raw material. It is **read-only**: never edit, rename or delete anything here. A settings rule enforces this.
- `20 Notes/` is my own writing. Read it freely. Edit it only when I ask for that specific change, and you will be prompted first. Never add AI summaries, links or tags here on your own initiative.
- `90 Agent Output/` is the only place you write freely: `Sessions/`, `Weekly/`, `Research/`, plus new subfolders when they are needed.

## Writing rules
- Use Obsidian syntax: `[[wikilinks]]`, callouts and frontmatter properties. The obsidian-skills plugin has the details.
- Every file you create starts with frontmatter `source: ai`, `created: YYYY-MM-DD`.
- Never rename or move notes, because that breaks `[[links]]` across the vault. Propose the change instead.
- Never write passwords, API keys or tokens into any file.
- Before a multi-file change, run `git add -A && git commit -m "checkpoint"`. Afterwards, show `git diff --stat`.

## Where to look
- "What do I think or know about X?" Search this vault first.
- "What happened, or what did someone say or write?" Use the `kb-search` skill, which covers email and past Claude sessions.
