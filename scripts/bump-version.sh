#!/usr/bin/env bash
# Bump the version in the VERSION file.
# Usage: ./scripts/bump-version.sh {major|minor|patch}
#
# This updates the VERSION file only. Does NOT create git tags.
# Tags are created on the rc branch at release time.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION_FILE="$REPO_ROOT/VERSION"

if [[ ! -f "$VERSION_FILE" ]]; then
    echo "ERROR: VERSION file not found at $VERSION_FILE" >&2
    exit 1
fi

BUMP_TYPE="${1:-}"
if [[ -z "$BUMP_TYPE" ]]; then
    echo "Usage: $0 {major|minor|patch}" >&2
    exit 1
fi

CURRENT="$(tr -d '[:space:]' < "$VERSION_FILE")"

# Parse major.minor.patch
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

case "$BUMP_TYPE" in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
    *)
        echo "ERROR: Unknown bump type '$BUMP_TYPE'. Use major, minor, or patch." >&2
        exit 1
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo "$NEW_VERSION" > "$VERSION_FILE"
echo "Bumped version: $CURRENT -> $NEW_VERSION"
