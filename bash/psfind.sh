#!/bin/bash
set -euo pipefail
#
# DESCRIPTION:
#   Find or kill processes matching given search terms.
#
# USAGE:
#   $0 [OPTIONS] <search-term> [refine-pattern]
#
# OPTIONS:
#   -h, --help              Show this help message and exit
#   -k, --kill              Kill matching processes instead of displaying them
#   -w, --word-regexp       Match whole words only
#   -n, --not <pattern>     Exclude processes matching this pattern
#
# ARGUMENTS:
#   search-term             Required. Process name or pattern to search for
#   refine-pattern          Optional. Additional pattern to refine results (default: '.')
#
# EXAMPLES:
#   $0 firefox              Find all processes containing 'firefox'
#   $0 -k node . "app.js"   Kill all node processes matching 'app.js'
#   $0 -w -n grep python    Find processes with word 'python' but exclude 'grep'
#

# Set default USER if not set
: "${USER:=$(whoami)}"

if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <search-term>"
    exit 1
fi

KILL=false
GREPARGS=("--ignore-case" "--extended-regexp")
NOT=""


POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      head -n 24 "$0" | tail -n +2 | sed 's/^# //' | sed 's/^#//'
      exit 0
      ;;
    -k|--kill)
      KILL=true
      shift # past argument
      ;;
    -w|--word-regexp)
      GREPARGS+=("-w")
      shift
      ;;
    -n|--not)
      if [[ -z "${2:-}" ]]; then
        echo "Error: --not requires a pattern argument"
        exit 1
      fi
      NOT="$2"
      shift
      shift
      ;;
    *)
      if [[ "$1" == -* ]]; then
        echo "Unknown option $1"
        exit 1
      fi
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done
# Restore other arguments
set -- "${POSITIONAL_ARGS[@]}"

# Check if search term was provided
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <search-term>"
    exit 1
fi

SEARCH_TERM="$1"
REFINE="${2:-.}"

# Show what we're doing
action="Finding"
if [[ "$KILL" == true ]]; then
    action="Killing"
fi
echo "$action processes with terms $SEARCH_TERM $REFINE"


# Capture the output of `ps -fa` into an array
readarray -t processes < <(ps -U "$USER" a)

# Remove the last entry from the array if it exists
if [[ ${#processes[@]} -gt 0 ]]; then
    unset 'processes[${#processes[@]}-1]'
fi

# Count the number of lines in the array
line_count=${#processes[@]}

# Optionally, print all processes except the last one
if [[ $line_count -gt 0 ]]; then
    for ((i = 0; i < line_count - 1; i++)); do
        line=$(echo "${processes[i]}" |  grep "${GREPARGS[@]}" "$SEARCH_TERM" | grep "${GREPARGS[@]}" "$REFINE" || true)
        if [ -n "$line" ]; then
            # Skip line if $NOT is non-empty and present
            if [[ -n "$NOT" && "$line" == *"$NOT"* ]]; then
                continue  # Skip the rest of the loop iteration
            fi
            p=$(echo "$line" | awk '{print $1}')
            if [[ "$KILL" == true ]]; then
                echo "KILLING $p"
                kill -9 "$p" || true
            else
                echo "$line"
                echo "$p"
            fi
        fi
    done
fi
