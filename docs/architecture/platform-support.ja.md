## macOS (darwin)
**パッケージマネージャー**: Nix（nix-darwin + home-manager）

**システム統合**:
- nix-darwin の `system.defaults` と activation scripts
- `launchd.user.agents` による LaunchAgent 管理
- Hammerspoon と Stats の設定は Home Manager で管理
- Home Manager の activation で、Stats/Hammerspoon の旧アプリ管理 LaunchAgent を無効化し二重起動を防止

**アプリ**:
- nixpkgs で不足する GUI アプリは nix-darwin の `homebrew` で管理

## Linux (x86_64-linux)
**パッケージマネージャー**: Nix（standalone home-manager）
**デスクトップ環境**: Hyprland（Wayland compositor）

**使い方**:
```bash
cd ~/.config/nix-config
home-manager switch --flake path:.#<user>@<linuxHostname>
```

利用前に `local/identity.nix` を環境に合わせて設定してください。

**デスクトップスタック**:
- Hyprland — タイル型ウィンドウ管理（Hammerspoon 相当）
- Waybar — ステータスバー（Stats.app 相当）
- Wofi — アプリランチャー（Sol 相当）
- fcitx5 + mozc（または hazkey）— 日本語入力
- cliphist + wl-clipboard — クリップボード管理（Maccy 相当）
- hypridle + hyprlock — アイドル管理と画面ロック
- mako — 通知デーモン
- grim + slurp — スクリーンショット

**サポート対象**: すべての CLI ツール、Nushell、Helix、Git、Taskwarrior、Yazi、Zellij、OpenCode、Starship、Zoxide、Atuin、Carapace、Direnv、Alacritty、および上記 Linux デスクトップスタック。

**キーバインド互換**: ウィンドウ操作の `Ctrl+Alt` + 矢印/`U``I``J``K`/`C`/`Enter` は macOS の Hammerspoon 設定と揃え、筋肉記憶を維持します。

**Hazkey 入力**: `local/preferences.nix` で `japaneseInputMethod = "hazkey"` を設定すると Linux でライブ変換が有効になります。standalone home-manager 環境では GPU ドライバ解決の不安定さを避けるため Vulkan はデフォルトで無効のまま運用してください。NixOS で適切な graphics モジュールを構成している場合に限り有効化を検討します。

**Fcitx5 入力環境**: fcitx5 の IM 変数は `home.sessionVariables` ではなく `~/.config/environment.d/fcitx5.conf` で配信されるため、GNOME セッションと systemd 管理の Hyprland セッションで同じ値を受け取れます。Debian `im-config` を使う Ubuntu GNOME / X11 ホストでは、`local/preferences.nix` に `imConfigXinputrc = true;` を設定して `run_im fcitx5` を含む `~/.xinputrc` を生成し、その後フル logout/login を実行してください。`XMODIFIERS` は X セッション開始時に固定されるため、fcitx5 の再起動やアプリの開き直しだけでは不十分です。全角/半角キーのない US 配列では、fcitx5 のデフォルト切り替えは `Ctrl+Space` です。

**Hammerspoon -> Hyprland 対応表**:

| macOS (Hammerspoon) | Linux (Hyprland) |
|---------------------|------------------|
| Window management (Ctrl+Alt) | Hyprland keybinds (Ctrl+Alt) |
| Sol launcher (Cmd+Space) | Wofi (Super+Space) |
| Auto input switching | socket2 event watcher (`hypr-input-watcher`, systemd user service) |
| Browser control (background app) | `dispatch sendshortcut` targeting `class:^(floorp)$` |

### 追加デスクトップユーティリティ
- SwayOSD（音量 / 輝度 / Caps Lock の OSD）
- hyprpicker（カラーピッカー — Digital Color Meter 相当）
- Blur トグルバインド（Super+B）
- タッチパッドのワークスペーススワイプ（Mission Control 横スワイプ相当）
- `dispatch sendshortcut` によるバックグラウンドブラウザ制御

**Linux で未提供**: macOS system defaults、LaunchAgents、Homebrew casks、Hammerspoon の直接 API。
