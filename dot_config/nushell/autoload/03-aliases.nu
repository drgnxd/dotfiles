# Aliases Module
# Modern command replacements and shortcuts

# =============================================================================
# MODERN CORE COMMANDS (with fallbacks)
# =============================================================================

# ls -> eza (with icons and git status)
export def ls [...args] {
    if (has-cmd eza) {
        eza --icons --git ...$args
    } else {
        ^ls ...$args
    }
}

export def ll [...args] {
    if (has-cmd eza) {
        eza --icons --git -l ...$args
    } else {
        ^ls -l ...$args
    }
}

export def la [...args] {
    if (has-cmd eza) {
        eza --icons --git -la ...$args
    } else {
        ^ls -la ...$args
    }
}

export def lt [...args] {
    if (has-cmd eza) {
        eza --icons --git --tree ...$args
    } else {
        ^ls -R ...$args
    }
}

# grep -> ripgrep
export def g [...args] {
    if (has-cmd rg) {
        rg ...$args
    } else {
        ^grep ...$args
    }
}

# find -> fd
export def f [...args] {
    if (has-cmd fd) {
        fd ...$args
    } else {
        ^find ...$args
    }
}

# cat -> bat
export def cat [...args] {
    if (has-cmd bat) {
        bat --paging=never ...$args
    } else {
        ^cat ...$args
    }
}

# =============================================================================
# APPLICATION SHORTCUTS
# =============================================================================

# LazyGit
export def lg [...args] {
    if (has-cmd lazygit) {
        lazygit ...$args
    } else {
        error make { msg: "lazygit not found" }
    }
}

# opencode
export def oc [...args] {
    if (has-cmd opencode) {
        opencode ...$args
    } else {
        error make { msg: "opencode not found" }
    }
}

export def ocd [...args] {
    if (has-cmd opencode) {
        opencode --continue ...$args
    } else {
        error make { msg: "opencode not found" }
    }
}

# Chezmoi
export def c [...args] {
    if (has-cmd chezmoi) {
        if (($args | length) > 0) and (($args | get 0) == "cd") {
            cd (chezmoi source-path)
        } else {
            chezmoi ...$args
        }
    } else {
        error make { msg: "chezmoi not found" }
    }
}

export def ca [...args] {
    if (has-cmd chezmoi) {
        chezmoi apply ...$args
    } else {
        error make { msg: "chezmoi not found" }
    }
}

export def ce [...args] {
    if (has-cmd chezmoi) {
        chezmoi edit ...$args
    } else {
        error make { msg: "chezmoi not found" }
    }
}

# Proton Pass
export def pload [...args] {
    if (has-cmd pass-cli) {
        pass-cli ssh-agent load ...$args
    } else {
        error make { msg: "pass-cli not found" }
    }
}
