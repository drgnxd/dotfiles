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
- このリポジトリでは `on-add.py` と `on-modify.py` の両方を有効なフックエントリーポイントとして配布し、両者は `hook_entrypoint.py` を介して `update_cache.py` の共通処理を呼び出します
- フックの標準入力は JSON ストリームとして厳密に解釈（単一オブジェクト/2オブジェクトの両形式に対応）
- JSON 解釈に失敗した場合は、後方互換のため最終非空行をそのまま転送
- フック内部エラーは `${XDG_CACHE_HOME:-~/.cache}/taskwarrior/hook_errors.log` に記録し、Taskwarrior 操作は継続
- デバッグ時は `TASKWARRIOR_HOOK_DEBUG=1` でエラー行を stderr にも出力
- Nushell のプロンプトプレビューが `desc.list` を参照し、`task` ラッパーがキャッシュ更新を実行
- Nushell 統合は積極読み込み: `config.nu` が起動時に `modules/taskwarrior.nu`（実体）と `autoload/08-taskwarrior.nu`（wrapper）を source します
- 2026-02-27 のベンチマークで遅延ロードの有意な効果は確認できず、積極読み込みのほうが分散が小さいことが分かりました
- Zsh 統合は git 履歴にアーカイブ済み

## パフォーマンス
- Taskwarrior モジュールと wrapper は起動時に source し、コマンド可用性を安定化します
- フック更新は5秒スロットリングで連続実行を抑制
- Nushell のプレビューはコマンドラインにIDがある場合のみキャッシュを読む
- Nushell の `task` ラッパーは実行後にキャッシュを更新（`uv` がある場合）

## 参考
- `dot_config/taskwarrior/CACHE_ARCHITECTURE.md`
