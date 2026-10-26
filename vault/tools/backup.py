"""Back up this vault to GitHub: commit everything, pull, push.

Schedule it every 30 minutes (Task Scheduler or cron, see SETUP.md) so backups
do not depend on Obsidian being open (Obsidian Git only runs while the app is).
Every run writes one line to .git/backup.log. `python tools/backup.py --test` checks the secret guard.
"""
import datetime
import re
import subprocess
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
LOG = VAULT / ".git" / "backup.log"
# High-confidence key shapes only. A hit stops the backup rather than pushing a key to GitHub.
SECRET = re.compile(
    r"sk-ant-[\w-]{20,}|sk-[A-Za-z0-9]{32,}|gh[pousr]_[A-Za-z0-9]{36}|github_pat_\w{40,}"
    r"|AKIA[0-9A-Z]{16}|AIza[\w-]{35}|xox[abprs]-[\w-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----"
)


def git(*args):
    r = subprocess.run(["git", *args], cwd=VAULT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {(r.stderr or r.stdout).strip()}")
    return r.stdout


def backup():
    git("add", "-A")
    added = [l for l in git("diff", "--cached", "-U0").splitlines()
             if l.startswith("+") and not l.startswith("+++")]
    hit = next((m.group(0) for l in added if (m := SECRET.search(l))), None)
    if hit:
        git("reset", "-q")  # unstage only; the files are untouched
        raise RuntimeError(f"possible secret starting '{hit[:6]}' in changed files; nothing committed. "
                           "Remove it, then the next run backs up as normal.")
    committed = bool(git("diff", "--cached", "--name-only").strip())
    if committed:
        git("commit", "-q", "-m", f"vault backup: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
    if not git("remote").strip():
        return f"ok: {'committed ' if committed else ''}locally (no remote to push to)"
    try:
        git("pull", "--rebase", "--autostash", "-q")
    except RuntimeError:
        subprocess.run(["git", "rebase", "--abort"], cwd=VAULT, capture_output=True)
        raise  # the local commit is kept; fix the conflict by hand
    ahead = int(git("rev-list", "--count", "@{u}..HEAD"))
    if ahead:
        git("push", "-q")
    return f"ok: {'committed, ' if committed else ''}{ahead} pushed"


def test():
    fake = "sk-ant-" + "a1" * 15
    assert SECRET.search(f"key = {fake}") and SECRET.search("gh" + "p_" + "x" * 36)
    assert not SECRET.search("Never write passwords, API keys or tokens. sk-learn is a library.")
    assert not SECRET.search(SECRET.pattern)  # this file can back itself up
    print("ok")


if __name__ == "__main__":
    if "--test" in sys.argv:
        test()
        sys.exit()
    try:
        result, code = backup(), 0
    except Exception as e:
        result, code = f"FAILED: {e}", 1
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M} {result}\n")
    sys.exit(code)  # non-zero shows up as Last Result in Task Scheduler
