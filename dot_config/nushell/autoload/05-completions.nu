# Completions Module
# Dynamic command completions

# Docker containers
def docker-containers [] {
    if (which docker | is-not-empty) {
        ^docker ps -a --format "{{.Names}}" | lines
    } else {
        []
    }
}

export extern "docker" [
    command?: string@docker-containers
]

# Chezmoi managed files
def chezmoi-files [] {
    if (which chezmoi | is-not-empty) {
        ^chezmoi managed | lines
    } else {
        []
    }
}

export extern "chezmoi edit" [
    file?: string@chezmoi-files
]

export extern "chezmoi cat" [
    file?: string@chezmoi-files
]

# Brew packages
def brew-packages [] {
    if (which brew | is-not-empty) {
        ^brew list --formula | lines
    } else {
        []
    }
}

export extern "brew uninstall" [
    package?: string@brew-packages
]

export extern "brew info" [
    package?: string@brew-packages
]
