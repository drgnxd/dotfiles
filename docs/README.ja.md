# dotfiles

Nix（nix-darwin + standalone home-manager）で管理している個人用のdotfilesです。

## 概要

このリポジトリには、私の macOS / Linux 環境の設定ファイルが含まれています：

*   **シェル:** Nushell（構造化データを扱うモダンなシェル、XDG準拠、モジュール構成）
    *   詳細は [architecture/nushell.ja.md](architecture/nushell.ja.md) を参照
    *   主なコマンド: `t` (task), `g` (ripgrep), `f` (fd), `cat` (bat), `y` (yazi), `update` (system upgrade)
    *   以前のZsh機能を全てNushellに移行済み
*   **レガシーシェル:** Zsh設定はgit履歴にアーカイブ済み
*   **ターミナル:** Alacritty (Solarized Darkテーマ)
*   **ブラウザ:** Floorp（Firefox系プライバシー重視ブラウザ、Homebrew cask で管理）
*   **ターミナルマルチプレクサ:** Zellij
*   **ファイルマネージャ:** Yazi (Solarized Darkテーマ)

*   **ウィンドウマネージャ:** Hammerspoon (macOSのみ)
*   **Linux デスクトップ（Phase 2）:** Hyprland、Waybar、Wofi、fcitx5 + mozc、cliphist + wl-clipboard、hypridle + hyprlock、mako、grim + slurp
*   **パッケージマネージャ:** Nix（nix-darwin + home-manager）
*   **ノート管理:** zk (Zettelkasten)
*   **タスク管理:** Taskwarrior
*   **開発ツール:** Git（delta・git-lfs・git-absorb・git-cliff統合）、clang-tools、lldb、ast-grep、nix-diff、nix-tree、lazygit、gh、opencode（`oc`・`ocd`エイリアス）、Guile（GNU Guile）
*   **コンテナ・仮想化:** Lima（Linux仮想マシン）、Docker、Docker Compose
    *   Lima管理コマンド: `lima-start`、`lima-stop`、`lls`（VM一覧）、`docker-ctx`（コンテキスト切り替え）
    *   完全XDG準拠（`~/.config/docker/`、`~/.local/share/lima/`）
*   **ユーティリティ:** atuin, bat, eza, fd, ripgrep, choose, sd, dust, duf, xh, jaq, grex, ncdu, tealdeer, tokei, typos, watchexec, hexyl, hyperfine, procs, smartmontools, age, direnv, shellcheck, pearcleaner, mas
*   **バージョンマネージャ:** uv (Python)、node、rust
*   **3D/CAD・シミュレーション:** OrcaSlicer, ngspice, Kicad（PCB設計）, qFlipper（デバイス書き込みツール）

## インストール

### 前提条件

*   macOS または Linux（Ubuntu/Fedora/Arch）
*   Git
*   Nix（flakes有効）

### 適用

```sh
darwin-rebuild switch --flake .#macbook
```

### Linux（standalone home-manager）

適用前に、`flake.nix` 冒頭の `user` と `linuxHostname` を自分の環境に合わせて変更してください。

```sh
home-manager switch --flake ~/.config/nix-config#<user>@<linuxHostname>
```

Linux サポートは CLI/シェル環境、Alacritty、および Hyprland ベースのデスクトップ環境までを対象としています。

## インストール後の設定

### 依存コマンドの確認

macOSセットアップスクリプトの実行前に、必要なコマンドを確認します：

```sh
bash scripts/check_dependencies.sh
```

不足しているコマンドがある場合は、`darwin-rebuild` を再実行してパッケージを適用してください：

```sh
darwin-rebuild switch --flake .#macbook
```

### Git設定

インストール後、ローカルのgit設定ファイルを作成してユーザー情報を設定してください：

```sh
cp ~/.config/git/config.local.example ~/.config/git/config.local
# ファイルを編集して名前とメールアドレスを設定
hx ~/.config/git/config.local
```

### Agenix 受信者設定（シークレット利用に必要）

> **注意**: `secrets/secrets.nix` に有効な SSH 公開鍵を設定しないと、暗号化されたシークレット
>（git config、npmrc、gh hosts）はアクティベーション時に復号されません。システム自体は
> 正常にビルドされますが、これらの機能は利用できません。

### OpenCode プロバイダー上書き（任意）

OpenCode のベース設定は `dot_config/opencode/opencode.json` で管理しています。
マシン固有のプロバイダー設定は `~/.config/opencode/opencode.local.json` を編集してください。

- activation 時に `~/.config/opencode/opencode.local.json` が空でなければ、その内容を `~/.config/opencode/opencode.json` にコピーします。
- 空の場合は、リポジトリ管理のテンプレートをコピーします。
- 初期サンプルは `~/.config/opencode/opencode.local.json.example` に配置されます。
- 管理対象の OpenCode plugin 一覧には `@mohak34/opencode-notifier@latest`、`opencode-supermemory@latest` を含めています。
- `~/.config/opencode/opencode.local.json` を空でない状態で使う場合は、必要な plugin が `plugin` 配列に残るようにしてください。

### pre-commit フック（任意）

pre-commit は任意です。CI では同等のセキュリティスキャンと設定検証を実行します。

ローカルでフックを有効化する場合：

```sh
nix shell nixpkgs#pre-commit -c pre-commit install
```

シークレット検出のベースラインを再生成する場合：

```sh
uv tool run detect-secrets scan --baseline .secrets.baseline
```


