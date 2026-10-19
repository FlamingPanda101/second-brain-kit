---
name: lint
description: Health check for the Obsidian vault, covering broken links, orphan notes, missing frontmatter and stale AI notes. Use when the user says "lint", "/lint", or "check the vault".
---

This is a report-only pass. Do not fix anything unless the user says so afterwards.

1. **Broken links**: for each `[[Target]]` or `[[Target|alias]]` in every `.md` file, check that `Target.md` exists somewhere in the vault.
2. **Orphans**: notes in `20 Notes/` that no other note links to.
3. **Frontmatter**: files in `90 Agent Output/` that are missing `source: ai` or `created:`.
4. **Stale AI notes**: files in `90 Agent Output/` older than 90 days that nothing links to. Suggest archiving them; do not delete anything.
5. **Contradictions**: if two notes make conflicting claims about the same fact, list both with paths.
6. **Secrets**: grep for `sk-`, `ghp_`, `gho_`, `AKIA`, `AIza`, `xox`, `-----BEGIN`, and for `password` followed by `:` or `=`.

Output: one short table per check (path, problem, suggested fix). Leave out any check that found nothing.
