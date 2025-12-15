# Fast-Syntax-Highlighting カスタムChroma定義

このディレクトリには、[fast-syntax-highlighting](https://github.com/zdharma-continuum/fast-syntax-highlighting) プラグイン用のカスタムChroma関数が含まれています。

## 概要

fast-syntax-highlightingは、Zshコマンドラインの構文ハイライトを提供しますが、デフォルトではモダンなCLIツールの多くをサポートしていません。このディレクトリのChroma定義により、以下のツールに対して適切なシンタックスハイライトが提供されます。

## サポートされているコマンド

| コマンド | 説明 | Chroma定義ファイル |
|---------|------|-------------------|
| `bat` | catの代替（シンタックスハイライト付き） | `chroma-bat.ch` |
| `brew` | macOS/Linux用パッケージマネージャ | `chroma-brew.ch` |
| `btop` | リソースモニター | `chroma-btop.ch` |
| `chezmoi` | dotfile管理ツール | `chroma-chezmoi.ch` |
| `delta` | git diffのページャー | `chroma-delta.ch` |
| `direnv` | ディレクトリごとの環境変数管理 | `chroma-direnv.ch` |
| `eza` | lsの代替（モダンなファイル一覧表示） | `chroma-eza.ch` |
| `fd` | findの代替（高速検索） | `chroma-fd.ch` |
| `fzf` | コマンドラインファジーファインダー | `chroma-fzf.ch` |
| `gh` | GitHub CLI | `chroma-gh.ch` |
| `git-crypt` | Gitでのファイル暗号化 | `chroma-git-crypt.ch` |
| `gpg` | GNU Privacy Guard (暗号化ツール) | `chroma-gpg.ch` |
| `helix` / `hx` | ポストモダンなモーダルテキストエディタ | `chroma-helix.ch` |
| `lazygit` | Git用のシンプルなTUI | `chroma-lazygit.ch` |
| `npm` | Node.jsパッケージマネージャ | `chroma-npm.ch` |
| `pyenv` | Pythonバージョン管理 | `chroma-pyenv.ch` |
| `rg` | ripgrep（grepの代替） | `chroma-rg.ch` |
| `starship` | クロスシェルプロンプト | `chroma-starship.ch` |
| `task` | Taskwarrior（タスク管理） | `chroma-task.ch` |
| `tmux` | ターミナルマルチプレクサ | `chroma-tmux.ch` |
| `wget` | ネットワークダウンローダ | `chroma-wget.ch` |
| `yazi` | ターミナルファイルマネージャ | `chroma-yazi.ch` |
| `zk` | Zettelkastenノート管理 | `chroma-zk.ch` |
| `zoxide` | スマートなディレクトリ移動 | `chroma-zoxide.ch` |

## ハイライトの種類

各Chroma定義は以下の要素を適切にハイライトします：

- **オプション**: `--long-option` や `-s` などのコマンドオプション
- **サブコマンド**: `git commit` の `commit` のようなサブコマンド
- **パス**: ファイルやディレクトリのパス
- **パターン**: 検索パターンやグロブパターン
- **値**: オプションに渡される値

## 自動読み込み

これらのChroma定義は、`.zsh_plugins` ファイルで fast-syntax-highlighting の読み込み後に自動的に登録されます：

```zsh
# カスタムChroma定義の読み込み
local fsh_config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fsh"

if [ -d "$fsh_config_dir" ]; then
    for chroma_file in "$fsh_config_dir"/chroma-*.ch(N); do
        local cmd_name="${chroma_file:t:r:s/chroma-//}"
        if [ -f "$chroma_file" ]; then
            source "$chroma_file"
            chroma_functions[${cmd_name}]="chroma/${cmd_name}"
        fi
    done
fi
```

## カスタムChroma定義の追加方法

新しいコマンドのChroma定義を追加するには：

1. このディレクトリに `chroma-<コマンド名>.ch` ファイルを作成
2. 以下のテンプレートを使用して定義を記述：

```zsh
# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for <コマンド名>

(( next_word = 2 | 8192 ))

local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
local __style

(( __first_call )) && {
    FAST_HIGHLIGHT[chroma-<コマンド名>-counter]=0
    FAST_HIGHLIGHT[chroma-<コマンド名>-counter-all]=1
    return 1
}

(( FAST_HIGHLIGHT[chroma-<コマンド名>-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

# ハイライトロジック
case "$__wrd" in
    --option)
        __style=${FAST_THEME_NAME}double-hyphen-option
        ;;
    -*)
        __style=${FAST_THEME_NAME}single-hyphen-option
        ;;
    *)
        __style=${FAST_THEME_NAME}default
        ;;
esac

[[ -n "$__style" ]] && (( __start >= 0 )) && reply+=("$__start $__end ${FAST_HIGHLIGHT_STYLES[$__style]}")

return 0
```

3. Zshを再起動するか、`.zshrc` を再読み込み

## 利用可能なスタイル

fast-syntax-highlighting で利用可能な主なスタイル：

- `${FAST_THEME_NAME}default` - デフォルトのテキスト
- `${FAST_THEME_NAME}unknown-token` - 不明なトークン
- `${FAST_THEME_NAME}reserved-word` - 予約語
- `${FAST_THEME_NAME}subcommand` - サブコマンド
- `${FAST_THEME_NAME}alias` - エイリアス
- `${FAST_THEME_NAME}suffix-alias` - サフィックスエイリアス
- `${FAST_THEME_NAME}global-alias` - グローバルエイリアス
- `${FAST_THEME_NAME}builtin` - ビルトインコマンド
- `${FAST_THEME_NAME}function` - 関数
- `${FAST_THEME_NAME}command` - コマンド
- `${FAST_THEME_NAME}precommand` - プリコマンド
- `${FAST_THEME_NAME}commandseparator` - コマンドセパレータ
- `${FAST_THEME_NAME}hashed-command` - ハッシュされたコマンド
- `${FAST_THEME_NAME}path` - パス
- `${FAST_THEME_NAME}path-to-dir` - ディレクトリへのパス
- `${FAST_THEME_NAME}globbing` - グロビングパターン
- `${FAST_THEME_NAME}single-hyphen-option` - 単一ハイフンオプション
- `${FAST_THEME_NAME}double-hyphen-option` - 二重ハイフンオプション
- `${FAST_THEME_NAME}back-quoted-argument` - バッククォート引数
- `${FAST_THEME_NAME}single-quoted-argument` - シングルクォート引数
- `${FAST_THEME_NAME}double-quoted-argument` - ダブルクォート引数
- `${FAST_THEME_NAME}dollar-quoted-argument` - ドルクォート引数
- `${FAST_THEME_NAME}redirection` - リダイレクション
- `${FAST_THEME_NAME}comment` - コメント
- `${FAST_THEME_NAME}variable` - 変数
- `${FAST_THEME_NAME}mathvar` - 数学変数
- `${FAST_THEME_NAME}mathnum` - 数学数値
- `${FAST_THEME_NAME}matherr` - 数学エラー
- `${FAST_THEME_NAME}assign` - 代入
- `${FAST_THEME_NAME}allowable-option` - 許可されたオプション

## 参考資料

- [fast-syntax-highlighting GitHub](https://github.com/zdharma-continuum/fast-syntax-highlighting)
- [Chroma Guide](https://github.com/zdharma-continuum/fast-syntax-highlighting/blob/main/CHROMA_GUIDE.adoc)
