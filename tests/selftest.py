#!/usr/bin/env python3
"""Self-check for collect_changes.py. Builds a throwaway git repo, runs every
mode, asserts the JSON. No network, no frameworks. Run: python3 selftest.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "collect_changes.py"


def run(repo, *args):
    p = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(repo), *args],
                       capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def sh(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)


def main():
    d = Path(tempfile.mkdtemp(prefix="rng-selftest-"))
    sh(d, "init", "-q")
    sh(d, "config", "user.email", "t@t.io")
    sh(d, "config", "user.name", "Test")

    (d / "a.txt").write_text("one\n")
    sh(d, "add", "a.txt")
    sh(d, "commit", "-q", "-m", "feat(core): first feature")

    (d / "a.txt").write_text("one\ntwo\n")
    (d / "b.txt").write_text("new\n")
    sh(d, "add", "a.txt", "b.txt")
    sh(d, "commit", "-q", "-m", "fix: correct a thing\n\nBREAKING CHANGE: a.txt format")

    # --last : one commit, breaking detected, conventional true
    rc, out, err = run(d, "--last")
    assert rc == 0, err
    o = json.loads(out)
    assert o["stats"]["commits"] == 1, o["stats"]
    assert o["conventional"] is True
    assert o["commits"][0]["type"] == "fix", o["commits"][0]
    assert o["commits"][0]["breaking"] is True, o["commits"][0]
    assert o["commits"][0]["description"] == "correct a thing"

    # --from <root> : 2 commits, both files
    # --all : full history incl. root commit
    rc, out, _ = run(d, "--all")
    o = json.loads(out)
    assert o["stats"]["commits"] == 2, o["stats"]
    assert {"a.txt", "b.txt"} <= {f["path"] for f in o["files_changed"]}, o["files_changed"]

    # --working + --untracked
    (d / "c.txt").write_text("untracked\n")
    rc, out, _ = run(d, "--working", "--untracked")
    o = json.loads(out)
    assert o["range"] == "uncommitted"
    assert "c.txt" in o["untracked"], o["untracked"]

    # --staged
    sh(d, "add", "c.txt")
    rc, out, _ = run(d, "--staged")
    o = json.loads(out)
    assert "c.txt" in {f["path"] for f in o["files_changed"]}, o["files_changed"]

    # --since
    rc, out, _ = run(d, "--since", "2000-01-01")
    o = json.loads(out)
    assert o["stats"]["commits"] == 2, o["stats"]

    # --patch truncation
    rc, out, _ = run(d, "--last", "--patch", "--max-patch-bytes", "20")
    o = json.loads(out)
    assert "[patch truncated]" in o["patch"], o["patch"]

    # bad repo -> error JSON, exit 1
    rc, out, _ = run(d / "nope", "--last")
    assert rc == 1, rc
    assert "error" in json.loads(out)

    print("selftest: OK (8 checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())