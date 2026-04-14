# macOS スクリプト

このディレクトリは、残っている macOS 補助スクリプトの説明です。基本的な設定は nix-darwin と home-manager により宣言的に適用します。

## 現在のスクリプト

- `scripts/darwin/setup_cloud_symlinks.sh`
  - `~/Library/CloudStorage` から `$HOME` へのシンボリックリンク作成を支援
  - `FORCE=1` が必要

## macOS 設定の所在

- `hosts/macbook/default.nix`
  - システム設定とセキュリティ
  - GUI アプリの cask/MAS 管理

- `hosts/macbook/launchd.nix`
  - nix-darwin による LaunchAgent 定義とログイン時アプリ起動
  - これとは別に、home-manager activation フックでアプリ側が作る旧 `LaunchAtLogin` Agent（Stats/Hammerspoon）を無効化

- `home/default.nix`
  - Home Manager のユーザー設定エントリーポイント（各モジュールを読込）

- `home/modules/activation/`
  - `directories.nix`（ローカルディレクトリ作成）
  - `macos_defaults.nix`（`defaults -currentHost` が必要なユーザー設定）
  - `nushell_ensure.nix`（`local.nu` と Nushell キャッシュディレクトリの保証）
  - `opencode.nix`（OpenCode 設定とルール同期）
  - `taskwarrior_ensure.nix`（Taskwarrior のローカル上書きファイル保証）

## 使用例
```bash
FORCE=1 scripts/darwin/setup_cloud_symlinks.sh
```

## 関連ドキュメント
- [リポジトリアーキテクチャ](../ARCHITECTURE.md)
- [セキュリティモデル](../architecture/security-model.ja.md)
