#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: verify-release-tag.sh <tag> <expected-commit>" >&2
  exit 2
fi

tag="$1"
expected_commit="$2"
tag_commit=$(git rev-list -n 1 "$tag")

if [ "$tag_commit" != "$expected_commit" ]; then
  echo "$tag points to $tag_commit, not release commit $expected_commit" >&2
  exit 1
fi
