---
name: release-notes-generator
description: Turn git changes into changelogs and release notes.
version: 0.1.0
author: Faza Syaquille Suny, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [changelog, release-notes, documentation, git, conventional-commits]
    related_skills: [git-workflow-and-versioning, documentation-and-adrs]
---

# Release Notes & Auto-Documenter Skill

Scan code changes (a git range, staged work, or the working tree) and write them
up as a Keep-a-Changelog entry, GitHub release notes, or a documentation diff
summary. The script does collection and structuring; you write the prose. No
dependencies beyond Python stdlib + `git`.

## When to Use

- User asks for a changelog, release notes, or "what changed since X"
- Cutting a release and needing a version entry
- Summarizing a branch/PR into human-readable documentation
- Auditing a working tree or staged set before commit

Don't use for: per-line code review (`requesting-code-review`), writing ADRs
for a single decision (`documentation-and-adrs`), or committing/branching
(`git-workflow-and-versioning`).

## How to Run

Collect structured JSON first, then write the document from it:

```
terminal(command="python3 ~/.hermes/skills/software-development/release-notes-generator/scripts/collect_changes.py --repo <PATH> --from <REF>", timeout=60)
```

Modes (pick one; default `--last` = `HEAD~1..HEAD`):

| Flag | Scope |
|---|---|
| `--last` | last commit |
| `--all` | entire history incl. root commit |
| `--from A --to B` | explicit range (`--to` defaults to `HEAD`) |
| `--since 2026-10-01` | commits since a date |
| `--staged` | staged changes |
| `--working` | uncommitted tracked changes |
| `--untracked` | add untracked files to the file list (combinable) |
| `--patch` | include raw unified diff (bulky; use for doc writing, not changelogs) |

Output JSON: `repo`, `branch`, `range`, `conventional` (bool — every commit
parsed as Conventional Commits), `commits[]` (hash/author/date/type/scope/
breaking/subject/body), `files_changed[]` (path ±insertions/deletions),
`untracked[]`, `stats{}`.

## Procedure

1. **Determine the range.** Ask or infer: unreleased work → `--working` /
   `--staged`; a release → `--from <last-tag>`. If tags exist, use
   `terminal(command="git -C <PATH> describe --tags --abbrev=0", timeout=10)`
   to get the previous release. Completion: one range chosen and its JSON
   printed.
2. **Collect.** Run the script for that range. Completion: valid JSON, and
   `stats.commits` matches `git log --oneline <range> | wc -l`.
3. **Group the changes.** Read `commits`; if `conventional` is true, bucket by
   `type` (see `references/formats.md`). If false, cluster by reading subjects
   and `files_changed` — never invent types. Completion: every commit placed in
   exactly one bucket, or listed under "Other".
4. **Write the document** from `references/formats.md` (Keep-a-Changelog,
   GitHub release, or doc-summary — pick per request). Every entry must trace to
   a commit hash or a file path in the JSON. Completion: no entry lacks a
   source line.
5. **Flag breaking changes** — any commit with `breaking: true` goes in a
   prominent Breaking Changes section. Completion: count matches the JSON.
6. **Deliver** the file (write to `CHANGELOG.md` or the requested path) and
   state the source range in the doc header.

## Pitfalls

- **First commit / single-commit repo**: `--last` fails (`HEAD~1` missing). Use
  `--all`, or `--from $(git rev-list --max-parents=0 HEAD)` (which excludes the
  root commit itself — use `--all` for the true full history).
- **`--patch` is not for changelogs.** It bloats the write-up; use it only when
  the user wants a prose *documentation* summary that needs actual diffs.
- **Binary files** show `insertions: null`, `binary: true` — don't report a
  line count for them.
- **Non-conventional history** (`conventional: false`): infer groups from
  subjects + paths; state that you inferred them. Don't fabricate scopes.
- **Author-time vs commit-time**: the `date` field is author date (`%aI`).
- **Renamed files** appear as delete+add in `--numstat` unless `-M` is used.
- Submodule/binary/`.db` files inflate `stats` — filter obvious noise
  (`*.db`, `package-lock.json`) from the user-facing summary, keep them in JSON.

## Verification

- `stats.commits` equals the real commit count for the range.
- Every changelog entry cites a hash or path present in the JSON.
- Breaking-change count in the doc equals `[c for c in commits if c['breaking']]`.
- `python3 scripts/collect_changes.py --repo <PATH> --last` exits 0 and prints
  parseable JSON. Full self-check: `python3 tests/selftest.py` (builds a scratch
  repo, exercises every mode, 8 asserts).

## Reference

- `references/formats.md` — Conventional-Commits → changelog section mapping,
  Keep-a-Changelog template, GitHub release template, doc-summary template.