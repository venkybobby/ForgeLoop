#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# setup-loopy.sh — prepare Loopy (loop library + skill) to run inside ForgeLoop.
# Idempotent. Detects Node / Python projects automatically.
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -z "$(find loopy -mindepth 1 -maxdepth 1 ! -name README.md 2>/dev/null)" ]; then
  echo "!! loopy/ is empty. Run ./scripts/vendor.sh first." >&2
  exit 1
fi

[ -f .env ] || { echo "==> Creating .env from .env.example"; cp .env.example .env; }

for sub in loopy loopy/loop-library loopy/skill; do
  [ -d "$sub" ] || continue
  if [ -f "$sub/package.json" ]; then
    echo "==> [node] installing in $sub"
    ( cd "$sub" && { command -v pnpm >/dev/null && pnpm install || npm install; } )
  fi
  if [ -f "$sub/requirements.txt" ]; then
    echo "==> [python] installing $sub/requirements.txt"
    ( cd "$sub" && python3 -m pip install -r requirements.txt )
  elif [ -f "$sub/pyproject.toml" ]; then
    echo "==> [python] installing $sub (pyproject)"
    ( cd "$sub" && python3 -m pip install -e . )
  fi
done

echo "==> Loopy setup complete. See docs/loopy-setup.md."
