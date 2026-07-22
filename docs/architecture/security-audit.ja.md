# macOS セキュリティ態勢監査

## 対象範囲

セキュリティ態勢監査は、現在の macOS マシンが実際に強制しているコントロールを観測し、宣言的な永続化状態をこの flake と比較します。証拠の報告だけを行います。コントロールの有効化、無効化、インストール、削除、その他の修復は一切行いません。

監査は読み取り専用です。ネットワークを使わず、`sudo` を呼び出さず、パスワード入力を求めず、秘密値を読みません。このレポートは activation や CI の gate ではないため、デフォルトモードは常に正常終了します。

## 監査の実行

リポジトリルートから監査を実行します。

```bash
just security-audit
just security-audit --json
just security-audit --strict
```

デフォルトの表と JSON 配列には同じチェックが含まれます。`--strict` は 1 件以上の `WARN` がある場合にステータス 1 で終了しますが、システム状態は変更しません。

## ステータス語彙

| ステータス | 意味 |
|------------|------|
| `OK` | コントロールが存在し、有効です。 |
| `WARN` | コントロールが存在しない、弱体化している、または宣言から drift しています。 |
| `MANUAL` | オペレーターによる権限昇格または確認が必要です。レポートにコマンドまたは System Settings の場所を表示します。 |
| `UNKNOWN` | ツールを利用できない、実行に失敗した、または監査が出力を解析できません。`OK` として扱うことはありません。 |

## 手動チェック

権限昇格が必要なチェックは自動化せず、`MANUAL` とします。監査は `sudo` を呼び出さず、パスワード入力を求めません。権限昇格が必要な監査は習慣的に実行されなくなり、実行されない監査は有用な証拠を提供できないためです。オペレーターは表示されたコマンドを実行する時期を選び、その出力を別途確認できます。

## 宣言状態からの drift

未宣言のユーザー LaunchAgent と残存する system extension は、宣言的に管理するリポジトリで最も重要な検出項目です。ここでの `WARN` は、マシン上の実際の永続化状態が Nix 宣言から drift したことを意味します。これは、このリポジトリが防ぐべき失敗そのものです。宣言済み LaunchAgent がディスク上にない場合も、activation が宣言状態を生成できていないため警告します。

System extension は、明示的に宣言して根拠を示すまで `WARN` になります。`brew uninstall --zap` 後も残る可能性があるため、Nix または Homebrew の宣言を削除しただけでは、その extension がマシン上で永続化を停止した証拠にはなりません。

## 許容済み System extension

以下は `casks` で宣言済みのアプリが必要とする system extension で、機能上必要なため意図的に許容している。監査は `WARN` を出し続けるが(自動的な根拠検証機構がないため)、これらは既知の drift ではない。

| Extension | 提供元 cask | 根拠 |
|-----------|------------|------|
| `ch.protonvpn.mac.WireGuard-Extension` | `protonvpn` | ProtonVPN の WireGuard トンネルに必須 |
| `ch.protonvpn.mac.Transparent-Proxy` | `protonvpn` | ProtonVPN の Split Tunneling(実験的機能)に必須 |

## 既知の残存 WARN

`com.objective-see.lulu.extension` は 2026-07-22 に `lulu` cask を削除(`brew uninstall --zap`)し、System Settings からも無効化(`[activated disabled]`)した後も `systemextensionsctl list` に残り続ける。`systemextensionsctl uninstall` は SIP 有効時は使用できず、この登録を完全に消すには SIP を無効化する必要がある。SIP を維持する方が優先度が高いため、無効化状態での残存を許容する。監査はこの extension について `WARN` を出し続けるが、これは既知の drift であり対応不要。

## プラットフォーム対応

この監査は macOS のみを対象とします。Linux 対応は今後の作業です。
