
# Constants Module

const config_dir = ($nu.home-dir | path join '.config' 'nushell')
const integrations_module = ($config_dir | path join 'modules' 'integrations.nu')
const taskwarrior_module = ($config_dir | path join 'modules' 'taskwarrior.nu')
const lima_module = ($config_dir | path join 'modules' 'lima.nu')

# Export for use in other sourced files
export const config_dir = $config_dir
export const integrations_module = $integrations_module
export const taskwarrior_module = $taskwarrior_module
export const lima_module = $lima_module
