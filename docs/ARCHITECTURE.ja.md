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
│   ├── darwin/                 # macOS 専用セットアップ
│   └── lib/                    # 共通 bash 関数
├── dot_config/                 # -> ~/.config/
│   ├── taskwarrior/            # Taskwarrior 設定
│   ├── zsh/                    # Zsh 設定
│   └── ...
├── dot_zshenv                  # -> ~/.zshenv
├── run_onchange_after_setup.sh.tmpl # セットアップオーケストレータ
└── docs/                       # ドキュメント
```

---

## 参考
- 英語版: [ARCHITECTURE.md](ARCHITECTURE.md)
