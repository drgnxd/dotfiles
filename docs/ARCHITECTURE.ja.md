# アーキテクチャ概要

## クイックリンク
- [Nushell 設定](architecture/nushell.ja.md) - モジュール構成のモダンなシェル
- [XDG Base Directory 準拠](architecture/xdg-compliance.ja.md)
- [セキュリティモデルとガードフラグ](architecture/security-model.ja.md)
- [プラットフォームサポート](architecture/platform-support.ja.md) - macOS（nix-darwin）+ Linux（standalone home-manager）
- [Taskwarrior 統合](architecture/taskwarrior.ja.md)
- [開発ワークフロー](architecture/workflow.ja.md)
- [トラブルシューティング](architecture/troubleshooting.ja.md)

## 設計原則
- XDG 準拠で設定の場所を統一
- ガード付きの対話操作のみ明示的に許可
- Nix モジュールでプラットフォーム差異を吸収（nix-darwin + home-manager）
- 宣言的な適用と冪等なフック

---

## ディレクトリ構成

```
~/.config/nix-config/                # Nix フレークリポジトリ
|- flake.nix                         # エントリポイント（nix-darwin + home-manager）
|- flake.lock                        # 依存固定
|- hosts/
|  |- macbook/
|  |  |- default.nix                 # nix-darwin システム設定
|  |  `- launchd.nix                 # launchd エージェント/サービス
|- home/
|  |- default.nix                    # home-manager エントリポイント（モジュール読込）
|  |- packages.nix                   # パッケージ一覧
|  `- modules/
|     |- activation/
|     |  |- directories.nix          # ローカル設定/キャッシュディレクトリ作成
|     |  |- macos_defaults.nix       # macOS デフォルト設定（Darwin専用）
|     |  |- nushell_ensure.nix       # Nushell ローカル上書きファイル保証
|     |  |- opencode.nix             # OpenCode 資産/ルール同期
|     |  `- taskwarrior_ensure.nix   # Taskwarrior ローカル上書きファイル保証
|     |- linux/
|     |  |- desktop.nix              # Linux デスクトップ統合モジュール
|     |  |- hyprland.nix             # Hyprland コンポジタ設定
|     |  |- waybar.nix               # Waybar ステータスバー設定
|     |  `- fcitx5.nix               # fcitx5/mozc 入力方式
|     |- alacritty.nix               # ターミナル設定 + 補助スクリプト
|     |- atuin.nix                   # Atuin 履歴連携
|     |- bat.nix                     # bat 設定
|     |- direnv.nix                  # direnv 連携
|     |- fzf.nix                     # fzf 連携
|     |- gh.nix                      # GitHub CLI 設定
|     |- git.nix                     # git/delta + local テンプレート
|     |- hammerspoon.nix             # Hammerspoon Lua スクリプト
|     |- helix.nix                   # Helix 設定 + テーマ
|     |- nushell.nix                 # Nushell ファイル（autoload/modules）
|     |- nushell-integrations.nix    # 生成済み Nushell init スクリプト作成
|     |- shellcheck.nix              # shellcheckrc
|     |- starship.nix                # Starship プロンプト設定
|     |- taskwarrior.nix             # Taskwarrior 設定 + 実行可能フック
|     |- xdg_config_files.nix        # Darwin専用 npmrc 配備
|     |- xdg_desktop_files.nix       # Darwin デスクトップ/Stats plist
|     |- yazi.nix                    # Yazi ファイルマネージャ設定
|     |- zellij.nix                  # Zellij ターミナルマルチプレクサ
|     `- zoxide.nix                  # zoxide 連携
|- dot_config/                       # 設定ソース（XDG）
|  |- alacritty/
|  |- bat/
|  |- gh/
|  |- git/
|  |- hammerspoon/
|  |- helix/
|  |- npm/
|  |- nushell/
|  |- opencode/
|  |- starship/
|  |- stats/
|  |- taskwarrior/
|  `- yazi/
|- scripts/
|  `- darwin/setup_cloud_symlinks.sh # CloudStorage シンボリックリンク補助
|- secrets/
|  `- secrets.nix                    # agenix キーマップ
|- docs/                             # アーキテクチャ/運用ドキュメント
|- README.md                         # メイン README（英語）
|- docs/README.ja.md                 # 日本語 README
`- docs/ARCHITECTURE.ja.md           # このファイル
```

---

## Component Architecture

### 1. Nushell Ecosystem (Active)

詳細は [Nushell 設定](architecture/nushell.ja.md) を参照してください。

**Entry Points**:
- `env.nu` - `autoload/01-env.nu` と `autoload/02-path.nu` を読み込み
- `config.nu` - autoload モジュールと local 上書きを読み込み

**Modular Architecture**:
```
autoload/
|- 01-env.nu           # XDG パス, ENV_CONVERSIONS
|- 02-path.nu          # path-add ヘルパー付き PATH
|- 03-aliases.nu       # 条件付きコマンドエイリアス
|- 04-functions.nu     # カスタムラッパー（yazi, zk など）
|- 05-completions.nu   # 動的補完
|- 06-integrations.nu  # 統合ラッパー
|- 07-abbreviations.nu # Fish風略語展開（Space/Enter）
|- 08-taskwarrior.nu   # Taskwarrior プロンプトプレビュー
|- 09-lima.nu          # Lima/Docker ヘルパー
`- 10-source-tools.nu  # キャッシュ済みツール初期化 + direnv PWD フック
```

