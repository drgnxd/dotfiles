# Load unmanaged machine-specific overrides after all managed startup files.
const local_file = ($nu.home-dir | path join '.config' 'nushell' 'local.nu')
const optional_local_file = if ($local_file | path exists) { $local_file } else { null }

source $optional_local_file
