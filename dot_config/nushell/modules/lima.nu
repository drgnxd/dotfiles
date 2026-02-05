# Lima and Docker management (lazy-loaded)

def lima_has_cmd [cmd: string] {
    (which $cmd | is-not-empty)
}

def lima_require_cmd [cmd: string] {
    if not (lima_has_cmd $cmd) {
        error make { msg: $"($cmd) not found" }
    }
}

export def lima_start [vm_name: string] {
    lima_require_cmd "limactl"

    print $"Starting Lima VM: ($vm_name)..."
    ^limactl start $vm_name
    if ($env.LAST_EXIT_CODE != 0) {
        print --stderr $"Error: Failed to start VM '($vm_name)'"
        return 1
    }

    let ctx_name = $"($vm_name)-context"
    if (lima_has_cmd "docker") {
        let ctx_check = (do { docker context inspect $ctx_name } | complete)
        if ($ctx_check.exit_code == 0) {
            print $"Switching to Docker context: ($ctx_name)"
            docker context use $ctx_name
        } else {
            print $"Note: Docker context '($ctx_name)' not found. Use 'lima-docker-context ($vm_name)' to create it."
        }
    } else {
        print "Note: Docker not found; skipping context switch."
    }
}

export def lima_stop [vm_name: string] {
    lima_require_cmd "limactl"

    print $"Stopping Lima VM: ($vm_name)..."
    ^limactl stop $vm_name
}

export def lima_status [] {
    lima_require_cmd "limactl"

    ^limactl list
}

export def lima_shell [vm_name: string] {
    lima_require_cmd "limactl"

    ^limactl shell $vm_name
}

export def lima_delete [
    vm_name: string
    --force(-f)
] {
    lima_require_cmd "limactl"

    if not $force {
        print $"Warning: This will permanently delete VM '($vm_name)' and all its data."
        let confirm = (input "Are you sure? (yes/no): ")
        if $confirm != "yes" {
            print "Deletion cancelled."
            return 0
        }
    }

    ^limactl delete $vm_name
}

export def docker_ctx [ctx?: string] {
    lima_require_cmd "docker"

    if ($ctx | is-empty) {
        print "Current Docker contexts:"
        docker context ls
    } else {
        docker context use $ctx
    }
}

export def docker_ctx_reset [] {
    lima_require_cmd "docker"

    docker context use default
}

export def lima_docker_context [vm_name: string] {
    lima_require_cmd "docker"

    let ctx_name = $"($vm_name)-context"
    let socket_path = ($env.LIMA_HOME | path join $vm_name "sock" "docker.sock")

    if not ($socket_path | path exists) {
        print --stderr $"Warning: Docker socket not found at: ($socket_path)"
        print --stderr "Make sure the VM is running and has Docker enabled."
        return 1
    }

    let ctx_check = (do { docker context inspect $ctx_name } | complete)
    if ($ctx_check.exit_code == 0) {
        print $"Updating existing Docker context: ($ctx_name)"
        docker context update $ctx_name --docker $"host=unix://($socket_path)"
    } else {
        print $"Creating new Docker context: ($ctx_name)"
        docker context create $ctx_name --docker $"host=unix://($socket_path)"
    }

    print $"Docker context '($ctx_name)' is ready."
    print $"Switch to it with: docker-ctx ($ctx_name)"
}
