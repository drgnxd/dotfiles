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
