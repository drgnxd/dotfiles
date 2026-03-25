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
home-manager switch --flake ~/.config/nix-config#<user>@<linuxHostname>
```

利用前に `flake.nix` の `user` と `linuxHostname` を環境に合わせて設定してください。

**デスクトップスタック**:
- Hyprland — タイル型ウィンドウ管理（Hammerspoon 相当）
- Waybar — ステータスバー（Stats.app 相当）
- Wofi — アプリランチャー（Sol 相当）
- fcitx5 + mozc — 日本語入力
- cliphist + wl-clipboard — クリップボード管理（Maccy 相当）
- hypridle + hyprlock — アイドル管理と画面ロック
- mako — 通知デーモン
- grim + slurp — スクリーンショット

**サポート対象**: すべての CLI ツール、Nushell、Helix、Git、Taskwarrior、Yazi、Zellij、OpenCode、Starship、Zoxide、Atuin、Carapace、Direnv、Alacritty、および上記 Linux デスクトップスタック。

**キーバインド互換**: ウィンドウ操作の `Ctrl+Alt` + 矢印/`U``I``J``K`/`C`/`Enter` は macOS の Hammerspoon 設定と揃え、筋肉記憶を維持します。

**Linux で未提供**: macOS system defaults、LaunchAgents、Homebrew casks、Hammerspoon の直接 API。
