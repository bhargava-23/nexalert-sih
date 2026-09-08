#!/bin/bash
# Run all linters for NexAlert

set -e

echo "=== Running Python formatters and linters ==="
echo "black --check ."
black --check .

echo "ruff check ."
ruff check .

echo ""
echo "=== Running TypeScript linters ==="
echo "npm run lint"
npm run lint

echo "npx tsc --noEmit"
npx tsc --noEmit

echo ""
echo "=== Running C/C++ formatter ==="
echo "clang-format --dry-run --Werror firmware/**/*.{c,h}"
find firmware -name '*.c' -o -name '*.h' | xargs clang-format --dry-run --Werror

echo ""
echo "=== All linters passed ==="
