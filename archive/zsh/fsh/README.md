# Fast Syntax Highlighting - Chroma System Guide

## 概要

このディレクトリには、Fast Syntax Highlighting (FSH) 用のカスタムChroma定義が含まれています。Chromaは特定のコマンドに対して、オプションやサブコマンドを認識し、インテリジェントなシンタックスハイライトを提供します。

---

## インストール済みChroma一覧

本リポジトリでは、**35個**のカスタムChroma定義を提供しています：

| コマンド | ファイル名 | 説明 |
|---------|-----------|------|
| `bat` | `chroma-bat.ch` | cat代替コマンドのハイライト |
| `brew` | `chroma-brew.ch` | Homebrewパッケージマネージャ |
| `btop` | `chroma-btop.ch` | リソースモニター |
| `chezmoi` | `chroma-chezmoi.ch` | dotfile管理ツール |
| `delta` | `chroma-delta.ch` | Git diff viewer |
| `direnv` | `chroma-direnv.ch` | 環境変数マネージャ |
| `eza` | `chroma-eza.ch` | ls代替コマンド |
| `fd` | `chroma-fd.ch` | find代替コマンド |
| `fzf` | `chroma-fzf.ch` | ファジーファインダー |
| `gh` | `chroma-gh.ch` | GitHub CLI |
| `git-crypt` | `chroma-git-crypt.ch` | Git暗号化ツール |
| `gpg` | `chroma-gpg.ch` | GnuPG暗号化 |
| `helix` | `chroma-helix.ch` | モーダルエディタ |
| `lazygit` | `chroma-lazygit.ch` | Git TUI |
| `mas` | `chroma-mas.ch` | Mac App Store CLI |
| `npm` | `chroma-npm.ch` | Node.jsパッケージマネージャ |
| `pip` | `chroma-pip.ch` | Pythonパッケージマネージャ |
| `ripgrep` | `chroma-ripgrep.ch` | grep代替コマンド |
| `uv` | `chroma-uv.ch` | Pythonパッケージマネージャ（uv） |
| `starship` | `chroma-starship.ch` | クロスシェルプロンプト |
| `task` | `chroma-task.ch` | Taskwarriorタスク管理（**高度な実装**） |
| `tmux` | `chroma-tmux.ch` | ターミナルマルチプレクサ |
| `wget` | `chroma-wget.ch` | ファイルダウンローダー |
| `yazi` | `chroma-yazi.ch` | ターミナルファイルマネージャ |
| `zk` | `chroma-zk.ch` | Zettelkastenノート管理 |
| `zoxide` | `chroma-zoxide.ch` | cd代替コマンド |
| `docker-compose` | `chroma-docker-compose.ch` | Docker Compose |
| `ollama` | `chroma-ollama.ch` | LLM実行・管理 |
| `xh` | `chroma-xh.ch` | HTTPクライアント |
| `typst` | `chroma-typst.ch` | タイプセットシステム |
| `dust` | `chroma-dust.ch` | ディスク使用量表示 |
| `duf` | `chroma-duf.ch` | ディスク使用状況 |
| `ncdu` | `chroma-ncdu.ch` | NCursesディスク使用量 |
| `jaq` | `chroma-jaq.ch` | JSONクエリツール |
| `sd` | `chroma-sd.ch` | 検索・置換ツール |

---

## Chromaの動作

### 基本原理

Chromaは、コマンドラインの各トークン（単語）を解析し、その役割に応じて適切なスタイルを適用します：

- **サブコマンド**: `git commit` → `commit`が緑色
- **オプション**: `--verbose`, `-v` → 青色
- **引数**: ファイルパスやパラメータ → 通常色
- **無効な値**: 存在しないオプション → 赤色

### スタイルの種類

Fast Syntax Highlightingは以下のスタイルを提供：

| スタイル | 用途 | デフォルト色 |
|---------|------|-------------|
| `subcommand` | サブコマンド | 緑 |
| `double-hyphen-option` | `--option` | 青 |
| `single-hyphen-option` | `-o` | シアン |
| `mathnum` | 数値 | マゼンタ |
| `assign` | 代入（`key=value`） | 黄 |
| `incorrect-subtle` | エラー | 赤（subtle） |
| `default` | その他 | 白/グレー |

---

## 新規Chroma追加手順

### 1. テンプレートをコピー

```bash
cd ${XDG_CONFIG_HOME:-~/.config}/zsh/fsh
cp chroma-template.ch chroma-mycmd.ch
```

### 2. ファイルを編集

