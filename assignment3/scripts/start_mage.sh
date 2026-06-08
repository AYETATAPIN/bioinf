#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}/mage_project"

if [[ ! -f "${ROOT_DIR}/.venv/bin/activate" ]]; then
  echo "Mage virtual environment is missing."
  echo "Run first: bash scripts/install_tools_wsl.sh"
  exit 1
fi

. "${ROOT_DIR}/.venv/bin/activate"

if command -v mage >/dev/null 2>&1; then
  mage start .
elif python -c "import mage_ai.cli.main" >/dev/null 2>&1; then
  python -c "from mage_ai.cli.main import app; app()" start .
else
  echo "Mage is not installed in ${ROOT_DIR}/.venv."
  echo "Run:"
  echo "  cd ${ROOT_DIR}"
  echo "  . .venv/bin/activate"
  echo "  python -m pip install mage-ai rich"
  exit 1
fi
