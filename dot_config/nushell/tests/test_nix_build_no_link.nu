use std/assert

source "../autoload/04-functions.nu"

let default_build = (nix-build-no-link-args ["build" ".#package"])
assert equal $default_build ["build" "--no-link" ".#package"]

let unrelated_command = (nix-build-no-link-args ["develop" ".#devShell"])
assert equal $unrelated_command ["develop" ".#devShell"]

let explicit_no_link = (nix-build-no-link-args ["build" ".#package" "--no-link"])
assert equal $explicit_no_link ["build" ".#package" "--no-link"]

let explicit_out_link = (nix-build-no-link-args ["build" ".#package" "--out-link" "./result"])
assert equal $explicit_out_link ["build" ".#package" "--out-link" "./result"]

let short_out_link = (nix-build-no-link-args ["build" ".#package" "-o" "./result"])
assert equal $short_out_link ["build" ".#package" "-o" "./result"]

let explicit_out_link_equals = (nix-build-no-link-args ["build" ".#package" "--out-link=./result"])
assert equal $explicit_out_link_equals ["build" ".#package" "--out-link=./result"]
