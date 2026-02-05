# Helper functions for Nushell modules

def has-cmd [cmd: string] {
    (which $cmd | is-not-empty)
}

def require-cmd [cmd: string] {
    if not (has-cmd $cmd) {
        error make { msg: $"($cmd) not found" }
    }
}

export def cmd-or-fallback [
    primary: string,
    fallback: string,
    --primary-args: list = [],
    --fallback-args: list = [],
    ...args
] {
    if (has-cmd $primary) {
        ^$primary ...$primary_args ...$args
    } else {
        ^$fallback ...$fallback_args ...$args
    }
}
