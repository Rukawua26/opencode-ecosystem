#!/usr/bin/env node
import { parse } from "yaml";

const UBUNTU_CONDITION = "matrix.os == 'ubuntu-latest'";
const SHELLCHECK_COMMAND = "shellcheck --severity=warning install.sh tools/scripts/*.sh tests/*.sh";
const ACTIONLINT_VERSION = "1.7.12";
const ACTIONLINT_SCRIPT = [
  "set -euo pipefail",
  'WORK_DIR="$(mktemp -d)"',
  'curl -sSLo "$WORK_DIR/actionlint.tar.gz" "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz"',
  'curl -sSLo "$WORK_DIR/actionlint-checksums.txt" "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_checksums.txt"',
  'grep "actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz" "$WORK_DIR/actionlint-checksums.txt" | sed "s|actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz|actionlint.tar.gz|" | (cd "$WORK_DIR" && sha256sum -c -)',
  'tar -xzf "$WORK_DIR/actionlint.tar.gz" -C "$WORK_DIR" actionlint',
  '"$WORK_DIR/actionlint" -color',
].join("\n");

const EXPECTED_BRANCHES = ["main", "develop"];
const CHECKOUT_USES = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1";
const CHECKOUT_REF = "${{ needs.preflight.outputs.source_sha }}";
const EXPECTED_DISPATCH_INPUTS = {
  version: { required: true, type: "string" },
  release_sha: { required: false, type: "string" },
};

const PROTECTED_STEPS = new Map([
  ["Run workflow static analysis", { expectIf: UBUNTU_CONDITION, exactScript: ACTIONLINT_SCRIPT, exactEnv: { ACTIONLINT_VERSION } }],
  ["Run shell script analysis", { expectIf: UBUNTU_CONDITION, exactRun: SHELLCHECK_COMMAND }],
  ["Run documentation and contract checks", { expectIf: null, exactRun: "npm run check-docs" }],
  ["Run release tag contract test", { expectIf: UBUNTU_CONDITION, exactRun: "npm run test:release" }],
]);
const FORBIDDEN_STEP_KEYS = ["shell", "working-directory", "continue-on-error", "timeout-minutes"];

function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function canonicalize(run) {
  return String(run ?? "")
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((line) => line.trimEnd())
    .join("\n")
    .trim();
}

function checkRequiredStep(step, name, rules, errors) {
  if (!step) {
    errors.push(`step '${name}' is missing`);
    return;
  }
  for (const key of FORBIDDEN_STEP_KEYS) {
    if (key in step) errors.push(`step '${name}' must not declare '${key}'`);
  }
  if ("env" in step) {
    if (rules.exactEnv === undefined) {
      errors.push(`step '${name}' must not declare env`);
    } else {
      const expectedKeys = Object.keys(rules.exactEnv).sort();
      const actualKeys = isPlainObject(step.env) ? Object.keys(step.env).sort() : [];
      if (JSON.stringify(actualKeys) !== JSON.stringify(expectedKeys)) {
        errors.push(`step '${name}' env must be exactly: ${expectedKeys.join(", ")}`);
      } else {
        for (const [key, value] of Object.entries(rules.exactEnv)) {
          if (String(step.env[key] ?? "") !== value) {
            errors.push(`step '${name}' env.${key} must equal ${value}`);
          }
        }
      }
    }
  } else if (rules.exactEnv !== undefined) {
    errors.push(`step '${name}' must declare env: ${Object.keys(rules.exactEnv).join(", ")}`);
  }
  if (rules.expectIf === null) {
    if ("if" in step) errors.push(`step '${name}' must not be conditional`);
  } else if (String(step.if ?? "").trim() !== rules.expectIf) {
    errors.push(`step '${name}' must be gated with ${rules.expectIf}`);
  }
  const run = canonicalize(step.run);
  if (rules.exactRun !== undefined && run !== rules.exactRun) {
    errors.push(`step '${name}' must run exactly: ${rules.exactRun}`);
  }
  if (rules.exactScript !== undefined && run !== rules.exactScript) {
    errors.push(`step '${name}' must execute the canonical verified script unchanged`);
  }
}

