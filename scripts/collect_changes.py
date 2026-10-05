#!/usr/bin/env python3
"""Collect git changes as structured JSON for documentation/release-notes generation.

Stdlib only. Prints JSON to stdout. Reads no config files.

Usage:
  collect_changes.py [--repo PATH] [--from REF] [--to REF] [--since DATE]
                     [--staged] [--working] [--last] [--untracked]
                     [--patch] [--max-patch-bytes N]

Modes (pick one; default --last):
  --last          changes in HEAD (diff HEAD~1..HEAD)
  --from/--to     explicit git range (--to defaults to HEAD)
  --since DATE    commits since a date (git log --since)
  --staged        staged changes (diff --cached)
  --working       uncommitted tracked changes (diff HEAD)

Add --untracked to include new untracked files (file list only, no patch).
"""
import argparse
import json
import re
import subprocess
import sys

CONVENTIONAL = re.compile(r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<subject>.+)$")
DEFAULT_TYPES = ["feat", "fix", "perf", "refactor", "docs", "test",
                 "build", "ci", "chore", "style", "revert"]


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout


def parse_commit(raw):
    """raw is one record from `git log --format=%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b%x1e`."""
    h, an, ae, ai, subject, body = (raw.split("\x1f") + [""] * 6)[:6]
    m = CONVENTIONAL.match(subject.strip())
    rec = {
        "hash": h.strip()[:12],
        "author": an.strip(),
        "email": ae.strip(),
        "date": ai.strip(),
        "subject": subject.strip(),
        "body": body.strip(),
        "type": None,
        "scope": None,
        "breaking": False,
        "description": subject.strip(),
    }
    if m:
        rec["type"] = m.group("type").lower()
        rec["scope"] = m.group("scope")
        rec["breaking"] = bool(m.group("breaking"))
        rec["description"] = m.group("subject").strip()
    # breaking change footer: `BREAKING CHANGE: ...`
    if "BREAKING CHANGE" in rec["body"] or "BREAKING-CHANGE" in rec["body"]:
        rec["breaking"] = True
    return rec


def numstat(repo, *diff_args):
    out = git(repo, "diff", "--numstat", *diff_args)
    files = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        add, dele, path = parts
        files.append({
            "path": path,
            "insertions": int(add) if add.isdigit() else None,
            "deletions": int(dele) if dele.isdigit() else None,
            "binary": add == "-",
        })
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--from", dest="frm")
    ap.add_argument("--to", dest="to")
    ap.add_argument("--since")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--working", action="store_true")
    ap.add_argument("--last", action="store_true")
    ap.add_argument("--all", action="store_true", help="entire history")
    ap.add_argument("--untracked", action="store_true")
    ap.add_argument("--patch", action="store_true",
                    help="include raw unified diff (bulky; for doc writing)")
    ap.add_argument("--max-patch-bytes", type=int, default=40000)
    a = ap.parse_args()

    repo = a.repo
    try:
        git(repo, "rev-parse", "--git-dir")
    except SystemExit as e:
        print(json.dumps({"error": str(e), "repo": repo}))
        return 1

    log_range = None      # args for `git log`
    diff_args = []        # args for `git diff --numstat`
    label = ""

    if a.frm:
        rng = f"{a.frm}..{a.to or 'HEAD'}"
        log_range = [rng]
        diff_args = [rng]
        label = rng
    elif a.since:
        log_range = [f"--since={a.since}"]
        diff_args = [f"--since={a.since}"]
        label = f"since {a.since}"
    elif a.staged:
        diff_args = ["--cached"]
        label = "staged"
    elif a.working:
        diff_args = ["HEAD"]
        label = "uncommitted"
    elif a.all:
        log_range = ["HEAD"]
        diff_args = ["4b825dc642cb6eb9a060e54bf8d69288fbee4904", "HEAD"]
        label = "all history"
    else:
        log_range = ["HEAD~1..HEAD"]
        diff_args = ["HEAD~1", "HEAD"]
        label = "HEAD~1..HEAD"

    commits = []
    if log_range:
        fmt = "%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b%x1e"
        raw = git(repo, "log", "--format=" + fmt, *log_range)
        commits = [parse_commit(r) for r in raw.split("\x1e") if r.strip()]

    files = numstat(repo, *diff_args)

    untracked = []
    if a.untracked:
        untracked = [f for f in git(repo, "ls-files", "--others",
                                    "--exclude-standard").splitlines() if f]

    result = {
        "repo": git(repo, "rev-parse", "--show-toplevel").strip(),
        "branch": git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip(),
        "range": label,
        "conventional": bool(commits) and all(c["type"] for c in commits) if commits else False,
        "commits": commits,
        "files_changed": files,
        "untracked": untracked,
        "stats": {
            "commits": len(commits),
            "files": len(files),
            "insertions": sum(f["insertions"] or 0 for f in files),
            "deletions": sum(f["deletions"] or 0 for f in files),
        },
    }

    if a.patch:
        patch = git(repo, "diff", *diff_args)
        if len(patch) > a.max_patch_bytes:
            patch = patch[:a.max_patch_bytes] + "\n... [patch truncated]"
        result["patch"] = patch

    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())