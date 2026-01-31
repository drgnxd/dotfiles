# Nushell functions module
# Equivalent to .functions in zsh

# ------------------------------------------------------------------------------
# Yazi Wrapper (follows cwd)
# Launch with 'y'; stay in last visited directory on exit
# ------------------------------------------------------------------------------
export def yazi-wrapper [...args: string] {
    let tmp_file = (mktemp -t "yazi-cwd.XXXXXX")
    yazi ...$args --cwd-file=$tmp_file
    
    let cwd = (open $tmp_file | str trim)
    if ($cwd | is-not-empty) and ($cwd != $env.PWD) {
        cd $cwd
    }
    
    rm -f $tmp_file
}

# Alias for the wrapper
export alias y = yazi-wrapper

# ------------------------------------------------------------------------------
# ZK Wrapper with Git Sync
# ------------------------------------------------------------------------------
export def zk-sync [] {
    let notebook_dir = ($env | get ZK_NOTEBOOK_DIR?)
    if ($notebook_dir | is-empty) {
        print --stderr "ZK_NOTEBOOK_DIR is not set"
        return 1
    }
    
    if not ($notebook_dir | path exists) {
        print --stderr $"Failed to enter ZK_NOTEBOOK_DIR: ($notebook_dir)"
        return 1
    }
    
    let git_check = (do { git -C $notebook_dir rev-parse --is-inside-work-tree } | complete)
    if ($git_check.exit_code != 0) {
        print --stderr $"Not a git repository: ($notebook_dir)"
        return 1
    }
    
    let status_check = (do { git -C $notebook_dir status --porcelain } | complete)
    if ($status_check.stdout | is-empty) {
        print "No changes to sync"
        return 0
    }
    
    git -C $notebook_dir add .
    
    let diff_check = (do { git -C $notebook_dir diff --cached --quiet } | complete)
    if ($diff_check.exit_code != 0) {
        let commit_msg = $"Update zettel: (date now | format date '%Y-%m-%d %H:%M')"
        git -C $notebook_dir commit -m $commit_msg
        if ($env.LAST_EXIT_CODE != 0) {
            print --stderr "Commit failed"
            return 1
        }
    }
    
    let remote_check = (do { git -C $notebook_dir remote get-url origin } | complete)
    if ($remote_check.exit_code == 0) {
        git -C $notebook_dir push origin main
    } else {
        print --stderr "Remote 'origin' not found; skipping push"
    }
}

export def zk [...args: string] {
    if ($args | is-empty) {
        ^zk
    } else if ($args | get 0) == "sync" {
        zk-sync
    } else {
        ^zk ...$args
    }
}

# ------------------------------------------------------------------------------
# Export Stats Preference Plist to XML
# ------------------------------------------------------------------------------
export def save-stats [] {
    let src = ($env.HOME | path join "Library" "Preferences" "eu.exelban.Stats.plist")
    let dest = ($env.HOME | path join ".local" "share" "chezmoi" "dot_config" "stats" "eu.exelban.Stats.plist")
    
    if not ($src | path exists) {
        print --stderr $"Stats plist not found at ($src)"
        return 1
    }
    
    print "Exporting Stats config to XML..."
    let result = (do { plutil -convert xml1 $src -o $dest } | complete)
    if ($result.exit_code != 0) {
        print --stderr "Failed to convert Stats plist"
        return 1
    }
    
    print $"Saved to ($dest)"
}

# ------------------------------------------------------------------------------
# Proton Pass Wrapper
# ------------------------------------------------------------------------------
export def ppget [
    query: string
    --field: string = "password"
] {
    let json_parser = if (which jq | is-not-empty) {
        "jq"
    } else if (which jaq | is-not-empty) {
        "jaq"
    } else {
        print --stderr "Error: jq or jaq is required."
        return 127
    }
    
    if (which pass-cli | is-empty) {
        print --stderr "Error: pass-cli not found."
        return 127
    }
    
    let search_result = (do { pass-cli search $query --json } | complete)
    if ($search_result.exit_code != 0) {
        print --stderr $"Error: Secret '($query)' not found."
        return 1
    }
    
    let item_id = ($search_result.stdout | from json | get 0.id?)
    if ($item_id | is-empty) or ($item_id == null) {
        print --stderr $"Error: Secret '($query)' not found."
        return 1
    }
    
    pass-cli get $item_id --field $field --output text
}

