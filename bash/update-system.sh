#!/bin/bash

# Script: System Update Script
# Description: Automates installation of packages, virtual environments, and
# configurations using a YAML config. Supports pacman, apt, dnf, brew, nix,
# npm, snap, cargo, go, flatpak, AppImage, and shell executables.
# Usage: ./update-system.sh [OPTIONS]
# Options:
#   -h, --help          Show this help message
#   -i, --init          Force initialization of pacman keyring
#   -c, --config FILE   Path to YAML config (default: config.yaml
#                       in project root, via .config-location.dat)

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
    - NPM package installation
    - Snap package installation
    - APT package installation
    - DNF package installation
    - Homebrew package installation
    - Nix package installation
    - Cargo package installation
    - Go package installation
    - AppImage package installation
    - Shell executable creation
    - Git configuration
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
    $0 -c my-config.yaml         # Override config location
    $0 -h                       # Display this help message

REQUIREMENTS:
    - bash 4.0+
    - sudo privileges
    - pacman package manager
    - python3 (for YAML config parsing)
    - Internet connection
    - npm/snap/apt/dnf/brew/nix/cargo/go (optional, for respective package managers)
    - wget (required for AppImage installation)

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

    python3 "$SCRIPTS_DIR/../python/yaml_parser.py" "$config_file" > "$tmp_config"

    # shellcheck source=/dev/null
    source "$tmp_config"
}

###############################################################################
# UTILITY FUNCTIONS
###############################################################################

declare -a CONFIG_TMP_FILES=()

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
    for line in "$@"; do
        [ -z "$line" ] && continue
        echo "  → Installing: $line"
        sudo pacman -S --noconfirm "$line"
    done
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
    local original_dir
    original_dir="$(pwd)"
    local build_dir
    build_dir="$(mktemp -d)"
    for package in "$@"; do
        echo "Installing AUR package: $package..."
        git clone "https://aur.archlinux.org/$package.git" "$build_dir/$package"
        cd "$build_dir/$package" || exit 1
        makepkg -si --noconfirm
        cd "$build_dir" || exit 1
        rm -rf "${build_dir:?}/$package"
    done
    rm -rf "${build_dir:?}"
    cd "$original_dir" || exit 1
    echo "✓ AUR installation complete"
}

# Check if a command exists before running package manager
# Arguments:
#   $1 - Command to check
#   $2 - Package manager name (for error message)
check_command() {
    if ! command -v "$1" &>/dev/null; then
        echo "⚠ $1 not found - skipping $2 package installation"
        return 1
    fi
    return 0
}

# Install npm packages globally
# Arguments:
#   $@ - Package names to install via npm
run_npm() {
    if [ "$#" -eq 0 ]; then
        echo "ℹ No npm packages configured, skipping"
        return 0
    fi
    if ! check_command "npm" "npm"; then
        return 0
    fi
    echo "Installing npm packages..."
    for package in "$@"; do
        echo "  → Installing: $package"
        sudo npm install -g "$package"
    done
    echo "✓ NPM installation complete"
}

# Install snap packages
# Arguments:
#   $@ - Package names to install via snap
run_snap() {
    if [ "$#" -eq 0 ]; then
        echo "ℹ No snap packages configured, skipping"
        return 0
    fi
    if ! check_command "snap" "snap"; then
        return 0
    fi
    # Check if snapd daemon is responsive
    if ! snap list >/dev/null 2>&1; then
        echo "⚠ snapd daemon not responding, attempting to start it..."
        if command -v systemctl &>/dev/null; then
            sudo systemctl start snapd 2>/dev/null || true
        elif command -v service &>/dev/null; then
            sudo service snapd start 2>/dev/null || true
        fi
        # Give snapd a moment to initialize
        sleep 2
        if ! snap list >/dev/null 2>&1; then
            echo "✗ snapd daemon could not be started — skipping snap package installation"
            return 1
        fi
        echo "✓ snapd daemon started successfully"
    fi
    echo "Installing snap packages..."
    for package in "$@"; do
        echo "  → Installing: $package"
        sudo snap install "$package"
    done
    echo "✓ Snap installation complete"
}

