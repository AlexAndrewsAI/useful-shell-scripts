# Bookmark aliases from config file
if [ "$(command -v yq)" ] && [ -n "$FILE_BASHRC_CONFIG" ] && [ -f "$FILE_BASHRC_CONFIG" ]; then
    # Create goto- aliases for each bookmark in config
    # Use a different approach to avoid subshell issues with process substitution
    bookmark_keys=$(yq '.bookmarks | keys | .[]' "$FILE_BASHRC_CONFIG" 2>/dev/null)
    if [[ -n "$bookmark_keys" ]]; then
        # First pass: validate all directories
        bookmark_error=0
        declare -a valid_keys=()
        declare -a valid_values=()
        
        while IFS= read -r key; do
            if [[ -n "$key" ]]; then
                # Strip leading and trailing double quotes from key
                key="${key#\"}"
                key="${key%\"}"
                value=$(yq ".bookmarks[\"$key\"]" "$FILE_BASHRC_CONFIG" 2>/dev/null)
                # Strip leading and trailing double quotes from value
                value="${value#\"}"
                value="${value%\"}"
                if [[ -n "$value" && "$value" != "null" ]]; then
                    # Expand tilde in path for directory check
                    expanded_value="${value/#\~/$HOME}"
                    # Check if the value is a directory
                    if [[ ! -d "$expanded_value" ]]; then
                        echo "Error: Bookmark '$key' value '$value' is not a directory" >&2
                        bookmark_error=1
                    else
                        valid_keys+=("$key")
                        valid_values+=("$value")
                    fi
                fi
            fi
        done <<< "$bookmark_keys"
        
        if [[ $bookmark_error -eq 1 ]]; then
            echo "Fatal: One or more bookmarks are invalid. Please fix the config file."
            return 1
        fi
        
        # Second pass: create aliases only for valid bookmarks
        for i in "${!valid_keys[@]}"; do
            key="${valid_keys[i]}"
            value="${valid_values[i]}"
            eval "alias goto-${key}='cd \"${value}\"'"
        done
    fi
fi

# Manual goto entry for useful-bash-scripts root directory
# The path should be set when the script is sourced
if [ -n "$SCRIPT_DIR" ]; then
    alias goto-useful-bash-scripts="cd \"$SCRIPT_DIR/..\""
else
    # Fallback if SCRIPT_DIR is not set
    script_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
    alias goto-useful-bash-scripts="cd \"$script_dir/..\""
fi

# File viewing and listing aliases
alias t="tail -f"
alias l="less"
alias topu="top -u $USER"
alias ll="ls -lha"
alias la="ls -a"
alias ld="ls -d"
alias lt="ls -lhatr"
alias g="grep --ignore-case --color=always -n"

# Open file from command line
if [ "$(command -v xdg-open)" ]; then
    alias open="xdg-open" # Arch Linux
fi
alias o="open"
alias md5sum-recursive="find -type f -not -path './md5sum.txt' -exec md5sum '{}' + > md5sum.txt"


# Redirect stderr to /dev/null for a command
# Usage: devnull-redirect <command> [args...]
devnull-redirect() {
    echo "$* 2>/dev/null"
    "$@" 2>/dev/null
}



if [ "$(command -v xclip)" ]; then
    alias clipboard-file='xclip -sel c < '
fi

# Find files containing a pattern, optionally filtered by filename
# Usage: findgrep <pattern> [filename_pattern]
findgrep() {
    if [[ "$2" == "" ]]; then
        find . -type f -exec grep --color=always -H "$1"  {} \;
    else
        find . -name "$1" -type f -exec grep  --color=always -H "$2" {} \;
    fi
}
alias grepfind=findgrep


# Get basenames of files/directories
# Usage: basenames <paths...>
basenames() {
    for f in $(ls -d "$@"); do
        basename "$f"
    done
}

# Go back through directory structure and give read permissions
# Input is list of files or nothing (defaults to current directory)
# Usage: chmod-recursive-give-access [-b|--base BASE_DIR] [files...]
chmod-recursive-give-access() {
    local BASE_DIR="$HOME"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -b|--base)
                BASE_DIR="$2"
                shift 2
                ;;
            *)
                break
                ;;
        esac
    done
    
    if [[ "$1" == "" ]]; then
        fls="."
    else
        fls="$*"
    fi
    for f in $fls; do
        echo "$f"
        chmod a+r "$f"
        d=$(dirname "$(realpath "$f")")
        while [ "$d" != "$BASE_DIR" ]; do
            echo "$d"
            chmod a+xr "$d"
            d=$(dirname "$d")
        done
    done
}

# Recursively remove write/execute permissions for group and others
# Input is list of files or nothing (defaults to current directory)
# Usage: chmod-recursive-locked-user-only [files...]
chmod-recursive-locked-user-only() {
    if [[ "$1" == "" ]]; then
        fls="."
    else
        fls=$*
    fi
    chmod -R go-wrx "$fls"
}

# Go to file's directory
# Usage: cdd <file_path>
cdd() {
    cd "$(realpath "$(dirname "$1")")"
}

# Move a file to a directory and create a symlink to it
# Usage: mv-ln <source_file> <target_directory>
mv-ln() {
    if [ $# -ne 2 ]; then
        return 1
    fi
    if [[ ! -d $2 ]]; then
        echo ERROR: "$2" must be existing directory
        return 1
    fi
    a=$(realpath "$1")
    aname=$(basename "$1")
    b=$(realpath "$2")

    echo "mv '$a' '$b'"
    mv "$a" "$b"
    echo "ln -s '$b/$aname' '$aname'"
    ln -s "$b/$aname" "$aname"
}
