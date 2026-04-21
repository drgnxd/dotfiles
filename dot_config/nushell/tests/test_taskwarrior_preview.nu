use std/assert

source "../modules/taskwarrior.nu"

assert equal (taskwarrior_preview_ids [task 1 done]) ["1"]
assert equal (taskwarrior_preview_ids [task 1-3 done]) ["1" "2" "3"]
assert equal (taskwarrior_preview_ids [task modify]) []
