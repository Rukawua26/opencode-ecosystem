import { describe, it, expect } from "vitest";
import { validateImage, buildDockerArgs } from "../../config/plugins/sandbox-helpers.js";

describe("Sandbox image validation", () => {
  it("accepts a valid image name", () => {
    expect(validateImage("alpine:latest")).toBe("alpine:latest");
    expect(validateImage("python:3.12-alpine")).toBe("python:3.12-alpine");
    expect(validateImage("node:22-alpine")).toBe("node:22-alpine");
  });

  it("returns default for empty or non-string", () => {
    expect(validateImage("")).toBe("alpine:latest");
    expect(validateImage(null)).toBe("alpine:latest");
    expect(validateImage(undefined)).toBe("alpine:latest");
  });

  it("rejects shell metacharacters", () => {
    expect(() => validateImage("alpine; rm -rf /")).toThrow("metacharacters");
    expect(() => validateImage("alpine && cat /etc/passwd")).toThrow("metacharacters");
    expect(() => validateImage("alpine|rce")).toThrow("metacharacters");
    expect(() => validateImage("alpine`whoami`")).toThrow("metacharacters");
    expect(() => validateImage("alpine$(id)")).toThrow("metacharacters");
  });

  it("rejects invalid image format", () => {
    expect(() => validateImage("ALPINE LATEST")).toThrow("invalid format");
    expect(() => validateImage("..")).toThrow("invalid format");
  });
});

describe("Docker args construction", () => {
  it("passes image as a separate argument, not interpolated", () => {
    const args = buildDockerArgs("echo hi", "python:3.12-alpine");
    const imageIndex = args.indexOf("python:3.12-alpine");
    expect(imageIndex).toBeGreaterThan(-1);
    expect(args[imageIndex]).toBe("python:3.12-alpine");
  });

  it("includes isolation flags", () => {
    const args = buildDockerArgs("ls", "alpine:latest");
    expect(args).toContain("--network");
    expect(args).toContain("none");
    expect(args).toContain("--read-only");
    expect(args).toContain("--memory");
    expect(args).toContain("512m");
    expect(args).toContain("--cpus");
    expect(args).toContain("1");
  });

  it("passes command as last arg to sh -c", () => {
    const args = buildDockerArgs("echo test", "alpine:latest");
    const shIndex = args.indexOf("sh");
    expect(args[shIndex + 1]).toBe("-c");
    expect(args[shIndex + 2]).toBe("echo test");
  });

  it("does not contain shell:true or string interpolation", () => {
    const args = buildDockerArgs("echo hi", "alpine:latest");
    const joined = args.join(" ");
    expect(joined).not.toMatch(/shell.*true/i);
    expect(args.every((a) => typeof a === "string")).toBe(true);
  });
});
