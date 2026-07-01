#!/bin/bash

################################################################################
# Git File Formatter
#
# Description:
#   Lists files tracked by git and outputs their contents formatted as code
#   blocks. Filters by file extension to include only relevant files.
#   Skips empty files and files with only whitespace.
#   Copies output to clipboard using xclip.
#
# Usage:
#   ./git2markdown.sh [OPTIONS]
#
# Options:
#   -a, --all              Include all files regardless of extension
#   -w, --whitelist EXTS   Custom extensions (pipe-separated, e.g., "js|ts|txt")
#   -h, --help             Display help message
#
# Examples:
#   ./git2markdown.sh                          # Default extensions (py|md|txt|yml|yaml|json|toml)
#   ./git2markdown.sh -a                       # All files
#   ./git2markdown.sh -w "js|ts|jsx|tsx"       # Custom extensions
#
################################################################################

# Default extension pattern
extensions='(py|md|txt|yml|yaml|json|toml)'
all=false
whitelist=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -a|--all)
      all=true
      shift
      ;;
    -w|--whitelist)
      whitelist="$2"
      shift 2
      ;;
    -h|--help)
      cat << 'EOF'
Usage: git2markdown.sh [OPTIONS]

Options:
  -a, --all              Include all files regardless of extension
  -w, --whitelist EXTS   Custom extensions (pipe-separated, e.g., "js|ts|txt")
  -h, --help             Display this help message

Examples:
  git2markdown.sh                          # Default extensions (py|md|txt|yml|yaml|json|toml)
  git2markdown.sh -a                       # All files
  git2markdown.sh -w "js|ts|jsx|tsx"       # Custom extensions
EOF
      exit 0
      ;;

    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# Build the grep pattern based on flags
if [ "$all" = true ]; then
  # Match all files (no extension filter)
  grep_pattern='.'
elif [ -n "$whitelist" ]; then
  # Use custom whitelist pattern
  grep_pattern="\\.(${whitelist})"'$'
else
  # Use default extensions
  grep_pattern="\\.${extensions}"'$'
fi

output=$(git ls-files | grep -E "$grep_pattern" | while read -r file; do
    if [ -s "$file" ] && [ -n "$(cat "$file" | tr -d ' \n\t')" ]; then
      echo "# $file"
      echo '```'
      cat "$file"
      echo '```'
      echo
    fi
  done)
echo "$output"
echo "$output" | xclip -selection clipboard
