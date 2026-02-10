# Zsh Configuration Archive

This directory contains the legacy Zsh configuration files that have been migrated to Nushell.

## Migration Date
2026-01-31

## Status
**ARCHIVED** - These files are no longer actively maintained but kept for reference.

## Migration Details

The Zsh configuration has been fully migrated to Nushell with the following improvements:

### Changes
- **Shell**: Zsh → Nushell (modern shell with structured data)
- **Configuration**: Multiple sourced files → Modular `autoload/` directory
- **Aliases**: Simple string replacement → `export def` functions with logic
- **PATH Management**: Manual string manipulation → `path-add` helper
- **Environment**: `.zshenv` + `.zshrc` → `env.nu` + `config.nu`

### Feature Parity
All Zsh functionality has been migrated to Nushell:
- Aliases (`c`, `ca`, `t`, `g`, `ll`, `la`, `lt`, etc.)
- Functions (yazi, zk, ppget, upgrade-all, lima management, etc.)
- Completions (docker, chezmoi, brew)
- Integrations (Starship, Zoxide, Direnv, Carapace, FZF)
- Environment variables (XDG compliance maintained)

### New Features in Nushell
- Structured data pipelines (tables/records instead of text streams)
- Better error messages with exact location
- Cross-platform consistency (works identically on macOS/Linux)
- Type safety and better debugging

## Files in This Archive

### Core Configuration
- `dot_zshrc.tmpl` - Main entry point
- `dot_zsh_options` - Zsh settings
- `dot_zsh_completion` - Completion system
- `dot_zsh_plugins` - Plugin management (zplug/zinit)

### Modules
- `dot_exports` - Environment variables and PATH
- `dot_aliases` - Command aliases
- `dot_functions` - Custom functions
- `dot_completions/` - Per-command completions
- `dot_homebrew` - Homebrew setup
- `dot_zoxide` - Smart cd integration
- `dot_proton` - Proton Pass CLI wrapper
- `dot_lima` - Lima/Docker functions
- `dot_direnv` - Per-directory environments
- `dot_fzf` / `dot_fzf_theme` - FZF integration and theme

### Fast Syntax Highlighting
- `fsh/` - 26 custom chromas for syntax highlighting
  - Custom themes for bat, brew, btop, chezmoi, delta, direnv, docker-compose, duf, dust, eza, fd, fzf, gh, git-crypt, gpg, helix, jaq, lazygit, lima, and more

## Usage

If you need to reference the old Zsh configuration:

```bash
# View archived files
ls -la archive/zsh/
cat archive/zsh/dot_aliases
cat archive/zsh/dot_functions
```

## Restoration

If you need to temporarily restore Zsh configuration:

```bash
# Copy from archive to dot_config
cp -r archive/zsh/* dot_config/zsh/
chezmoi add dot_config/zsh/
```

Note: This is not recommended as Nushell is now the primary shell.

## References

- [Nushell Configuration](../dot_config/nushell/)
- [Nushell Documentation](https://www.nushell.sh/book/)
- [Migration Guide: docs/architecture/nushell.md](../docs/architecture/nushell.md)
