#!/bin/bash
# create-plugin.sh - Scaffold a new OpenCode plugin
# Usage: bash tools/scripts/create-plugin.sh <plugin-name>

set -euo pipefail

PLUGIN_NAME="${1:-}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PLUGINS_DIR="$REPO_ROOT/config/plugins"

if [ -z "$PLUGIN_NAME" ]; then
  echo "Usage: bash tools/scripts/create-plugin.sh <plugin-name>"
  echo "Example: bash tools/scripts/create-plugin.sh my-plugin"
  exit 1
fi

PLUGIN_FILE="$PLUGINS_DIR/$PLUGIN_NAME.js"

if [ -f "$PLUGIN_FILE" ]; then
  echo "Error: Plugin '$PLUGIN_NAME' already exists at $PLUGIN_FILE"
  exit 1
fi

echo "Creating plugin: $PLUGIN_NAME"

cat > "$PLUGIN_FILE" << 'EOF'
import { tool } from "@opencode-ai/plugin";

export const PLUGIN_NAMEPlugin = async () => {
  return {
    tool: {
      PLUGIN_NAME_action: tool({
        description: "TODO - Describe what this tool does.",
        args: {
          input: tool.schema.string().describe("Input parameter"),
        },
        async execute(args, ctx) {
          // TODO - Implement the tool logic
          return `Result for: ${args.input}`;
        },
      }),
    },
  };
};
EOF

sed -i "s/PLUGIN_NAME/$PLUGIN_NAME/g" "$PLUGIN_FILE"

echo "Created: $PLUGIN_FILE"
echo ""
echo "Next steps:"
echo "  1. Edit $PLUGIN_FILE"
echo "  2. Add the plugin to opencode.jsonc"
echo "  3. Add the plugin to the relevant profile"
echo "  4. Run 'npm test' to verify"
echo ""
