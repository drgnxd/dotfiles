# Taskwarrior 統合

## 構成
```
[Task add/modify]
      -> [Python Hooks] -> update_cache.py -> [Cache Files]
      -> [Nushell プロンプトプレビュー]（キャッシュ参照）
      -> [Zsh 統合]（アーカイブ済み）
```

## コンポーネント
- Python フックが `${XDG_CACHE_HOME:-~/.cache}/taskwarrior/ids.list` と `desc.list` を更新
- Nushell のプロンプトプレビューが `desc.list` を参照し、`task` ラッパーがキャッシュ更新を実行
- Nushell 統合は遅延ロード: `autoload/08-taskwarrior.nu` が初回利用時に `modules/taskwarrior.nu` を読み込み
- Zsh 統合は `archive/zsh` にアーカイブ済み

## パフォーマンス
- Taskwarrior モジュールはオンデマンドで読み込むため、起動を軽くします
- フック更新は5秒スロットリングで連続実行を抑制
- Nushell のプレビューはコマンドラインにIDがある場合のみキャッシュを読む
- Nushell の `task` ラッパーは実行後にキャッシュを更新（`uv` がある場合）

## 参考
- `dot_config/taskwarrior/CACHE_ARCHITECTURE.md`
