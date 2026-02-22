let
  macbook = ""; # set your ssh-ed25519 public key before running agenix -r
  macbook_keys = builtins.filter (key: key != "") [ macbook ];
in
{
  "gh-hosts.age".publicKeys = macbook_keys;
  "npmrc.age".publicKeys = macbook_keys;
  "git-config-local.age".publicKeys = macbook_keys;
}
