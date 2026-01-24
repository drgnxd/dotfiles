# Taskwarrior Integration

## Architecture
```
[Task add/modify]
      -> [Python Hooks] -> update_cache.py -> [Cache Files]
      -> [Zsh Functions] -> [Fast Syntax Highlighting]
```

## Components
- Python hooks update `${XDG_CACHE_HOME:-~/.cache}/taskwarrior/ids.list` and `desc.list`.
- Zsh functions load cache data for completion and inline previews.
- Fast Syntax Highlighting validates IDs using cached lists.

## Performance Notes
- Hook updates are throttled (5-second minimum interval) to reduce latency.
- Zsh `task` wrapper refreshes the cache asynchronously for interactive speed.
- Cache reloads are skipped unless the file mtime changes.

## Reference
- `dot_config/taskwarrior/CACHE_ARCHITECTURE.md`
