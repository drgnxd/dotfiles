
# PATH Configuration Module

def detect-nix-paths [] {
    # -i (ignore-errors) is deprecated, use -o (optional)
    let user = ($env | get --optional USER | default '')
    let per_user = if ($user | is-not-empty) { $'/etc/profiles/per-user/($user)/bin' } else { '' }
    
    let candidates = [
        ($env.HOME | path join '.nix-profile' 'bin')
        '/nix/var/nix/profiles/default/bin'
        '/run/current-system/sw/bin'
        $per_user
    ]
    
    $candidates | where { |it| ($it | is-not-empty) and ($it | path exists) }
}

# FIX: use 'def --env' instead of 'def-env'
def --env path-add [new_path: string] {
    if ($new_path | path exists) {
        $env.PATH = ($env.PATH | prepend $new_path | uniq)
    }
}

for p in (detect-nix-paths) {
    path-add $p
}

path-add ($env.HOME | path join '.local' 'bin')
path-add ($env.CARGO_HOME | path join 'bin')
path-add '/opt/homebrew/bin'
path-add '/opt/homebrew/sbin'

if (which fd | is-not-empty) {
    $env.FZF_DEFAULT_COMMAND = 'fd --type f --hidden --follow --exclude .git'
    $env.FZF_CTRL_T_COMMAND = $env.FZF_DEFAULT_COMMAND
    $env.FZF_ALT_C_COMMAND = 'fd --type d --hidden --follow --exclude .git'
}
