#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP_REPO=$(mktemp -d)
trap 'rm -rf "$TMP_REPO"' EXIT

git -C "$TMP_REPO" init -q
git -C "$TMP_REPO" config user.name "Release Test"
git -C "$TMP_REPO" config user.email "release-test@example.invalid"
printf '%s\n' "release" > "$TMP_REPO/release.txt"
git -C "$TMP_REPO" add release.txt
git -C "$TMP_REPO" commit -qm "release candidate"
release_commit=$(git -C "$TMP_REPO" rev-parse HEAD)
git -C "$TMP_REPO" tag -a v1.10.0 -m "Release v1.10.0"

GIT_DIR="$TMP_REPO/.git" GIT_WORK_TREE="$TMP_REPO" \
  bash "$ROOT_DIR/tools/scripts/verify-release-tag.sh" v1.10.0 "$release_commit"

printf '%s\n' "later" >> "$TMP_REPO/release.txt"
git -C "$TMP_REPO" add release.txt
git -C "$TMP_REPO" commit -qm "later commit"
later_commit=$(git -C "$TMP_REPO" rev-parse HEAD)

if GIT_DIR="$TMP_REPO/.git" GIT_WORK_TREE="$TMP_REPO" \
  bash "$ROOT_DIR/tools/scripts/verify-release-tag.sh" v1.10.0 "$later_commit" >/dev/null 2>&1; then
  echo "Expected a conflicting release tag to fail" >&2
  exit 1
fi

echo "[PASS] Annotated release tags must resolve to the expected commit"
