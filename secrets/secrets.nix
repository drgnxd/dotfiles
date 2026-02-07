let
  darwin = "ssh-ed25519 AAAA..."; # replace with your SSH public key
in
{
  "gh-hosts.age".publicKeys = [ darwin ];
  "npmrc.age".publicKeys = [ darwin ];
  "git-config-local.age".publicKeys = [ darwin ];
}
