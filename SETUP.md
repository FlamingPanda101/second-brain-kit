# Setup

These steps are written for Claude Code to follow, but you can do them by hand. Before running anything that needs a login or costs money, ask the user first. Never print or store their keys.

Defaults: the vault goes in `~/SecondBrain` and the knowledge base in `~/kb`. If the user wants other locations, update the paths in `kb/connectors.py` (`VAULT`), in both `claude-skills/*/SKILL.md` files, and in `vault/.claude/skills/weekly/SKILL.md`.

Keep both folders **outside** cloud-synced folders such as Google Drive, OneDrive, iCloud or Dropbox. Cloud sync can corrupt a live SQLite file or a `.git` folder, and the knowledge base holds private data.

## 1. Vault
1. Copy `vault/` to `~/SecondBrain`, including the hidden `.claude` and `.obsidian` folders and `.gitignore`.
2. Run `git init -b main`, then `git add -A`, then `git commit -m "Initial vault"` inside it.
3. Optional off-site backup: create a **private** repo and push to it, for example `gh repo create second-brain --private --source=. --push`. Ask first; it needs the user's GitHub login. Section 4 then backs it up automatically.
4. In Obsidian: **Open folder as vault** → `~/SecondBrain` → **Trust**. Optional: the "Git" community plugin (by Vinzent) adds a history view inside Obsidian. Don't rely on it for backups, because it only runs while Obsidian is open. The scheduled `tools/backup.py` in section 4 handles backups.
5. Edit the **Areas** list in `Home.md` to match the user's life: their jobs, classes, projects.

## 2. Knowledge base
1. Copy `kb/` to `~/kb`.
2. Run `python ~/kb/test_kb.py`. It should print `ok`.
3. Run `python ~/kb/kb.py ingest`, then `python ~/kb/kb.py status`. Claude Code sessions and vault notes should show item counts.
4. Copy `kb/evals.example.tsv` to `~/kb/evals.tsv`, then replace the examples with 10 real questions the user would ask, each paired with text from the result that should come back. Run `python ~/kb/kb.py eval`.

## 3. Claude Code
1. Copy `claude-skills/kb-search` and `claude-skills/session-log` into `~/.claude/skills/`.
2. In `~/.claude/settings.json`, set `"cleanupPeriodDays": 3650` so session history isn't deleted after 30 days. Merge it into the existing JSON; don't overwrite other settings.
3. Append this to `~/.claude/CLAUDE.md`:
   ```markdown
   ## Second brain
   - Obsidian vault: `~/SecondBrain`. Read its `CLAUDE.md` before writing there; agent writes go only in `90 Agent Output/`.
   - Before answering questions about my past work, decisions, emails or earlier Claude sessions, use the `kb-search` skill.
   ```
4. Optional: install Obsidian's official skills with `claude plugin marketplace add kepano/obsidian-skills`, then `claude plugin install obsidian@obsidian-skills`.

## 4. Keep it fresh (every 6 hours)
Use the full path to Python. Logs go to `~/kb/kb.log`.

- **Windows** (PowerShell):
  ```powershell
  $py = (Get-Command pythonw).Source
  $a = New-ScheduledTaskAction -Execute $py -Argument "`"$HOME\kb\kb.py`" ingest" -WorkingDirectory "$HOME\kb"
  $t = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 6)
  $s = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
  Register-ScheduledTask -TaskName "Second Brain KB ingest" -Action $a -Trigger $t -Settings $s
  ```
- **macOS / Linux** (cron): run `crontab -e` and add the line `0 */6 * * * python3 ~/kb/kb.py ingest`.

**Vault backup, every 30 minutes.** `tools/backup.py` commits everything, pulls, and pushes. With no remote, it commits locally. It refuses to commit anything shaped like an API key or private key, and it writes one line per run to `.git/backup.log`. First run `python ~/SecondBrain/tools/backup.py --test`, which should print `ok`.

- **Windows** (PowerShell):
  ```powershell
  $py = (Get-Command pythonw).Source
  $a = New-ScheduledTaskAction -Execute $py -Argument "`"$HOME\SecondBrain\tools\backup.py`"" -WorkingDirectory "$HOME\SecondBrain"
  $t = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 30)
  $s = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
  Register-ScheduledTask -TaskName "Second Brain vault backup" -Action $a -Trigger $t -Settings $s
  ```
- **macOS / Linux** (cron): add `*/30 * * * * python3 ~/SecondBrain/tools/backup.py`.

## 5. Optional extras (ask the user first)
- **AI summaries** (Claude Haiku, usually under $1 for the first backfill): `pip install anthropic`, then put `ANTHROPIC_API_KEY=...` in `~/kb/.env` and run `python ~/kb/kb.py summarize`. It shows the cost and asks before spending anything.
- **Gmail (read-only):** follow the "Connecting Gmail" steps in `kb/README.md`.

## Done when
- [ ] `python ~/kb/kb.py status` shows recent `last ok` times.
- [ ] Asking Claude "what did I work on last week?" from any folder triggers `kb-search`.
- [ ] In a Claude session started in `~/SecondBrain`, asking it to create a file in `10 Sources` is **refused**.
- [ ] Obsidian shows the vault, and `Second Brain Map` opens.
- [ ] Within 30 minutes of setup, `.git/backup.log` in the vault ends with an `ok` line.
