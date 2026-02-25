# Custom Functions Module
# Advanced wrappers and utilities

# YAZI FILE MANAGER
export def --wrapped y [...args] {
    let tmp_file = (mktemp -t "yazi-cwd.XXXXXX")
    yazi ...$args --cwd-file=$tmp_file
    let cwd = (open $tmp_file | str trim)
    if ($cwd | is-not-empty) and ($cwd != $env.PWD) {
        cd $cwd
    }
    ^rm -f $tmp_file
}

# ZK WITH GIT SYNC
export def zk-sync [] {
    let notebook_dir = ($env | get ZK_NOTEBOOK_DIR?)
    if ($notebook_dir | is-empty) {
        error make { msg: "ZK_NOTEBOOK_DIR is not set" }
    }
    if not ($notebook_dir | path exists) {
        error make { msg: $"Failed to enter ZK_NOTEBOOK_DIR: ($notebook_dir)" }
    }
    let git_check = (do { git -C $notebook_dir rev-parse --is-inside-work-tree } | complete)
    if ($git_check.exit_code != 0) {
        error make { msg: $"Not a git repository: ($notebook_dir)" }
    }
    let status_check = (do { git -C $notebook_dir status --porcelain } | complete)
    if ($status_check.stdout | is-empty) {
        print "No changes to sync"
        return
    }
    git -C $notebook_dir add .
    let diff_check = (do { git -C $notebook_dir diff --cached --quiet } | complete)
    if ($diff_check.exit_code != 0) {
        let commit_msg = $"Update zettel: (date now | format date '%Y-%m-%d %H:%M')"
        let commit_result = (do { git -C $notebook_dir commit -m $commit_msg } | complete)
        if ($commit_result.exit_code != 0) {
            error make { msg: $"Commit failed: ($commit_result.stderr)" }
        }
    }
    let remote_check = (do { git -C $notebook_dir remote get-url origin } | complete)
    if ($remote_check.exit_code == 0) {
        git -C $notebook_dir push origin main
    } else {
        print --stderr "Remote 'origin' not found; skipping push"
    }
}

export def --wrapped zk [...args] {
    if ($args | is-empty) {
        ^zk
    } else if ($args | get 0) == "sync" {
        zk-sync
    } else {
        ^zk ...$args
    }
}

# STATS CONFIG EXPORT
export def save-stats [] {
    let src = ($env.HOME | path join "Library" "Preferences" "eu.exelban.Stats.plist")
    let dotfiles_dir = ($env | get -o DOTFILES_DIR | default ($env.HOME | path join ".config" "nix-config"))
    let dest = ($dotfiles_dir | path join "dot_config" "stats" "eu.exelban.Stats.plist")
    if not ($src | path exists) {
        error make { msg: $"Stats plist not found at ($src)" }
    }
    print "Exporting Stats config to XML..."
    let result = (do { plutil -convert xml1 $src -o $dest } | complete)
    if ($result.exit_code != 0) {
        error make { msg: $"Failed to convert Stats plist: ($result.stderr)" }
    }
    print $"Saved to ($dest)"
}

# PROTON PASS CLI
export def ppget [query: string, --field: string = "password"] {
    require-cmd pass-cli
    let search_result = (do { pass-cli search $query --json } | complete)
    if ($search_result.exit_code != 0) {
        error make { msg: $"Secret '($query)' not found" }
    }
    let item_id = ($search_result.stdout | from json | get 0.id?)
    if ($item_id | is-empty) or ($item_id == null) {
        error make { msg: $"Secret '($query)' not found" }
    }
    pass-cli get $item_id --field $field --output text
}

# SYSTEM UPGRADE (split into composable steps)

# Nix flake update + system rebuild
export def upgrade-nix [] {
    require-cmd nix

    let dotfiles_dir = ($env | get -o DOTFILES_DIR | default ($env.HOME | path join ".config" "nix-config"))
    if not ($dotfiles_dir | path exists) {
        error make { msg: $"Dotfiles directory not found: ($dotfiles_dir)" }
    }

    let target = ($env | get -o DOTFILES_FLAKE_TARGET | default "")
    let fallback_target = ($env | get -o USER | default "default")
    let target_name = if ($target | is-empty) { $fallback_target } else { $target }
    let flake_ref = $"($dotfiles_dir)#($target_name)"

    print "--- Nix flake update ---"
    let update_result = (do { nix flake update $dotfiles_dir } | complete)
    if ($update_result.exit_code != 0) {
        error make { msg: $"nix flake update failed: ($update_result.stderr)" }
    }

    if (has-cmd darwin-rebuild) {
        print "--- darwin-rebuild ---"
        darwin-rebuild switch --flake $flake_ref
    } else if (has-cmd home-manager) {
        print "--- home-manager ---"
        home-manager switch --flake $flake_ref
    } else {
        error make { msg: "Neither darwin-rebuild nor home-manager found" }
    }
}

# Mac App Store upgrade
export def upgrade-mac-apps [] {
    require-cmd mas
    print "--- Mac App Store ---"
    let result = (do { mas upgrade } | complete)
    if ($result.exit_code != 0) {
        error make { msg: $"mas upgrade failed: ($result.stderr)" }
    }
}

# Full system upgrade (orchestrator)
export def upgrade-all [] {
    upgrade-nix

    if (has-cmd mas) {
        upgrade-mac-apps
    }
}

export alias update = upgrade-all

# BUNDLE ID HELPER
export def bundle-id [app_path: string] {
    if not ($app_path | path exists) {
        error make { msg: $"App bundle not found: ($app_path)" }
    }
    /usr/bin/mdls -name kMDItemCFBundleIdentifier -raw $app_path
}
