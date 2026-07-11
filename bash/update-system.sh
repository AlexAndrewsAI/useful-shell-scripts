#!/bin/bash

# Script: SteamDeck System Update Script
# Description: Automates installation of packages, virtual environments, and
# configurations for a SteamDeck development environment using a YAML config.
# Usage: ./update-system.sh [OPTIONS]
# Options:
#   -h, --help          Show this help message
#   -i, --init          Force initialization of pacman keyring
#   -c, --config FILE   Path to YAML config (default: update-system.yml
#                       next to this script)

###############################################################################
# HELP FUNCTION
###############################################################################

show_help() {
    cat << EOF
SteamDeck System Update Script

DESCRIPTION:
    Automates setup of a SteamDeck development environment including:
    - Pacman keyring initialization
    - Flatpak package installation
    - Pacman package installation
    - AUR package installation
    - Git configuration
    - Desktop shortcuts and configurations
    - Distrobox container setup
    - Bash configuration and Python venv (via setup.sh)

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help          Show this help message and exit
    -i, --init          Force initialization of pacman keyring
                        (Use this first time after a system update)
    -c, --config FILE   Override config path from .config-location.dat

EXAMPLES:
    $0                          # Normal execution (reads .config-location.dat)
    $0 --init                   # Force keyring initialization
    $0 -c my-config.yml         # Override config location
    $0 -h                       # Display this help message

REQUIREMENTS:
    - bash 4.0+
    - sudo privileges
    - pacman package manager
    - python3 (for YAML config parsing)
    - Internet connection

CONFIGURATION:
    Requires .config-location.dat (created by setup.sh) which points to
    the YAML config file. Run setup.sh first, or manually create this
    file containing the path to your config.

EOF
}

###############################################################################
# CONFIG PARSING
###############################################################################

# Parse the YAML config file into bash variables using a built-in, dependency
# free YAML parser. The parsed values are written to a temporary file that is
# sourced by the main script.
load_config() {
    local config_file="$1"
    if [ ! -f "$config_file" ]; then
        echo "ERROR: Config file not found: $config_file"
        exit 1
    fi

    local tmp_config
    tmp_config="$(mktemp)"
    CONFIG_TMP_FILES+=("$tmp_config")

    python3 "$SCRIPTS_DIR/yaml_parser.py" "$config_file" > "$tmp_config"

    # shellcheck source=/dev/null
    source "$tmp_config"
}

###############################################################################
# UTILITY FUNCTIONS
###############################################################################

# Initialize pacman keyring if needed
# Populates the pacman keyring with Holo and Arch Linux keys
# Sets git default branch to main
initialize_pacman_keyring() {
    echo "Initializing pacman keyring..."
    git config --global init.defaultBranch main
    sudo pacman-key --init
    sudo pacman-key --populate holo
    sudo pacman-key --populate archlinux
    echo "✓ Pacman keyring initialized"
}

# Install flatpak packages from a list of package ids
# Arguments:
#   $@ - Flatpak package ids to install
run_flatpak() {
    if [ "$#" -eq 0 ]; then
        echo "ℹ No flatpak packages configured, skipping"
        return 0
    fi
    echo "Installing flatpak packages..."
    flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    flatpak update -y --noninteractive
    for package in "$@"; do
        echo "  → Installing: $package"
        sudo flatpak install -y --noninteractive flathub "$package"
    done
    echo "✓ Flatpak installation complete"
}

# Install pacman packages from a list of package names
# Arguments:
#   $@ - Package names to install
run_pacman() {
    if [ "$#" -eq 0 ]; then
        echo "ℹ No pacman packages configured, skipping"
        return 0
    fi
    echo "Installing pacman packages..."
    local dir
    dir="$(pwd)"
    cd ~ || exit 1
    for line in "$@"; do
        [ -z "$line" ] && continue
        echo "  → Installing: $line"
        sudo pacman -S --noconfirm "$line"
    done
    cd "$dir" || exit 1
    echo "✓ Pacman installation complete"
}

# Install AUR packages using makepkg
# Arguments:
#   $@ - Package names to install from AUR
aur_install() {
    if [ "$#" -eq 0 ]; then
        echo "ℹ No AUR packages configured, skipping"
        return 0
    fi
    local home
    home="$(pwd)"
    cd /tmp || exit 1
    for package in "$@"; do
        echo "Installing AUR package: $package..."
        rm -fr "$package"
        git clone "https://aur.archlinux.org/$package.git"
        cd "$package" || exit 1
        makepkg -si --noconfirm
        cd .. || exit 1
        rm -fr "$package"
    done
    cd "$home" || exit 1
    echo "✓ AUR installation complete"
}

