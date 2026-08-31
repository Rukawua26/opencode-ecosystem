#!/usr/bin/env node
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { checkWorkflowAnalysisSteps } from "./check-workflow.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..", "..");

let errors = 0;

function checkFile(relPath, checks) {
  const absPath = join(repoRoot, relPath);
  if (!existsSync(absPath)) {
    console.error(`[FAIL] ${relPath}: file not found`);
    errors++;
    return;
  }
  const content = readFileSync(absPath, "utf-8");
  for (const { name, pattern, shouldNotExist } of checks) {
    const found = typeof pattern === "string" ? content.includes(pattern) : pattern.test(content);
    if (shouldNotExist && found) {
      console.error(`[FAIL] ${relPath}: ${name}`);
      errors++;
    } else if (!shouldNotExist && !found) {
      console.error(`[FAIL] ${relPath}: ${name}`);
      errors++;
    }
  }
}

function checkPatternCount(relPath, name, pattern, expected) {
  const content = readFileSync(join(repoRoot, relPath), "utf-8");
  const count = content.match(pattern)?.length ?? 0;
  if (count !== expected) {
    console.error(`[FAIL] ${relPath}: ${name} (expected ${expected}, found ${count})`);
    errors++;
  }
}

function checkPassiveSvg(relPath) {  const content = readFileSync(join(repoRoot, relPath), "utf-8");
  const forbidden = [
    /<!DOCTYPE|<!ENTITY/i,
    /<(?:\w+:)?(?:script|foreignObject|style|use|image|a|animate|animateColor|animateTransform|animateMotion|mpath|discard|set|iframe|object|embed)\b/i,
    /\son\w+\s*=/i,
    /(?:href|src)\s*=/i,
    /(?:javascript|data):/i,
    /@import/i,
    /url\((?!["']?#)/i,
    /\\/,
  ];
  if (forbidden.some((pattern) => pattern.test(content))) {
    console.error(`[FAIL] ${relPath}: should remain a passive, self-contained SVG`);
    errors++;
  }
}

function checkTaggedInstallerBlocks() {
  const content = readFileSync(join(repoRoot, "README.md"), "utf-8");
  const blocks = [...content.matchAll(/```(bash|powershell)\n([\s\S]*?)```/g)];
  for (const [, language, block] of blocks) {
    const downloadsRepository = /git (?:clone|fetch)\b/.test(block);
    const executesInstaller = /(?:bash install\.sh|\.\\install\.ps1)/.test(block);
    if (!downloadsRepository || !executesInstaller) continue;

    const executionIndex = block.search(/(?:bash install\.sh|\.\\install\.ps1)/);
    const beforeExecution = block.slice(0, executionIndex);
    let verifiesTag = false;
    if (language === "bash") {
      const declaration = beforeExecution.match(/^([A-Z_]+)="(v\d+\.\d+\.\d+)"$/m);
      if (declaration) {
        const variable = declaration[1];
        verifiesTag = beforeExecution.includes(`test "$(git describe --tags --exact-match)" = "$${variable}"`);
      }
    } else {
      const declaration = beforeExecution.match(/^\$([A-Za-z][A-Za-z0-9]*) = "(v\d+\.\d+\.\d+)"$/m);
      if (declaration) {
        const variable = declaration[1];
        verifiesTag = beforeExecution.includes(`if ((git describe --tags --exact-match) -ne $${variable})`);
      }
    }
    if (!verifiesTag) {
      console.error("[FAIL] README.md: every downloaded installer checkout must verify its exact tag");
      errors++;
    }
  }
}

checkFile("README.md", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
  { name: "should not include local hypruse session history", pattern: /hypruse|ADR-004/i, shouldNotExist: true },
  { name: "should not claim an unmeasured 61 percent saving", pattern: /61%/, shouldNotExist: true },
  { name: "should not present deterministic checks as 137 agent checks", pattern: /137 checks locales/i, shouldNotExist: true },
  { name: "should document v1.10.0", pattern: /v1\.10\.0/, shouldNotExist: false },
  { name: "should not install the previous memory-adapter release", pattern: /opencode-memory-adapter@1\.9\.0/, shouldNotExist: true },
  { name: "should document the current memory-adapter test count", pattern: /45 tests del memory adapter/, shouldNotExist: false },
  { name: "should mention local-model-router", pattern: /local-model-router/, shouldNotExist: false },
  { name: "should mention obsidian-ingest", pattern: /obsidian-ingest/, shouldNotExist: false },
  { name: "should document opt-in installer sync", pattern: /--sync/, shouldNotExist: false },
  { name: "should document read-only installer preview", pattern: /--dry-run/, shouldNotExist: false },
  { name: "should document structured doctor output", pattern: /opencode-doctor --json/, shouldNotExist: false },
  { name: "should document profile status", pattern: /opencode-profile --status/, shouldNotExist: false },
  { name: "should document direct light profile", pattern: /opencode-light/, shouldNotExist: false },
  { name: "should document index-first skill registry", pattern: /opencode-skills --refresh/, shouldNotExist: false },
  { name: "should use the representative toolkit illustration", pattern: /assets\/toolkit\.svg/, shouldNotExist: false },
  { name: "should bind local illustrations to the current revision", pattern: "raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/assets/", shouldNotExist: true },
  { name: "should verify the Bash checkout against the exact release tag", pattern: /RELEASE_TAG="v1\.10\.0"[\s\S]*git describe --tags --exact-match[\s\S]*bash install\.sh/, shouldNotExist: false },
  { name: "should verify the PowerShell checkout against the exact release tag", pattern: /\$releaseTag = "v1\.10\.0"[\s\S]*git describe --tags --exact-match[\s\S]*\.\\install\.ps1/, shouldNotExist: false },
  { name: "should not pipe remote installers into a shell", pattern: /(?:curl|wget|irm|iwr|Invoke-WebRequest)[^\n|]*\|\s*(?:bash|sh|zsh|iex|Invoke-Expression)\b/i, shouldNotExist: true },
  { name: "should not embed flowcharts or graphs", pattern: /```mermaid|\bflowchart\s+(?:LR|RL|TB|BT)|\bgraph\s+(?:LR|RL|TD|TB|BT)/i, shouldNotExist: true },
  { name: "should not use made-with-love closings", pattern: /hecho con amor|made with love/i, shouldNotExist: true },
  { name: "should document safe scaffolder names", pattern: /scaffolders[\s\S]*kebab-case/i, shouldNotExist: false },
  { name: "should distinguish deterministic checks from agent evals", pattern: /checks deterministas de software, no Agent Evals/i, shouldNotExist: false },
  { name: "should describe provider keys as optional", pattern: /API keys son opcionales/i, shouldNotExist: false },
]);
checkTaggedInstallerBlocks();

checkFile("README.es.md", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
  { name: "should document v1.10.0", pattern: /v1\.10\.0/, shouldNotExist: false },
  { name: "should mention local-model-router or Router local", pattern: /local-model-router|Router local/, shouldNotExist: false },
  { name: "should not duplicate obsolete plugin counts", pattern: /8 plugins|4 MCP servers/i, shouldNotExist: true },
]);

checkFile("docs/comparison.md", [
  { name: "should require Node.js 22 or newer", pattern: /Node\.js 22\+/, shouldNotExist: false },
  { name: "should not require obsolete Node.js 18", pattern: /Node\.js 18\+/, shouldNotExist: true },
  { name: "should not publish obsolete skills or plugin counts", pattern: /18 skills|18\+|Si \(8\)/i, shouldNotExist: true },
  { name: "should not publish unmeasured savings percentages", pattern: /\d{2,3}-\d{2,3}%/, shouldNotExist: true },
  { name: "should not claim unconfigured MCP servers", pattern: /playwright|5\+ MCP/i, shouldNotExist: true },
]);

checkFile("docs/_sidebar.md", [
  { name: "should not expose the historical v1.3 pending page", pattern: /pending-v1\.3|Pendientes v1\.3/i, shouldNotExist: true },
]);

checkFile("packages/memory-adapter/README.md", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
  { name: "should document v1.10.0", pattern: /v1\.10\.0/, shouldNotExist: false },
  { name: "should mention SQLite", pattern: /SQLite/, shouldNotExist: false },
  { name: "should mention MCP", pattern: /MCP/, shouldNotExist: false },
  { name: "should not execute an installer from mutable main", pattern: "raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install", shouldNotExist: true },
]);

checkFile("docs/architecture/diagrams.md", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
  { name: "should not include local hypruse session history", pattern: /hypruse|ADR-004/i, shouldNotExist: true },
]);

checkFile("docs/architecture/overview.md", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
  { name: "should not publish unmeasured savings percentages", pattern: /\d{2,3}-\d{2,3}%/, shouldNotExist: true },
]);

checkFile("docs/token-economy/study.md", [
  { name: "should mark savings as hypotheses", pattern: /Hipotesis/, shouldNotExist: false },
  { name: "should not publish unmeasured savings percentages", pattern: /\d{2,3}-\d{2,3}%/, shouldNotExist: true },
]);

checkFile("docs/README.md", [
  { name: "should not expose machine-local vault commands", pattern: /~\/docs\/scripts/, shouldNotExist: true },
  { name: "should link to the canonical Quick Start", pattern: /README\.md#quick-start/, shouldNotExist: false },
  { name: "should not execute an installer from mutable main", pattern: "raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install", shouldNotExist: true },
  { name: "should document 45 memory-adapter tests", pattern: /Memory adapter: 45 tests/, shouldNotExist: false },
]);

checkFile("docs/guides/quick-start.md", [
  { name: "should link to the canonical Quick Start", pattern: /README\.md#quick-start/, shouldNotExist: false },
  { name: "should not execute an installer from mutable main", pattern: "raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install", shouldNotExist: true },
  { name: "should not document unsupported installer profiles", pattern: /install\.sh --profile|opencode --profile/, shouldNotExist: true },
  { name: "should not claim MCP write tools", pattern: /`save_(?:decision|bug_fix|architecture)`/, shouldNotExist: true },
]);

checkFile("assets/hero.svg", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
  { name: "should expose accessible image metadata", pattern: /role="img"[\s\S]*aria-labelledby="title desc"[\s\S]*<title id="title">[\s\S]*<desc id="desc">/, shouldNotExist: false },
]);
checkPassiveSvg("assets/hero.svg");

checkFile("assets/toolkit.svg", [
  { name: "should describe the local toolkit", pattern: /OpenCode local toolkit/, shouldNotExist: false },
  { name: "should expose accessible image metadata", pattern: /role="img"[\s\S]*aria-labelledby="title desc"[\s\S]*<title id="title">[\s\S]*<desc id="desc">/, shouldNotExist: false },
]);
checkPassiveSvg("assets/toolkit.svg");

checkFile("config/mcp/package.json", [
  { name: "should declare SDK", pattern: /@modelcontextprotocol\/sdk/, shouldNotExist: false },
]);

checkFile(".github/workflows/test.yml", [
  { name: "should release only through explicit dispatch", pattern: /workflow_dispatch:[\s\S]*github\.event_name == 'workflow_dispatch'/, shouldNotExist: false },
  { name: "should reject an existing release tag for another commit", pattern: /git\/ref\/tags\/\$TAG[\s\S]*TAG_SHA[\s\S]*RELEASE_SHA/, shouldNotExist: false },
  { name: "should run the executable release tag contract", pattern: /npm run test:release/, shouldNotExist: false },
  { name: "should pin first-party actions to immutable SHAs", pattern: /uses:\s+actions\/(?:checkout|setup-node)@v\d/, shouldNotExist: true },
  { name: "should not request unsupported private-repository provenance", pattern: /npm publish[^\n]*--provenance/, shouldNotExist: true },
  { name: "should publish npm without lifecycle scripts", pattern: /npm publish --registry=https:\/\/registry\.npmjs\.org --access public --ignore-scripts/, shouldNotExist: false },
  { name: "should verify existing npm package gitHead", pattern: /PUBLISHED_GIT_HEAD[\s\S]*RELEASE_SHA/, shouldNotExist: false },
  { name: "should pin idempotent retries to a full release commit", pattern: /release_sha:[\s\S]*\^\[0-9a-f\]\{40\}\$/, shouldNotExist: false },
  { name: "should validate retries before candidate checkout", pattern: /preflight:[\s\S]*Existing tag does not point to[\s\S]*source_sha=\$SOURCE_SHA/, shouldNotExist: false },
  { name: "should require tag absence for new releases", pattern: /already exists; release_sha is required for a retry/, shouldNotExist: false },
  { name: "should require tag presence for retries", pattern: /does not exist; retry refused/, shouldNotExist: false },
  { name: "should reject a tag race instead of changing modes", pattern: /appeared after preflight; start an explicit retry/, shouldNotExist: false },
  { name: "should require successful main push CodeQL for the release commit", pattern: /workflows\/codeql\.yml\/runs[\s\S]*head_sha="\$SOURCE_SHA"[\s\S]*branch=main[\s\S]*event=push[\s\S]*status=success/, shouldNotExist: false },
  { name: "should create releases only from an existing verified tag", pattern: /gh release create[^\n]*--verify-tag/, shouldNotExist: false },
  { name: "should pin the Node release toolchain", pattern: /node-version: 22\.23\.2/, shouldNotExist: false },
  { name: "should fail closed on the npm release toolchain version", pattern: /test "\$\(npm --version\)" = "10\.9\.8"/, shouldNotExist: false },
]);

const workflowSource = readFileSync(join(repoRoot, ".github/workflows/test.yml"), "utf-8");
for (const message of checkWorkflowAnalysisSteps(workflowSource)) {
  console.error(`[FAIL] .github/workflows/test.yml: ${message}`);
  errors++;
}
checkPatternCount(".github/workflows/test.yml", "all checkouts should use the preflight commit", /ref: \$\{\{ needs\.preflight\.outputs\.source_sha \}\}/g, 4);
checkPatternCount(".github/workflows/test.yml", "all checkouts should discard credentials", /persist-credentials: false/g, 4);
checkPatternCount(".github/workflows/test.yml", "both packages should use the fixed npm registry", /npm publish --registry=https:\/\/registry\.npmjs\.org --access public --ignore-scripts/g, 2);
checkPatternCount(".github/workflows/test.yml", "both publications should verify gitHead", /publication could not be verified/g, 2);
checkPatternCount(".github/workflows/test.yml", "both publications should verify tarball integrity", /tarball does not match the release source/g, 2);
checkPatternCount(".github/workflows/test.yml", "both publications should recheck the tag afterward", /moved during publication/g, 2);

checkFile("tests/release-workflow.test.sh", [
  { name: "should test a new release without a tag", pattern: /run_case new-release success/, shouldNotExist: false },
  { name: "should reject a new release with an existing tag", pattern: /run_case new-release-existing-tag failure/, shouldNotExist: false },
  { name: "should reject a retry without a tag", pattern: /run_case retry-missing-tag failure/, shouldNotExist: false },
  { name: "should accept an exact retry", pattern: /run_case retry-matching-tag success/, shouldNotExist: false },
  { name: "should reject a conflicting retry", pattern: /run_case retry-conflicting-tag failure/, shouldNotExist: false },
]);

checkFile(".github/workflows/codeql.yml", [
  { name: "should pin CodeQL workflow actions to immutable SHAs", pattern: /uses:\s+(?:actions\/checkout|github\/codeql-action\/[^@]+)@v\d/, shouldNotExist: true },
]);

checkFile("config/plugins.disabled/sandbox.js", [
  { name: "should not use shell: true", pattern: /shell:\s*true/, shouldNotExist: true },
]);

checkFile("config/plugins/checkpoints.js", [
  { name: "should exclude .env", pattern: /\.env/, shouldNotExist: false },
]);

checkFile("tools/scripts/doctor.js", [
  { name: "should check router SDK", pattern: /@modelcontextprotocol\/sdk/, shouldNotExist: false },
  { name: "should inspect effective configuration", pattern: /inspectConfiguration/, shouldNotExist: false },
]);

checkFile("config/opencode.jsonc", [
  { name: "should not use unsupported private SDD config keys", pattern: /sdd_multi_model/, shouldNotExist: true },
]);

checkFile("tools/scripts/skills.js", [
  { name: "should expose explicit refresh", pattern: /--refresh/, shouldNotExist: false },
  { name: "should only index SKILL.md files", pattern: /SKILL\.md/, shouldNotExist: false },
]);

checkFile("install.sh", [
  { name: "should install v1.10.0 by default", pattern: /INSTALL_TAG=.*v1\.10\.0/, shouldNotExist: false },
]);

checkFile("install.ps1", [
  { name: "should install v1.10.0 by default", pattern: /InstallTag[\s\S]*v1\.10\.0/, shouldNotExist: false },
]);

if (errors === 0) {
  console.log("[OK] All documentation and contract checks passed");
  process.exit(0);
} else {
  console.error(`[FAIL] ${errors} check(s) failed`);
  process.exit(1);
}
