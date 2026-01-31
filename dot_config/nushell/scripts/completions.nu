# Nushell custom completions module
# Per-command completion definitions

# ------------------------------------------------------------------------------
# Docker Container Completions
# ------------------------------------------------------------------------------
export extern "docker" [
    command?: string@docker-containers
]

def docker-containers [] {
    if (which docker | is-not-empty) {
        ^docker ps -a --format '{{.Names}}' | lines
    } else {
        []
    }
}

# ------------------------------------------------------------------------------
# Chezmoi Managed Files Completions
# ------------------------------------------------------------------------------
export extern "chezmoi edit" [
    file?: string@chezmoi-files
]

export extern "chezmoi cat" [
    file?: string@chezmoi-files
]

def chezmoi-files [] {
    if (which chezmoi | is-not-empty) {
        ^chezmoi managed | lines
    } else {
        []
    }
}

# ------------------------------------------------------------------------------
# Brew Installed Packages Completions
# ------------------------------------------------------------------------------
export extern "brew uninstall" [
    package?: string@brew-packages
]

export extern "brew info" [
    package?: string@brew-packages
]

def brew-packages [] {
    if (which brew | is-not-empty) {
        ^brew list --formula | lines
    } else {
        []
    }
}
