# Darwin Setup Scripts

This directory contains macOS-specific setup and configuration scripts.

## Overview

The scripts in this directory are orchestrated by `run_onchange_after_setup.sh.tmpl` in the repository root. They handle system configuration, security hardening, keyboard settings, and application setup.

## Script Organization

### Regular Scripts (`.sh`)
Scripts without template logic, executed directly:
- `audit_security.sh` - Audit macOS security settings
- `keyboard.sh` - Configure keyboard repeat rates and Fn key behavior
- `login_items.sh` - Manage Login Items (applications launched at login)
- `menubar.sh` - Configure Menu Bar and Control Center items
- `security_hardening.sh` - Apply security hardening settings
- `system_defaults.sh` - Set macOS system defaults (Finder, Dock, etc.)

### Template Scripts (`.sh.tmpl`)
Scripts containing chezmoi template logic, rendered at runtime:
- `import_stats.sh.tmpl` - Import Stats app configuration
- `install_packages.sh.tmpl` - Install Homebrew packages via Brewfile
- `setup_cloud_symlinks.sh.tmpl` - Create symlinks to cloud storage directories

## Guard Flags

Several scripts require explicit environment variables to prevent accidental execution:

| Flag | Script | Purpose |
|------|--------|---------|
| `ALLOW_DEFAULTS=1` | `system_defaults.sh` | Modify macOS defaults (Finder, Dock, etc.) |
| `ALLOW_HARDEN=1` | `security_hardening.sh` | Apply security hardening settings |
| `ALLOW_GUI=1` | `login_items.sh` | Modify GUI Login Items |
| `ALLOW_KEYBOARD_APPLY=1` | `keyboard.sh` | Apply keyboard settings (use `--apply` flag) |
| `FORCE=1` | `setup_cloud_symlinks.sh.tmpl` | Overwrite existing symlinks |

### Optional Guard Flags

| Flag | Script | Purpose |
|------|--------|---------|
| `ALLOW_LSQUARANTINE_OFF=1` | `system_defaults.sh` | Disable Gatekeeper quarantine warnings |
| `ALLOW_SPOTLIGHT_DISABLE=1` | `system_defaults.sh` | Disable Spotlight keyboard shortcuts |

## System Defaults Profile

`system_defaults.sh` applies a developer-friendly defaults profile:

- Language/region: English UI (Japan), locale `en_JP`, metric units, Celsius
- Date format (short): `yyyy/MM/dd`
- Text input: disable autocorrect, capitalization, smart quotes/dashes/periods
- Finder: show hidden files and POSIX path, show extensions/status/path bars
- Dock: remove autohide delay/animation, disable Spaces animation
- Screenshots: PNG, no shadow, save to `~/Desktop/Screenshots`

## Usage Examples

### Run all setup scripts
```bash
# Via chezmoi (recommended - triggers on content change)
chezmoi apply

# Or manually execute the orchestrator
bash ~/.local/share/chezmoi/run_onchange_after_setup.sh.tmpl

# Continue even if a step fails
CONTINUE_ON_ERROR=1 bash ~/.local/share/chezmoi/run_onchange_after_setup.sh.tmpl
```

### Run individual scripts
```bash
# With guard flags
ALLOW_DEFAULTS=1 bash .internal_scripts/darwin/system_defaults.sh

# Keyboard settings (preview mode)
bash .internal_scripts/darwin/keyboard.sh

# Keyboard settings (apply mode)
ALLOW_KEYBOARD_APPLY=1 bash .internal_scripts/darwin/keyboard.sh --apply

# For a different user
ALLOW_KEYBOARD_APPLY=1 bash .internal_scripts/darwin/keyboard.sh --apply --user johndoe
```

## Common Functions Library

All scripts source `../lib/common.sh` which provides:

### Logging Functions
- `log_info "message"` - Blue informational message
- `log_success "message"` - Green success message
- `log_error "message"` - Red error message
- `log_warning "message"` - Yellow warning message

### Guard Functions
- `require_flag "FLAG_NAME" "description"` - Exit if environment flag not set
- `check_command "command"` - Check if command exists in PATH

### macOS Functions
- `safe_defaults_write <args>` - Wrapper for `defaults write` with error checking
- `safe_defaults_write_current_host <args>` - Wrapper for `defaults -currentHost write`
- `quit_app "App Name"` - Quit application gracefully via osascript
- `kill_process "ProcessName"` - Kill process by name (used for System UI restarts)
- `get_console_user` - Get the current GUI console user

### Failure Tracking
- `record_failure "message"` - Record failure for batch reporting
- `report_failures` - Print summary of all recorded failures

## Strict Mode

All bash scripts use strict mode for robust error handling:
```bash
set -euo pipefail
```

- `-e`: Exit on command failure
- `-u`: Exit on undefined variable usage
- `-o pipefail`: Fail if any command in a pipeline fails

## Architecture Integration

These scripts integrate with:
- **chezmoi**: Template rendering and change detection
- **Homebrew**: Package installation via Brewfile
- **XDG Base Directory**: Compliance with `$XDG_CONFIG_HOME`, `$XDG_DATA_HOME`, etc.
- **LaunchAgents**: Application auto-start (Stats, Hammerspoon, Maccy)

## Related Documentation

- [Repository Architecture](../../ARCHITECTURE.md)
- [Common Functions](../lib/common.sh)
- [Main Setup Orchestrator](../../run_onchange_after_setup.sh.tmpl)
