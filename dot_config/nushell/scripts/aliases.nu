# Nushell aliases module
# Legacy mapping from .aliases (Zsh)

# Helper function to check if command exists
def has-cmd [cmd: string] {
    (which $cmd | is-not-empty)
}

# ------------------------------------------------------------------------------
# Modernized Core Commands (conditionally defined using def)
# ------------------------------------------------------------------------------

# ls -> eza (icons, git status, tree, grouping)
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

# grep -> rg
export def g [...args] {
    if (has-cmd rg) {
        rg ...$args
    } else {
        ^grep ...$args
    }
}

# fd (find replacement)
export def f [...args] {
    if (has-cmd fd) {
        fd ...$args
    } else {
        ^find ...$args
    }
}

# bat (cat replacement)
export def cat [...args] {
    if (has-cmd bat) {
        bat --paging=never ...$args
    } else {
        ^cat ...$args
    }
}

# ------------------------------------------------------------------------------
# Application Shortcuts (conditionally defined using def)
# ------------------------------------------------------------------------------

# LazyGit
export def lg [...args] {
    if (has-cmd lazygit) {
        lazygit ...$args
    } else {
        error make { msg: "lazygit is not installed" }
    }
}

# opencode
export def oc [...args] {
    if (has-cmd opencode) {
        opencode ...$args
    } else {
        error make { msg: "opencode is not installed" }
    }
}

export def ocd [...args] {
    if (has-cmd opencode) {
        opencode --continue ...$args
    } else {
        error make { msg: "opencode is not installed" }
    }
}

# chezmoi
export def c [...args] {
    if (has-cmd chezmoi) {
        chezmoi ...$args
    } else {
        error make { msg: "chezmoi is not installed" }
    }
}

export def ca [...args] {
    if (has-cmd chezmoi) {
        chezmoi apply ...$args
    } else {
        error make { msg: "chezmoi is not installed" }
    }
}

export def ce [...args] {
    if (has-cmd chezmoi) {
        chezmoi edit ...$args
    } else {
        error make { msg: "chezmoi is not installed" }
    }
}

# ------------------------------------------------------------------------------
# Proton Pass
# ------------------------------------------------------------------------------
export def pload [...args] {
    pass-cli ssh-agent load ...$args
}

# ------------------------------------------------------------------------------
# Lima Quick Aliases
# ------------------------------------------------------------------------------
export def lls [...args] {
    lima-status ...$args
}

export def dctx [...args] {
    docker-ctx ...$args
}

export def dctx-reset [...args] {
    docker-ctx-reset ...$args
}
