import eslint from "@eslint/js";

export default [
  eslint.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: "module",
      globals: {
        console: "readonly",
        process: "readonly",
        Buffer: "readonly",
        __dirname: "readonly",
        __filename: "readonly",
        module: "readonly",
        require: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
        setInterval: "readonly",
        clearInterval: "readonly",
        URL: "readonly",
        fetch: "readonly",
        AbortController: "readonly",
        Response: "readonly",
        Request: "readonly",
      },
    },
    rules: {
      "no-unused-vars": ["warn", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
      "no-console": "off",
      "no-undef": "error",
      "prefer-const": "warn",
      "eqeqeq": ["warn", "always"],
      "no-control-regex": "off",
      "preserve-caught-error": "off",
    },
    ignores: [
      "node_modules/**",
      "packages/*/node_modules/**",
      "packages/memory-adapter/dist/**",
      "coverage/**",
      "docs/**",
      "assets/**",
    ],
  },
];
