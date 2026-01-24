# Taskwarrior 統合

## 構成
```
[Task add/modify]
      -> [Python Hooks] -> update_cache.py -> [Cache Files]
      -> [Zsh Functions] -> [Fast Syntax Highlighting]
```

## コンポーネント
- Python フックが `~/.cache/taskwarrior/ids.list` と `desc.list` を更新
- Zsh 関数がキャッシュを読み込み補完/プレビューに利用
- Fast Syntax Highlighting がIDの妥当性を検証

## パフォーマンス
- フック更新は5秒スロットリングで連続実行を抑制
- Zsh の `task` ラッパーは非同期更新で操作感を維持
- キャッシュは更新時刻が変わらない限り再読込しない

## 参考
- `dot_config/taskwarrior/CACHE_ARCHITECTURE.md`
