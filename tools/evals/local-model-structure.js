#!/usr/bin/env node

import { askLocalModel, MODELS } from "../../config/mcp/local-model-router.js";

const cases = [
  { name: "code-json", role: "code" },
  { name: "chat-json", role: "chat" },
  { name: "reasoning-json", role: "reasoning" },
];

const prompt = [
  "Return only valid JSON without Markdown fences or explanation.",
  'The exact schema is: {"status":"ok","items":["alpha","beta"]}.',
  "Use exactly those keys and values.",
].join(" ");

function validate(response) {
  const parsed = JSON.parse(response);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return false;
  if (Object.keys(parsed).sort().join(",") !== "items,status") return false;
  if (parsed.status !== "ok") return false;
  return Array.isArray(parsed.items)
    && parsed.items.length === 2
    && parsed.items[0] === "alpha"
    && parsed.items[1] === "beta";
}

const results = [];
for (const testCase of cases) {
  const startedAt = Date.now();
  try {
    const answer = await askLocalModel(testCase.role, prompt);
    const valid = validate(answer.untrusted_response);
    results.push({
      ...testCase,
      model: answer.model,
      valid,
      duration_ms: Date.now() - startedAt,
      error: valid ? null : "response did not match the required JSON schema",
    });
  } catch (error) {
    results.push({
      ...testCase,
      model: MODELS[testCase.role],
      valid: false,
      duration_ms: Date.now() - startedAt,
      error: error instanceof Error ? error.message : String(error),
    });
  }
}

const byModel = {};
for (const result of results) {
  const model = result.model || `unavailable:${result.role}`;
  byModel[model] ||= { total: 0, valid: 0, failed: 0, success_rate: 0 };
  byModel[model].total += 1;
  byModel[model].valid += result.valid ? 1 : 0;
  byModel[model].failed += result.valid ? 0 : 1;
  byModel[model].success_rate = byModel[model].valid / byModel[model].total;
}

const valid = results.filter((result) => result.valid).length;
console.log(JSON.stringify({
  generated_at: new Date().toISOString(),
  scope: "local JSON structure only; not a semantic quality or cloud comparison",
  total: results.length,
  valid,
  failed: results.length - valid,
  success_rate: valid / results.length,
  by_model: byModel,
  cases: results,
}, null, 2));

process.exitCode = valid === results.length ? 0 : 1;
