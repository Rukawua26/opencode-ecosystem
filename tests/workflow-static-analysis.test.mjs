import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { parse, stringify } from "yaml";
import { checkWorkflowAnalysisSteps } from "../tools/scripts/check-workflow.js";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const source = readFileSync(join(repoRoot, ".github/workflows/test.yml"), "utf8");

function mutate(mutator) {
  const doc = parse(source);
  mutator(doc);
  return stringify(doc);
}

function testJob(doc) {
  return doc.jobs.test;
}

function stepByName(doc, name) {
  return testJob(doc).steps.find((step) => step && step.name === name);
}

function expectErrors(mutatedSource, match) {
  const errors = checkWorkflowAnalysisSteps(mutatedSource);
  assert.ok(errors.length > 0, "mutated workflow must be rejected");
  if (match) {
    assert.ok(
      errors.some((message) => message.includes(match)),
      `expected an error mentioning "${match}", got: ${JSON.stringify(errors)}`,
    );
  }
}

test("current workflow passes structural static-analysis checks", () => {
  assert.deepEqual(checkWorkflowAnalysisSteps(source), []);
});

test("immutable triggers are required", () => {
  expectErrors(mutate((doc) => { delete doc.on.workflow_dispatch; }), "workflow_dispatch must declare inputs");
  expectErrors(mutate((doc) => { doc.on.push.branches = ["develop"]; }), "must be exactly main and develop");
  expectErrors(mutate((doc) => { delete doc.on.pull_request; }), "pull_request");
  expectErrors(mutate((doc) => { doc.on.push["paths-ignore"] = ["**"]; }), "must not use filters");
  expectErrors(mutate((doc) => { doc.on.schedule = [{ cron: "0 0 * * *" }]; }), "unexpected trigger");
});

test("job-level fail-open controls are rejected", () => {
  expectErrors(mutate((doc) => { testJob(doc).if = "${{ false }}"; }), "must not declare 'if'");
  expectErrors(mutate((doc) => { testJob(doc)["continue-on-error"] = true; }), "continue-on-error");
  expectErrors(mutate((doc) => { testJob(doc).defaults = { run: { shell: "bash {0} || true" } }; }), "must not declare 'defaults'");
  expectErrors(mutate((doc) => { testJob(doc).env = { BASH_ENV: "evil.sh" }; }), "must not declare 'env'");
});

test("workflow-level fail-open controls are rejected", () => {
  expectErrors(mutate((doc) => { doc.defaults = { run: { shell: "bash {0} || true" } }; }), "must not declare defaults");
  expectErrors(mutate((doc) => { doc.env = { BASH_ENV: "evil.sh" }; }), "must not declare top-level env");
});

test("matrix mutations are rejected", () => {
  expectErrors(mutate((doc) => { testJob(doc).strategy.matrix.os = ["macos-latest"]; }), "exactly");
  expectErrors(mutate((doc) => { testJob(doc).strategy.matrix.os = ["ubuntu-latest"]; }), "exactly");
  expectErrors(mutate((doc) => { testJob(doc).strategy.matrix["node-version"] = [20]; }), "node-version must be exactly");
  expectErrors(mutate((doc) => {
    testJob(doc).strategy.matrix.exclude = [{ os: "ubuntu-latest", "node-version": 22 }];
  }), "exclude/include");
  expectErrors(mutate((doc) => {
    testJob(doc).strategy.matrix.exclude = '${{ fromJSON(\'[{"os":"ubuntu-latest"}]\') }}';
  }), "exclude/include");
});

test("container execution is forbidden on the analysis job", () => {
  expectErrors(mutate((doc) => {
    testJob(doc).container = "attacker/image:latest";
  }), "must not declare 'container'");
});

test("continue-on-error is forbidden on every step, not only protected ones", () => {
  expectErrors(mutate((doc) => {
    stepByName(doc, "Run memory-adapter tests (node:test)")["continue-on-error"] = true;
  }), "continue-on-error");
});

test("fail-open controls are forbidden on every step", () => {
  expectErrors(mutate((doc) => {
    stepByName(doc, "Run memory-adapter tests (node:test)").if = "${{ false }}";
  }), "may only be gated with matrix.os == 'ubuntu-latest'");
  expectErrors(mutate((doc) => {
    stepByName(doc, "Run memory-adapter tests (node:test)").shell = "bash {0} || true";
  }), "'Run memory-adapter tests (node:test)' must not declare shell");
});

test("step-level continue-on-error is rejected in any value or key order", () => {
  for (const value of [true, "${{ true }}", false]) {
    expectErrors(mutate((doc) => {
      stepByName(doc, "Run workflow static analysis")["continue-on-error"] = value;
    }), "continue-on-error");
    expectErrors(mutate((doc) => {
      stepByName(doc, "Run shell script analysis")["continue-on-error"] = value;
    }), "continue-on-error");
  }
});

test("protected steps cannot override shell or working directory", () => {
  expectErrors(mutate((doc) => {
    stepByName(doc, "Run workflow static analysis").shell = "bash {0} || true";
  }), "'shell'");
  expectErrors(mutate((doc) => {
    stepByName(doc, "Run workflow static analysis")["working-directory"] = "packages/skills";
  }), "'working-directory'");
});

test("missing ubuntu-only gate is rejected", () => {
  expectErrors(mutate((doc) => {
    delete stepByName(doc, "Run workflow static analysis").if;
  }), "matrix.os == 'ubuntu-latest'");
});

test("weakened shellcheck command is rejected", () => {
  expectErrors(mutate((doc) => {
    stepByName(doc, "Run shell script analysis").run += " || true";
  }), "shellcheck --severity=warning");
});

