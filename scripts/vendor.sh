#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# vendor.sh — pull the upstream Forge + Loopy code into forge/ and loopy/.
#
# These directories are gitignored (only their README.md is tracked), so the
# upstream code lives here locally but is never committed into ForgeLoop.
#
# Usage:
#   ./scripts/vendor.sh            # vendor both forge and loopy
#   ./scripts/vendor.sh forge      # vendor only forge
#   ./scripts/vendor.sh loopy      # vendor only loopy
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

FORGE_REPO="${FORGE_REPO:-https://github.com/venkybobby/Browser-BC.git}"
LOOPY_REPO="${LOOPY_REPO:-https://github.com/venkybobby/loopy.git}"
FORGE_REF="${FORGE_REF:-HEAD}"
LOOPY_REF="${LOOPY_REF:-HEAD}"

vendor() {
  local name="$1" repo="$2" ref="$3" dest="$4"
  echo "==> Vendoring ${name} from ${repo} (${ref}) into ${dest}/"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  if ! git clone --depth 1 --branch "$ref" "$repo" "$tmp" 2>/dev/null; then
    # branch flag fails for a raw HEAD/sha; fall back to full-ish clone.
    if ! git clone "$repo" "$tmp"; then
      echo "!! Failed to clone ${repo}." >&2
      echo "   If this environment's access is scoped to a single repo, clone" >&2
      echo "   ${name} from a machine with access and rsync it into ${dest}/." >&2
      echo "   See ${dest}/README.md for instructions." >&2
      return 1
    fi
    if [ "$ref" != "HEAD" ]; then ( cd "$tmp" && git checkout "$ref" ); fi
  fi

  # Sync everything except git metadata, preserving the tracked README.md.
  rsync -a --delete \
        --exclude '.git' \
        --exclude 'README.md' \
        "$tmp"/ "$dest"/
  echo "    done: $(find "$dest" -mindepth 1 -maxdepth 1 | wc -l | tr -d ' ') entries in ${dest}/"
}

target="${1:-all}"
case "$target" in
  forge) vendor forge "$FORGE_REPO" "$FORGE_REF" forge ;;
  loopy) vendor loopy "$LOOPY_REPO" "$LOOPY_REF" loopy ;;
  all)
    vendor forge "$FORGE_REPO" "$FORGE_REF" forge
    vendor loopy "$LOOPY_REPO" "$LOOPY_REF" loopy
    ;;
  *) echo "Usage: $0 [forge|loopy|all]" >&2; exit 2 ;;
esac

echo "==> Vendor complete. Next: cp .env.example .env && ./scripts/setup-forge.sh"
