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

export def upgrade-nix [] {
    require-cmd nix

    let dotfiles_dir = dotfiles-dir
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
