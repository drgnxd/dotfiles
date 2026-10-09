use std/assert

let fake_bin = (mktemp --directory)
"#!/bin/sh\nexit 0\n" | save ($fake_bin | path join "direnv")
chmod +x ($fake_bin | path join "direnv")
$env.PATH = ($env.PATH | prepend $fake_bin)

$env.config = ($env.config | upsert hooks.env_change.PWD [{ __zoxide_hook: true, code: {|_, dir| null } }])

source "../autoload/06-direnv.nu"

let hooks = $env.config.hooks.env_change.PWD
assert equal ($hooks | length) 2
assert equal ($hooks | get 0.__zoxide_hook) true
assert equal ($hooks | get 1.__direnv_hook) true

source "../autoload/06-direnv.nu"
assert equal ($env.config.hooks.env_change.PWD | length) 2

rm -rf $fake_bin
