#!/bin/bash

################################################################################
# Git File List Generator
#
# Description:
#   Generates a Markdown list of all tracked files in a git repository
#   with clickable links to the files on GitHub. Automatically detects
#   the remote URL and current branch.
#
# Usage:
#   ./git2linksremote.sh
#
# Output:
#   Markdown formatted list of files with GitHub links
#
################################################################################

# Check if we are inside a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a git repository."
    exit 1
fi

# Get the remote URL for 'origin'
REMOTE_URL=$(git remote get-url origin 2>/dev/null) || {
    echo "Error: Git remote 'origin' not found."
    exit 1
}

# Clean the URL to ensure it is a web link
# Remove '.git' from the end if it exists
REMOTE_URL="${REMOTE_URL%.git}"

# Convert SSH format to HTTPS format for GitHub
if [[ $REMOTE_URL == git@github.com:* ]]; then
    REMOTE_URL="${REMOTE_URL/git@github.com:/https:\/\/github.com\/}"
fi

# Get the current branch name
BRANCH=$(git branch --show-current)

# Double-check branch is available
if [ -z "$BRANCH" ]; then
    echo "Error: Not a git repository or no branch detected."
    exit 1
fi

echo "## File List ($BRANCH branch)"
echo ""

# List all tracked files and format them as Markdown links
git ls-files | while read -r FILE_PATH; do
    # GitHub file URLs follow the pattern:
    # [Base URL]/blob/[Branch]/[File Path]
    echo "* [$FILE_PATH]($REMOTE_URL/blob/$BRANCH/$FILE_PATH)"
done