# Apply global git configuration from the config's git section
configure_git() {
    if [ -z "${CONFIG_GIT_USER_NAME:-}" ] && [ -z "${CONFIG_GIT_USER_EMAIL:-}" ]; then
        echo "ℹ No git configuration provided, skipping"
        return 0
    fi
    echo "Configuring Git..."
    if [ -n "${CONFIG_GIT_USER_NAME:-}" ]; then
        git config --global user.name "${CONFIG_GIT_USER_NAME}"
    fi
    if [ -n "${CONFIG_GIT_USER_EMAIL:-}" ]; then
        git config --global user.email "${CONFIG_GIT_USER_EMAIL}"
    fi
}

# Install the Decky plugin loader
install_decky() {
    echo "Installing Decky plugin..."
    local fin="$HOME/Downloads/decky_installer.desktop"
    wget -O "$fin" "https://github.com/SteamDeckHomebrew/decky-installer/releases/latest/download/decky_installer.desktop"
    chmod a+rx "$fin"
    gio launch "$fin"
}

# Setup a Distrobox container using the configured image and name
setup_distrobox() {
    local image="${CONFIG_DISTROBOX_IMAGE:-}"
    local name="${CONFIG_DISTROBOX_NAME:-}"
    if [ -z "$image" ] || [ -z "$name" ]; then
        echo "ℹ Distrobox not fully configured, skipping"
        return 0
    fi
    echo "Setting up Distrobox..."
    export DBX_CONTAINER_IMAGE="$image"
    export DBX_CONTAINER_NAME="$name"
    if ! distrobox-list | grep -Fq "$name"; then
        distrobox-create
        echo "✓ Distrobox container created"
    else
        echo "ℹ Distrobox container already exists"
    fi
}

###############################################################################
# ARGUMENT PARSING
###############################################################################

POSITIONAL_ARGS=()
FORCE_INIT=FALSE
CONFIG_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -i|--init)
            FORCE_INIT="TRUE"
            shift
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -*|--*)
            echo "ERROR: Unknown option $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done

set -- "${POSITIONAL_ARGS[@]}"

###############################################################################
# MAIN SETUP EXECUTION
###############################################################################

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_TMP_FILES=()

# Read config location from .config-location.dat (created by setup.sh)
DAT_FILE="$SCRIPTS_DIR/../.config-location.dat"
if [ ! -f "$DAT_FILE" ]; then
    echo "ERROR: .config-location.dat not found at $DAT_FILE"
    echo "Run setup.sh first, or create this file containing the path to your config."
    exit 1
fi

if [ -z "$CONFIG_FILE" ]; then
    CONFIG_FILE="$(cat "$DAT_FILE")"
fi

# Validate the config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found: $CONFIG_FILE"
    exit 1
fi

load_config "$CONFIG_FILE"

# Treat force_init from CLI or config as a trigger
if [ "${CONFIG_FORCE_INIT:-false}" = "true" ]; then
    FORCE_INIT="TRUE"
fi

trap 'rm -f "${CONFIG_TMP_FILES[@]}"' EXIT

echo "=========================================="
echo "SteamDeck System Update Script"
echo "=========================================="

# Initialize pacman keyring if needed
if [ "$FORCE_INIT" = TRUE ] || [ ! -s /etc/pacman.d/gnupg/pubring.kbx ]; then
    initialize_pacman_keyring
fi

# Create necessary directories
mkdir -p ~/.local/bin

# On SteamOS, disable the read-only filesystem before system changes
if [ "${CONFIG_STEAMOS:-false}" = "true" ]; then
    echo "Disabling SteamOS read-only filesystem..."
    sudo steamos-readonly disable
fi

# Prepare system for compilation
sudo pacman -S --noconfirm binutils make gcc pkg-config fakeroot

# Install flatpak packages
run_flatpak "${CONFIG_FLATPAK[@]}"

# Install pacman packages
run_pacman "${CONFIG_PACMAN[@]}"

# Run setup.sh for bash configuration and Python venv
"$SCRIPTS_DIR/../setup.sh" "$CONFIG_FILE"

# Install AUR packages
aur_install "${CONFIG_AUR[@]}"

# Configure git
configure_git

# Install Decky plugin
if [ "${CONFIG_DECKY:-false}" = "true" ]; then
    install_decky
fi

# Setup Distrobox
setup_distrobox

# Print completion message
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Further manual configuration required:"
echo ""
echo "1. System Settings → Autostart:"
echo "   - add desired programs"
echo ""
echo "2. Add Quicklaunch:"
echo "   ~/.local/share/applications/quicklaunch.desktop"
echo "   (Try to pin to taskbar)"
echo ""
echo "=========================================="
