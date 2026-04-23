let
  # Set your SSH public key, then run: agenix -r
  macbook = "";
  macbook_keys = builtins.filter (key: key != "") [ macbook ];
in
{
  "gh-hosts.age".publicKeys = macbook_keys;
  "npmrc.age".publicKeys = macbook_keys;
  "git-config-local.age".publicKeys = macbook_keys;
}
