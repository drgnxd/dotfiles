# Guard: tracked empty-key file for CI compatibility.
# For real usage, set your ssh-ed25519 public key here and run `agenix -r`.
# Empty keys keep evaluation/builds working even without local secrets.
let
  macbook = ""; # set your ssh-ed25519 public key before running agenix -r
  macbook_keys = builtins.filter (key: key != "") [ macbook ];
in
{
  "gh-hosts.age".publicKeys = macbook_keys;
  "npmrc.age".publicKeys = macbook_keys;
  "git-config-local.age".publicKeys = macbook_keys;
}
