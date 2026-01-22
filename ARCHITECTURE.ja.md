# アーキテクチャ概要

## 設計原則

### 1. **XDG Base Directory 準拠**
すべての設定ファイルは [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html) に従います：

```
$XDG_CONFIG_HOME (~/.config)  → アプリケーション設定
$XDG_CACHE_HOME (~/.cache)    → 非必須キャッシュデータ
$XDG_DATA_HOME (~/.local/share) → ユーザー固有データファイル
```

**利点**:
- クリーンなホームディレクトリ
- 予測可能なファイル配置
- バックアップ・同期が容易

### 2. **セキュリティファースト設計**
- **ガードフラグ**: 破壊的操作には明示的な環境変数が必要
- **フェイルセーフ**: スクリプトはエラー時に終了 (`set -euo pipefail`)
- **秘密情報の除外**: `.chezmoiignore.tmpl` で機密ファイルを追跡から除外

### 3. **プラットフォーム独立性**
- chezmoi テンプレートによる条件付き包含
- `.internal_scripts/darwin/` 内のプラットフォーム固有スクリプト
- macOS と Linux 両対応の共有ツール設定

### 4. **冪等性**
すべてのスクリプトは複数回安全に実行可能：
- 変更前のチェック
- 非破壊的デフォルト
- ステートベース実行 (`run_onchange_` スクリプト)

---

## セキュリティモデル

### ガードフラグシステム

**目的**: システム変更スクリプトの誤実行を防止

**実装**:
```bash
# スクリプト内
require_flag "ALLOW_DEFAULTS" "macOS defaults modification"

# ユーザー実行
ALLOW_DEFAULTS=1 ./script.sh
```

**フラグ一覧**:
| フラグ | スクリプト | リスクレベル |
|------|--------|-----------|
| `ALLOW_DEFAULTS` | system_defaults.sh | 中 |
| `ALLOW_HARDEN` | security_hardening.sh | 高 |
| `ALLOW_GUI` | login_items.sh | 低 |
| `ALLOW_KEYBOARD_APPLY` | keyboard.sh | 低 |
| `FORCE` | setup_cloud_symlinks.sh | 中 |

### 秘密情報管理

**除外設定** (`.chezmoiignore.tmpl`):
```
# ユーザー固有設定
**config.local
**hosts.yml

# macOS 固有ファイル（Linux 上では除外）
{{ if ne .chezmoi.os "darwin" }}
.internal_scripts/darwin
{{ end }}
```

**Proton Pass 統合**:
- `ppget` コマンド経由で SSH 鍵を取得
- `config.local` で Git 署名を設定
- 認証情報は決してコミットしない

---

## プラットフォームサポート

### macOS (darwin)

**パッケージマネージャー**: Homebrew (`Brewfile.tmpl`)

**システム統合**:
- `system_defaults.sh`: NSUserDefaults の変更
- `Hammerspoon`: ウィンドウ管理、入力切り替え
- `Stats`: システムモニター（plist ベース設定）

**自動化**:
- AppleScript によるログイン項目管理
- `defaults` コマンドによるメニューバー設定

### Linux

**パッケージマネージャー**: システム依存（apt、dnf、pacman など）

**XDG 準拠**: すべてのツールが XDG パスをネイティブサポート

---

## Container & 仮想化

### Lima (Linux Virtual Machines)

**設定**:
```bash
export LIMA_HOME="${XDG_DATA_HOME}/lima"  # ~/.local/share/lima/
```

**管理コマンド** (`.config/zsh/.lima`):
- `lima-start` - Lima VM の起動
- `lima-stop` - Lima VM の停止
- `lima-status` / `lls` - ステータス確認
- `lima-shell` - VM シェルに接続
- `lima-delete` - VM の削除

### Docker

**設定**:
```bash
export DOCKER_CONFIG="$XDG_CONFIG_HOME/docker"  # ~/.config/docker/
```

**Lima 統合**:
- Lima VM 内で Docker デーモンを実行
- ホストから Docker CLI を使用
- XDG 準拠の設定パス

---

## 開発ワークフロー

### 1. ローカル変更
```bash
# 設定を編集
cd ~/.local/share/chezmoi
$EDITOR dot_config/zsh/.zshrc.tmpl

# 変更を適用
chezmoi apply

# 差分確認
chezmoi diff
```

### 2. Git 管理
```bash
# 変更をステージング
cd ~/.local/share/chezmoi
git add .

# コミット
git commit -m "feat(zsh): add new alias"

# プッシュ
git push origin main
```

### 3. 新マシンへのデプロイ
```bash
# リポジトリをクローン
chezmoi init --apply https://github.com/yourusername/dotfiles.git

# ユーザー固有設定を追加
cp ~/.config/git/config.local.example ~/.config/git/config.local
$EDITOR ~/.config/git/config.local
```

---

## トラブルシューティング

### chezmoi の問題

**状態がおかしい場合**:
```bash
chezmoi state dump  # 現在の状態を確認
chezmoi state reset # 状態をリセット
```

**差分が大きすぎる場合**:
```bash
chezmoi diff | less  # ページャーで確認
```

### スクリプト実行エラー

**ガードフラグが設定されていない**:
```
[ERROR] Refusing to proceed without ALLOW_DEFAULTS=1
```
**解決策**: 必要な環境変数を設定して再実行

**sudo パスワードのタイムアウト**:
```
sudo: a password is required
```
**解決策**: `sudo -v` で認証を更新

### Homebrew の問題

**Brewfile のロックエラー**:
```bash
rm ~/Library/Caches/Homebrew/Brewfile.lock.json
brew bundle --file ~/.config/homebrew/Brewfile
```

---

## 関連ドキュメント

### プロジェクトドキュメント
- [README.md](README.md) / [README.ja.md](README.ja.md) - プロジェクト概要
- [CONTRIBUTING.md](.github/CONTRIBUTING.md) - 開発ガイド
- [Darwin Scripts README](.internal_scripts/darwin/README.md) - macOS スクリプト詳細

### 外部リソース
- [chezmoi Documentation](https://www.chezmoi.io/)
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
- [Homebrew Documentation](https://docs.brew.sh/)

---

**注記**: より詳細な情報は [ARCHITECTURE.md](ARCHITECTURE.md)（英語版）を参照してください。
