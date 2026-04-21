use std/assert

source "../autoload/07-abbreviations.nu"

let case_lg = (nu_abbr_expand_buffer "lg" 2)
assert equal $case_lg.buffer "lazygit "
assert equal $case_lg.cursor 8
assert equal $case_lg.expanded true

let case_echo = (nu_abbr_expand_buffer "echo hello" 10)
assert equal $case_echo.expanded false

let case_sudo_lg = (nu_abbr_expand_buffer "sudo lg" 7)
assert equal $case_sudo_lg.buffer "sudo lazygit "
assert equal $case_sudo_lg.expanded true

let case_empty = (nu_abbr_expand_buffer "" 0)
assert equal $case_empty.buffer " "
assert equal $case_empty.cursor 1
