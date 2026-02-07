let
  macbook = "ssh-ed25519 AAAA..."; # replace with your SSH public key
in
{
  "gh-hosts.age".publicKeys = [ macbook ];
  "npmrc.age".publicKeys = [ macbook ];
  "git-config-local.age".publicKeys = [ macbook ];
}
