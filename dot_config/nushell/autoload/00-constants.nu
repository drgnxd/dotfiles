
# Constants Module

# Use ~/.config/nushell unconditionally (see config.nu for rationale).
const config_dir = ($nu.home-dir | path join '.config' 'nushell')
const integrations_module = ($config_dir | path join 'modules' 'integrations.nu')
const lima_module = ($config_dir | path join 'modules' 'lima.nu')

# Export for use in other sourced files
export const config_dir = $config_dir
export const integrations_module = $integrations_module
export const lima_module = $lima_module
