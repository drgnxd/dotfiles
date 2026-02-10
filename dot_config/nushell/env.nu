
# Nushell Environment Entry Point
$env.config.show_banner = false

# FIX: Hardcode path to avoid const evaluation errors
const env_dir = '/Users/drgnxd/.config/nushell'

source ($env_dir | path join 'autoload' '01-env.nu')
source ($env_dir | path join 'autoload' '02-path.nu')
