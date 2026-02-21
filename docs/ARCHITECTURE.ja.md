# アーキテクチャ概要

## クイックリンク
- [Nushell 設定](architecture/nushell.ja.md) - モジュール構成のモダンなシェル
- [XDG Base Directory 準拠](architecture/xdg-compliance.ja.md)
- [セキュリティモデルとガードフラグ](architecture/security-model.ja.md)
- [プラットフォームサポート](architecture/platform-support.ja.md)
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
~/.config/nix-config/           # Nix フレークのリポジトリ
├── flake.nix                   # エントリポイント（nix-darwin + home-manager）
├── flake.lock                  # 依存の固定
├── hosts/
│   └── macbook/default.nix     # nix-darwin システム設定
├── home/
│   ├── default.nix             # home-manager エントリーポイント（モジュール読込）
│   ├── packages.nix            # パッケージ一覧
│   └── modules/
│       ├── activation.nix      # activation フックとユーザー設定
│       ├── xdg_config_files.nix # xdg.configFile の集約
│       ├── xdg_terminal_files.nix # ターミナル/CLI の割当
│       ├── xdg_editor_files.nix # エディタの割当
│       ├── xdg_nushell_files.nix # Nushell の割当
│       ├── xdg_yazi_files.nix  # Yazi の割当
│       └── xdg_desktop_files.nix # デスクトップ系アプリの割当
├── dot_config/                 # 設定ファイルのソース（XDG）
│   ├── alacritty/              # ターミナルエミュレータ
│   ├── bat/                    # シンタックスハイライト cat
│   ├── gh/                     # GitHub CLI
│   ├── git/                    # バージョン管理
│   ├── hammerspoon/            # macOS 自動化 (Lua)
│   ├── helix/                  # テキストエディタ
│   ├── npm/                    # Node.js 設定
│   ├── opencode/               # AI コーディングエージェント
│   ├── starship/               # シェルプロンプト
│   ├── stats/                  # システムモニター
│   ├── taskwarrior/            # タスク管理
│   ├── zellij/                 # ターミナルマルチプレクサ
│   ├── yazi/                   # ファイルマネージャー
│   ├── nushell/                # モダンなシェル設定
│   │   ├── autoload/           # モジュール化された設定
│   │   │   ├── 01-env.nu       # 環境変数
│   │   │   ├── 02-path.nu      # PATH 設定
│   │   │   ├── 03-aliases.nu   # コマンドエイリアス
│   │   │   ├── 04-functions.nu # カスタム関数
│   │   │   ├── 05-completions.nu # コマンド補完
│   │   │   ├── 06-integrations.nu # 統合ラッパー + Direnv 初期化
│   │   │   ├── 07-source-tools.nu # キャッシュ読み込み
│   │   │   ├── 08-taskwarrior.nu # Taskwarrior プロンプトプレビュー
│   │   │   └── 09-lima.nu       # Lima/Docker ヘルパー
│   │   ├── env.nu              # エントリーポイント
│   │   └── config.nu           # メイン設定
├── scripts/
│   └── darwin/setup_cloud_symlinks.sh # CloudStorage シンボリックリンク補助
├── secrets/
│   └── secrets.nix             # agenix キーマップ
├── docs/                       # ドキュメント
└── archive/                    # 旧設定のアーカイブ
```

---

## 参考
- 英語版: [ARCHITECTURE.md](ARCHITECTURE.md)