# ------------------------------------------------------------------------------
# Taskwarrior Wrapper and Cache Management
# ------------------------------------------------------------------------------
export def task-wrapper [...args: string] {
    ^task ...$args
    let ret = $env.LAST_EXIT_CODE
    
    do { task-cache-update } | ignore
    
    return $ret
}

export def task-cache-update [] {
    let cache_dir = ($env.XDG_CACHE_HOME | path join "taskwarrior")
    let update_script = ($env.XDG_CONFIG_HOME | path join "taskwarrior" "hooks" "update_cache.py")
    
    if not ($cache_dir | path exists) {
        mkdir $cache_dir
    }
    
    if not ($update_script | path exists) {
        return
    }
    
    do { python3 $update_script --update-only } | ignore
    task-cache-load
}

export def task-cache-load [] {
    let cache_dir = ($env.XDG_CACHE_HOME | path join "taskwarrior")
    let ids_file = ($cache_dir | path join "ids.list")
    let desc_file = ($cache_dir | path join "desc.list")
    
    if ($ids_file | path exists) {
        let ids = (open $ids_file | lines)
        $env.TASK_CACHE_IDS = $ids
    } else {
        $env.TASK_CACHE_IDS = []
    }
    
    if ($desc_file | path exists) {
        let desc_lines = (open $desc_file | lines)
        mut task_map = {}
        for line in $desc_lines {
            let parts = ($line | split row ":" -n 2)
            if ($parts | length) == 2 {
                let id = ($parts | get 0)
                let desc = ($parts | get 1)
                $task_map = ($task_map | insert $id $desc)
            }
        }
        $env.TASK_CACHE_MAP = $task_map
    } else {
        $env.TASK_CACHE_MAP = {}
    }
}

export-env {
    task-cache-load
}

export alias t = task-wrapper

# ------------------------------------------------------------------------------
# Unified Upgrade Function
# ------------------------------------------------------------------------------
export def upgrade-all [] {
    if (which brew | is-empty) {
        print --stderr "Homebrew not found; aborting unified upgrade"
        return 127
    }
    
    print "--- Homebrew Formulae ---"
    brew update
    if ($env.LAST_EXIT_CODE != 0) { return 1 }
    
    brew upgrade
    if ($env.LAST_EXIT_CODE != 0) { return 1 }
    
    print "--- Homebrew Casks ---"
    let tap_check = (do { brew tap-info buo/cask-upgrade } | complete)
    if ($tap_check.exit_code == 0) {
        brew cu --all --cleanup --yes
        if ($env.LAST_EXIT_CODE != 0) { return 1 }
    } else {
        print --stderr "Install buo/cask-upgrade to manage casks: brew tap buo/cask-upgrade"
    }
    
    print "--- Mac App Store ---"
    if (which mas | is-not-empty) {
        mas upgrade
        if ($env.LAST_EXIT_CODE != 0) { return 1 }
    } else {
        print --stderr "Install mas for App Store apps: brew install mas"
    }
    
    print "--- Cleanup ---"
    brew cleanup
}

# ------------------------------------------------------------------------------
# Bundle ID Helper for macOS Apps
# ------------------------------------------------------------------------------
export def bundle-id [app_path: string] {
    if not ($app_path | path exists) {
        print --stderr $"App bundle not found: ($app_path)"
        return 1
    }
    
    /usr/bin/mdls -name kMDItemCFBundleIdentifier -raw $app_path
}

export alias update = upgrade-all
