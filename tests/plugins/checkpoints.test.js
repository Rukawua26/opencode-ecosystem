import { describe, it, expect } from "vitest";
import { SKIP_PATTERNS, isSkippable } from "../../config/plugins/checkpoints-helpers.js";

describe("Checkpoints skip patterns", () => {
  it("excludes .env files", () => {
    expect(isSkippable("/home/user/.config/opencode/.env")).toBe(true);
    expect(isSkippable("/home/user/.config/opencode/.env.local")).toBe(true);
    expect(isSkippable("/home/user/.config/opencode/.env.production")).toBe(true);
  });

  it("excludes private keys", () => {
    expect(isSkippable("/home/user/.ssh/id_rsa")).toBe(true);
    expect(isSkippable("/home/user/.ssh/id_ed25519")).toBe(true);
    expect(isSkippable("/home/user/.ssh/id_ecdsa")).toBe(true);
    expect(isSkippable("/home/user/.ssh/id_dsa")).toBe(true);
  });

  it("excludes certificate files", () => {
    expect(isSkippable("/home/user/certs/server.pem")).toBe(true);
    expect(isSkippable("/home/user/certs/private.key")).toBe(true);
    expect(isSkippable("/home/user/certs/cert.pfx")).toBe(true);
    expect(isSkippable("/home/user/certs/cert.p12")).toBe(true);
  });

  it("excludes credential files", () => {
    expect(isSkippable("/home/user/credentials.json")).toBe(true);
    expect(isSkippable("/home/user/service-account-key.json")).toBe(true);
  });

  it("excludes node_modules and git", () => {
    expect(isSkippable("/home/user/node_modules/foo")).toBe(true);
    expect(isSkippable("/home/user/.git/config")).toBe(true);
  });

  it("does NOT exclude normal source files", () => {
    expect(isSkippable("/home/user/config/opencode.jsonc")).toBe(false);
    expect(isSkippable("/home/user/config/plugins/sandbox.js")).toBe(false);
    expect(isSkippable("/home/user/docs/README.md")).toBe(false);
  });

  it("excludes plugins-data directory", () => {
    expect(isSkippable("/home/user/.local/share/opencode/plugins-data/checkpoints")).toBe(true);
  });
});

describe("Skip patterns coverage", () => {
  it("does not duplicate patterns", () => {
    expect(new Set(SKIP_PATTERNS.map(String)).size).toBe(SKIP_PATTERNS.length);
  });
});
