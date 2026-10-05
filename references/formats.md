# Output Formats

Templates for the three target outputs. The script gives you structured JSON
(see SKILL.md); you fill these in. Every entry must trace to a commit hash or a
path in the JSON.

## 1. Conventional-Commits → changelog sections

Map `type` to a section heading. Use only sections that have entries.

| type | Keep-a-Changelog section | GitHub release section |
|---|---|---|
| feat | Added | Features |
| fix | Fixed | Bug Fixes |
| perf | Changed | Performance |
| refactor | Changed | Refactors |
| revert | Removed | Reverts |
| docs | (skip or Documentation) | Documentation |
| test | (skip) | Tests |
| build / ci | (skip) | Build / CI |
| chore / style | (skip) | (skip) |

Rules:
- Drop `chore`, `style`, `test`, `ci`, `build` from user-facing changelogs
  unless the user asks for a full technical log.
- Use `scope` as a prefix when present: `**api:** add rate limiting`.
- `description` is the commit subject with the `type(scope):` prefix stripped.
- Deduplicate: one line per user-visible change, even if several commits touch it.
- `breaking: true` commits go in Breaking Changes AND their normal section.

## 2. Keep-a-Changelog (CHANGELOG.md)

```markdown
# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Source range: `<FROM>..<TO>` (branch `<branch>`, <N> commits).

## [Unreleased]

### Added
- <feature> (<scope>) — <hash>

### Changed
### Fixed
### Removed

### Breaking Changes
- <what broke and the migration step> (<hash>)

## [x.y.z] - YYYY-MM-DD
...
```

## 3. GitHub Release Notes

```markdown
## What's Changed

### Features
- <feature> by @<author> in <hash>

### Bug Fixes
- <fix> by @<author> in <hash>

### Breaking Changes
- <change> — migration: <step>

**Full Changelog**: <FROM>...<TO>
```

## 4. Documentation / diff summary (uses `--patch`)

For "explain what this change does" rather than a changelog:

```markdown
# Changes: <range> (<branch>)

## Summary
<2-3 sentences: what this change set accomplishes, in domain terms.>

## Modules touched
### `<path/group>`
- <what changed and why, referencing the diff>
- API/behavior impact: <none | description>

## Migration / compatibility
<only if breaking changes; else "None".>

## Files changed
| Path | ±  | Note |
|---|---|---|
| <path> | +N/-M | <short note> |
```

When writing this template, read the diff hunks from the JSON `patch` field —
do not summarize file *names* as if they were content.

## Choosing

- Release / version bump → template 2 or 3.
- PR description or "what changed" → template 3.
- "Understand / document this code" → template 4 (needs `--patch`).