use std/assert

source "../autoload/07-abbreviations.nu"

let case_lg = (nu_abbr_expand_buffer "lg" 2 --submit)
assert equal $case_lg.buffer "lg"
assert equal $case_lg.cursor 2
assert equal $case_lg.expanded false

let case_oc = (nu_abbr_expand_buffer "oc" 2 --submit)
assert equal $case_oc.buffer "oc"
assert equal $case_oc.expanded false

let case_ocd = (nu_abbr_expand_buffer "ocd" 3 --submit)
assert equal $case_ocd.buffer "ocd"
assert equal $case_ocd.expanded false

let case_echo = (nu_abbr_expand_buffer "echo hello" 10)
assert equal $case_echo.expanded false

let case_sudo_lg = (nu_abbr_expand_buffer "sudo lg" 7 --submit)
assert equal $case_sudo_lg.buffer "sudo lg"
assert equal $case_sudo_lg.expanded false

let case_empty = (nu_abbr_expand_buffer "" 0)
assert equal $case_empty.buffer " "
assert equal $case_empty.cursor 1
