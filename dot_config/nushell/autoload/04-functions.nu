# Custom Functions Module
# Advanced wrappers and utilities

# YAZI FILE MANAGER
export def y [...args] {
    let tmp_file = (mktemp -t "yazi-cwd.XXXXXX")
    yazi ...$args --cwd-file=$tmp_file
    let cwd = (open $tmp_file | str trim)
    if ($cwd | is-not-empty) and ($cwd != $env.PWD) {
        cd $cwd
    }
    rm -f $tmp_file
}

# ZK WITH GIT SYNC
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

export def zk [...args] {
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

# PROTON PASS CLI
export def ppget [query: string, --field: string = "password"] {
    if not (has-cmd pass-cli) {
        print --stderr "Error: pass-cli not found."
        return 127
    }
    let search_result = (do { pass-cli search $query --json } | complete)
    if ($search_result.exit_code != 0) {
        print --stderr $"Error: Secret '(query)' not found."
        return 1
    }
    let item_id = ($search_result.stdout | from json | get 0.id?)
    if ($item_id | is-empty) or ($item_id == null) {
        print --stderr $"Error: Secret '(query)' not found."
        return 1
    }
    pass-cli get $item_id --field $field --output text
}

# SYSTEM UPGRADE
export def upgrade-all [] {
    if not (has-cmd brew) {
        print --stderr "Homebrew not found"
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
        print --stderr "Install buo/cask-upgrade: brew tap buo/cask-upgrade"
    }
    print "--- Mac App Store ---"
    if (has-cmd mas) {
        mas upgrade
        if ($env.LAST_EXIT_CODE != 0) { return 1 }
    } else {
        print --stderr "Install mas: brew install mas"
    }
    print "--- Cleanup ---"
    brew cleanup
}

export alias update = upgrade-all

# BUNDLE ID HELPER
export def bundle-id [app_path: string] {
    if not ($app_path | path exists) {
        print --stderr $"App bundle not found: ($app_path)"
        return 1
    }
    /usr/bin/mdls -name kMDItemCFBundleIdentifier -raw $app_path
}
