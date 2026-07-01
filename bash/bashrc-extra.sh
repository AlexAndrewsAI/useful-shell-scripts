#!/bin/bash

# Get script directory
SCRIPT_DIR=$(dirname "$(realpath "${BASH_SOURCE[0]}")")

# Parse positional argument (required)
CONFIG_FILE="$1"

# Require config file argument
if [[ -z "$CONFIG_FILE" ]]; then
    echo "Error: Config file argument is required" >&2
    echo "Usage: source bashrc-extra.sh <config_file>" >&2
    return 1
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
    CONFIG_FILE="$SCRIPT_DIR/$CONFIG_FILE"
    CONFIG_FILE=$(realpath "$CONFIG_FILE" 2>/dev/null || echo "$CONFIG_FILE")
fi

# Check if config file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Error: Config file does not exist: $CONFIG_FILE"
    return 1
fi

# Export config file path
export FILE_BASHRC_CONFIG="$CONFIG_FILE"

# Source themed bashrc files
source "$SCRIPT_DIR/bashrc-files.sh"
source "$SCRIPT_DIR/bashrc-processes.sh"
source "$SCRIPT_DIR/bashrc-dev.sh"

# System
alias bashrc=". ~/.bashrc"
alias chown-me='sudo chown -R "$(whoami)":"$(id -gn)"'



# Add this script's directory to PATH so bundled utilities are accessible
if [[ -n "${BASH_SOURCE[0]}" ]]; then
    export PATH="$SCRIPT_DIR:$PATH"
fi


# region KDE
if [ "$(command -v plasmashell)" ]; then
    alias kderestart="killall plasmashell; kstart plasmashell"
fi
# endregion KDE

#region Arch Linux utilities
if [ "$(command -v pacman)" ]; then
    # Package managers
    alias pacman-search="echo 'Use \`pacman -Ss\`'; pacman -Ss"
    # Install a package from AUR
    # Usage: aur-install <package_name>
    aur-install() {
        home=$(pwd)
        cd /tmp || return
        rm -fr "$*"
        git clone "https://aur.archlinux.org/$*.git"
        cd "$*" || return
        makepkg -si
        cd "$home"
    }
fi
#endregion Arch Linux utilities

#region Flatpak utilities
if [ "$(command -v flatpak)" ]; then
    if [[ "$(flatpak list | grep io.mpv.Mpv)" != "" ]]; then
        mpv() {
            flatpak run --branch=stable --arch=x86_64 --command=mpv --file-forwarding io.mpv.Mpv "$@"
        }
    fi
    if [[ "$(flatpak list | grep org.gnome.meld)" != "" ]]; then
        meld() {
            flatpak run --branch=stable --arch=x86_64 --command=meld --file-forwarding org.gnome.meld "$@"
        }
    fi
    if [[ "$(flatpak list | grep com.vscodium.codium)" != "" ]]; then
        vscodium() {
            flatpak run --branch=stable com.vscodium.codium "$@"
        }
    fi
    # Note: flatpak doesn't always list Firefox since it's installed separately
    alias ff="nohup flatpak run org.mozilla.firefox &> ~/.nohup.log &"
    alias flatpak-find="flatpak list | grep --color=never -i"
    # Run a flatpak application by name
    # Usage: flatpak-run <app_name> [args...]
    flatpak-run() {
        program=$(flatpak list | grep --color=never -i "$1" | head -n 1 | awk '{print $2}')
        shift;
        echo "flatpak run $program"
        flatpak run "$program" "$@"
    }
    # Update a flatpak application by name
    # Usage: flatpak-update <app_name> [args...]
    flatpak-update() {
        program=$(flatpak list | grep --color=never -i "$1" | head -n 1 | awk '{print $2}')
        shift
        echo "flatpak update $program $*"
        flatpak update "$program" "$@"
    }
fi
#endregion Flatpak utilities


alias histfind="history | grep --color=always --ignore-case"

alias datetime="date '+%F-%H-%M-%S'"

#region Audio utilities
if [ "$(command -v ffmpeg)" ]; then
    # Downsample audio files to 12K opus format for voice
    # Can process single files or all files in a directory
    # Usage: ffmpeg-voice-downsample <file_or_directory>
    ffmpeg-voice-downsample() {
        QUALITY="12K"
        input_file="${1:-.}"

        # Check if it's a directory, if so process all files in this directory (non-recursive)
        if [[ -d "$input_file" ]]; then
            for f in "$input_file"/*; do
                # Not recursive
                if [[ -f "$f" ]]; then
                    ffmpeg-voice-downsample "$f"
                fi
            done
        # If it's a file
        else
            if [[ "$input_file" == *_$QUALITY.opus ]]; then
                echo "$input_file is a '_$QUALITY.opus' file."
            else
                 output_file="${input_file%.*}_$QUALITY.opus"
                if [[ -e "$output_file" ]]; then
                    echo "$input_file file already has a '_$QUALITY.opus' file."
                else
                    echo  ffmpeg -i "$input_file" -c:a libopus -b:a $QUALITY -ac 1 "$output_file"
                    ffmpeg -i "$input_file" -c:a libopus -b:a $QUALITY -ac 1 -vbr on "$output_file"
                    echo "$output_file"
                fi
            fi
        fi
    }
fi
#endregion Audio utilities

#region Rclone utilities
if [ "$(command -v rclone)" ]; then
    alias rclone-encrypt-config="rclone config encryption set"
    alias rclone-decrypt-config="rclone config encryption remove"
    alias rclone-gui="rclone rcd --rc-web-gui"

    # Backup rclone configuration with encryption
    # Prompts for password, decrypts config, backs it up, and re-encrypts
    # Usage: rclone-backup-config
    # Environment variable: RCLONE_PASSWORD (optional, avoids interactive prompt)
    rclone-backup-config() {
        fin=$(rclone config file | tail -1)
        
        # Check for TTY or environment variable
        if [ -t 0 ]; then
            read -r -s -p "Enter Password: " pswd
            echo
        elif [ -n "$RCLONE_PASSWORD" ]; then
            pswd="$RCLONE_PASSWORD"
        else
            echo "Error: No TTY available and RCLONE_PASSWORD not set" >&2
            echo "Usage: RCLONE_PASSWORD=your_password rclone-backup-config" >&2
            return 1
        fi
        
        echo "$pswd" | rclone-decrypt-config
        cp "$fin" "./rclone-$(date +%F).conf"
        echo "config file backed up to: ./rclone-$(date +%F).conf"
        # Use a subshell to send the password twice to rclone-encrypt-config
        (
            echo "$pswd"
            sleep 1
            echo "$pswd"
        ) | rclone-encrypt-config
        unset pswd
    }
fi
#endregion Rclone utilities