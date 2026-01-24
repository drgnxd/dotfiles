# Taskwarrior Cache Architecture

## 概要

本システムは、Taskwarriorのタスク情報をローカルキャッシュし、Zsh統合機能（シンタックスハイライト、補完、ライブプレビュー）のパフォーマンスを大幅に向上させるアーキテクチャです。

### 目的

- **高速なID検証**: コマンド入力中にタスクIDの有効性をリアルタイムで確認
- **ライブプレビュー**: タスクIDを入力すると、ミニバッファに詳細を即座に表示
- **スマート補完**: タスク説明を含む補完候補を瞬時に提示
- **非侵入的設計**: Taskwarriorのパフォーマンスに影響を与えない

---

## キャッシュディレクトリ構造

```
${XDG_CACHE_HOME:-~/.cache}/taskwarrior/
├── ids.list       # タスクIDのリスト（1行1ID）
└── desc.list      # タスク説明（ID:description形式）
```

### ファイル形式

#### `ids.list`
```
1
2
5
10
```
- **用途**: Fast Syntax Highlightingによる高速なID検証
- **更新頻度**: タスク追加・変更時に自動更新

#### `desc.list`
```
1:Buy groceries
2:Fix bug in authentication module
5:Schedule dentist appointment
10:Review pull request #123
```
- **用途**: ライブプレビューと補完
- **フォーマット**: `{ID}:{description}`（1行1タスク）

---

## データフロー

### 1. キャッシュ更新フロー

```
[ユーザー操作]
    ↓
task add "New task"  または  task 1 done
    ↓
[Taskwarrior Hooks]
    ├─ on-add.py       (新規タスク時)
    └─ on-modify.py    (変更時)
    ↓
[共通ライブラリ]
    update_cache.py
    ├─ task status:pending -WAITING export
    ├─ JSON解析
    ├─ ids.listとdesc.listを生成
    └─ ${XDG_CACHE_HOME:-~/.cache}/taskwarrior/へ書き込み
```

### 2. Zsh統合読み込みフロー

```
[Zshシェル起動 or コマンド入力]
    ↓
[Fast Syntax Highlighting]
    chroma-task.ch
    ├─ ids.listを読み込み
    ├─ 入力されたIDを検証
    └─ 有効: mathnum / 無効: incorrect-subtle
    ↓
[Zsh Functions]
    .functions (_task_preview_widget)
    ├─ desc.listを読み込み
    ├─ コマンドライン上のIDを抽出
    └─ zle -M で説明をミニバッファに表示
```

---

## 実装詳細

### Python Hooks

#### `update_cache.py` (共通ライブラリ)
**場所**: `dot_config/taskwarrior/hooks/update_cache.py`

**主要関数**:
- `update_cache()`: キャッシュファイルを更新
  - `task status:pending -WAITING export`でJSON取得
  - IDとdescriptionを抽出
  - 2つのキャッシュファイルに書き込み
  - 直近5秒以内の更新はスキップ（連続フックの負荷軽減）
- `process_hook_input()`: フック入力を処理
  - stdinからJSON読み込み
  - 最後のJSONオブジェクトをstdoutに出力（Taskwarrior要求）
  - 出力後に`update_cache()`を実行

**エラーハンドリング**:
- すべての例外を`pass`で吸収（Taskwarrior操作をブロックしないため）
- `subprocess.DEVNULL`でstderr抑制

#### `on-add.py` / `on-modify.py` (薄いラッパー)
**場所**: `dot_config/taskwarrior/hooks/`

**役割**:
- `update_cache.py`をimportして`process_hook_input()`を呼び出すのみ
- コード重複を排除

---

### Zsh統合

#### Fast Syntax Highlighting (`chroma-task.ch`)
**場所**: `dot_config/zsh/fsh/chroma-task.ch`

**動作**:
1. 初回呼び出し時に`ids.list`をメモリへロード
2. 各トークンを解析:
   - 数値のみ → `ids.list`に存在するかチェック
   - 存在 → `mathnum`スタイル（緑）
   - 不在 → `incorrect-subtle`スタイル（赤）
3. サブコマンド、オプション、UUID、属性も適切にハイライト

**パフォーマンス**:
- キャッシュファイルは1回のみ読み込み
- Zsh配列による高速検索（`${CHROMA_TASK_IDS[(Ie)$__wrd]}`）

#### Zsh Functions (`dot_functions`)
**場所**: `dot_config/zsh/dot_functions`

**主要関数**:

##### `_task_cache_load()`
- `desc.list`を連想配列`TASK_CACHE_MAP`にロード
- 1秒間のTTLキャッシュ（連続呼び出しでも1回のみ読み込み）
- フォーマット: `TASK_CACHE_MAP[1]="Buy groceries"`

##### `_task_preview_widget()`
- コマンドライン上のタスクIDを抽出
- ID範囲表記（`1-5`）をサポート
- `_task_cache_load()`で説明を取得
- `zle -M`でミニバッファに表示
- Zsh Line Editorウィジェット（キーバインド: 自動呼び出し）

---

## 技術仕様

### キャッシュ更新条件

**含まれるタスク**:
- `status:pending`: 未完了のタスク
- `-WAITING`: 現在待機中ではないタスク（`task list`と同じ挙動）

