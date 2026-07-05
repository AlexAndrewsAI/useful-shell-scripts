#!/bin/bash
# Auto-install: Add source line to ~/.bashrc if not already present
# Also sets up Python venv if configured in config file

# Parse positional argument (optional)
CONFIG_FILE="$1"

SCRIPT_DIR=$(dirname "$(realpath "${BASH_SOURCE[0]}")")
SCRIPT_PATH="$SCRIPT_DIR/bash/bashrc-extra.sh"

# Default to example config if not provided
if [[ -z "$CONFIG_FILE" ]]; then
    CONFIG_FILE="$SCRIPT_DIR/config.example.yml"
fi

# Resolve config file path
# If absolute path, use as-is
# If relative path, check if it exists relative to current directory first
if [[ "$CONFIG_FILE" = /* ]]; then
    # Absolute path
    CONFIG_FILE=$(realpath "$CONFIG_FILE" 2>/dev/null || echo "$CONFIG_FILE")
elif [[ -f "$CONFIG_FILE" ]]; then
    # Relative path that exists from current directory
    CONFIG_FILE=$(realpath "$CONFIG_FILE" 2>/dev/null || echo "$CONFIG_FILE")
else
    # Relative path that doesn't exist from current directory, try script directory
    potential_path="$SCRIPT_DIR/$CONFIG_FILE"
    if [[ -f "$potential_path" ]]; then
        CONFIG_FILE=$(realpath "$potential_path" 2>/dev/null || echo "$potential_path")
    else
        CONFIG_FILE=$(realpath "$CONFIG_FILE" 2>/dev/null || echo "$CONFIG_FILE")
    fi
fi

# Check if config file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Error: Config file does not exist: $CONFIG_FILE"
    exit 1
fi

SOURCE_LINE="source \"$SCRIPT_PATH\" \"$CONFIG_FILE\""

# Ensure .bashrc exists
if [[ ! -f "$HOME/.bashrc" ]]; then
    touch "$HOME/.bashrc"
fi

# Check if this exact source line already exists
if grep -Fqx "$SOURCE_LINE" "$HOME/.bashrc" 2>/dev/null; then
    echo "Already in ~/.bashrc: $SOURCE_LINE"
    SKIP_BASHRC=true
else
    SKIP_BASHRC=false
fi

# Remove any existing source line for this script (with different config)
if [ "$SKIP_BASHRC" = false ]; then
    if grep -q "source \"$SCRIPT_PATH\"" "$HOME/.bashrc" 2>/dev/null; then
        # Create temporary file
        TEMP_FILE=$(mktemp)
        # Remove lines containing source of this script using grep
        grep -v "source \"$SCRIPT_PATH\"" "$HOME/.bashrc" > "$TEMP_FILE" || true
        # Replace original file
        mv "$TEMP_FILE" "$HOME/.bashrc"
        echo "Removed existing source line from ~/.bashrc"
    fi

    # Add new source line
    echo "$SOURCE_LINE" >> "$HOME/.bashrc"
    echo "Added to ~/.bashrc: $SOURCE_LINE"
fi

# Handle venv setup if configured
if [ "$(command -v yq)" ] && [ "$(command -v uv)" ]; then
    # Skip venv operations if running in test environment
    if [[ -z "$SKIP_VENV_SETUP" ]]; then
        # Check if venv is configured as an object with location field
        venv_location=$(yq '.venv.location' "$CONFIG_FILE" 2>/dev/null)
        if [[ -n "$venv_location" && "$venv_location" != "null" ]]; then
            # Strip leading and trailing double quotes
            venv_location="${venv_location#\"}"
            venv_location="${venv_location%\"}"
            
            # Resolve venv path relative to config file directory
            config_dir=$(dirname "$CONFIG_FILE")
            if [[ "$venv_location" != /* ]]; then
                venv_path="$config_dir/$venv_location"
            else
                venv_path="$venv_location"
            fi
            
            # Check if pyproject.toml exists in config directory
            pyproject_path="$config_dir/pyproject.toml"
            if [[ -f "$pyproject_path" ]]; then
                echo "Setting up venv at: $venv_path"
                cd "$config_dir" || return
                
                # Check if venv exists and has a valid Python interpreter
                venv_needs_creation=false
                if [[ ! -d "$venv_path" ]]; then
                    venv_needs_creation=true
                else
                    # Try to run the Python interpreter to check if it's valid
                    python_bin="$venv_path/bin/python"
                    if [[ -x "$python_bin" ]]; then
                        if ! "$python_bin" --version >/dev/null 2>&1; then
                            echo "Warning: Existing venv has broken Python interpreter, recreating..."
                            rm -rf "$venv_path"
                            venv_needs_creation=true
                        fi
                    else
                        # Try python3 as fallback
                        python_bin="$venv_path/bin/python3"
                        if [[ -x "$python_bin" ]]; then
                            if ! "$python_bin" --version >/dev/null 2>&1; then
                                echo "Warning: Existing venv has broken Python interpreter, recreating..."
                                rm -rf "$venv_path"
                                venv_needs_creation=true
                            fi
                        else
                            echo "Warning: No Python interpreter found in venv, recreating..."
                            rm -rf "$venv_path"
                            venv_needs_creation=true
                        fi
                    fi
                fi
                
                # Create venv if needed
                if [[ "$venv_needs_creation" = true ]]; then
                    echo "Creating venv..."
                    uv venv "$venv_path"
                fi
                
                # Sync dependencies
                export UV_PROJECT_ENVIRONMENT="$venv_path"
                echo "Syncing dependencies from pyproject.toml..."
                if ! uv sync --python "$venv_path/bin/python"; then
                    echo "Warning: uv sync failed, recreating venv..."
                    rm -rf "$venv_path"
                    echo "Creating venv..."
                    uv venv "$venv_path"
                    echo "Syncing dependencies from pyproject.toml..."
                    uv sync --python "$venv_path/bin/python"
                fi
                
                # Add packages if specified
                if yq '.venv.add' "$CONFIG_FILE" >/dev/null 2>&1; then
                    add_packages=$(yq '.venv.add[]' "$CONFIG_FILE" 2>/dev/null)
                    if [[ -n "$add_packages" && "$add_packages" != "null" ]]; then
                        echo "Adding packages from config..."
                        while IFS= read -r package; do
                            if [[ -n "$package" && "$package" != "null" ]]; then
                                # Strip leading and trailing double quotes
                                package="${package#\"}"
                                package="${package%\"}"
                                echo "Adding package: $package"
                                uv add "$package" --python "$venv_path/bin/python"
                            fi
                        done <<< "$add_packages"
                    fi
                fi
                
                # Remove packages if specified
                if yq '.venv.remove' "$CONFIG_FILE" >/dev/null 2>&1; then
                    remove_packages=$(yq '.venv.remove[]' "$CONFIG_FILE" 2>/dev/null)
                    if [[ -n "$remove_packages" && "$remove_packages" != "null" ]]; then
                        echo "Removing packages from config..."
                        while IFS= read -r package; do
                            if [[ -n "$package" && "$package" != "null" ]]; then
                                # Strip leading and trailing double quotes
                                package="${package#\"}"
                                package="${package%\"}"
                                echo "Removing package: $package"
                                uv remove "$package" --python "$venv_path/bin/python"
                            fi
                        done <<< "$remove_packages"
                    fi
                fi
                
                cd - > /dev/null || true
                echo "Venv setup complete."
            else
                echo "Warning: pyproject.toml not found at $pyproject_path, skipping venv setup"
            fi
        fi
    fi
fi
