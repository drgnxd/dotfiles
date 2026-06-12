let
  # Set your SSH public keys, then run: agenix -r
  darwin = "";
  linux = "";
  darwin_keys = builtins.filter (key: key != "") [ darwin ];
  linux_keys = builtins.filter (key: key != "") [ linux ];
  public_keys = darwin_keys ++ linux_keys;
in
{
  "gh-hosts.age".publicKeys = public_keys;
  "npmrc.age".publicKeys = public_keys;
  "git-config-local.age".publicKeys = public_keys;
}
