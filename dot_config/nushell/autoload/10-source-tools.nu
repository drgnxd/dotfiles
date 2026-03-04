# Integrations consumer (source-only)
#
# Plan B (Nix-built, deterministic):
#   starship, zoxide, atuin — init scripts generated at nix-build time
#   and deployed to ~/.config/nushell/generated/*.nu
#
# Plan A (runtime hash sync):
#   carapace — requires $HOME access, cached at runtime
#   via modules/integrations.nu → integrations-cache-update

# Load order guards: abort early if dependencies are missing
require-loaded "integrations-cache-update" "06-integrations.nu"
require-loaded "task_preview_enable" "08-taskwarrior.nu"

# Plan B: Nix-managed init scripts (read-only, always up-to-date after rebuild)
const starship_file = ($nu.home-dir | path join ".config" "nushell" "generated" "starship.nu")
const zoxide_file = ($nu.home-dir | path join ".config" "nushell" "generated" "zoxide.nu")
const atuin_file = ($nu.home-dir | path join ".config" "nushell" "generated" "atuin.nu")

# Plan A: runtime-cached init script
const carapace_file = ($nu.home-dir | path join ".cache" "nushell-init" "carapace.nu")

# DIRENV
if (has-cmd direnv) {
    let envrc_file = (do {
        let direnv_file = ($env | get -o DIRENV_FILE | default "")
        if ($direnv_file | is-not-empty) and ($direnv_file | path exists) {
            $direnv_file
        } else {
            mut dir = ($env | get -o PWD | default $nu.home-dir | path expand)
            mut found = null
            loop {
                let candidate = ($dir | path join ".envrc")
                if ($candidate | path exists) {
                    $found = $candidate
                    break
                }
                let parent = ($dir | path dirname)
                if $parent == $dir {
                    break
                }
                $dir = $parent
            }
            $found
        }
    })

    if $envrc_file != null {
        let direnv_init = (do { direnv export json } | complete)
        if ($direnv_init.exit_code == 0) {
            let direnv_json = ($direnv_init.stdout | from json)
            if ($direnv_json | is-not-empty) {
                $direnv_json | load-env
            }
        }
    }
}

# Refresh carapace cache (Plan A only — Plan B tools need no runtime work)
integrations-cache-update

# STARSHIP PROMPT
if (has-cmd starship) {
    if ($starship_file | path exists) {
        source $starship_file
    }
}

# ZOXIDE
if ((has-cmd zoxide) and ($zoxide_file | path exists)) {
    source $zoxide_file
}

# CARAPACE
if ((has-cmd carapace) and ($carapace_file | path exists)) {
    source $carapace_file
}

# ATUIN
if (has-cmd atuin) {
    if ($atuin_file | path exists) {
        source $atuin_file
    }
}

# Taskwarrior preview (wraps right prompt after prompt tools load)
task_preview_enable
