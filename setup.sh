#!/usr/bin/env bash

# Check if script is being sourced (which causes issues)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "✅ Running setup script..."
else
    echo "❌ Error: Do not source this script with 'source setup.sh'"
    echo "   Run it directly with: ./setup.sh"
    return 1 2>/dev/null || exit 1
fi

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [ -d ".venv" ]; then
  rm -rf .venv
fi

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install PyQt6

echo "✅ Setup complete! Virtual environment is ready at .venv"
echo "To activate: source .venv/bin/activate"
