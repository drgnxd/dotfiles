
# Nushell Environment Entry Point
$env.config.show_banner = false

# Use ~/.config/nushell unconditionally.
# home-manager symlinks env.nu into /nix/store, so $nu.env-path dirname is
# /nix/store (not useful). XDG_CONFIG_HOME is set system-wide by nix-darwin,
# but $env is unavailable in const. $nu.home-dir is a parse-time constant.
const config_dir = ($nu.home-dir | path join '.config' 'nushell')

source ($config_dir | path join 'autoload' '01-env.nu')
source ($config_dir | path join 'autoload' '02-path.nu')