**除外されるタスク**:
- 完了済み（`status:completed`）
- 削除済み（`status:deleted`）
- 待機中（`wait`属性が設定され、かつ未来の日時）

### パフォーマンス最適化

1. **フック後更新**: Taskwarrior操作完了後に実行
2. **ローカルファイル**: ネットワークアクセス不要
3. **差分更新なし**: 全再構築（平均10ms以下）
4. **Zsh側TTL**: 1秒間のメモリキャッシュで連続読み込みを回避
5. **更新スロットリング**: 5秒以内の重複更新を抑制

---

## トラブルシューティング

### キャッシュが更新されない

**症状**: 新しく追加したタスクIDがハイライトされない

**原因と対処**:
1. **Pythonフックが実行されていない**
   ```bash
   # フックファイルを確認
   ls -la ${XDG_CONFIG_HOME:-~/.config}/taskwarrior/hooks/
   # 実行権限があることを確認（-rwxr-xr-x）
   
   # 権限付与
   chmod +x ${XDG_CONFIG_HOME:-~/.config}/taskwarrior/hooks/*.py
   ```

2. **taskコマンドがフックをスキップ**
   - Taskwarriorの設定で`confirmation=off`や`hooks=off`になっていないか確認
   ```bash
   task show | grep hooks
   ```

3. **キャッシュディレクトリが存在しない**
   ```bash
   mkdir -p ${XDG_CACHE_HOME:-~/.cache}/taskwarrior
   ```

4. **手動でキャッシュを再構築**
   ```bash
   python3 ${XDG_CONFIG_HOME:-~/.config}/taskwarrior/hooks/update_cache.py --update-only
   ```

### プレビューが表示されない

**症状**: タスクIDを入力してもミニバッファに何も表示されない

**原因と対処**:
1. **desc.listが空または壊れている**
   ```bash
   cat ${XDG_CACHE_HOME:-~/.cache}/taskwarrior/desc.list
   # 各行が "ID:description" 形式か確認
   ```

2. **Zsh関数が読み込まれていない**
   ```bash
   # 関数が定義されているか確認
   type _task_preview_widget
   
   # ソースファイルを再読み込み
   source ${XDG_CONFIG_HOME:-~/.config}/zsh/.functions
   ```

3. **キーバインドが設定されていない**
   ```bash
   # ウィジェットが登録されているか確認
   zle -la | grep task
   ```

### ハイライトが効かない

**症状**: `task 1`のIDが通常色で表示される

**原因と対処**:
1. **Fast Syntax Highlighting未インストール**
   ```bash
   # プラグインリストを確認
   cat ${XDG_CONFIG_HOME:-~/.config}/zsh/.zsh_plugins
   
   # 手動インストール（zplugの場合）
   zplug "zdharma-continuum/fast-syntax-highlighting"
   ```

2. **chromaファイルが読み込まれていない**
   ```bash
   # chromaパスを確認
   echo $FAST_WORK_DIR
   ls -la ${XDG_CONFIG_HOME:-~/.config}/zsh/fsh/
   ```

3. **IDs.listが空**
   ```bash
   cat ${XDG_CACHE_HOME:-~/.cache}/taskwarrior/ids.list
   # 空なら手動再構築（上記参照）
   ```

---

## 拡張・カスタマイズ

### キャッシュ対象の変更

`update_cache.py`の17行目を編集:
```python
# 例: 待機中タスクも含める
output = subprocess.check_output(
    ["task", "status:pending", "export"],  # -WAITINGを削除
    stderr=subprocess.DEVNULL
)
```

### プレビュー形式のカスタマイズ

`dot_functions`の`_task_preview_widget()`を編集:
```zsh
# 例: プロジェクト名も表示
desc="${TASK_CACHE_MAP[$id]}"
project=$(task _get "$id".project)
msg+="${id}:${desc} (${project})"
```

### 追加キャッシュファイル

`update_cache.py`に以下を追加:
```python
# プロジェクト一覧
projects = set(t.get('project', '') for t in tasks if t.get('project'))
with open(os.path.join(cache_dir, "projects.list"), "w") as f:
    f.write("\n".join(sorted(projects)))
```

---

## 関連ファイル

| ファイルパス | 役割 |
|-------------|------|
| `dot_config/taskwarrior/hooks/update_cache.py` | キャッシュ更新ライブラリ |
| `dot_config/taskwarrior/hooks/on-add.py` | 新規タスク追加時のフック |
| `dot_config/taskwarrior/hooks/on-modify.py` | タスク変更時のフック |
| `dot_config/zsh/fsh/chroma-task.ch` | Syntax Highlighting定義 |
| `dot_config/zsh/.functions` | Zshヘルパー関数 |
| `${XDG_CACHE_HOME:-~/.cache}/taskwarrior/ids.list` | キャッシュ（IDリスト） |
| `${XDG_CACHE_HOME:-~/.cache}/taskwarrior/desc.list` | キャッシュ（説明付き） |

---

## 参考リンク

- [Taskwarrior Hooks Documentation](https://taskwarrior.org/docs/hooks.html)
- [Fast Syntax Highlighting Chroma Guide](https://github.com/zdharma-continuum/fast-syntax-highlighting)
- [Zsh Line Editor (ZLE) Manual](http://zsh.sourceforge.net/Doc/Release/Zsh-Line-Editor.html)
