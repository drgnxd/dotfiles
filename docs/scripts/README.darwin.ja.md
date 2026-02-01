# Darwin セットアップスクリプト

このディレクトリには macOS 固有のセットアップと設定スクリプトが含まれています。

## 概要

このディレクトリ内のスクリプトは、リポジトリルートの `run_onchange_after_setup.sh.tmpl` によってオーケストレーションされます。システム設定、セキュリティハードニング、キーボード設定、アプリケーションセットアップを処理します。

## スクリプト構成

### 通常スクリプト (`.sh`)
テンプレートロジックを含まず、直接実行されるスクリプト：
- `audit_security.sh` - macOS セキュリティ設定の監査
- `keyboard.sh` - キーボードリピート速度と Fn キー動作の設定
- `login_items.sh` - ログイン項目（起動時に実行されるアプリケーション）の管理
- `menubar.sh` - メニューバーとコントロールセンター項目の設定
- `security_hardening.sh` - セキュリティハードニング設定の適用
- `system_defaults.sh` - macOS システムデフォルト（Finder、Dock など）の設定

### テンプレートスクリプト (`.sh.tmpl`)
chezmoi テンプレートロジックを含み、実行時にレンダリングされるスクリプト：
- `import_stats.sh.tmpl` - Stats アプリ設定のインポート
- `install_packages.sh.tmpl` - Brewfile を介した Homebrew パッケージのインストール
- `setup_cloud_symlinks.sh.tmpl` - クラウドストレージディレクトリへのシンボリックリンク作成

## ガードフラグ

いくつかのスクリプトは、誤実行を防ぐために明示的な環境変数を要求します：

| フラグ | スクリプト | 目的 |
|------|--------|------|
| `ALLOW_DEFAULTS=1` | `system_defaults.sh` | macOS デフォルト（Finder、Dock など）の変更 |
| `ALLOW_HARDEN=1` | `security_hardening.sh` | セキュリティハードニング設定の適用 |
| `ALLOW_GUI=1` | `login_items.sh` | GUI ログイン項目の変更 |
| `ALLOW_KEYBOARD_APPLY=1` | `keyboard.sh` | キーボード設定の適用（`--apply` フラグを使用） |
| `FORCE=1` | `setup_cloud_symlinks.sh.tmpl` | 既存のシンボリックリンクの上書き |

### オプショナルガードフラグ

| フラグ | スクリプト | 目的 |
|------|--------|------|
| `ALLOW_LSQUARANTINE_OFF=1` | `system_defaults.sh` | Gatekeeper 隔離警告の無効化 |
| `ALLOW_SPOTLIGHT_DISABLE=1` | `system_defaults.sh` | Spotlight キーボードショートカットの無効化 |

## システムデフォルト適用内容

`system_defaults.sh` は以下の開発者向け設定を適用します。

- 言語/地域: 英語UI（日本）、`en_JP` ロケール、メートル法、摂氏
- 日付形式（短い形式）: `yyyy/MM/dd`
- 入力補正: 自動スペル/大文字化/スマート引用符/ダッシュ/ピリオドを無効化
- Finder: 隠しファイル表示、フルパス表示、拡張子/ステータス/パスバー表示
- Dock: 自動表示ディレイ/アニメーション無効化、スペース切替アニメーション無効化

## 使用例

### すべてのセットアップスクリプトを実行
```bash
# chezmoi 経由（推奨 - コンテンツ変更時にトリガー）
chezmoi apply

# または手動でオーケストレーターを実行
bash ~/.local/share/chezmoi/run_onchange_after_setup.sh.tmpl

# 失敗しても続行する場合
CONTINUE_ON_ERROR=1 bash ~/.local/share/chezmoi/run_onchange_after_setup.sh.tmpl
```

### 個別スクリプトの実行
```bash
# ガードフラグを指定して実行
ALLOW_DEFAULTS=1 bash .internal_scripts/darwin/system_defaults.sh

# キーボード設定（プレビューモード）
bash .internal_scripts/darwin/keyboard.sh

# キーボード設定（適用モード）
ALLOW_KEYBOARD_APPLY=1 bash .internal_scripts/darwin/keyboard.sh --apply

# 別のユーザーに対して実行
ALLOW_KEYBOARD_APPLY=1 bash .internal_scripts/darwin/keyboard.sh --apply --user johndoe
```

## 共通関数ライブラリ

すべてのスクリプトは `../lib/bootstrap.sh` をソースし、`common.sh` を読み込んだ上で以下を提供します：

### ログ関数
- `log_info "message"` - 青色の情報メッセージ
- `log_success "message"` - 緑色の成功メッセージ
- `log_error "message"` - 赤色のエラーメッセージ
- `log_warning "message"` - 黄色の警告メッセージ

### ガード関数
- `require_flag "FLAG_NAME" "description"` - 環境フラグが設定されていない場合に終了
- `check_command "command"` - コマンドが PATH に存在するかチェック

### macOS 関数
- `safe_defaults_write <args>` - エラーチェック付き `defaults write` のラッパー
- `safe_defaults_write_current_host <args>` - `defaults -currentHost write` のラッパー
- `safe_defaults_write_as_user <user> <args>` - 特定ユーザーとして defaults write を実行
- `safe_defaults_write_current_host_as_user <user> <args>` - 特定ユーザーとして -currentHost 付きで実行
- `read_defaults <domain> <key>` - 安全に defaults 値を読み取り（存在しない場合は "not set" を返す）
- `quit_app "App Name"` - osascript 経由でアプリケーションを終了
- `kill_process "ProcessName"` - プロセス名でプロセスを終了（System UI 再起動用）
- `get_console_user` - 現在の GUI コンソールユーザーを取得
- `is_macos` - macOS 上で実行されているかチェック（Darwin の場合は 0 を返す）

### 失敗トラッキング
- `record_failure "message"` - バッチレポート用に失敗を記録
- `report_failures` - 記録されたすべての失敗の要約を出力

## Strict モード

すべての bash スクリプトは堅牢なエラーハンドリングのために strict モードを使用します：
```bash
set -euo pipefail
```

- `-e`: コマンド失敗時に終了
- `-u`: 未定義変数使用時に終了
- `-o pipefail`: パイプライン内のいずれかのコマンドが失敗した場合に失敗

## アーキテクチャ統合

これらのスクリプトは以下と統合されています：
- **chezmoi**: テンプレートレンダリングと変更検出
- **Homebrew**: Brewfile を介したパッケージインストール
- **XDG Base Directory**: `$XDG_CONFIG_HOME`、`$XDG_DATA_HOME` などへの準拠
- **LaunchAgents**: アプリケーションの自動起動（Stats、Hammerspoon、Maccy）

## 関連ドキュメント

- [リポジトリアーキテクチャ](../../ARCHITECTURE.md)
- [共通関数](../lib/common.sh)
- [メインセットアップオーケストレーター](../../run_onchange_after_setup.sh.tmpl)
