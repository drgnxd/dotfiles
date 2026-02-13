# Nushell設定

Nushellは、全てをデータとして扱うモダンなシェルです。この設定は、XDG準拠と条件付きコマンド読み込みを備えた、モジュール化され保守性の高い構成を提供します。

## アーキテクチャ

`autoload/`ディレクトリパターンを使用したモジュール構造を採用しています：

```
dot_config/nushell/
├── env.nu                  # ~/.config/nushell/env.nu
├── config.nu               # ~/.config/nushell/config.nu
├── autoload/
    ├── 00-helpers.nu       # 共通ヘルパー
    ├── 01-env.nu           # 環境変数とXDGパス
    ├── 02-path.nu          # path-addヘルパーを使ったPATH設定
    ├── 03-aliases.nu       # フォールバック付きエイリアス
    ├── 04-functions.nu     # カスタム関数とラッパー
    ├── 05-completions.nu   # コマンド補完
    ├── 06-integrations.nu  # 統合キャッシュ更新の遅延ラッパー
    ├── 07-source-tools.nu  # キャッシュ読み込み
    ├── 08-taskwarrior.nu   # Taskwarriorプレビュー/コマンドの遅延ラッパー
    └── 09-lima.nu          # Lima/Dockerの遅延ラッパー
└── modules/
    ├── integrations.nu     # キャッシュ生成（オンデマンド）
    ├── taskwarrior.nu      # Taskwarriorプレビュー＋キャッシュ更新
    └── lima.nu             # Lima/Dockerコマンド
```

## モジュール読み込み

`env.nu` と `config.nu` は、`$nu.home-dir` から `~/.config/nushell` を組み立てて `config_dir` を求め、その配下を相対的に `source` します：

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

この方式により、Home Manager で設定ファイル本体が `/nix/store` 側にあっても、`~/.config/nushell` を基準に安定してモジュール解決できます。

ユーザー名やホームディレクトリが変わっても、手動で固定パスを書き換える必要はありません。

重い処理は`modules/`に分離し、`autoload/`の軽量ラッパーが `autoload/00-constants.nu` で定義したモジュール定数経由で `overlay use` して必要時に読み込みます。これにより起動を軽くしつつ、ハードコードされたパス依存を避けます。

## 主な機能

### 1. XDG Base Directory準拠

全てのアプリケーションデータはXDG準拠の場所に保存されます：
- 設定: `~/.config/`
- キャッシュ: `~/.cache/`
- データ: `~/.local/share/`
- 状態: `~/.local/state/`

完全なXDGパス設定は`01-env.nu`を参照してください。

### 2. 条件付きコマンド読み込み

コマンドは、標準ツールへの自動フォールバック付きで定義されます：

```nushell
export def g [...args] {
    if (has-cmd rg) {
        rg ...$args
    } else {
        ^grep ...$args
    }
}
```

これにより、モダンなツール（bat、fd、ripgrep）がインストールされていない異なるシステムでも設定が機能します。

### 3. PATH管理ヘルパー

PATHは、存在するパスだけを先頭追加する小さなヘルパーで管理します：

```nushell
def --env path-add [new_path: string] {
    if ($new_path | path exists) {
        $env.PATH = ($env.PATH | prepend $new_path | uniq)
    }
}
```

### 4. ENV_CONVERSIONS

コロン区切りの環境変数（PATH、TERMINFO_DIRS等）は、適切なコンバータで処理されます：

```nushell
$env.ENV_CONVERSIONS = ($env.ENV_CONVERSIONS | default {}) | merge {
    "PATH": {
        from_string: {|s| $s | split row (char esep) | path expand --no-symlink }
        to_string: {|v| $v | path expand --no-symlink | str join (char esep) }
    }
}
```

## 利用可能なエイリアスとコマンド

### ファイル操作
- `la`, `ld`, `lf`, `lsize` - リスト表示の派生（全/ディレクトリ/ファイル/サイズ順）
- `cat` - ファイル表示（使用可能な場合はbatを使用）
- `f` - ファイル検索（使用可能な場合はfdを使用）

### 検索
- `g` - ripgrepで検索（フォールバックはgrep）

### アプリケーションショートカット
- `t` - Taskwarrior
- `lg` - LazyGit
- `oc`, `ocd` - opencode
- `pload` - Proton Pass CLI

### Lima/Docker
- `lls` - Lima VM一覧
- `dctx` - Dockerコンテキスト切り替え
- `dctx-reset` - デフォルトにリセット

### 関数
- `y` - cwd追跡付きYaziファイルマネージャ
- `zk` - git同期付きZettelkastenノート
- `ppget` - Proton Passパスワード取得
- `upgrade-all` / `update` - 統合システムアップグレード
- `save-stats` - Stats.app設定のエクスポート
- `bundle-id` - macOSアプリのバンドルID取得
- `integrations-cache-update` - キャッシュ初期化スクリプト再生成（Starship/Zoxide/Carapace/Atuin）

## サードパーティ統合

### キャッシュ統合ツール
- **Starship** - クロスシェルプロンプト
- **Zoxide** - スマートディレクトリジャンプ
- **Carapace** - コマンド補完
- **Atuin** - シェル履歴同期
- **Direnv** - 環境管理（起動時に読み込み、キャッシュなし）

キャッシュ生成は`integrations-cache-update`でオンデマンド実行します。生成された初期化スクリプトは`~/.cache/nushell-init`にキャッシュされ、`autoload/07-source-tools.nu`で読み込みます。

## 設定値

### 履歴
- 形式: SQLite
- 最大サイズ: 1,000,000エントリ
- 入力時同期: 有効
- 分離: 無効

### UI
- バナー: 無効
- エラースタイル: Fancy
- 編集モード: Readline互換（Nushell の `emacs` モード）
- Kittyプロトコル: 有効
- ブラケット貼り付け: 有効

### 補完
- 大文字小文字区別: なし
- アルゴリズム: Prefix
- 外部補完: Carapace（使用可能な場合）

## Zshからの移行

この設定は以前のZshセットアップを置き換えます。主な変更点：

1. **.zshenv/.zshrcなし** - Nushellは`env.nu`と`config.nu`を使用
2. **.aliasesなし** - エイリアスは`03-aliases.nu`の`export def`コマンド
3. **.functionsなし** - 関数は`04-functions.nu`の`export def`
4. **モジュールシステム** - シェルのソースではなくNushellのモジュールシステムを使用

## ローカル上書き

マシン固有の設定には`~/.config/nushell/local.nu`を作成してください：

```nushell
# ~/.config/nushell/local.nu
$env.MY_LOCAL_VAR = "value"
alias mylocal = echo "local alias"
```

このファイルは`config.nu`の最後で自動的に読み込まれます。

## 参考

- [Nushell Book](https://www.nushell.sh/book/)
- [Nushell Cookbook](https://www.nushell.sh/cookbook/)
