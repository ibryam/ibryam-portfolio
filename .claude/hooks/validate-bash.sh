#!/bin/bash
# PreToolUse hook — blocks dangerous bash commands before execution.
# Receives tool input as JSON on stdin. Exit 0 = allow, exit 2 = block.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    # Handle both {command: ...} and {tool_input: {command: ...}} shapes
    cmd = data.get('command') or data.get('tool_input', {}).get('command', '')
    print(cmd)
except Exception:
    print('')
" 2>/dev/null)

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Patterns that are unconditionally blocked
BLOCKED_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "rm -rf \$HOME"
  "rm -rf \*"
  "git push --force"
  "git push -f "
  "git push -f$"
  "DROP TABLE"
  "DROP DATABASE"
  "TRUNCATE TABLE"
  "dd if=/dev/zero"
  "dd if=/dev/random"
  "> /dev/sda"
  "mkfs\."
  "chmod -R 777 /"
  ":(){:|:&};:"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -Eqi "$pattern"; then
    echo "BLOCKED by validate-bash.sh: matched dangerous pattern '$pattern'"
    echo "Command: $COMMAND"
    exit 2
  fi
done

exit 0
