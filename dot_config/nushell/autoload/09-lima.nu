
# Lima and Docker wrappers (lazy-loaded)

export def lima-start [vm_name: string] {
    overlay use '/Users/drgnxd/.config/nushell/modules/lima.nu'
    lima_start $vm_name
}

export def lima-stop [vm_name: string] {
    overlay use '/Users/drgnxd/.config/nushell/modules/lima.nu'
    lima_stop $vm_name
}

export def lima-status [] {
    overlay use '/Users/drgnxd/.config/nushell/modules/lima.nu'
    lima_status
}

export def lima-shell [vm_name: string] {
    overlay use '/Users/drgnxd/.config/nushell/modules/lima.nu'
    lima_shell $vm_name
}

export def lima-delete [
    vm_name: string
    --force(-f)
] {
    overlay use '/Users/drgnxd/.config/nushell/modules/lima.nu'
    if $force {
        lima_delete $vm_name --force
    } else {
        lima_delete $vm_name
    }
}

export def docker-ctx [ctx?: string] {
    overlay use '/Users/drgnxd/.config/nushell/modules/lima.nu'
    docker_ctx $ctx
}

export def docker-ctx-reset [] {
    overlay use '/Users/drgnxd/.config/nushell/modules/lima.nu'
    docker_ctx_reset
}

export def lima-docker-context [vm_name: string] {
    overlay use '/Users/drgnxd/.config/nushell/modules/lima.nu'
    lima_docker_context $vm_name
}

export alias lls = lima-status
export alias dctx = docker-ctx
export alias dctx-reset = docker-ctx-reset
