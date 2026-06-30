# Useful Shell Scripts

A collection of practical shell scripts and Python development tools for system administration, development workflows, and productivity enhancement. This is primarily set up for running [AlexAndrewsAI](https://github.com/AlexAndrewsAI/)'s repos.

## Overview

This repository contains curated utilities for:
- **Git automation** - Copy repositories, generate documentation
- **Process management** - Find and kill processes efficiently
- **System administration** - Port monitoring, file operations
- **Development environment** - Comprehensive Python setup with common libraries

## Quick Start

### Bash Scripts

Clone the repository and make scripts executable:

```bash
git clone https://github.com/AlexAndrewsAI/useful-shell-scripts.git
cd useful-shell-scripts
chmod +x setup.sh bash/*.sh
```

#### Using bashrc-extra.sh

The main utility file is `bashrc-extra.sh`, which provides extensive bash aliases and functions.

**Automatic setup (recommended):**

Run the setup script to automatically add the source line to your ~/.bashrc:

```bash
./setup.sh
```

With custom configuration:

```bash
./setup.sh /path/to/config.yml
```

**Manual setup:**

Add the following line to your ~/.bashrc (config file is required):

```bash
source /path/to/useful-shell-scripts/bash/bashrc-extra.sh /path/to/config.yml
```

The script sets the `FILE_BASHRC_CONFIG` environment variable to the specified config file path. The config file argument is required when sourcing bashrc-extra.sh directly, but optional when using setup.sh (defaults to `config.example.yml`). Both scripts validate that the config file exists before proceeding and resolve relative paths intelligently (checking current directory first, then script directory).

### Configuration File

The config file (YAML format) supports bookmark shortcuts and venv configuration. Example `config.example.yml`:

```yaml
bookmarks:
  downloads: ~/Downloads
  documents: ~/Documents
  home: ~

venv:
  location: .venv  # relative to config directory, or absolute path
  add:             # packages to add (runs uv add [package])
    - pytest
  remove:          # packages to remove (runs uv remove [package])
    - some-package
```

If `yq` is installed, the script automatically creates `goto-` aliases for each bookmark:
- `goto-downloads` → `cd ~/Downloads`
- `goto-documents` → `cd ~/Documents`
- `goto-home` → `cd ~`

If `venv` is configured and both `yq` and `uv` are available, the setup script will automatically create/sync the virtual environment using the project's `pyproject.toml`. It will also run `uv add` for packages in the `add` list and `uv remove` for packages in the `remove` list.

When the venv is configured, the bashrc will:
- Set the `DIR_VENV` environment variable to the venv path
- Create a `venv-main` alias to activate the venv: `venv-main`
- Create a `goto-venv-main` alias to go to the venv directory: `goto-venv-main`

**Requirements for bookmarks:**
- `yq` command must be available
- Config file must contain a `bookmarks` section with key-value pairs

**Requirements for venv:**
- `yq` command must be available
- `uv` command must be available
- Config file must contain a `venv` field as an object with `location` field
- `pyproject.toml` must exist in the config directory

### Python Environment

The Python environment is configured with `uv` package manager. If you have configured the `venv` field in your config file, the setup script will automatically create and sync the virtual environment.

**Manual setup:**

```bash
uv sync
source .venv/bin/activate
```

**Automatic setup via config:**

Configure the venv path in your config file (e.g., `venv: .venv`) and run the setup script. It will automatically create the venv and sync dependencies from `pyproject.toml`.

## Bash Scripts

### setup.sh

Automatically adds the bashrc-extra.sh source line to your ~/.bashrc for easy integration.

**Usage:**
```bash
./setup.sh
```

With custom configuration (optional):

```bash
./setup.sh /path/to/config.yml
```

**What it does:**
- Calculates the absolute path to bashrc-extra.sh
- Defaults to `config.example.yml` if no config file is specified
- Resolves config file paths: absolute paths used as-is, relative paths checked from current directory first, then from script directory
- Validates that the config file exists before proceeding
- Adds `source "/absolute/path/to/bashrc-extra.sh /absolute/path/to/config"` to ~/.bashrc
- If the source line already exists with the same config, it skips bashrc modification but continues with venv setup
- If the source line exists with a different config, it removes the old line and adds the new one
- Provides feedback on what was done
- If venv is configured in config file and both yq and uv are available:
  - Validates existing venv Python interpreter before sync
  - Recreates venv if Python interpreter is broken or missing
  - Automatically recreates venv if uv sync fails
  - Creates/syncs the virtual environment using pyproject.toml
  - Runs `uv add` for packages in the `add` list
  - Runs `uv remove` for packages in the `remove` list

### git-copy-bare.sh

Copy all files tracked by git from a repository to an output directory, preserving directory structure and symlinks.

**Usage:**
```bash
./git-copy-bare.sh [OPTIONS] <output>
```

**Options:**
- `-i, --input DIR` - Git repository directory (default: current directory)
- `-h, --help` - Display help message

**Examples:**
```bash
# Copy current repo to /tmp/export
./git-copy-bare.sh /tmp/export

# Copy specific repo
./git-copy-bare.sh -i /path/to/repo /tmp/export
```

### git2linksremote.sh

Generate a markdown list of all git-tracked files with clickable GitHub links for the current branch.

**Usage:**
```bash
./git2linksremote.sh
```

**Output:**
```markdown
## File List (main branch)

* [README.md](https://github.com/user/repo/blob/main/README.md)
* [script.sh](https://github.com/user/repo/blob/main/script.sh)
```

### git2markdown.sh

Format git-tracked files as markdown code blocks, with extension filtering. Automatically copies output to clipboard via `xclip`.

**Usage:**
```bash
./git2markdown.sh [OPTIONS]
```

**Options:**
- `-a, --all` - Include all files regardless of extension
- `-w, --whitelist EXTS` - Custom extensions (pipe-separated, e.g., "js|ts|txt")
- `-h, --help` - Display help message

**Examples:**
```bash
# Default extensions (py|md|txt|yml|yaml|json|toml)
./git2markdown.sh

# All files
./git2markdown.sh -a

# Custom extensions
./git2markdown.sh -w "js|ts|jsx|tsx"
```

### ports-in-use.sh

Display all network ports currently in use on the system.

**Usage:**
```bash
./ports-in-use.sh
```

**Requirements:**
- `ss` command (usually installed by default)

### psfind.sh

Advanced process finding with multiple search options and kill capability.

**Usage:**
```bash
./psfind.sh [OPTIONS] <search-term> [refine-pattern]
```

**Options:**
- `-h, --help` - Show help message
- `-k, --kill` - Kill matching processes instead of displaying them
- `-w, --word-regexp` - Match whole words only
- `-n, --not <pattern>` - Exclude processes matching this pattern

**Examples:**
```bash
# Find all processes containing 'firefox'
./psfind.sh firefox

# Kill all node processes matching 'app.js'
./psfind.sh -k node . "app.js"

# Find processes with word 'python' but exclude 'grep'
./psfind.sh -w -n grep python
```

## bashrc-extra.sh

The comprehensive bash configuration file provides extensive utilities across multiple categories:

### Bookmark Aliases
If `yq` is installed and a config file is provided, automatically creates `goto-` aliases for directory bookmarks defined in the config file's `bookmarks` section.

### Python Environment
If `yq` is installed and a config file is provided with a `venv` field:
- Sets the `DIR_VENV` environment variable to the configured venv path
- When `uv` is available, provides venv utilities:
  - `venv-here` - Create and activate a venv in the current directory
  - `venv-which` - Display the current virtual environment path
  - `venv-deactivate` - Deactivate the current virtual environment
  - `venv-main` - Activate the main venv specified in config
  - `goto-venv-main` - Go to the main venv directory
  - `uv-tests` - Run complete test suite with coverage and formatting

### System Management
- **Arch Linux**: `pacman-search`, `aur-install` for AUR packages
- **Flatpak**: Smart aliases for installed applications, `flatpak-run`, `flatpak-update`
- **KDE Plasma**: `kderestart` to restart the desktop environment

### File Operations
- `findgrep`/`grepfind` - Search files with patterns
- `chmod-recursive-give-access` - Recursive permission management
- `mv-ln` - Move files and create symlinks
- `cdd` - Change to file's directory
- `f` - Case-insensitive file finding

### Git Integration
- Multiple git aliases and utilities
- `git-unzip-update` - Update repos from zip files
- Branch and diff shortcuts

### Process Management
- `psfind` - Advanced process finding/killing
- `psnice` - Renice processes
- `pstoggle` - Toggle process run state (SIGSTOP/SIGCONT)
- `process-kill-threshhold` - Kill processes exceeding CPU threshold
- `repeat` - Repeat commands at intervals

### Audio/Media
- `ffmpeg-voice-downsample` - Convert audio to 12K opus for voice

### Docker
- `docker-delete-images-search` - Clean up dangling images
- `docker-delete-nonlatest` - Remove non-latest images
- `docker-start-attach` - Start and attach to containers

### Additional Features
- Platform detection (Arch Linux, KDE, Flatpak)
- YAML to Bash array conversion
- Python-style string to array conversion
- Comprehensive alias collection

## Python Environment

The `pyproject.toml` in the repository root defines a comprehensive development environment suitable for data science, automation, and general development. The Python package `useful_shell_scripts/` contains minimal source code for testing and validation utilities.

### Core Dependencies

**Data Science:**
- pandas, numpy, scipy, scikit-learn
- matplotlib, plotly

**Audio Processing:**
- pydub, pyaudioanalysis, edge-tts, eyed3

**Automation:**
- pyautogui, keyboard, pynput, selenium

**Security:**
- cryptography, pycryptomator, pykeepass

**File Handling:**
- openpyxl, pillow, bitmath

**Development:**
- black, pydantic, tqdm

### Setup

```bash
# Install with uv (recommended)
uv sync
source .venv/bin/activate
```

### Custom Git Dependencies

The environment includes several custom packages from the author's GitHub:
- keepass-wrapper
- python-package-template
- mount-encrypted-filesystem
- backup-keepass-unlock
- scheduler-run
- timetracker-utils

## Requirements

### System Requirements
- Bash shell
- Linux/Unix-like operating system (some features are Arch Linux-specific)
- `git` for git-related scripts
- `xclip` for clipboard functionality (git2markdown.sh)
- `yq` for bookmark aliases (optional, but recommended)

### Python Requirements
- Python >=3.13
- `uv` package manager (recommended)

## License

MIT License - See LICENSE file for details

## Contributing

This is a personal utility collection. Feel free to fork and adapt for your own needs.

## Use Cases

This repository is valuable for:
- Developers seeking bash productivity enhancements
- System administrators needing process management tools
- Git users wanting automation scripts
- Arch Linux users specifically
- People needing to extract/copy git-tracked files cleanly
- Those needing audio conversion utilities
- Anyone wanting a comprehensive Python development environment