# Aliases Module
# Modern command replacements and shortcuts

# =============================================================================
# MODERN CORE COMMANDS (with fallbacks)
# =============================================================================

# ls -> eza (with icons and git status) - DISABLED
# export def ls [...args] {
#     if (has-cmd eza) {
#         eza --icons --git ...$args
#     } else {
#         ^ls ...$args
#     }
# }
#
# export def ll [...args] {
#     if (has-cmd eza) {
#         eza --icons --git -l ...$args
#     } else {
#         ^ls -l ...$args
#     }
# }
#
# export def la [...args] {
#     if (has-cmd eza) {
#         eza --icons --git -la ...$args
#     } else {
#         ^ls -la ...$args
#     }
# }
#
# export def lt [...args] {
#     if (has-cmd eza) {
#         eza --icons --git --tree ...$args
#     } else {
#         ^ls -R ...$args
#     }
# }

# grep -> ripgrep
export def --wrapped g [...args] {
    cmd-or-fallback rg grep ...$args
}

# find -> fd
export def --wrapped f [...args] {
    cmd-or-fallback fd find ...$args
}

# cat -> bat
export def --wrapped cat [...args] {
    cmd-or-fallback bat cat --primary-args ["--paging=never"] ...$args
}

# =============================================================================
# DIRECTORY NAVIGATION SHORTCUTS
# =============================================================================

# Go up directories
export alias .. = cd ..
export alias ... = cd ../..
export alias .... = cd ../../..

# Clear screen
export alias c = clear

# =============================================================================
# INTERACTIVE FILE OPERATIONS (confirm before overwrite/delete)
# =============================================================================

export def --wrapped cp [...args] {
    ^cp -i ...$args
}

export def --wrapped mv [...args] {
    ^mv -i ...$args
}

export def --wrapped rm [...args] {
    # Skip -i if -f/--force is specified to allow non-interactive removal
    if ($args | any { $in == "-f" or $in == "--force" }) {
        ^rm ...$args
    } else {
        ^rm -i ...$args
    }
}

# =============================================================================
# LS VARIANTS
# =============================================================================

# List with hidden files
export def --wrapped la [...args] {
    let paths = ($args | default [])
    if ($paths | is-empty) {
        ls -a
    } else {
        ls -a ...$paths
    }
}

# List only directories
export def --wrapped ld [...args] {
    let paths = ($args | default [])
    if ($paths | is-empty) {
        ls | where type == dir
    } else {
        ls ...$paths | where type == dir
    }
}

# List only files
export def --wrapped lf [...args] {
    let paths = ($args | default [])
    if ($paths | is-empty) {
        ls | where type == file
    } else {
        ls ...$paths | where type == file
    }
}

# List sorted by size (descending)
export def --wrapped lsize [...args] {
    let paths = ($args | default [])
    if ($paths | is-empty) {
        ls | sort-by size -r
    } else {
        ls ...$paths | sort-by size -r
    }
}

# =============================================================================
# APPLICATION SHORTCUTS
# =============================================================================

# LazyGit
export def --wrapped lg [...args] {
    require-cmd lazygit
    lazygit ...$args
}

# opencode
export def --wrapped oc [...args] {
    require-cmd opencode
    opencode ...$args
}

export def --wrapped ocd [...args] {
    require-cmd opencode
    opencode --continue ...$args
}

# Proton Pass
export def --wrapped pload [...args] {
    require-cmd pass-cli
    pass-cli ssh-agent load ...$args
}
