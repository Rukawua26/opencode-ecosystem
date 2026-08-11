import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    include: [
      "tests/**/*.test.js",
    ],
    exclude: [
      "packages/**",
      "**/node_modules/**",
    ],
    coverage: {
      reporter: ["text", "json-summary"],
    },
  },
});
