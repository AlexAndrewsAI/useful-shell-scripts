#!/bin/bash
set -euo pipefail

# ─── git-lite-mirror.sh — Sync main → mirror branch using .gitignore.lite ───
#
# Produces independent linear commits on the mirror branch.
# No merge commits, no parent links to main's history.
#
# Uses a hotswap technique: .gitignore.lite (at the root of main) is
# temporarily combined with (or replaces) .gitignore so that git operations
# naturally respect the lite-mirror exclusion rules.
#
# Usage:
#   ./git-lite-mirror.sh -m my-mirror -r origin
#
# Options:
#   -m, --mirror-branch   Name of the mirror branch           (default: lite-mirror)
#   -r, --remote          Remote to push to                   (default: origin)
#   -i, --inherit-gitignore  Append main's .gitignore to the  (default: enabled)
#                            hotswap .gitignore so the lite
#                            mirror inherits the original repo
#                            ignore rules
#   --no-inherit-gitignore   Disable inheritance from main's
#                            .gitignore (only .gitignore.lite
#                            patterns are used)
#   -l, --local-only        Only create the local mirror branch;  (default: disabled)
#                            skip the push-to-remote suggestion
#   -h, --help            Show this help message
#
# The .gitignore.lite file must exist at the root of the main branch.
# Patterns follow standard .gitignore syntax.
# ─────────────────────────────────────────────────────────────────────────────

# ─── Defaults ────────────────────────────────────────────────────────────────
MIRROR_BRANCH="lite-mirror"
REMOTE="origin"
INHERIT_GITIGNORE=true
LOCAL_ONLY=false

# ─── Arg parsing ─────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--mirror-branch)
      echo "  [arg] mirror-branch = $2"
      MIRROR_BRANCH="$2"; shift 2 ;;
    -r|--remote)
      echo "  [arg] remote = $2"
      REMOTE="$2"; shift 2 ;;
    -i|--inherit-gitignore)
      INHERIT_GITIGNORE=true; shift ;;
    --no-inherit-gitignore)
      INHERIT_GITIGNORE=false; shift ;;
    -l|--local-only)
      LOCAL_ONLY=true; shift ;;
    -h|--help)
      cat <<'HELPBLOCK'
Usage: git-lite-mirror.sh [OPTIONS]

Options:
  -m, --mirror-branch   Mirror branch name  (default: lite-mirror)
  -r, --remote          Remote to push to   (default: origin)
  -i, --inherit-gitignore  Append main's .gitignore to the hotswap
  --no-inherit-gitignore   Only use .gitignore.lite patterns
  -l, --local-only         Skip push suggestion
  -h, --help               Show this help message
HELPBLOCK
      exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1 ;;
  esac
done

# ─── Setup ───────────────────────────────────────────────────────────────────
SYNC_REF="refs/mirror-sync/${MIRROR_BRANCH}"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "FATAL: not inside a git repository." >&2; exit 1
}

git rev-parse --verify --quiet main >/dev/null 2>&1 || {
  echo "FATAL: branch 'main' does not exist." >&2; exit 1
}

# Read sources from main branch
MAIN_HEAD=$(git rev-parse main)
EMPTY_TREE=$(git hash-object -t tree /dev/null)
LITE_CONTENT=$(git show main:.gitignore.lite 2>/dev/null || echo "")
MAIN_GITIGNORE=$(git show main:.gitignore 2>/dev/null || echo "")

# Save current branch
ORIG_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "[setup] Original branch: $ORIG_BRANCH"
echo "[setup] Main HEAD:       ${MAIN_HEAD:0:12}"

# Track whether we stashed changes (used by trap on exit)
STASHED=false
# Track git hooks state (used by trap to restore)
HOOKS_WAS_SET=false
ORIG_HOOKS_PATH=""

# ─── Trap: restore branch, hooks, stash on any exit ─────────────────────────
trap 'EXIT_CODE=$?; echo ""; echo "[trap] Recovering from step failure (exit code $EXIT_CODE)..."; echo "[trap] Restoring branch $ORIG_BRANCH (force)..."; git checkout --force "$ORIG_BRANCH" >/dev/null 2>&1 && echo "[trap] Restored to $ORIG_BRANCH" || echo "[trap] WARNING: could not restore $ORIG_BRANCH" >&2; echo "[trap] Cleaning leftover files..."; git clean -fd --quiet 2>/dev/null || true; if [ "${HOOKS_WAS_SET:-false}" = true ]; then echo "[trap] Restoring git hooks path..."; git config --local core.hooksPath "${ORIG_HOOKS_PATH:-}" 2>/dev/null || true; else echo "[trap] Removing hooks path override..."; git config --local --unset core.hooksPath 2>/dev/null || true; fi; if [ "${STASHED:-false}" = true ]; then echo "[trap] Popping stash..."; git stash pop 2>/dev/null && echo "[trap] Stash popped" || echo "[trap] WARNING: could not pop stash" >&2; fi; if [ "$EXIT_CODE" -ne 0 ]; then echo ""; echo "✖ Mirror sync FAILED at step with exit code $EXIT_CODE. See log above." >&2; fi; echo "[trap] Done."' EXIT

# Stash any uncommitted changes before we start
echo "[stash] Stashing any uncommitted changes..."
STASH_OUTPUT=$(git stash push -m "git-lite-mirror: pre-sync stash" 2>&1) || true
if echo "$STASH_OUTPUT" | grep -q "No local changes to save"; then
  STASHED=false
  echo "[stash] Working tree clean, no stash needed."
