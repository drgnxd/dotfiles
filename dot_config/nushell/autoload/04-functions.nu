# requires: 00-helpers

export def --wrapped y [...args] {
    let tmp_file = (mktemp -t "yazi-cwd.XXXXXX")
    yazi ...$args --cwd-file=$tmp_file
    let cwd = (open $tmp_file | str trim)
    if ($cwd | is-not-empty) and ($cwd != $env.PWD) {
        cd $cwd
    }
    ^rm -f $tmp_file
}

export def save-stats [] {
    let src = ($env.HOME | path join "Library" "Preferences" "eu.exelban.Stats.plist")
    let dotfiles_dir = dotfiles-dir
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

export def refresh-nix [input_name?: string] {
    require-cmd nix
    require-cmd git

    let dotfiles_dir = dotfiles-dir
    if not ($dotfiles_dir | path exists) {
        error make { msg: $"Dotfiles directory not found: ($dotfiles_dir)" }
    }
    let flake_path = $"path:($dotfiles_dir)"

    let lock_status = (do { ^git -C $dotfiles_dir status --short -- flake.lock } | complete)
    if ($lock_status.exit_code != 0) or ($lock_status.stdout | str trim | is-not-empty) {
        error make { msg: "flake.lock has uncommitted changes; review or commit them before refreshing inputs" }
    }

    if $input_name == null {
        print "--- Refresh all Nix flake inputs ---"
    } else {
        print $"--- Refresh Nix flake input: ($input_name) ---"
    }

    let update_result = if $input_name == null {
        do { nix flake update $flake_path } | complete
    } else {
        do { nix flake lock --update-input $input_name $flake_path } | complete
    }
    if ($update_result.exit_code != 0) {
        error make { msg: $"Nix flake refresh failed: ($update_result.stderr)" }
    }

    print "--- Review flake.lock before applying ---"
    ^git -C $dotfiles_dir diff -- flake.lock
}

export def upgrade-nix [] {
    require-cmd nix

    let dotfiles_dir = dotfiles-dir
    if not ($dotfiles_dir | path exists) {
        error make { msg: $"Dotfiles directory not found: ($dotfiles_dir)" }
    }

    let target = ($env | get -o DOTFILES_FLAKE_TARGET | default "")
    let fallback_target = ($env | get -o USER | default "default")
    let target_name = if ($target | is-empty) { $fallback_target } else { $target }
    let flake_ref = $"path:($dotfiles_dir)#($target_name)"

    if (has-cmd darwin-rebuild) {
        print "--- Authenticate for darwin-rebuild ---"
        let auth_result = (do { ^sudo -v } | complete)
        if ($auth_result.exit_code != 0) {
            error make { msg: $"sudo authentication failed: ($auth_result.stderr)" }
        }
        print "--- darwin-rebuild ---"
        ^sudo /run/current-system/sw/bin/darwin-rebuild switch --flake $flake_ref
    } else if (has-cmd home-manager) {
        print "--- home-manager ---"
        home-manager switch --flake $flake_ref
    } else {
        error make { msg: "Neither darwin-rebuild nor home-manager found" }
    }
}

export def refresh-brew [] {
    require-cmd brew
    print "--- Refresh Homebrew metadata ---"
    let result = (do { brew update } | complete)
    if ($result.exit_code != 0) {
        error make { msg: $"brew update failed: ($result.stderr)" }
    }
    print "--- Homebrew outdated packages ---"
    brew outdated --verbose
}

export def upgrade-brew [] {
    require-cmd brew
    print "--- Homebrew ---"
    let result = (do { brew upgrade } | complete)
    if ($result.exit_code != 0) {
        error make { msg: $"brew upgrade failed: ($result.stderr)" }
    }
}

export def upgrade-mac-apps [] {
    require-cmd mas
    print "--- Mac App Store ---"
    let result = (do { mas upgrade } | complete)
    if ($result.exit_code != 0) {
        error make { msg: $"mas upgrade failed: ($result.stderr)" }
    }
}

export def upgrade-all [] {
    upgrade-nix

    if (has-cmd mas) {
        upgrade-mac-apps
    }
}

export alias update = upgrade-all

# ZELLIJ SESSION NAMED AFTER THE CURRENT DIRECTORY
# No args: attach to (or create) the session named after $env.PWD.
# Any args: pass straight through to `zellij`.
export def --wrapped zj [...args] {
    require-cmd zellij
    if ($args | is-empty) {
        let name = ($env.PWD | path basename)
        zellij attach -c $name
    } else {
        ^zellij ...$args
    }
}

export def bundle-id [app_path: string] {
    if not ($app_path | path exists) {
        error make { msg: $"App bundle not found: ($app_path)" }
    }
    /usr/bin/mdls -name kMDItemCFBundleIdentifier -raw $app_path
}
