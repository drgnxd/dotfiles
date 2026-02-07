# macOS スクリプト

このディレクトリは、残っている macOS 補助スクリプトの説明です。基本的な設定は nix-darwin と home-manager により宣言的に適用します。

## 現在のスクリプト

- `scripts/darwin/setup_cloud_symlinks.sh`
  - `~/Library/CloudStorage` から `$HOME` へのシンボリックリンク作成を支援
  - `FORCE=1` が必要

## macOS 設定の所在

- `hosts/macbook/default.nix`
  - システム設定とセキュリティ
  - LaunchAgents とログイン時起動
  - GUI アプリの cask/MAS 管理

- `home/default.nix`
  - ユーザー設定（Finder/Dock/メニューバー）
  - Stats.app 設定のインポート

## 使用例
```bash
FORCE=1 scripts/darwin/setup_cloud_symlinks.sh
```

## 関連ドキュメント
- [リポジトリアーキテクチャ](../../ARCHITECTURE.md)
- [セキュリティモデル](../architecture/security-model.ja.md)
