#!/bin/bash

################################################################################
# Git Copy Bare
#
# Description:
#   Copies all files tracked by git in the input repository to an output
#   directory, preserving directory structure. Uses `git ls-tree -r --name-only
#   HEAD` to enumerate tracked files.
#
# Usage:
#   ./git-copy-bare.sh [OPTIONS] <output>
#
# Options:
#   -i, --input DIR    Git repository directory (default: current directory)
#   -h, --help         Display this help message
#
# Examples:
#   ./git-copy-bare.sh /tmp/export
#   ./git-copy-bare.sh -i /path/to/repo /tmp/export
#
################################################################################

set -euo pipefail

input_dir="."

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -i|--input)
      input_dir="$2"
      shift 2
      ;;
    -h|--help)
      cat << 'EOF'
Usage: git-copy-bare.sh [OPTIONS] <output>

Copy all files tracked by git from the input repository to an output directory.

Options:
  -i, --input DIR    Git repository directory (default: current directory)
  -h, --help         Display this help message

Arguments:
  output             Destination directory for copied files

Examples:
  ./git-copy-bare.sh /tmp/export
  ./git-copy-bare.sh -i /path/to/repo /tmp/export
EOF
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
    *)
      output_dir="$1"
      shift
      ;;
  esac
done

# Validate: output directory is required
if [ -z "${output_dir:-}" ]; then
  echo "Error: output directory is required" >&2
  echo "Usage: $0 [OPTIONS] <output>" >&2
  exit 1
fi

# Resolve the input directory to an absolute path
input_dir="$(cd "$input_dir" && pwd)"

# Create output directory if it doesn't exist
mkdir -p "$output_dir"

# Resolve output directory to an absolute path
output_dir="$(cd "$output_dir" && pwd)"

echo "Source: $input_dir"
echo "Destination: $output_dir"

# Enumerate tracked files and copy them
cd "$input_dir"
git ls-tree -r --name-only HEAD | while IFS= read -r file; do
  # Create the parent directory for this file in the output
  mkdir -p "$(dirname "$output_dir/$file")"
  # Copy the file, preserving symlinks as symlinks
  cp -a "$file" "$output_dir/$file"
  echo "  copied: $file"
done

echo "Done. Copied all tracked files to $output_dir"