# Install apt packages
# Arguments:
#   $@ - Package names to install via apt
run_apt() {
    if [ "$#" -eq 0 ]; then
        echo "ℹ No apt packages configured, skipping"
        return 0
    fi
    if ! check_command "apt" "apt"; then
        return 0
    fi
    echo "Installing apt packages..."
    sudo apt update
    for package in "$@"; do
        echo "  → Installing: $package"
        sudo apt install -y "$package"
    done
    echo "✓ APT installation complete"
}

# Install DNF packages (Fedora/RHEL)
# Arguments:
#   $@ - Package names to install via dnf
run_dnf() {
    if [ "$#" -eq 0 ]; then
        echo "ℹ No dnf packages configured, skipping"
        return 0
    fi
    if ! check_command "dnf" "dnf"; then
        return 0
    fi
    echo "Installing dnf packages..."
    for package in "$@"; do
        echo "  → Installing: $package"
        sudo dnf install -y "$package"
    done
    echo "✓ DNF installation complete"
}

# Install Homebrew packages (Linux/macOS)
# Arguments:
#   $@ - Package names to install via brew
run_brew() {
    if [ "$#" -eq 0 ]; then
        echo "ℹ No brew packages configured, skipping"
        return 0
    fi
    if ! check_command "brew" "Homebrew"; then
        return 0
    fi
    echo "Installing Homebrew packages..."
    for package in "$@"; do
        echo "  → Installing: $package"
        brew install "$package"
    done
    echo "✓ Homebrew installation complete"
}

# Install Nix packages (any Linux distro)
# Arguments:
#   $@ - Package names to install via nix profile
run_nix() {
    if [ "$#" -eq 0 ]; then
        echo "ℹ No nix packages configured, skipping"
        return 0
    fi
    if ! check_command "nix" "nix"; then
        return 0
    fi
    echo "Installing Nix packages..."
    for package in "$@"; do
        echo "  → Installing: $package"
        nix profile install "nixpkgs#$package"
    done
    echo "✓ Nix installation complete"
}

# Install Cargo packages (Rust)
# Arguments:
#   $@ - Package names to install via cargo
run_cargo() {
    if [ "$#" -eq 0 ]; then
        echo "ℹ No cargo packages configured, skipping"
        return 0
    fi
    if ! check_command "cargo" "Cargo"; then
        return 0
    fi
    echo "Installing Cargo packages..."
    for package in "$@"; do
        echo "  → Installing: $package"
        cargo install "$package"
    done
    echo "✓ Cargo installation complete"
}

# Install Go packages
# Arguments:
#   $@ - Package names to install via go install
run_go() {
    if [ "$#" -eq 0 ]; then
        echo "ℹ No go packages configured, skipping"
        return 0
    fi
    if ! check_command "go" "Go"; then
        return 0
    fi
    echo "Installing Go packages..."
    # Ensure GOPATH/bin is in PATH for the user
    local gopath
    gopath="$(go env GOPATH)"
    export PATH="$PATH:$gopath/bin"
    for package in "$@"; do
        echo "  → Installing: $package"
        go install "$package"
    done
    echo "✓ Go installation complete"
}

