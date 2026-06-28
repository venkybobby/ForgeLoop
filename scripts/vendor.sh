#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# vendor.sh — refresh the Forge + Loopy code in forge/ and loopy/ from upstream.
#
# Unlike the original scaffold, forge/ and loopy/ are now COMMITTED in-tree so
# ForgeLoop is self-contained and runnable anywhere. This script is an optional
# convenience for pulling newer upstream code on top of what is committed; review
# the resulting diff and commit it deliberately.
#
# Usage:
#   ./scripts/vendor.sh            # refresh both forge and loopy
#   ./scripts/vendor.sh forge      # refresh only forge
#   ./scripts/vendor.sh loopy      # refresh only loopy
#
# Pin a version with FORGE_REF / LOOPY_REF (branch or SHA).
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

FORGE_REPO="${FORGE_REPO:-https://github.com/venkybobby/Browser-BC.git}"
LOOPY_REPO="${LOOPY_REPO:-https://github.com/venkybobby/loopy.git}"
FORGE_REF="${FORGE_REF:-HEAD}"
LOOPY_REF="${LOOPY_REF:-HEAD}"

# Prefer rsync; fall back to a cp-based sync when rsync is unavailable.
sync_tree() {
  local src="$1" dest="$2"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete --exclude '.git' "$src"/ "$dest"/
  else
    rm -rf "${dest:?}"/* "${dest:?}"/.[!.]* 2>/dev/null || true
    ( cd "$src" && cp -a ./. "$dest"/ )
    rm -rf "$dest/.git"
  fi
}

vendor() {
  local name="$1" repo="$2" ref="$3" dest="$4"
  echo "==> Refreshing ${name} from ${repo} (${ref}) into ${dest}/"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  if ! git clone --depth 1 --branch "$ref" "$repo" "$tmp" 2>/dev/null; then
    # branch flag fails for a raw HEAD/sha; fall back to a full clone.
    if ! git clone "$repo" "$tmp"; then
      echo "!! Failed to clone ${repo}." >&2
      echo "   forge/ and loopy/ are already committed in-tree, so this is only" >&2
      echo "   needed to pull NEWER upstream code. Retry from a host with access." >&2
      return 1
    fi
    if [ "$ref" != "HEAD" ]; then ( cd "$tmp" && git checkout "$ref" ); fi
  fi

  sync_tree "$tmp" "$dest"
  echo "    done. Review 'git diff ${dest}/' and commit deliberately."
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

echo "==> Refresh complete. Next: ./scripts/setup-forge.sh && ./scripts/setup-loopy.sh"
