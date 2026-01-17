# dotfiles

[chezmoi](https://www.chezmoi.io/)で管理している個人用のdotfilesです。

## 概要

このリポジトリには、私のmacOSおよびLinux環境の設定ファイルが含まれています：

*   **シェル:** Zsh (Starshipプロンプト、zoxide、fzf)
*   **ターミナル:** Alacritty (Solarized Darkテーマ)
*   **ファイルマネージャ:** Yazi (Solarized Darkテーマ)

*   **ウィンドウマネージャ:** Hammerspoon (macOSのみ)
*   **パッケージマネージャ:** Homebrew (macOS), ネイティブパッケージマネージャ (Linux)
*   **ノート管理:** zk (Zettelkasten)
*   **タスク管理:** Taskwarrior
*   **開発ツール:** Git (delta・git-lfs統合)、lazygit、gh、opencode（`oc`・`ocd`エイリアス）、Guile（GNU Guile）
*   **ユーティリティ:** bat, eza, fd, ripgrep, ncdu, smartmontools, direnv, pearcleaner
*   **バージョンマネージャ:** pyenv、node、rust
*   **3D/CAD・シミュレーション:** OrcaSlicer, ngspice, Kicad（PCB設計）, qFlipper（デバイス書き込みツール）

## インストール

### 前提条件

*   macOS または Linux
*   Git
*   curl/wget

### ワンライナーインストール

```sh
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply drgnxd
```

または、すでに`chezmoi`がインストールされている場合：

```sh
chezmoi init --apply drgnxd
```

## インストール後の設定


### Git設定


インストール後、ローカルのgit設定ファイルを作成してユーザー情報を設定してください：


```sh
cp ~/.config/git/config.local.example ~/.config/git/config.local
# ファイルを編集して名前とメールアドレスを設定
hx ~/.config/git/config.local
```



## 運用・管理

### Homebrewパッケージの管理

本リポジトリでは、`dot_Brewfile` を `chezmoi` のソースディレクトリ内で直接管理し、`~/.Brewfile`は使わず`$XDG_CONFIG_HOME/homebrew/Brewfile`（既定: `~/.config/homebrew/Brewfile`）を使用します。

**実行フラグ（安全性関連）**
- `run_onchange_darwin_install_packages.sh.tmpl`: Brewfileをレンダリングして `brew bundle` を実行（追加フラグなし）。
- `run_onchange_darwin_import_stats.sh.tmpl`: plistが無い場合は失敗で終了。
- `run_onchange_darwin_setup_cloud_symlinks.sh.tmpl`: シンボリックリンク作成に `FORCE=1` が必須（対話式。非symlinkターゲットは上書きしない）。
- `run_onchange_darwin_login_items.sh.tmpl`: ログイン項目変更に `ALLOW_GUI=1` が必須。
- `run_onchange_darwin_security_hardening.sh.tmpl`: ハードニング実行に `ALLOW_HARDEN=1` が必須。失敗を集計して報告。
- `run_onchange_darwin_system_defaults.sh.tmpl`: macOSデフォルト変更に `ALLOW_DEFAULTS=1` が必須。オプションで `ALLOW_LSQUARANTINE_OFF=1`, `ALLOW_SPOTLIGHT_DISABLE=1`。
- `run_onchange_darwin_keyboard.sh.tmpl`: キーボード設定適用に `ALLOW_KEYBOARD_APPLY=1` が必須（`--apply`時）。

#### パッケージの追加・削除

**推奨フロー (宣言的管理):**

1. ソースファイルを編集してパッケージを追記・削除します：
    ```sh
    chezmoi edit dot_Brewfile
    ```
2. 変更をシステムに適用（インストール）します：
    ```sh
    chezmoi apply
    ```

**代替フロー (現在の環境を取り込み):**

手動で `brew install` したパッケージを管理ファイルに反映させる場合：

```sh
# 現在の環境で dot_Brewfile を上書き更新（説明文付き）
brew bundle dump --file="$(chezmoi source-path)/dot_Brewfile" --force --describe
```

#### 同期状態の確認

定義ファイル（`dot_Brewfile`）と現在のシステム状態の差異を確認します。

  * **不足パッケージの確認** (定義にあるがインストールされていないもの):

    ```sh
    brew bundle check --file="$(chezmoi source-path)/dot_Brewfile" --verbose
    ```

  * **管理外パッケージの確認** (インストールされているが定義にないもの):

    ```sh
    # 削除はせず、削除対象リストを表示 (Dry Run)
    brew bundle cleanup --file="$(chezmoi source-path)/dot_Brewfile"
    ```

#### 自動アップデート

本設定では、パッケージを最新に保つために `homebrew/autoupdate` を導入しています。
自動アップデート（`--greedy` によるGUIアプリを含む）を有効にするには、以下のコマンドを実行します：

```sh
brew autoupdate start 43200 --upgrade --cleanup --greedy
```

これにより、12時間ごとにアップデートがチェックされます。

<!-- end list -->

## ディレクトリ構造

*   `.chezmoiignore.tmpl`: OSに基づいてファイルを無視するためのテンプレート（例：LinuxでmacOSアプリを無視）
*   `dot_Brewfile`: インストールするHomebrewパッケージのリスト（macOSのみ）
*   `dot_config/`: 各種ツールの設定ファイル（XDG Base Directory準拠）
    *   `alacritty/`: GPU高速化ターミナルエミュレータの設定
    *   `fsh/`: Zsh Fast Syntax Highlightingのカスタムテーマ
    *   `gh/`: GitHub CLIの設定
    *   `git/`: Git設定（delta統合）
    *   `hammerspoon/`: macOS自動化（ウィンドウ管理、入力切替、カフェインモード）
    *   `helix/`: ポストモダンなモーダルテキストエディタの設定
    *   `npm/`: Node.jsパッケージマネージャの設定
    *   `opencode/`: OpenCode (AIコーディングエージェント) の設定
    *   `starship/`: クロスシェルプロンプトの設定
    *   `stats/`: Stats（システムモニター）の設定
    *   `taskwarrior/`: タスク管理の設定
    *   `tmux/`: ターミナルマルチプレクサ（Solarized Darkテーマ）
    *   `yazi/`: 高速ターミナルファイルマネージャ（カスタムテーマ）
    *   `zsh/`: Zsh設定（プラグインと補完機能）
*   `run_onchange_darwin_install_packages.sh.tmpl`: `chezmoi apply`後に`brew bundle`を実行するスクリプト（macOSのみ）

## 機能

### Taskwarrior 

タスク管理を効率化するための高度なZsh連携機能を搭載しています： 

*   **動的シンタックスハイライト**: 入力されたタスクIDの有効性をキャッシュと照合し、リアルタイムでハイライト表示します。 
*   **ライブプレビュー**: タスクIDの入力中、ミニバッファに該当するタスクの内容を自動的に表示します。 
*   **高速な補完機能**: ローカルキャッシュを利用し、タスクの説明文を含む補完候補を瞬時に提示します。 
*   **自動キャッシュ管理**: タスクの追加・変更時にPythonフックが自動的にキャッシュを更新します。 


### Hammerspoon

ウィンドウ管理と自動化機能：

*   **ウィンドウ管理** (Ctrl+Alt): Rectangleスタイルのウィンドウリサイズ
    *   `←/→`: 左右半分
    *   `↑/↓`: 上下半分
    *   `Enter`: 最大化
    *   `U/I/J/K`: 4分割配置（左上、右上、左下、右下）
    *   `C`: 中央配置（80%サイズ）
*   **自動入力切替**: AlacrittyとSolに自動的に英語入力へ切り替え
*   **カフェインモード**: メニューバーアイコンからディスプレイスリープを防止（☕️/💤）
*   **チートシート** (Ctrl+Alt+/): 全キーバインドを表示
*   **自動リロード**: 設定ファイルの変更時に自動的にリロード
*   **手動リロード**: Ctrl+Shift+Rで設定をリロード

## ライセンス

MIT License