## 運用・管理

### Nixパッケージの管理

パッケージ定義は `home/packages.nix` にあります。

#### 追加・削除

1. `home/packages.nix` を編集
2. 適用：

```sh
darwin-rebuild switch --flake .#macbook
```

#### 入力更新

```sh
nix flake update
darwin-rebuild switch --flake .#macbook
```

## ディレクトリ構造

*   `flake.nix`: Nixエントリポイント（nix-darwin + home-manager）
*   `hosts/`: nix-darwinのシステム設定
*   `home/`: home-managerモジュールとパッケージ定義
*   `secrets/`: agenix暗号化シークレット（任意）
*   `scripts/`: プラットフォーム補助スクリプト（Nix管理）
*   `dot_config/`: 各種ツールの設定ファイル（XDG Base Directory準拠）
    *   `alacritty/`: GPU高速化ターミナルエミュレータの設定
    *   `gh/`: GitHub CLIの設定
    *   `git/`: Git設定（delta統合）
    *   `hammerspoon/`: macOS自動化（ウィンドウ管理、入力切替、カフェインモード）
    *   `helix/`: ポストモダンなモーダルテキストエディタの設定
    *   `npm/`: Node.jsパッケージマネージャの設定
    *   `opencode/`: OpenCode (AIコーディングエージェント) の設定
    *   `starship/`: クロスシェルプロンプトの設定
    *   `stats/`: Stats（システムモニター）の設定
    *   `taskwarrior/`: タスク管理の設定
    *   `zellij`: `home/modules/zellij.nix` で管理
    *   `yazi/`: 高速ターミナルファイルマネージャ（カスタムテーマ）
    *   `nushell/`: モダンなシェル設定（詳細は architecture/nushell.ja.md を参照）
        *   `autoload/`: モジュール化された設定ファイル

## 機能

### Taskwarrior

シェル非依存のTaskwarriorキャッシュシステム：

*   **自動キャッシュ**: 追加・変更時にPythonフックがキャッシュを更新
*   **構造化出力**: プロンプト/補完向けにIDと説明のリストを生成
*   **旧UI**: Zsh専用のハイライト/プレビューはアーカイブ済み


### Hammerspoon

ウィンドウ管理と自動化機能：

*   **ウィンドウ管理** (Ctrl+Alt): Rectangleスタイルのウィンドウリサイズ
    *   `←/→`: 左右半分
    *   `↑/↓`: 上下半分
    *   `Enter`: 最大化
    *   `U/I/J/K`: 4分割配置（左上、右上、左下、右下）
    *   `C`: 中央配置（80%サイズ）
*   **自動入力切替**: AlacrittyとSolに自動的に英語入力へ切り替え（SolをCmd+Spaceで呼び出した場合を含む）
*   **カフェインモード**: メニューバーアイコンからディスプレイスリープを防止（☕️/💤）
*   **チートシート** (Ctrl+Alt+/): 全キーバインドを表示
*   **自動リロード**: 設定ファイルの変更時に自動的にリロード
*   **手動リロード**: Ctrl+Shift+Rで設定をリロード

### Nushell

構造化データとモジュール構成を備えたモダンなシェル：

*   **全てがデータ**: パイプラインはプレーンテキストではなく構造化データ（テーブル、レコード）を使用
*   **XDG準拠**: 全ての設定はXDG Base Directory仕様に準拠
*   **モジュール構成**: `autoload/` ディレクトリに分割された保守性の高い設定
*   **条件付きコマンド**: スマートフォールバック（`g`は`rg`/`grep`、`f`は`fd`/`find`、`cat`は`bat`/`cat`）
*   **PATHヘルパー**: 既存パスのみを順序通りに先頭追加する`path-add`を使用
*   **主なコマンド**:
    *   `t` - Taskwarrior
    *   `g` - Ripgrep検索
    *   `f` - fd検索
    *   `cat` - bat（無い場合はcat）
    *   `la`, `ld`, `lf`, `lsize` - リスト表示の派生
    *   `y` - cwd追跡付きYaziファイルマネージャ
    *   `update` / `upgrade-all` - 統合システムアップグレード
*   **自動初期化ツール**: Starship、Zoxide、Direnv、Carapace、Atuin
*   **ローカル上書き**: マシン固有の設定用に未管理ファイル `~/.config/nushell/local.nu` をサポート（activation時に空ファイルを自動作成）
*   **ドキュメント**: 詳細は [architecture/nushell.ja.md](architecture/nushell.ja.md) を参照

### Helix の Language Server (LSP) サポート

この設定では Helix エディタ用の言語サーバ統合を追加し、それに対応する Nix パッケージをドキュメント化しています。`pyright`, `ruff`, `marksman`, `taplo`, `lua-language-server`, `yaml-language-server`, `texlab` などの推奨LSPは Nix パッケージで提供します。Rust の `rust-analyzer` は `rustup` 前提（`rustup component add rust-analyzer`）です。エディタ設定は `dot_config/helix/`、パッケージ定義は `home/packages.nix` を参照してください。

## ソフトウェアポリシー

新しいツールを追加する場合は OSS ライセンス（MIT、Apache 2.0、GPL、MPL 等）を優先します。
既存のツールはライセンスに関わらず維持します。

新規ツール提案時:
1. ライセンスが OSS 互換であることを確認
2. PR の説明にライセンスを記載
3. プロプライエタリツールがやむを得ない場合は、コミット本文に理由を記載

## ライセンス

MIT License
