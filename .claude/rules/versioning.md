# Versioning

## Format

```
v{MAJOR}.{MINOR}.{PATCH}[-{STAGE}][+build.{GIT_SHORT_HASH}]
```

Examples:
- Feature branch: `v0.8.0-dev+build.a3f2c1d`
- QA branch: `v0.8.0-qa+build.b4e5f6a`
- RC branch: `v0.8.0-rc+build.c7d8e9f`
- Tagged release: `v0.8.0`
- Untagged main commit: `v0.8.0+build.d1e2f3a`

## Stages

Stages are determined automatically by the current branch:

| Branch | Stage | Meaning |
|---|---|---|
| `feature/*`, `fix/*`, other | `-dev` | Active development |
| `qa` | `-qa` | In QA testing |
| `rc` | `-rc` | Release candidate |
| `main` (tagged) | _(none)_ | Stable production release |
| `main` (untagged) | _(none)_ | Post-release, pre-next-tag |

## Source of Truth

- **`VERSION`** file at repo root contains the base version number (e.g., `0.8.0`).
- **Git tags** on main mark exact releases (e.g., `v0.8.0`). A tagged commit IS that release.
- **`scripts/get-version.sh`** computes the full version string from VERSION + branch + git hash.

## Bump Rules

- **Patch** (0.8.0 -> 0.8.1): Bug fixes, minor improvements between milestones.
- **Minor** (0.8.0 -> 0.9.0): Planned milestones/workstreams from roadmap.
- **Major** (0.x -> 1.0): Production readiness. v1.0.0 = first stable release.

Bumps happen on feature branches and flow through QA -> RC -> Main.
Use `scripts/bump-version.sh {major|minor|patch}` to bump.

## Branch Flow

```
feature/* --> qa --> rc --> main
```

- Feature branches merge into `qa` for testing.
- Passed features merge from `qa` into `rc`.
- `rc` gets `main` merged in before deploy (stays current with production).
- `qa` gets `rc` merged in before deploy (stays current with RC).
- When a release is ready: tag on `rc`, merge into `main`.

## Build Identification

Every commit on every branch gets a unique build identifier via the git short hash.
The full version string is injected into the frontend at build time via Vite's `define` config.

## Frontend Display

- Version badge: small gray text, fixed to bottom-left of screen.
- Shows the full build string (e.g., `v0.8.0-dev+build.a3f2c1d`).
- If the frontend is running in Vite dev mode, a `DEV` indicator is also shown.

## Tagging a Release

```bash
# On the rc branch, when ready:
git tag v0.8.0
git push origin v0.8.0
git checkout main
git merge rc
git push origin main
```
