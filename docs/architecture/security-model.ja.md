## ガードフラグ
ほとんどの変更は Nix により宣言的に適用します。明示的なガードが必要なのはクラウドシンボリックリンク作成のみです。

| フラグ | スクリプト | 目的 |
|------|-----------|------|
| `FORCE=1` | `scripts/darwin/setup_cloud_symlinks.sh` | CloudStorage のシンボリックリンク作成 |

## 秘密情報管理
秘密情報は `secrets/*.age` に格納し、`agenix` で管理し、macOS と Linux の両方で `home/modules/secrets.nix` の home-manager layer に定義します。平文の秘密情報はコミットしません。復号はアクティベーション時にユーザーの設定パスへ行います。

## 依存関係更新の自動化
Dependabot は GitHub Actions を週次で確認し、minor と patch 更新を 1 つの pull request にまとめます。major 更新は個別の pull request として残し、手動レビューします。週次の flake.lock 更新 workflow も自動 pull request を作成します。どちらの自動依存関係 PR も、required CI が通った後にのみ auto-merge のキューへ入ります。branch protection が引き続き gate です。

CI で使う `gitleaks` や `actionlint` などの security / lint tool binary は、`nix run --inputs-from .` により `flake.lock` から解決します。そのため tool version は手動 checksum 編集ではなく、週次の flake.lock 更新に追随します。

## デフォルトブランチ ruleset
デフォルトブランチは GitHub repository ruleset で保護し、変更は pull request 経由で入り、設定済みの required status checks に合格することを要求します。

repository admin role は、この ruleset の bypass list に `bypass_mode: always` で登録しています。これにより、デフォルトブランチへの直接 push が可能になり、pull-request requirement と required status checks の両方をスキップします。admin による直接 push は CI で gate されません。push 後に CI は走るため、失敗は事後に検出されるだけで、事前には防止されません。デフォルトブランチが壊れると、以後の自動依存関係 pull request は、その依存関係更新とは無関係な理由で CI に失敗します。

Dependabot や flake.lock updater などの自動 pull request は bypass list に入れておらず、required checks による gate を完全に受けます。これは ruleset を置く理由を保つためです。required status checks が設定されていない場合、`gh pr merge --auto` は即時に merge します。

## 目的
- 変更の宣言的管理により安全性を担保
- インタラクティブ操作にのみ明示的な許可を要求
- 秘密情報を暗号化したまま管理
- 依存関係更新の自動化により tooling の陳腐化を抑えつつ、major version 変更はレビュー対象に保つ

[macOS セキュリティ態勢監査](security-audit.ja.md)