**Key Features**:
- すべてを構造化データとして扱う（テキストストリームではない）
- XDG Base Directory 準拠
- fallback 付きの条件分岐ロード
- 存在確認付き PATH ヘルパー（`path-add`）
- `~/.config/nushell/local.nu` によるローカル上書き（activation で空ファイル保証）

**Module Loading**:
```nushell
# env.nu
const config_dir = ($nu.home-dir | path join '.config' 'nushell')
source ($config_dir | path join 'autoload' '01-env.nu')
source ($config_dir | path join 'autoload' '02-path.nu')

# config.nu
const config_dir = ($nu.home-dir | path join '.config' 'nushell')
source ($config_dir | path join 'autoload' '00-constants.nu')
source ($config_dir | path join 'autoload' '00-helpers.nu')
...
```

モジュールパスを `$nu.home-dir` 基準に固定することで、実体が Nix store 側でも安定して読み込めます。

### 2. Linux Desktop Ecosystem (Hyprland)

Linux デスクトップ統合は `home/modules/linux/` の Home Manager モジュールと、`dot_config/` 配下の XDG 設定ソースで管理します。

**Desktop components**:
- Hyprland (`dot_config/hypr/hyprland.conf`)
- Waybar (`dot_config/waybar/config.jsonc`, `dot_config/waybar/style.css`)
- Wofi (`dot_config/wofi/config`, `dot_config/wofi/style.css`)
- Mako (`dot_config/mako/config`)
- hypridle + hyprlock (`dot_config/hypr/hypridle.conf`, `dot_config/hypr/hyprlock.conf`)
- fcitx5 + mozc (`home/modules/linux/fcitx5.nix`)
- 補助スクリプト (`scripts/linux/hypr-*`)

**Hammerspoon -> Hyprland mapping**:

| macOS (Hammerspoon) | Linux (Hyprland) |
|---------------------|------------------|
| Window management (Ctrl+Alt) | Hyprland keybinds (Ctrl+Alt) |
| Sol launcher (Cmd+Space) | Wofi (Super+Space) |
| Auto input switching | fcitx5 `windowrulev2` |
| Caffeine mode | hypridle toggle script |
| Cheatsheet (Ctrl+Alt+/) | Wofi dmenu script |
| Stats.app menubar | Waybar modules |
| Maccy clipboard | cliphist + wl-clipboard |

### 3. Taskwarrior Integration

詳細は [Taskwarrior 統合](architecture/taskwarrior.ja.md) を参照してください。

### 4. Nix Integration

**Flake-based entrypoint**:
- `flake.nix` で nix-darwin / home-manager / agenix を統合
- `hosts/macbook/default.nix` がシステム設定を管理
- `hosts/macbook/launchd.nix` が launchd エージェント/サービスを管理
- `home/default.nix` がユーザーモジュールを合成
- `home/modules/activation/` がユーザーデフォルト・OpenCode 同期・ローカル雛形作成を管理
- `home/modules/linux/` が Linux デスクトップモジュール（Hyprland/Waybar/fcitx5）を管理
- ツール別モジュール（`alacritty.nix`, `bat.nix`, `atuin.nix`, `zoxide.nix`, `direnv.nix`, `fzf.nix`, `gh.nix`, `starship.nix` など）が個別設定を保持

**Secrets**:
- `secrets/*.age` を `agenix` で暗号化
- activation 時にユーザー設定パスへ復号配置

### 5. Container and Virtualization (Docker + Lima)

**Architecture**: シンボリックリンク不要の XDG 準拠コンテナ環境

**Configuration** (`dot_config/nushell/autoload/01-env.nu`):
```nushell
$env.DOCKER_CONFIG = ($env.XDG_CONFIG_HOME | path join "docker")
$env.LIMA_HOME = ($env.XDG_DATA_HOME | path join "lima")
```

**Directory Structure**:
```
~/.config/docker/
  |- config.json           # Docker CLI 設定（context, auth）
  `- contexts/             # Docker context 定義
     `- meta/*/meta.json   # context メタデータ（endpoint）

~/.local/share/lima/
  |- _config/              # Lima グローバル設定
  `- <vm-name>/            # VM インスタンス（myvm, dev, prod など）
     |- lima.yaml          # VM 設定（CPU, memory, mounts）
     |- sock/docker.sock   # Docker ソケット（VM内Docker有効時）
     |- diffdisk           # VM ディスクイメージ
     `- ...                # VM ランタイムデータ
```

