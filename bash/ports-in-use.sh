#!/bin/bash
set -euo pipefail

################################################################################
# Port Usage Display
#
# Description:
#   Displays all currently used network ports on the system.
#   Uses the ss command to gather socket information and extracts port numbers.
#
# Usage:
#   ./ports-in-use.sh
#
# Output:
#   Space-separated list of port numbers currently in use
#
################################################################################

# Check if ss command is available
if ! command -v ss &> /dev/null; then
    echo "Error: 'ss' command not found. Please install iproute2 package." >&2
    exit 1
fi

# Display used ports
ports=$(ss -tulnp | awk '{print $5}' | awk -F: '{print $2}' | grep -v '^$' | sort -n | uniq)
# Convert newlines to spaces for output (test requirement)
if [ -n "$ports" ]; then
    (set -f; for p in $ports; do echo -n "$p "; done; echo)
else
    echo ""
fi
