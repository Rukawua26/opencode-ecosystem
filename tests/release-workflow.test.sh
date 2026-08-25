#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT
PREFLIGHT_SCRIPT="$TMP_DIR/preflight.sh"
MOCK_BIN="$TMP_DIR/bin"
mkdir "$MOCK_BIN"

node - "$ROOT_DIR/.github/workflows/test.yml" "$PREFLIGHT_SCRIPT" <<'NODE'
const fs = require("node:fs");
const lines = fs.readFileSync(process.argv[2], "utf8").split("\n");
const step = lines.findIndex((line) => line === "      - name: Resolve trusted source commit");
const run = lines.findIndex((line, index) => index > step && line === "        run: |");
if (step < 0 || run < 0) throw new Error("Trusted preflight block not found");
const body = [];
for (let index = run + 1; index < lines.length; index++) {
  if (lines[index] && !lines[index].startsWith("          ")) break;
  body.push(lines[index].slice(10));
}
fs.writeFileSync(process.argv[3], `${body.join("\n")}\n`);
NODE

cat > "$MOCK_BIN/gh" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
case "$*" in
  *matching-refs*)
    if [ "$MOCK_TAG_EXISTS" = true ]; then printf '%s\n' "refs/tags/v1.10.0"; fi
    ;;
  *git/ref/tags*) printf '%s\n' "tag tag-object" ;;
  *git/tags/tag-object*) printf '%s\n' "$MOCK_TAG_SHA" ;;
  *actions/workflows/codeql.yml/runs*)
    printf '%s\tpush\tmain\t%s\tsuccess\n' "https://example.invalid/codeql" "$MOCK_CODEQL_SHA"
    ;;
  *) echo "Unexpected gh call: $*" >&2; exit 1 ;;
esac
MOCK
chmod +x "$MOCK_BIN/gh"

MAIN_SHA=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
RELEASE_SHA=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

run_case() {
  local name=$1 expected=$2 release_input=$3 tag_exists=$4 tag_sha=$5 codeql_sha=$6 expected_source=${7:-}
  local output="$TMP_DIR/${name}.output"
  if PATH="$MOCK_BIN:$PATH" GITHUB_EVENT_NAME=workflow_dispatch GITHUB_REPOSITORY=owner/repo \
    GITHUB_SHA="$MAIN_SHA" GITHUB_OUTPUT="$output" REQUESTED_VERSION=1.10.0 \
    RELEASE_SHA_INPUT="$release_input" MOCK_TAG_EXISTS="$tag_exists" MOCK_TAG_SHA="$tag_sha" \
    MOCK_CODEQL_SHA="$codeql_sha" bash --noprofile --norc -e -o pipefail "$PREFLIGHT_SCRIPT" >/dev/null 2>&1; then
    actual=success
  else
    actual=failure
  fi
  test "$actual" = "$expected" || { echo "$name: expected $expected, got $actual" >&2; exit 1; }
  if [ "$expected" = success ]; then
    # shellcheck disable=SC1090
    source "$output"
    # shellcheck disable=SC2154
    test "$source_sha" = "$expected_source" || { echo "$name: unexpected source SHA" >&2; exit 1; }
  fi
}

run_case new-release success "" false "" "$MAIN_SHA" "$MAIN_SHA"
run_case new-release-existing-tag failure "" true "$RELEASE_SHA" "$MAIN_SHA"
run_case retry-missing-tag failure "$RELEASE_SHA" false "" "$RELEASE_SHA"
run_case retry-matching-tag success "$RELEASE_SHA" true "$RELEASE_SHA" "$RELEASE_SHA" "$RELEASE_SHA"
run_case retry-conflicting-tag failure "$RELEASE_SHA" true "$MAIN_SHA" "$RELEASE_SHA"

echo "[PASS] Release preflight enforces new and retry modes"
