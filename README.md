# release-notes-generator

Turn git changes into changelogs and release notes.

Scans a git range (or staged / working-tree changes) and emits **structured JSON**
— parsed Conventional Commits, breaking-change flags, per-file stats, optional
patch. The JSON is the input to a changelog, GitHub release, or documentation
summary (see `references/formats.md`). Collection is deterministic and scripted;
only the prose is written by a model.

This is also a **Hermes Agent skill**: drop `SKILL.md` into your skills dir and
the agent loads it automatically when the task matches.

## Requirements

- Python 3.8+
- `git` on `PATH`

No third-party packages. Stdlib only.

## Usage

```bash
python3 scripts/collect_changes.py --repo /path/to/repo [MODE] [OPTIONS]
```

Modes (pick one; default `--last`):

| Flag | Scope |
|---|---|
| `--last` | last commit (`HEAD~1..HEAD`) |
| `--all` | entire history incl. root commit |
| `--from A --to B` | explicit range (`--to` defaults to `HEAD`) |
| `--since 2026-10-01` | commits since a date |
| `--staged` | staged changes |
| `--working` | uncommitted tracked changes |
| `--untracked` | add untracked files to the file list (combinable) |
| `--patch` | include raw unified diff (`--max-patch-bytes N`, default 40000) |

Output is JSON on stdout: `repo`, `branch`, `range`, `conventional` (bool),
`commits[]`, `files_changed[]`, `untracked[]`, `stats{}`.

### Example

```bash
python3 scripts/collect_changes.py --repo ~/myapp --from v1.2.0
```

```json
{
  "repo": "/home/me/myapp",
  "branch": "main",
  "range": "v1.2.0..HEAD",
  "conventional": true,
  "commits": [
    { "hash": "a1b2c3d4e5f6", "type": "feat", "scope": "api",
      "breaking": false, "description": "add rate limiting", "...": "..." }
  ],
  "files_changed": [ { "path": "src/api.ts", "insertions": 42, "deletions": 3, "binary": false } ],
  "stats": { "commits": 1, "files": 1, "insertions": 42, "deletions": 3 }
}
```

## Develop

```bash
python3 tests/selftest.py     # builds a scratch repo, exercises every mode
```

## License

MIT — see [LICENSE](LICENSE).