function checkTriggerShape(on, errors) {
  if (!isPlainObject(on)) {
    errors.push("workflow must declare triggers");
    return;
  }
  for (const key of Object.keys(on)) {
    if (!["push", "pull_request", "workflow_dispatch"].includes(String(key))) {
      errors.push(`unexpected trigger '${key}'`);
    }
  }
  for (const trigger of ["push", "pull_request"]) {
    const config = on[trigger];
    if (!isPlainObject(config)) {
      errors.push(`trigger '${trigger}' must use the branches form`);
      continue;
    }
    const keys = Object.keys(config).map(String);
    if (keys.some((key) => key !== "branches")) {
      errors.push(`trigger '${trigger}' must not use filters other than branches (paths/paths-ignore narrow analysis coverage)`);
    }
    const branches = Array.isArray(config.branches) ? config.branches.map(String).sort() : [];
    if (JSON.stringify(branches) !== JSON.stringify([...EXPECTED_BRANCHES].sort())) {
      errors.push(`trigger '${trigger}' branches must be exactly ${EXPECTED_BRANCHES.join(" and ")}`);
    }
  }
  const dispatch = on.workflow_dispatch;
  if (!isPlainObject(dispatch) || !isPlainObject(dispatch.inputs)) {
    errors.push("workflow_dispatch must declare inputs");
  } else {
    const actualInputs = Object.keys(dispatch.inputs).map(String).sort();
    const expectedInputs = Object.keys(EXPECTED_DISPATCH_INPUTS).sort();
    if (JSON.stringify(actualInputs) !== JSON.stringify(expectedInputs)) {
      errors.push(`workflow_dispatch inputs must be exactly: ${expectedInputs.join(", ")}`);
    }
    const allowedKeys = ["description", "required", "type"];
    for (const [input, shape] of Object.entries(EXPECTED_DISPATCH_INPUTS)) {
      const actual = dispatch.inputs?.[input];
      if (!isPlainObject(actual)) {
        errors.push(`workflow_dispatch input '${input}' must be an object definition`);
        continue;
      }
      for (const key of Object.keys(actual)) {
        if (!allowedKeys.includes(String(key))) {
          errors.push(`workflow_dispatch input '${input}' must not declare '${key}'`);
        }
      }
      if (Boolean(actual.required) !== shape.required) {
        errors.push(`workflow_dispatch input '${input}' required must be ${shape.required}`);
      }
      if (String(actual.type ?? "") !== shape.type) {
        errors.push(`workflow_dispatch input '${input}' type must be ${shape.type}`);
      }
    }
  }
}

export function checkWorkflowAnalysisSteps(source) {
  let doc;
  try {
    doc = parse(source);
  } catch (err) {
    return [`workflow YAML does not parse: ${err.message}`];
  }
  const errors = [];
  if (!isPlainObject(doc)) return ["workflow document is not an object"];
  if ("if" in doc) errors.push("workflow must not declare a top-level if");
  if ("defaults" in doc) errors.push("workflow must not declare defaults");
  if ("env" in doc) errors.push("workflow must not declare top-level env");
  checkTriggerShape(doc.on, errors);

  const job = doc.jobs?.test;
  if (!isPlainObject(job)) return errors.concat(["job 'test' is missing"]);
  for (const key of ["if", "defaults", "env", "continue-on-error", "timeout-minutes", "container"]) {
    if (key in job) errors.push(`job 'test' must not declare '${key}'`);
  }
  if (String(job["runs-on"] ?? "") !== "${{ matrix.os }}") {
    errors.push("job 'test' must run on the matrix os");
  }

  const matrix = job.strategy?.matrix;
  const osList = Array.isArray(matrix?.os) ? matrix.os.map(String) : [];
  if (JSON.stringify(osList.slice().sort()) !== JSON.stringify(["macos-latest", "ubuntu-latest"])) {
    errors.push("matrix.os must be exactly [ubuntu-latest, macos-latest]");
  }
  const nodeList = Array.isArray(matrix?.["node-version"]) ? matrix["node-version"].map(String) : [];
  if (JSON.stringify(nodeList) !== JSON.stringify(["22"])) {
    errors.push("matrix.node-version must be exactly [22]");
  }
  if (isPlainObject(matrix) && Object.keys(matrix).some((key) => !["os", "node-version"].includes(key))) {
    errors.push("matrix must declare only os and node-version (exclude/include would bypass coverage)");
  }

  const steps = Array.isArray(job.steps) ? job.steps : [];
  for (const step of steps) {
    const name = String(step?.name ?? "unnamed");
    if (!isPlainObject(step)) continue;
    if ("continue-on-error" in step) {
      errors.push(`step '${name}' must not declare continue-on-error`);
    }
    if ("shell" in step) {
      errors.push(`step '${name}' must not declare shell`);
    }
    if ("if" in step && String(step.if ?? "").trim() !== UBUNTU_CONDITION) {
      errors.push(`step '${name}' may only be gated with ${UBUNTU_CONDITION}`);
    }
  }
  const byName = new Map();
  for (const step of steps) {
    if (!isPlainObject(step) || !step.name) continue;
    const name = String(step.name);
    if (PROTECTED_STEPS.has(name)) {
      if (byName.has(name)) errors.push(`step '${name}' must not appear more than once`);
      byName.set(name, step);
    }
  }

  // Trusted prefix: pinned checkout then analyzers; candidate code executes only afterwards.
  const expectedPrefix = [
    { pred: (s) => String(s.uses ?? "") === CHECKOUT_USES, label: CHECKOUT_USES },
    { name: "Run workflow static analysis" },
    { name: "Run shell script analysis" },
  ];
  expectedPrefix.forEach((expected, index) => {
    const step = steps[index];
    if (!isPlainObject(step)) {
      errors.push(`step #${index + 1} must be ${expected.name ?? expected.label}`);
      return;
    }
    if (expected.pred) {
      if (!expected.pred(step)) errors.push(`step #${index + 1} must be ${expected.label}`);
      if (String(step.with?.ref ?? "") !== CHECKOUT_REF) {
        errors.push("checkout step must use the preflight-approved source_sha");
      }
      if (step.with?.["persist-credentials"] !== false) {
        errors.push("checkout step must set persist-credentials: false");
      }
    } else if (String(step.name ?? "") !== expected.name) {
      errors.push(`step #${index + 1} must be '${expected.name}', found '${step.name ?? "unnamed"}'`);
    }
  });

  for (const [name, rules] of PROTECTED_STEPS) {
    checkRequiredStep(byName.get(name), name, rules, errors);
  }

  return errors;
}