**Management Functions** (`dot_config/nushell/autoload/09-lima.nu`):

| Function | Purpose | Example |
|----------|---------|---------|
| `lima-start <vm>` | VM 起動 + Docker context 自動切替 | `lima-start dev` |
| `lima-stop <vm>` | VM を正常停止 | `lima-stop dev` |
| `lima-status` (alias: `lls`) | VM 一覧と状態表示 | `lls` |
| `lima-shell <vm>` | VM 内シェルを開く | `lima-shell dev` |
| `lima-delete <vm>` | 確認付き VM 削除 | `lima-delete old-vm` |
| `docker-ctx <name>` (alias: `dctx`) | Docker context 切替 | `dctx dev-context` |
| `docker-ctx-reset` | default context へ戻す | `docker-ctx-reset` |
| `lima-docker-context <vm>` | VM 用 Docker context 作成/更新 | `lima-docker-context dev` |

**Typical Workflow**:
```bash
# 1. Docker 付き Lima VM を作成
limactl create --name=dev template://docker

# 2. VM を起動（context があれば自動切替）
lima-start dev

# 3. VM 用 Docker context を作成
lima-docker-context dev

# 4. Docker 接続確認
docker ps
docker info

# 5. 通常どおり Docker を利用
docker run -d --name nginx nginx:alpine

# 6. 作業後に VM 停止
lima-stop dev
```

**Design Benefits**:
- XDG 準拠でパスの可搬性が高い
- Docker/Lima にシンボリックリンクが不要
- VM ごとの context 分離で複数環境を扱いやすい

---

## Key Technical Decisions

### 1. XDG Base Directory

詳細は [XDG Base Directory 準拠](architecture/xdg-compliance.ja.md) を参照してください。

### 2. Guard Flags Over Prompts

詳細は [セキュリティモデルとガードフラグ](architecture/security-model.ja.md) を参照してください。

### 3. Declarative macOS Configuration

- システム設定と launch agent は nix-darwin で管理
- ユーザー設定は home-manager で管理

### 4. Taskwarrior Cache System

詳細は [Taskwarrior 統合](architecture/taskwarrior.ja.md) を参照してください。

### 5. No Symlinks for Docker/Lima

- 環境変数ベースでシンプルに管理
- 間接層を減らしてデバッグしやすくする

---

## Performance Optimizations

### 1. Nushell Startup

- 決定的な autoload 順序で起動を安定化
- `~/.cache/nushell-init` のキャッシュ済み init を読み込み
- 任意ツールのランタイムチェックを最小限に抑制

### 2. Taskwarrior

- キャッシュ更新はスロットリング + 非同期実行（taskwarrior ドキュメント参照）

---

## Future Enhancements

**検討中（未実装）**:
- [ ] マルチマシンプロファイル（work/personal）
- [ ] git hook による自動バックアップ
- [ ] 初期セットアップ用 Ansible playbook
- [ ] Docker ベースのテスト環境

---

## Reference

**関連ドキュメント**:
- [Nushell 設定](architecture/nushell.ja.md)
- [Taskwarrior キャッシュ設計](../dot_config/taskwarrior/CACHE_ARCHITECTURE.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Commit Convention](COMMIT_CONVENTION.md)

## Archived Components

### Zsh Configuration (Legacy)

Zsh 設定は **アーカイブ済み** で、現在は Nushell へ移行済みです。旧構成は以下を含みます。

- **Entry Point**: `.zshrc.tmpl` によるモジュール読み込み
- **Plugin System**: zplug/zinit + Fast Syntax Highlighting
- **Modules**: `.exports`, `.aliases`, `.functions`, `.zsh_plugins`
- **Completions**: コマンド別補完定義
- **Custom Themes**: 26 種類の FSH カラーテーマ

**Migration Date**: 2026-01
**Status**: Nushell 構成へ置き換え済み
**Access**: 必要時は git history を参照

**Key Differences from Zsh**:
| Feature | Zsh | Nushell |
|---------|-----|---------|
| Data Model | Text streams | Structured tables/records |
| Configuration | Multiple sourced files | Modular `autoload/` structure |
| Aliases | Simple string replacement | `export def` functions with logic |
| PATH Management | Manual string manipulation | `path-add` helper (prepend + exists check) |
| Environment | `.zshenv` + `.zshrc` | `env.nu` + `config.nu` |

---

**External Resources**:
- [Nix Manual](https://nixos.org/manual/nix/stable/)
- [nix-darwin](https://github.com/LnL7/nix-darwin)
- [home-manager](https://github.com/nix-community/home-manager)
- [XDG Base Directory Spec](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Last Updated**: 2026-04
**Author**: drgnxd
**License**: MIT
