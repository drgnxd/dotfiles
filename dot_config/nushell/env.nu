# Nushell Environment Entry Point
# Loaded first by Nushell, then config.nu

# Disable welcome banner (must be set early in env.nu)
$env.config.show_banner = false

# Use an explicit path for source
source "/Users/author/.config/nushell/autoload/01-env.nu"
