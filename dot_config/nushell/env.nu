
# Nushell Environment Entry Point
$env.config.show_banner = false

const config_dir = ($nu.home-dir | path join '.config' 'nushell')

source ($config_dir | path join 'autoload' '01-env.nu')
source ($config_dir | path join 'autoload' '02-path.nu')
