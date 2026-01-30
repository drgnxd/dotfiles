# アーキテクチャ概要

## クイックリンク
- [XDG Base Directory 準拠](architecture/xdg-compliance.ja.md)
- [セキュリティモデルとガードフラグ](architecture/security-model.ja.md)
- [プラットフォームサポート](architecture/platform-support.ja.md)
- [Taskwarrior 統合](architecture/taskwarrior.ja.md)
- [開発ワークフロー](architecture/workflow.ja.md)
- [トラブルシューティング](architecture/troubleshooting.ja.md)

## 設計原則
- XDG 準拠で設定の場所を統一
- ガードフラグで破壊的操作を明示化
- chezmoi テンプレートでプラットフォーム差異を吸収
- 冪等性を維持して再実行可能

---

## ディレクトリ構成

```
~/.local/share/chezmoi/         # chezmoi ソースディレクトリ
├── .chezmoiignore.tmpl         # プラットフォーム別除外
├── .internal_scripts/
│   ├── darwin/                 # macOS 専用セットアップスクリプト
│   │   ├── system_defaults.sh  # UI/UX 設定
│   │   ├── security_hardening.sh # ファイアウォール、リモートアクセス
│   │   ├── keyboard.sh         # キーリピート設定
│   │   ├── login_items.sh      # ログイン時アプリケーション
│   │   ├── menubar.sh          # メニューバー設定
│   │   ├── audit_security.sh   # セキュリティ監査
│   │   ├── install_packages.sh.tmpl # Brewfile 実行
│   │   ├── import_stats.sh.tmpl # Stats アプリ設定
│   │   └── setup_cloud_symlinks.sh.tmpl # iCloud/Dropbox リンク
│   └── lib/
│       └── common.sh           # 共有 bash 関数
├── dot_config/                 # -> ~/.config/
│   ├── alacritty/              # ターミナルエミュレータ
│   ├── bat/                    # シンタックスハイライト cat
│   ├── gh/                     # GitHub CLI
│   ├── git/                    # バージョン管理
│   ├── hammerspoon/            # macOS 自動化 (Lua)
│   ├── helix/                  # テキストエディタ
│   ├── homebrew/               # パッケージマネージャー
│   ├── npm/                    # Node.js パッケージ
│   ├── opencode/               # AI コーディングエージェント
│   ├── starship/               # シェルプロンプト
│   ├── stats/                  # システムモニター
│   ├── taskwarrior/            # タスク管理
│   ├── tmux/                   # ターミナルマルチプレクサ
│   ├── yazi/                   # ファイルマネージャー
│   └── zsh/                    # シェル設定
│       ├── .zshrc.tmpl         # メインエントリーポイント
│       ├── .exports            # PATH と環境変数
│       ├── .aliases            # コマンドショートカット
│       ├── .functions          # カスタム関数
│       ├── .zsh_options        # Zsh 設定
│       ├── .zsh_completion     # 補完システム
│       ├── .zsh_plugins        # プラグイン管理
│       ├── .completions/       # コマンド別補完
│       ├── .homebrew           # Homebrew セットアップ
│       ├── .zoxide             # スマート cd
│       ├── .proton             # Proton Pass 統合
│       ├── .lima               # Lima/Docker 関数
│       ├── .fzf / .fzf_theme   # FZF 統合とテーマ
│       ├── .direnv             # ディレクトリ別環境
│       └── fsh/                # ファストシンタックスハイライト
├── dot_zshenv                  # -> ~/.zshenv (XDG セットアップ)
├── run_onchange_after_setup.sh.tmpl # セットアップオーケストレータ
└── docs/                       # ドキュメント
```

---

## 参考
- 英語版: [ARCHITECTURE.md](ARCHITECTURE.md)