test("actionlint version must stay pinned", () => {
  expectErrors(mutate((doc) => {
    stepByName(doc, "Run workflow static analysis").env.ACTIONLINT_VERSION = "1.7.99";
  }), "ACTIONLINT_VERSION");
});

test("any mutation of the canonical actionlint script is rejected", () => {
  const cases = {
    "||true on checksum": (run) => run.replace('(cd "$WORK_DIR" && sha256sum -c -)', '(cd "$WORK_DIR" && sha256sum -c -) || true'),
    "set+e": (run) => run.replace("set -euo pipefail", "set +e"),
    "early exit": (run) => run.replace("set -euo pipefail", "exit 0\nset -euo pipefail"),
    "hardcoded version": (run) => run.replaceAll("${ACTIONLINT_VERSION}", "1.7.12"),
    "no checksum": (run) => run.split("\n").filter((line) => !line.includes("sha256sum -c -")).join("\n"),
    "no execution": (run) => run.split("\n").filter((line) => !line.includes('"$WORK_DIR/actionlint" -color')).join("\n"),
    "override env prefix": (run) => run.replace("set -euo pipefail", "ACTIONLINT_VERSION=1.7.99\nset -euo pipefail"),
    "reordered verification": (run) => {
      const lines = run.split("\n");
      const extraction = lines.pop();
      const execution = lines.pop();
      const checksum = lines.pop();
      return [...lines, extraction, execution, checksum].join("\n");
    },
    "fixed /tmp path": (run) => run.replaceAll("$WORK_DIR", "/tmp"),
  };
  for (const mutator of Object.values(cases)) {
    expectErrors(mutate((doc) => {
      const step = stepByName(doc, "Run workflow static analysis");
      step.run = mutator(step.run);
    }), "canonical");
  }
});

test("invoker steps must run unconditionally and unchanged", () => {
  expectErrors(mutate((doc) => {
    stepByName(doc, "Run documentation and contract checks")["continue-on-error"] = true;
  }), "continue-on-error");
  expectErrors(mutate((doc) => {
    stepByName(doc, "Run documentation and contract checks").if = "matrix.os == 'ubuntu-latest'";
  }), "must not be conditional");
  expectErrors(mutate((doc) => {
    stepByName(doc, "Run release tag contract test").run = "npm test";
  }), "npm run test:release");
  expectErrors(mutate((doc) => {
    delete stepByName(doc, "Run release tag contract test").if;
  }), "matrix.os == 'ubuntu-latest'");
});

test("analysis steps must form the trusted prefix after checkout", () => {
  expectErrors(mutate((doc) => {
    const steps = testJob(doc).steps;
    const analysis = steps.splice(steps.findIndex((s) => s.name === "Run workflow static analysis"), 1)[0];
    steps.push(analysis);
  }), "step #2 must be");
  expectErrors(mutate((doc) => {
    testJob(doc).steps.splice(1, 0, { name: "Early code", run: "bash install.sh --help" });
  }), "step #2 must be");
});

test("checkout must be pinned to the approved immutable SHA", () => {
  expectErrors(mutate((doc) => {
    testJob(doc).steps[0].uses = "actions/checkout@main";
  }), "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1");
  expectErrors(mutate((doc) => {
    testJob(doc).steps[0].with.ref = "main";
  }), "preflight-approved source_sha");
  expectErrors(mutate((doc) => {
    delete testJob(doc).steps[0].with["persist-credentials"];
  }), "persist-credentials");
});

test("required actionlint env cannot be removed", () => {
  expectErrors(mutate((doc) => {
    delete stepByName(doc, "Run workflow static analysis").env;
  }), "must declare env");
});

test("job must run on the matrix os", () => {
  expectErrors(mutate((doc) => {
    testJob(doc)["runs-on"] = "self-hosted";
  }), "must run on the matrix os");
});

test("workflow_dispatch inputs are exact", () => {
  expectErrors(mutate((doc) => {
    doc.on.workflow_dispatch.inputs.extra = { type: "string" };
  }), "inputs must be exactly");
  expectErrors(mutate((doc) => {
    doc.on.workflow_dispatch.inputs.release_sha.required = true;
  }), "release_sha");
  expectErrors(mutate((doc) => {
    doc.on.workflow_dispatch.inputs.version.required = false;
  }), "version");
});

test("malformed or behavior-changing dispatch inputs are rejected", () => {
  expectErrors(mutate((doc) => {
    doc.on.workflow_dispatch.inputs.version = "string";
  }), "must be an object definition");
  expectErrors(mutate((doc) => {
    doc.on.workflow_dispatch.inputs.release_sha = null;
  }), "must be an object definition");
  expectErrors(mutate((doc) => {
    doc.on.workflow_dispatch.inputs.release_sha.default = "aa119ef0db12fa168cabe468ad7c5c1fab86eeba";
  }), "must not declare 'default'");
});

test("protected steps may not carry unexpected environment", () => {
  expectErrors(mutate((doc) => {
    stepByName(doc, "Run shell script analysis").env = { PATH: "./fake-bin" };
  }), "must not declare env");
  expectErrors(mutate((doc) => {
    stepByName(doc, "Run workflow static analysis").env.EXTRA = "whatever";
  }), "env must be exactly");
});

test("duplicate protected step names are rejected", () => {
  expectErrors(mutate((doc) => {
    testJob(doc).steps.unshift({ name: "Run shell script analysis", if: "always()", run: "true" });
  }), "must not appear more than once");
});

test("missing steps are rejected", () => {
  expectErrors(mutate((doc) => {
    testJob(doc).steps = testJob(doc).steps.filter((step) => step.name !== "Run shell script analysis");
  }), "Run shell script analysis");
});
