# Previous wtctl lifecycle binary

The previous lifecycle-capable `wtctl` input was revision `35012a129704b3a5825b5134983e922f1a49dee9`.
When its documented legacy recovery is required, build that exact revision without deploying it from this repository's root:

```sh
nix build --no-link --print-out-paths 'github:drgnxd/wtctl/35012a129704b3a5825b5134983e922f1a49dee9#default'
```

The printed store path contains `bin/wtctl`; `--no-link` neither deploys it nor protects it from garbage collection, so rebuild when needed.
This historical revision supports `aarch64-darwin` only.
Consult the documentation at that same revision and follow the global `git-workflow` legacy-state safeguards before any recovery; do not bypass refusals or remove quarantine manually.