```zsh
# chroma-mycmd.ch
# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for mycmd
# Provides syntax highlighting for mycmd command options and subcommands

chroma/mycmd() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style
    local __start __end

    if (( __first_call )); then
        # 初回呼び出し時の初期化処理
        FAST_HIGHLIGHT[chroma-mycmd-subcommand-seen]=0
        return 1
    fi

    (( __start = __start_pos - ${#PREBUFFER}, __end = __end_pos - ${#PREBUFFER} ))

    # サブコマンドの認識
    if [[ "$__wrd" =~ ^(init|build|deploy|test)$ ]]; then
        if (( FAST_HIGHLIGHT[chroma-mycmd-subcommand-seen] == 0 )); then
            __style=${FAST_THEME_NAME}subcommand
            FAST_HIGHLIGHT[chroma-mycmd-subcommand-seen]=1
        else
            __style=${FAST_THEME_NAME}default
        fi
    # オプションの認識
    elif [[ "$__wrd" == --* ]]; then
        __style=${FAST_THEME_NAME}double-hyphen-option
    elif [[ "$__wrd" == -* ]]; then
        __style=${FAST_THEME_NAME}single-hyphen-option
    # その他の引数
    else
        __style=${FAST_THEME_NAME}default
    fi

    # ハイライトを適用
    if [[ -n "$__style" && $__start -ge 0 ]]; then
        reply+=("$__start $__end ${FAST_HIGHLIGHT_STYLES[$__style]}")
    fi

    return 1
}
```

### 3. Zshに登録

Chromaファイルは`${XDG_CONFIG_HOME:-~/.config}/zsh/fsh/`に配置するだけで、Fast Syntax Highlightingが自動的に検出します。

### 4. テスト

```bash
# Zshを再起動
exec zsh

# コマンドを入力してハイライトを確認
mycmd init --verbose
```

---

## 高度な例: `chroma-task.ch`

Taskwarriorの`chroma-task.ch`は、キャッシュファイルを使用したリアルタイムID検証を実装しています。

### 特徴

1. **キャッシュファイルの読み込み**
   ```zsh
   local cache_file="${XDG_CACHE_HOME:-$HOME/.cache}/taskwarrior/ids.list"
   if [[ -f "$cache_file" ]]; then
       CHROMA_TASK_IDS=( ${(f)"$(<"$cache_file")"} )
   fi
   ```

2. **動的ID検証**
   ```zsh
   if [[ "$__wrd" =~ ^[0-9]+$ ]]; then
       if (( ${CHROMA_TASK_IDS[(Ie)$__wrd]} )); then
           __style=${FAST_THEME_NAME}mathnum  # 有効なID
       else
           __style=${FAST_THEME_NAME}incorrect-subtle  # 無効なID
       fi
   fi
   ```

3. **複雑な正規表現パターン**
   - UUID認識: `^[0-9a-fA-F-]{8,}$`
   - 属性代入: `^(project|priority|due):.*$`
   - 状態値: `^(pending|completed|deleted)$`

詳細は `CACHE_ARCHITECTURE.md` を参照。

---

## トラブルシューティング

### Chromaが適用されない

**原因1**: Fast Syntax Highlightingが未インストール
```bash
# 確認
zplug list | grep fast-syntax-highlighting

# インストール（zplugの場合）
echo 'zplug "zdharma-continuum/fast-syntax-highlighting"' >> ${XDG_CONFIG_HOME:-~/.config}/zsh/.zsh_plugins
zplug install
```

**原因2**: Chromaディレクトリが認識されていない
```bash
# FAST_WORK_DIRを確認
echo $FAST_WORK_DIR

# 正しく設定されているか確認（.zshrcで設定）
export FAST_WORK_DIR="$XDG_CONFIG_HOME/zsh/fsh"
```

**原因3**: ファイル名が規則に従っていない
- 正: `chroma-mycmd.ch`
- 誤: `mycmd-chroma.ch`, `chroma_mycmd.ch`

### ハイライトが期待通りに動作しない

**デバッグ方法**:
1. **エラーメッセージを確認**
   ```bash
   # Zshを冗長モードで起動
   zsh -x
   ```

2. **Chromaが読み込まれているか確認**
   ```bash
   # 関数が定義されているか確認
   type chroma/mycmd
   ```

3. **スタイル定義を確認**
   ```zsh
   # 現在のテーマのスタイルを表示
   echo $FAST_HIGHLIGHT_STYLES[${FAST_THEME_NAME}subcommand]
   ```

---

## ベストプラクティス

### 1. サブコマンド検出の最適化

**推奨**: 最初のサブコマンドのみを認識
```zsh
if (( FAST_HIGHLIGHT[chroma-mycmd-subcommand-seen] == 0 )); then
    # 初回のみsubcommandスタイルを適用
    __style=${FAST_THEME_NAME}subcommand
    FAST_HIGHLIGHT[chroma-mycmd-subcommand-seen]=1
fi
```

### 2. パフォーマンス最適化

- **キャッシュを活用**: 外部ファイルは初回のみ読み込み
- **正規表現を最小化**: 複雑なパターンは避ける
- **早期リターン**: 不要な処理をスキップ

### 3. コメントの記載

```zsh
# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for <command-name> (<brief-description>)
# Provides syntax highlighting for <details>
```

---

## 参考リソース

- [Fast Syntax Highlighting公式ドキュメント](https://github.com/zdharma-continuum/fast-syntax-highlighting)
- [Chromaテンプレート集](https://github.com/zdharma-continuum/fast-syntax-highlighting/tree/main/chroma)
- [Zshスクリプティングガイド](http://zsh.sourceforge.net/Guide/)

---

## 貢献

新しいChromaを作成した場合は、以下の手順でリポジトリに貢献できます：

1. `chroma-<command>.ch`を作成
2. このREADMEの「インストール済みChroma一覧」に追加
3. Pull Requestを作成

---

**最終更新**: 2026年1月
