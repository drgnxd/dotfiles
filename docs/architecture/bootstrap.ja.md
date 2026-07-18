## フレッシュインストール / ブートストラップ ガイド

ゼロからマシンをセットアップし、完全に設定された環境を得るまでの手順です。

### 前提条件

* Git（リポジトリのクローン用）
* インターネット接続

### 手順 1: Nix のインストール（Determinate Systems インストーラー）

```bash
curl --proto '=https' --tlsv1.2 -fsSL https://install.determinate.systems/nix | sh -s -- install
```

プロンプトに従って進めてください。このインストーラーは flakes をデフォルトで有効化し、Nix デーモンをセットアップします。

インストール後、**シェルを再起動**（または新しいターミナルを開く）してください。

### 手順 2: リポジトリをクローン

```bash
git clone https://github.com/<your-username>/dotfiles ~/.config/nix-config
cd ~/.config/nix-config
```

### 手順 3: マシン固有の識別情報を設定

テンプレートをコピーして、自分のマシンに必要な識別情報を編集します。`preferences.nix` は任意であり、作成しない場合は可搬性を優先した既定値を使います：

```bash
cp local/identity.nix.example local/identity.nix
cp local/preferences.nix.example local/preferences.nix
# local/identity.nix を編集して user, hostname, linux_hostname を設定
```

`local/identity.nix` の例：

```nix
{
  user = "youruser";
  hostname = "your-macos-hostname";        # macOS: scutil --get LocalHostName
  linux_hostname = "your-linux-hostname";  # Linux: hostname
}
```

**注意**: `local/identity.nix` と `local/preferences.nix` は gitignore 対象です。これらのファイルがマシン外に出ることはありません。項目とプラットフォーム別の確認コマンドは [`local/README.md`](../../local/README.md) を参照してください。

### 手順 4: ブートストラップ実行

**macOS (nix-darwin):**

```bash
nix run path:.#bootstrap-darwin
```

**Linux (standalone home-manager):**

```bash
nix run path:.#bootstrap-linux
```

ブートストラップ用アプリは `path:.` を使用するため、git 管理外の `local/identity.nix` も Nix から見える状態になります。

### 手順 5: アクティベーション後の作業

初回アクティベーション完了後：

1. **デフォルトシェルは Nushell** — シェルプロンプトが即座に変わります。必要に応じて `exec nu` を実行してください。
2. **フォント** — `fc-cache -f` でフォントキャッシュを更新し、確認します：
   ```bash
   fc-list | grep -i HackGen
   ```
3. **日本語入力（Linux）** — `local/preferences.nix` で `japaneseInputMethod = "hazkey"` を設定した場合、hazkey の systemd ユーザーサービスが有効になります。開始するには：
   ```bash
   systemctl --user start hazkey-server
   ```
   fcitx5 + mozc（デフォルト）の場合、グラフィカルログイン時に fcitx5 が自動起動します。IM 変数は `home.sessionVariables` ではなく `~/.config/environment.d/fcitx5.conf` で配信されます。
   Debian `im-config` を使う Ubuntu GNOME / X11 ホストでは、activation 前に `local/preferences.nix` へ `imConfigXinputrc = true;` を設定し、activation 後にフル logout/login を実行してください。`XMODIFIERS` は X セッション開始時に固定されるため、fcitx5 の再起動やアプリの開き直しだけでは不十分です。全角/半角キーのない US 配列では、fcitx5 のデフォルト切り替えは `Ctrl+Space` です。
4. **Floorp** — Linux では `floorp-bin` (nixpkgs)、macOS では Homebrew cask で利用可能です。
5. **Helix の nixd** — 生成される `~/.config/helix/languages.toml` が実際のホスト設定名を指すようになりました（Phase 7 参照）。手動編集なしでオプション補完が動作します。

### 既知の注意事項

* **ホストごとの nixd 設定** — Helix に配信される `languages.toml` は、プレースホルダーの設定名（`darwinConfigurations.<hostname>`、`homeConfigurations."<user>@<linuxHostname>"`）を、 `local/identity.nix` の実際の `hostname` と `user@linuxHostname` に自動で置換します。手動操作は不要です。
* **Linux の Vulkan** — standalone home-manager 環境では GPU ドライバ解決の不安定さを避けるため、hazkey 用の Vulkan はデフォルトで無効です。NixOS で適切な graphics モジュールを構成している場合にのみ有効化を検討してください。
* **シークレット** — agenix を使う場合、`secrets/secrets.nix` に SSH 公開鍵を追加し、`nix run .#rekey-secrets` を実行してください。
