# Nushell Lima and Docker management module

# Helper function to check if command exists
def has-cmd [cmd: string] {
    (which $cmd | is-not-empty)
}

# Helper function to require command
def require-cmd [cmd: string] {
    if not (has-cmd $cmd) {
        print --stderr $"Error: ($cmd) not found"
        return 127
    }
}

# Helper function to require VM name argument
def require-vm [action: string vm_name?: string] {
    if ($vm_name | is-empty) {
        print $"Usage: ($action) <vm-name>"
        print $"Example: ($action) myvm"
        return 1
    }
}

# ------------------------------------------------------------------------------
# Lima VM Management
# ------------------------------------------------------------------------------

# Start Lima VM and optionally switch Docker context
export def lima-start [vm_name: string] {
    require-cmd limactl
    if ($env.LAST_EXIT_CODE != 0) { return $env.LAST_EXIT_CODE }
    
    print $"Starting Lima VM: ($vm_name)..."
    
    ^limactl start $vm_name
    if ($env.LAST_EXIT_CODE != 0) {
        print --stderr $"Error: Failed to start VM '($vm_name)'"
        return 1
    }
    
    let ctx_name = $"($vm_name)-context"
    if (has-cmd docker) {
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

# Stop Lima VM
export def lima-stop [vm_name: string] {
    require-cmd limactl
    if ($env.LAST_EXIT_CODE != 0) { return $env.LAST_EXIT_CODE }
    
    print $"Stopping Lima VM: ($vm_name)..."
    ^limactl stop $vm_name
}

# List all Lima VMs
export def lima-status [] {
    require-cmd limactl
    if ($env.LAST_EXIT_CODE != 0) { return $env.LAST_EXIT_CODE }
    
    ^limactl list
}

# Open shell in Lima VM
export def lima-shell [vm_name: string] {
    require-cmd limactl
    if ($env.LAST_EXIT_CODE != 0) { return $env.LAST_EXIT_CODE }
    
    ^limactl shell $vm_name
}

# Delete Lima VM
export def lima-delete [
    vm_name: string
    --force(-f)
] {
    require-cmd limactl
    if ($env.LAST_EXIT_CODE != 0) { return $env.LAST_EXIT_CODE }
    
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

# ------------------------------------------------------------------------------
# Docker Context Management
# ------------------------------------------------------------------------------

# List or switch Docker context
export def docker-ctx [ctx?: string] {
    require-cmd docker
    if ($env.LAST_EXIT_CODE != 0) { return $env.LAST_EXIT_CODE }
    
    if ($ctx | is-empty) {
        print "Current Docker contexts:"
        docker context ls
    } else {
        docker context use $ctx
    }
}

# Reset Docker context to default
export def docker-ctx-reset [] {
    require-cmd docker
    if ($env.LAST_EXIT_CODE != 0) { return $env.LAST_EXIT_CODE }
    
    docker context use default
}

# Create or update Docker context for Lima VM
export def lima-docker-context [vm_name: string] {
    require-cmd docker
    if ($env.LAST_EXIT_CODE != 0) { return $env.LAST_EXIT_CODE }
    
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

# ------------------------------------------------------------------------------
# Quick Aliases
# ------------------------------------------------------------------------------
export alias lls = lima-status
export alias dctx = docker-ctx
export alias dctx-reset = docker-ctx-reset
