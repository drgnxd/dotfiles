
# Nushell Environment Entry Point
$env.config.show_banner = false

const env_dir = ($nu.env-path | path dirname)

source ($env_dir | path join 'autoload' '01-env.nu')
source ($env_dir | path join 'autoload' '02-path.nu')
