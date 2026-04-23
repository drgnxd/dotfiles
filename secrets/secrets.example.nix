let
  # Set your SSH public key, then run: agenix -r
  darwin = "";
  darwin_keys = builtins.filter (key: key != "") [ darwin ];
in
{
  "gh-hosts.age".publicKeys = darwin_keys;
  "npmrc.age".publicKeys = darwin_keys;
  "git-config-local.age".publicKeys = darwin_keys;
}
