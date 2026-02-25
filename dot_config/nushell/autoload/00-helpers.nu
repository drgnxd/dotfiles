# Helper functions for Nushell modules

export def has-cmd [cmd: string] {
    (which $cmd | is-not-empty)
}

export def require-cmd [cmd: string] {
    if not (has-cmd $cmd) {
        error make { msg: $"($cmd) not found" }
    }
}

# Assert that a command is in scope (for load-order guards)
export def require-loaded [name: string, source: string] {
    if (scope commands | where name == $name | is-empty) {
        error make { msg: $"'($name)' not found. ($source) must be loaded first. Check config.nu source ordering." }
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