else
  STASHED=true
  echo "$STASH_OUTPUT"
  echo "[stash] Done."
fi

# ─── Determine sync range ────────────────────────────────────────────────────
LAST_SYNCED=$(git rev-parse --verify --quiet "$SYNC_REF" 2>/dev/null || echo "")

if [ -z "$LAST_SYNCED" ]; then
  echo "[sync] SYNC_REF not found. Starting from empty tree."
  LAST_SYNCED="$EMPTY_TREE"
else
  echo "[sync] Last synced: ${LAST_SYNCED:0:12}"
fi

if [ -z "$LITE_CONTENT" ]; then
  echo "[sync] WARNING: .gitignore.lite not found in main. Mirror will be an exact copy." >&2
fi


# ─── Disable git hooks for mirror operations ─────────────────────────────────
# prek/pre-commit may install post-checkout or other hooks that fire during
# checkout --orphan and other git operations. We disable all hooks here and
# restore them in the EXIT trap.
echo "[hooks] Saving git hooks configuration..."
if git config --local core.hooksPath >/dev/null 2>&1; then
  HOOKS_WAS_SET=true
  ORIG_HOOKS_PATH=$(git config --local core.hooksPath)
  echo "[hooks]   saved: hooksPath=$ORIG_HOOKS_PATH"
fi
echo "[hooks] Disabling hooks for mirror operations (core.hooksPath=/dev/null)..."
git config --local core.hooksPath /dev/null

# ─── Initialize mirror branch if needed ──────────────────────────────────────
MIRROR_EXISTS=true
if ! git rev-parse --verify --quiet "$MIRROR_BRANCH" >/dev/null 2>&1; then
  MIRROR_EXISTS=false
  echo "[mirror] Branch '$MIRROR_BRANCH' doesn't exist. Creating as orphan..."
  git checkout --orphan "$MIRROR_BRANCH"
  git rm -rf --quiet . 2>/dev/null || true
  git update-ref "$SYNC_REF" "$EMPTY_TREE"
  echo "[mirror] Orphan branch created."
else
  echo "[mirror] Branch '$MIRROR_BRANCH' exists."
fi

# ─── Build hotswap .gitignore content ────────────────────────────────────────
echo "[hotswap] Building combined .gitignore..."
HOTSWAP_CONTENT=""
if [ "$INHERIT_GITIGNORE" = true ] && [ -n "$MAIN_GITIGNORE" ]; then
  echo "[hotswap]   + inherited from main's .gitignore"
  HOTSWAP_CONTENT="${MAIN_GITIGNORE}
"
fi
if [ -n "$LITE_CONTENT" ]; then
  echo "[hotswap]   + patterns from .gitignore.lite"
  HOTSWAP_CONTENT="${HOTSWAP_CONTENT}${LITE_CONTENT}
"
fi

# ─── Perform the hotswap sync ────────────────────────────────────────────────
echo "[sync] Switching to mirror branch $MIRROR_BRANCH..."
if [ "$MIRROR_EXISTS" = true ]; then
  git checkout --force "$MIRROR_BRANCH"
fi

echo "[sync] Cleaning working tree..."
git rm -rf --quiet . 2>/dev/null || true

echo "[sync] Restoring files from main (working tree only, index stays empty)..."
git restore --source=main --worktree -- . 2>/dev/null || {
  echo "[sync]   (fallback: git checkout main -- .)"
  git checkout main -- .
  git reset HEAD -- . 2>/dev/null || true
}

echo "[sync] Hotswapping .gitignore..."
printf '%s' "$HOTSWAP_CONTENT" > .gitignore

echo "[sync] Staging files (lite exclusions will be respected)..."
git add -A

echo "[sync] Restoring .gitignore to main's version..."
if [ -n "$MAIN_GITIGNORE" ]; then
  printf '%s' "$MAIN_GITIGNORE" > .gitignore
else
  rm -f .gitignore
fi
git add .gitignore

echo "[sync] Cleaning up excluded clutter from working tree..."
git clean -fd --quiet 2>/dev/null || true

# ─── Commit ──────────────────────────────────────────────────────────────────
if git diff --cached --quiet; then
  echo "[sync] No changes after filtering. Updating sync ref only."
  git update-ref "$SYNC_REF" "$MAIN_HEAD"
  exit 0
fi

COMMIT_MSG="Sync from main ${MAIN_HEAD:0:12}

Lite-mirror sync from main branch, excluding patterns in .gitignore.lite"
if [ "$INHERIT_GITIGNORE" = true ]; then
  COMMIT_MSG="${COMMIT_MSG} (inherited from .gitignore)"
fi
COMMIT_MSG="${COMMIT_MSG}
Source: $MAIN_HEAD"

echo "[commit] Creating mirror commit (hooks disabled)..."
git commit --no-verify -m "$COMMIT_MSG"
COMMITTED=$(git rev-parse HEAD)
echo "[commit] Commit created: ${COMMITTED:0:12}"

# ─── Update tracking ref ─────────────────────────────────────────────────────
echo "[sync] Updating SYNC_REF..."
git update-ref "$SYNC_REF" "$MAIN_HEAD"

# ─── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "✓ Mirror branch '$MIRROR_BRANCH' updated:"
echo "  Last synced main: ${LAST_SYNCED:0:12}"
echo "  New main HEAD:     ${MAIN_HEAD:0:12}"
echo "  New mirror commit: ${COMMITTED:0:12}"
echo ""
if [ "$LOCAL_ONLY" = false ]; then
  echo "  Push with:"
  echo "    git push $REMOTE $MIRROR_BRANCH --force-with-lease"
fi
