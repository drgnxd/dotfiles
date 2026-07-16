# Nix-managed integrations consumer (source-only)
#
# requires: 00-helpers
#
# Starship, zoxide, and atuin init scripts are generated at nix-build time
# and deployed to ~/.config/nushell/generated/*.nu. Carapace completion is
# configured directly in config.nu and has no runtime init cache.

# Plan B: Nix-managed init scripts (read-only, always up-to-date after rebuild)
const starship_file = ($nu.home-dir | path join ".config" "nushell" "generated" "starship.nu")
const zoxide_file = ($nu.home-dir | path join ".config" "nushell" "generated" "zoxide.nu")
const atuin_file = ($nu.home-dir | path join ".config" "nushell" "generated" "atuin.nu")

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

# ATUIN
if (has-cmd atuin) {
    if ($atuin_file | path exists) {
        source $atuin_file
    }
}

def --env direnv-sync [] {
    let direnv_out = (do { ^direnv export json } | complete)
    if $direnv_out.exit_code == 0 {
        hide-env --ignore-errors DIRENV_BLOCKED
        if ($direnv_out.stdout | is-not-empty) {
            let env_changes = ($direnv_out.stdout | from json)
            let clears_direnv_dir = (
                ($env_changes | columns | any { |column| $column == "DIRENV_DIR" })
                and (($env_changes | get -o DIRENV_DIR) == null)
            )
            if $clears_direnv_dir {
                hide-env --ignore-errors DIRENV_DIR
            }
            let applicable_changes = if $clears_direnv_dir {
                $env_changes | reject -o DIRENV_DIR
            } else {
                $env_changes
            }
            if ($applicable_changes | is-not-empty) {
                $applicable_changes | load-env
            }
        } else if $env.DIRENV_DIR? == null {
            hide-env --ignore-errors DIRENV_DIR
        }
    } else {
        let direnv_status = (do { ^direnv status --json } | complete)
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
}

# DIRENV (hooks into PWD change for automatic env loading)
if (which --all direnv | any { |entry| $entry.type == "external" }) {
    $env.config = ($env.config | upsert hooks.env_change.PWD {|config|
        [ {|| direnv-sync } ]
    })
}

# Refresh immediately after approval without moving direnv onto the prompt path.
export def --env --wrapped direnv [...args] {
    ^direnv ...$args
    let exit_code = $env.LAST_EXIT_CODE
    let action = ($args | get -o 0 | default "")
    if ($exit_code == 0) and ($action == "allow") {
        direnv-sync
    }
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
