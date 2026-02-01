# Helper functions for Nushell modules

def has-cmd [cmd: string] {
    (which $cmd | is-not-empty)
}
