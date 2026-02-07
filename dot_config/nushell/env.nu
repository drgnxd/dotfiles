# Nushell Environment Entry Point
# Loaded first by Nushell, then config.nu

# Disable welcome banner (must be set early in env.nu)
$env.config.show_banner = false

# Use an explicit path for source
const env_dir = ($nu.env-path | path dirname)
source ($env_dir | path join "autoload" "01-env.nu")
