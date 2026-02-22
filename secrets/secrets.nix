let
  darwin = ""; # set your ssh-ed25519 public key before running agenix -r
  darwin_keys = builtins.filter (key: key != "") [ darwin ];
in
{
  "gh-hosts.age".publicKeys = darwin_keys;
  "npmrc.age".publicKeys = darwin_keys;
  "git-config-local.age".publicKeys = darwin_keys;
}
