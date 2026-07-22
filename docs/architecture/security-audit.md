# macOS Security Posture Audit

## Scope

The security posture audit observes the controls enforced by the current macOS machine and compares declarative persistence with this flake. It reports evidence only. It never enables, disables, installs, removes, or otherwise remediates a control.

The audit is read-only. It does not use the network, invoke `sudo`, prompt for a password, or read secret values. Default mode always exits successfully because the report is not an activation or CI gate.

## Running the Audit

Run the audit from the repository root:

```bash
just security-audit
just security-audit --json
just security-audit --strict
```

The default table and the JSON array contain the same checks. `--strict` exits with status 1 when at least one check is `WARN`; it does not change any system state.

## Status Vocabulary

| Status | Meaning |
|--------|---------|
| `OK` | The control is present and enabled. |
| `WARN` | The control is absent, weakened, or has drifted from the declaration. |
| `MANUAL` | The check requires operator elevation or review; the report provides the command or System Settings location. |
| `UNKNOWN` | The tool was unavailable, failed, or returned output the audit could not parse. This is never treated as `OK`. |

## Manual Checks

Checks that require elevation are `MANUAL`, not automated. The audit never invokes `sudo` and never prompts for a password. An audit that requires elevation will not be run habitually, and an audit that is not run cannot provide useful evidence. The operator can choose when to run the displayed command and review its output separately.

## Declarative Drift

Undeclared user LaunchAgents and stray system extensions are the highest-value findings in a declaratively managed repository. A `WARN` means the machine's real persistence has drifted from the Nix declaration, which is the failure this repository exists to prevent. A declared LaunchAgent missing from disk also warns because activation did not produce the declared state.

System extensions receive `WARN` until they are explicitly declared and justified. They can survive `brew uninstall --zap`, so removing the Nix or Homebrew declaration does not prove that the extension stopped persisting on the machine.

## Justified System Extensions

The following system extensions are required by apps declared in `casks` and are intentionally accepted because they are load-bearing for the app's core function. The audit keeps reporting `WARN` for them (there is no automated justification mechanism), but these are not unknown drift.

| Extension | Source cask | Justification |
|-----------|------------|------|
| `ch.protonvpn.mac.WireGuard-Extension` | `protonvpn` | Required for ProtonVPN's WireGuard tunnel |
| `ch.protonvpn.mac.Transparent-Proxy` | `protonvpn` | Required for ProtonVPN's split tunneling (experimental feature) |

## Known Residual WARN

`com.objective-see.lulu.extension` remained registered in `systemextensionsctl list` after the `lulu` cask was removed (`brew uninstall --zap`) and the extension was disabled via System Settings (`[activated disabled]`) on 2026-07-22. `systemextensionsctl uninstall` cannot run while SIP is enabled, and clearing this registration fully would require disabling SIP. Keeping SIP enabled takes priority, so the disabled residual entry is accepted. The audit keeps reporting `WARN` for it; this is known drift that requires no action.

## Platform Support

This audit supports macOS only. Linux parity is future work.
