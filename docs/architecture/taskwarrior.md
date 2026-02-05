# Taskwarrior Integration

## Architecture
```
[Task add/modify]
      -> [Python Hooks] -> update_cache.py -> [Cache Files]
      -> [Nushell prompt preview] (uses cache)
      -> [Legacy Zsh integration] (archived)
```

## Components
- Python hooks update `${XDG_CACHE_HOME:-~/.cache}/taskwarrior/ids.list` and `desc.list`.
- Nushell prompt preview reads `desc.list` for inline task descriptions and wraps `task` to refresh the cache.
- Nushell integration is lazy-loaded: `autoload/08-taskwarrior.nu` loads `modules/taskwarrior.nu` on first use.
- Zsh integration is archived under `archive/zsh`.

## Performance Notes
- The Taskwarrior module is loaded on demand to keep shell startup light.
- Hook updates are throttled (5-second minimum interval) to reduce latency.
- Nushell preview reads cache only when task IDs are present in the command line.
- The Nushell `task` wrapper refreshes the cache after each invocation (via `uv` when available).

## Reference
- `dot_config/taskwarrior/CACHE_ARCHITECTURE.md`
