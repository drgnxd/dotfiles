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
- This repository ships both `on-add.py` and `on-modify.py` as active hook entrypoints; both delegate to `hook_entrypoint.py`, which calls shared logic in `update_cache.py`.
- Hook stdin is parsed as a JSON stream (supports both single-object and two-object payload formats).
- If JSON parsing fails, hooks fall back to forwarding the last non-empty input line for compatibility.
- Hook runtime errors are written to `${XDG_CACHE_HOME:-~/.cache}/taskwarrior/hook_errors.log` without blocking task operations.
- Set `TASKWARRIOR_HOOK_DEBUG=1` to mirror hook error lines to stderr while debugging.
- Nushell prompt preview reads `desc.list` for inline task descriptions and wraps `task` to refresh the cache.
- Nushell integration is eager-loaded: `config.nu` sources `modules/taskwarrior.nu` (implementation) and `autoload/08-taskwarrior.nu` (wrapper) during startup.
- 2026-02-27 benchmark showed lazy-load had no measurable benefit; eager loading has lower variance.
- Zsh integration is archived in git history.

## Performance Notes
- The Taskwarrior module and wrapper are sourced at startup for deterministic command availability.
- Hook updates are throttled (5-second minimum interval) to reduce latency.
- Nushell preview reads cache only when task IDs are present in the command line.
- The Nushell `task` wrapper refreshes the cache after each invocation (via `uv` when available).

## Reference
- `dot_config/taskwarrior/CACHE_ARCHITECTURE.md`
