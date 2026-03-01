
# Lima and Docker wrappers (eager-loaded via config.nu → modules/lima.nu)

export def lima-start [vm_name: string] {
    lima_start $vm_name
}

export def lima-stop [vm_name: string] {
    lima_stop $vm_name
}

export def lima-status [] {
    lima_status
}

export def lima-shell [vm_name: string] {
    lima_shell $vm_name
}

export def lima-delete [
    vm_name: string
    --force(-f)
] {
    if $force {
        lima_delete $vm_name --force
    } else {
        lima_delete $vm_name
    }
}

export def docker-ctx [ctx?: string] {
    docker_ctx $ctx
}

export def docker-ctx-reset [] {
    docker_ctx_reset
}

export def lima-docker-context [vm_name: string] {
    lima_docker_context $vm_name
}

export alias lls = lima-status
export alias dctx = docker-ctx
export alias dctx-reset = docker-ctx-reset
