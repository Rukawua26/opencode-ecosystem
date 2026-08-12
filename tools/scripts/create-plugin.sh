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

if [[ ! "$PLUGIN_NAME" =~ ^[a-z][a-z0-9]*(-[a-z][a-z0-9]*)*$ ]]; then
  echo "Error: Plugin name must use lowercase kebab-case (for example, my-plugin)"
  exit 1
fi

case "$PLUGIN_NAME" in
  arguments|await|break|case|catch|class|const|continue|debugger|default|delete|do|else|enum|eval|export|extends|false|finally|for|function|if|implements|import|in|instanceof|interface|let|new|null|package|private|protected|public|return|static|super|switch|this|throw|true|try|typeof|var|void|while|with|yield)
    echo "Error: Plugin name must not be a reserved JavaScript word"
    exit 1
    ;;
esac

PLUGIN_FILE="$PLUGINS_DIR/$PLUGIN_NAME.js"

if [ -e "$PLUGIN_FILE" ] || [ -L "$PLUGIN_FILE" ]; then
  echo "Error: Plugin '$PLUGIN_NAME' already exists at $PLUGIN_FILE"
  exit 1
fi

echo "Creating plugin: $PLUGIN_NAME"

# Pass the name as data rather than interpolating it into JavaScript source.
CAMEL_NAME=$(node -e 'const s=process.argv[1]; process.stdout.write(s.replace(/-([a-z])/g, (_, c) => c.toUpperCase()))' "$PLUGIN_NAME" 2>/dev/null || echo "$PLUGIN_NAME" | tr '-' ' ' | awk '{for(i=1;i<=NF;i++) if(i==1) printf tolower($i); else printf toupper(substr($i,1,1)) tolower(substr($i,2))}')

cat > "$PLUGIN_FILE" << EOF
import { tool } from "@opencode-ai/plugin";

export const ${CAMEL_NAME} = async () => {
  return {
    tool: {
      ${CAMEL_NAME}Action: tool({
        description: "TODO - Describe what this tool does.",
        args: {
          input: tool.schema.string().describe("Input parameter"),
        },
        async execute(args, ctx) {
          // TODO - Implement the tool logic
          return \`Result for: \${args.input}\`;
        },
      }),
    },
  };
};
EOF

echo "Created: $PLUGIN_FILE"
echo ""
echo "Next steps:"
echo "  1. Edit $PLUGIN_FILE"
echo "  2. Add the plugin to opencode.jsonc"
echo "  3. Add the plugin to the relevant profile"
echo "  4. Run 'npm test' to verify"
echo ""
