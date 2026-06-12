# Guard: tracked empty-key file for CI compatibility.
# For real usage, set your ssh-ed25519 public keys here and run `agenix -r`.
# Empty keys keep evaluation/builds working even without local secrets.
let
  darwin = ""; # set your Darwin ssh-ed25519 public key before running agenix -r
  linux = ""; # set your Linux ssh-ed25519 public key before running agenix -r
  darwin_keys = builtins.filter (key: key != "") [ darwin ];
  linux_keys = builtins.filter (key: key != "") [ linux ];
  public_keys = darwin_keys ++ linux_keys;
in
{
  "gh-hosts.age".publicKeys = public_keys;
  "npmrc.age".publicKeys = public_keys;
  "git-config-local.age".publicKeys = public_keys;
}
