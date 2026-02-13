
# Nushell Environment Entry Point
$env.config.show_banner = false

const config_dir = (
    if (((($nu.env-path | path dirname) | path join 'autoload' '01-env.nu') | path exists)) {
        ($nu.env-path | path dirname)
    } else {
        $nu.default-config-dir
    }
)

source ($config_dir | path join 'autoload' '01-env.nu')
source ($config_dir | path join 'autoload' '02-path.nu')
