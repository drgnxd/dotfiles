# Constants Module
# Centralized XDG base directories

def xdg-dirs [] {
    {
        config: ($env.HOME | path join ".config")
        cache: ($env.HOME | path join ".cache")
        data: ($env.HOME | path join ".local" "share")
        state: ($env.HOME | path join ".local" "state")
    }
}
