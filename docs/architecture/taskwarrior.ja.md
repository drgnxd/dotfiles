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
- このリポジトリでは `on-add.py` と `on-modify.py` の両方を有効なフックエントリーポイントとして配布（共通処理は `update_cache.py`）
- フックの標準入力は JSON ストリームとして厳密に解釈（単一オブジェクト/2オブジェクトの両形式に対応）
- JSON 解釈に失敗した場合は、後方互換のため最終非空行をそのまま転送
- フック内部エラーは `${XDG_CACHE_HOME:-~/.cache}/taskwarrior/hook_errors.log` に記録し、Taskwarrior 操作は継続
- デバッグ時は `TASKWARRIOR_HOOK_DEBUG=1` でエラー行を stderr にも出力
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
