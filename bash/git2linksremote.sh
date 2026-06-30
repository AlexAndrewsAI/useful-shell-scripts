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

# Get the remote URL for 'origin'
REMOTE_URL=$(git remote get-url origin)

# Clean the URL to ensure it is a web link
# Remove '.git' from the end if it exists
REMOTE_URL="${REMOTE_URL%.git}"

# Convert SSH format to HTTPS format for GitHub
if [[ $REMOTE_URL == git@github.com:* ]]; then
    REMOTE_URL="${REMOTE_URL/git@github.com:/https:\/\/github.com\/}"
fi

# Get the current branch name
BRANCH=$(git branch --show-current)

# Check if we are actually in a git repo
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