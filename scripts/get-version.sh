#!/usr/bin/env bash
# Computes the full version string from VERSION file + git state.
# Usage: ./scripts/get-version.sh
#
# Output examples:
#   v0.8.0-dev+build.a3f2c1d   (feature branch)
#   v0.8.0-qa+build.b4e5f6a    (qa branch)
#   v0.8.0-rc+build.c7d8e9f    (rc branch)
#   v0.8.0                      (tagged release on main)
#   v0.8.0+build.d1e2f3a       (untagged main commit)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Read base version
VERSION_FILE="$REPO_ROOT/VERSION"
if [[ ! -f "$VERSION_FILE" ]]; then
    echo "ERROR: VERSION file not found at $VERSION_FILE" >&2
    exit 1
fi
BASE_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"

# Get git info
GIT_HASH="$(git -C "$REPO_ROOT" rev-parse --short=7 HEAD 2>/dev/null || echo "unknown")"
GIT_BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"

# Check if current commit is an exact version tag
EXACT_TAG="$(git -C "$REPO_ROOT" tag --points-at HEAD 2>/dev/null | grep -E "^v[0-9]" | head -1 || true)"

# If this commit is exactly tagged with a version, use that tag directly
if [[ -n "$EXACT_TAG" ]]; then
    echo "$EXACT_TAG"
    exit 0
fi

# Determine stage from branch name
case "$GIT_BRANCH" in
    main|master)
        STAGE=""
        ;;
    qa)
        STAGE="-qa"
        ;;
    rc)
        STAGE="-rc"
        ;;
    *)
        STAGE="-dev"
        ;;
esac

# Build the full version string
echo "v${BASE_VERSION}${STAGE}+build.${GIT_HASH}"
