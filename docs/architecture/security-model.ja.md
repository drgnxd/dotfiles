# セキュリティモデルとガードフラグ

## ガードフラグ
破壊的な変更を伴うスクリプトは、明示的な環境変数がないと実行されません。

```bash
# 例
ALLOW_DEFAULTS=1 ./system_defaults.sh
```

| フラグ | スクリプト | リスク |
|------|-----------|--------|
| `ALLOW_DEFAULTS` | system_defaults.sh | 中 |
| `ALLOW_HARDEN` | security_hardening.sh | 高 |
| `ALLOW_GUI` | login_items.sh | 低 |
| `ALLOW_KEYBOARD_APPLY` | keyboard.sh | 低 |
| `FORCE` | setup_cloud_symlinks.sh | 中 |

## 秘密情報管理
ユーザー固有/機密ファイルは `.chezmoiignore.tmpl` で除外します。

```
**config.local
**hosts.yml
```

## 目的
- 意図しない実行を防止
- 自動化でも安全性を担保
- ガードロジックとヘルパー関数を `common.sh` に集約
- マルチユーザー安全性のため `run_as_user <username> <command>` でユーザーコンテキスト実行