# Install AppImage packages from configured alias:url mappings
# Downloads AppImages and installs them to specified locations
run_appimage() {
    # Check if any AppImage packages are configured
    local has_appimage=false
    for var in ${!CONFIG_APPIMAGE_*}; do
        # Skip the _ALIAS variables
        case "$var" in
            *_ALIAS) continue ;;
        esac
        has_appimage=true
        break
    done

    if [ "$has_appimage" = false ]; then
        echo "ℹ No AppImage packages configured, skipping"
        return 0
    fi

    if ! check_command "wget" "AppImage"; then
        return 0
    fi

    echo "Installing AppImage packages..."

    for var in ${!CONFIG_APPIMAGE_*}; do
        # Skip the _ALIAS variables
        case "$var" in
            *_ALIAS) continue ;;
        esac

        local url="${!var}"
        local alias_var="${var}_ALIAS"
        local alias="${!alias_var}"

        if [ -z "$url" ] || [ -z "$alias" ]; then
            continue
        fi

        echo "  → Installing: $alias from $url"

        # Determine the target path
        local target_path
        if [[ "$alias" == */* ]]; then
            # Full path provided
            target_path="$alias"
        else
            # Single word, put in ~/.local/bin
            target_path="$HOME/.local/bin/$alias"
        fi

        # Create parent directories if needed
        local parent_dir
        parent_dir="$(dirname "$target_path")"
        if [ ! -d "$parent_dir" ]; then
            mkdir -p "$parent_dir"
        fi

        # Download the AppImage
        wget -O "$target_path" "$url"

        # Make it executable
        chmod +x "$target_path"

        echo "    ✓ Installed to $target_path"
    done

    echo "✓ AppImage installation complete"
}

# Create shell executables from configured name:command mappings
# Writes a shell script with proper shebang and safety options, then
# makes it executable. If name is a path (contains /), the script is
# written there; otherwise it goes to $HOME/.local/bin/<name>.
run_shell_exe() {
    # Check if any shell executables are configured
    local has_shell_exe=false
    for var in ${!CONFIG_SHELL_EXE_*}; do
        # Skip the _ALIAS variables
        case "$var" in
            *_ALIAS) continue ;;
        esac
        has_shell_exe=true
        break
    done

    if [ "$has_shell_exe" = false ]; then
        echo "ℹ No shell executables configured, skipping"
        return 0
    fi

    echo "Creating shell executables..."

    for var in ${!CONFIG_SHELL_EXE_*}; do
        # Skip the _ALIAS variables
        case "$var" in
            *_ALIAS) continue ;;
        esac

        local command="${!var}"
        local alias_var="${var}_ALIAS"
        local name="${!alias_var}"

        if [ -z "$command" ] || [ -z "$name" ]; then
            continue
        fi

        echo "  → Creating: $name"

        # Determine the target path
        local target_path
        if [[ "$name" == */* ]]; then
            # Full path provided
            target_path="$name"
        else
            # Single word, put in ~/.local/bin
            target_path="$HOME/.local/bin/$name"
        fi

        # Create parent directories if needed
        local parent_dir
        parent_dir="$(dirname "$target_path")"
        if [ ! -d "$parent_dir" ]; then
            mkdir -p "$parent_dir"
        fi

        # Write the shell script
        {
            echo '#!/bin/sh'
            echo 'set -euo pipefail'
            echo ''
            echo "$command"
        } > "$target_path"

        # Make it executable
        chmod +x "$target_path"

        echo "    ✓ Created executable at $target_path"
    done

    echo "✓ Shell executable creation complete"
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
    if command -v gio &>/dev/null; then
        gio launch "$fin"
    else
        echo "⚠ gio not found — launch $fin manually to complete Decky installation"
    fi
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
    if ! check_command "distrobox-list" "distrobox"; then
        return 0
    fi
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
# ARGUMENT PARSING & MAIN EXECUTION
# Skipped when sourced with _SOURCE_ONLY=true (for testing individual functions)
###############################################################################

if [[ "${_SOURCE_ONLY:-}" != "true" ]]; then

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

# Prepare system for compilation (detect package manager)
if command -v pacman &>/dev/null; then
    sudo pacman -S --noconfirm binutils make gcc pkg-config fakeroot
elif command -v apt-get &>/dev/null; then
    sudo apt-get install -y build-essential pkg-config fakeroot
elif command -v dnf &>/dev/null; then
    sudo dnf install -y binutils make gcc pkg-config fakeroot
elif command -v brew &>/dev/null; then
    brew install make gcc pkg-config
fi

# Install flatpak packages
run_flatpak "${CONFIG_FLATPAK[@]}"

# Install pacman packages
run_pacman "${CONFIG_PACMAN[@]}"

# Install npm packages
run_npm "${CONFIG_NPM[@]}"

# Install snap packages
run_snap "${CONFIG_SNAP[@]}"

# Install apt packages
run_apt "${CONFIG_APT[@]}"

# Install dnf packages
run_dnf "${CONFIG_DNF[@]}"

# Install Homebrew packages
run_brew "${CONFIG_BREW[@]}"

# Install Nix packages
run_nix "${CONFIG_NIX[@]}"

# Install Cargo packages
run_cargo "${CONFIG_CARGO[@]}"

# Install Go packages
run_go "${CONFIG_GO[@]}"

# Install AppImage packages
run_appimage

# Create shell executables
run_shell_exe

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

fi  # end _SOURCE_ONLY guard
