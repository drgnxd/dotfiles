# Helper functions for Nushell modules

def has-cmd [cmd: string] {
    (which $cmd | is-not-empty)
}

def require-cmd [cmd: string] {
    if not (has-cmd $cmd) {
        error make { msg: $"($cmd) not found" }
    }
}
