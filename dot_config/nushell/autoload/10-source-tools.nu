# Integrations consumer (source-only)
#
# requires: 00-helpers, 06-integrations
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

# Plan B: Nix-managed init scripts (read-only, always up-to-date after rebuild)
const starship_file = ($nu.home-dir | path join ".config" "nushell" "generated" "starship.nu")
const zoxide_file = ($nu.home-dir | path join ".config" "nushell" "generated" "zoxide.nu")
const atuin_file = ($nu.home-dir | path join ".config" "nushell" "generated" "atuin.nu")

# Plan A: runtime-cached init script
const carapace_file = ($nu.home-dir | path join ".cache" "nushell-init" "carapace.nu")

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

# DIRENV (hooks into PWD change for automatic env loading)
if (has-cmd direnv) {
    $env.config = ($env.config | upsert hooks.env_change.PWD {|config|
        [ {||
            let direnv_out = (do { direnv export json } | complete)
            if $direnv_out.exit_code == 0 {
                hide-env --ignore-errors DIRENV_BLOCKED
                if ($direnv_out.stdout | is-not-empty) {
                    let env_changes = ($direnv_out.stdout | from json)
                    if ($env_changes | is-not-empty) {
                        $env_changes | load-env
                    }
                }
            } else {
                let direnv_status = (do { direnv status --json } | complete)
                let found_rc = if ($direnv_status.exit_code == 0) and ($direnv_status.stdout | is-not-empty) {
                    try {
                        $direnv_status.stdout | from json | get -o state.foundRC
                    } catch {
                        null
                    }
                } else {
                    null
                }

                # direnv 2.37 reports foundRC.allowed as 0 when allowed.
                if ($found_rc != null) and (($found_rc.allowed? | default 0) != 0) {
                    # Blocked exports still contain cleanup changes. Apply them
                    # without DIRENV_DIR so stale environments do not look loaded.
                    hide-env --ignore-errors DIRENV_DIR
                    if ($direnv_out.stdout | is-not-empty) {
                        let env_changes = ($direnv_out.stdout | from json | reject -o DIRENV_DIR)
                        if ($env_changes | is-not-empty) {
                            $env_changes | load-env
                        }
                    }
                    load-env { DIRENV_BLOCKED: "!" }
                } else {
                    hide-env --ignore-errors DIRENV_BLOCKED
                }
            }
        } ]
    })
}

# PASS SSH-AGENT INDICATOR (anomaly-only)
# Sets PASS_AGENT_DOWN when $env.SSH_AUTH_SOCK is unset or its socket file
# is missing; starship renders it via ${env_var.PASS_AGENT_DOWN}.
# Socket existence is a liveness proxy: a stale socket (process died, file
# left behind) is NOT detected. `path exists` is a builtin stat call — no
# subprocess is spawned, keeping the prompt's zero-spawn budget intact.
$env.config = ($env.config | upsert hooks.pre_prompt {|config|
    ($config | get -o hooks.pre_prompt | default []) ++ [
        {||
            let sock = ($env.SSH_AUTH_SOCK? | default "")
            if ($sock | is-empty) or (not ($sock | path exists)) {
                load-env { PASS_AGENT_DOWN: "✗" }
            } else {
                hide-env --ignore-errors PASS_AGENT_DOWN
            }
        }
    ]
})
