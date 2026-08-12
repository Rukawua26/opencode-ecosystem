import { describe, expect, it } from "vitest";
import guardrailsPlugin from "../../config/plugins/guardrails.js";

async function execute(hooks, input, output = { output: "valid output", metadata: {} }) {
  await hooks["tool.execute.before"](input, { args: {} });
  await hooks["tool.execute.after"](input, output);
  return output;
}

describe("Guardrails behavior", () => {
  it("emits one deterministic consecutive warning as metadata", async () => {
    const hooks = await guardrailsPlugin();
    const sessionID = "guardrail-consecutive";
    const outputs = [];
    for (let index = 1; index <= 6; index++) {
      const output = await execute(hooks, { sessionID, callID: `call-${index}`, tool: "read" });
      outputs.push(output);
      if (index < 5) expect(output.metadata.guardrail_warning).toBeUndefined();
    }
    expect(outputs[4].metadata.guardrail_triggered).toBe("consecutive_tools");
    expect(outputs[4].metadata.guardrail_warning).toContain("5 veces");
    expect(outputs[5].metadata.guardrail_warning).toBeUndefined();
  });

  it("emits total and empty-output warnings without mutating tool args", async () => {
    const hooks = await guardrailsPlugin();
    let totalOutput;
    for (let index = 1; index <= 20; index++) {
      totalOutput = await execute(hooks, {
        sessionID: "guardrail-total",
        callID: `total-${index}`,
        tool: `tool-${index}`,
      });
    }
    expect(totalOutput.metadata.guardrail_triggered).toBe("total_calls");

    let emptyOutput;
    for (let index = 1; index <= 3; index++) {
      emptyOutput = await execute(
        hooks,
        { sessionID: "guardrail-empty", callID: `empty-${index}`, tool: "read" },
        { output: "", metadata: {} },
      );
    }
    expect(emptyOutput.metadata.guardrail_triggered).toBe("empty_output");
  });

  it("resets state on compaction", async () => {
    const hooks = await guardrailsPlugin();
    for (let index = 1; index <= 4; index++) {
      await execute(hooks, { sessionID: "guardrail-reset", callID: `before-${index}`, tool: "read" });
    }
    await hooks.event({ event: { type: "session.compacted", properties: { sessionID: "guardrail-reset" } } });
    const output = await execute(hooks, { sessionID: "guardrail-reset", callID: "after", tool: "read" });
    expect(output.metadata.guardrail_warning).toBeUndefined();
  });
});
