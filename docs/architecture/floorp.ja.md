# Floorp プロファイル管理

## 宣言的に管理するもの
- Home Manager が固定の Floorp `default` プロファイルに `user.js` を書き込みます。
- 設定には `browser.toolbars.bookmarks.visibility = "never"` によるブックマークバー非表示を含みます。
- `toolkit.legacyUserProfileCustomizations.stylesheets = true` が `userChrome.css` と `userContent.css` を有効にします。
- 共有 UI CSS は `dot_config/floorp/chrome/userChrome.css` と `dot_config/floorp/chrome/userContent.css` にあります。

## 管理しないもの
- `places.sqlite` はブックマークと履歴を含むマシンローカルな実行時状態のため管理しません。
- `cookies.sqlite` は Cookie の実行時状態のため管理しません。
- `logins.json` と `key4.db` は秘密情報を含むため管理しません。
- `sessionstore` データはセッションの実行時状態のため管理しません。
- `cache2`、`storage/`、その他のキャッシュはマシンローカルな実行時状態のため管理しません。
- デバイス間のブックマークと履歴の同期は git ではなく Floorp/Firefox Sync で行います。

## プロファイルパス
- macOS のプロファイル root: `$HOME/Library/Application Support/Floorp`。
- Linux のプロファイル root: `$HOME/.floorp`。
- 管理対象プロファイルは両プラットフォームで固定の `default` プロファイルです。
- ブラウザ本体のインストールは変更しません。macOS は Homebrew cask、Linux は `floorp-bin` nixpkg を使います。

## 移行
- 既存のランダムハッシュ名プロファイルにあるブックマークと履歴は自動移行しません。
- 1回だけ移行するには、古いプロファイルで Floorp を起動し、ブックマークをエクスポートするか Floorp/Firefox Sync を使ってから、`default` プロファイルへインポートまたは同期します。
- 移行後も実行時データは git に入れず、Floorp にローカル管理させます。
