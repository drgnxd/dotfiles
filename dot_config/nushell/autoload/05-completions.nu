# Completions Module
# Dynamic command completions

# Docker containers
def docker-containers [] {
    if (has-cmd docker) {
        ^docker ps -a --format "{{.Names}}" | lines
    } else {
        []
    }
}

export extern "docker" [
    command?: string@docker-containers
]
