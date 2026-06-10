# Floorp Profile Management

## Managed Declaratively
- Home Manager writes `user.js` into the fixed `default` Floorp profile.
- Preferences include bookmark bar visibility via `browser.toolbars.bookmarks.visibility = "never"`.
- `toolkit.legacyUserProfileCustomizations.stylesheets = true` enables `userChrome.css` and `userContent.css`.
- Shared UI CSS lives in `dot_config/floorp/chrome/userChrome.css` and `dot_config/floorp/chrome/userContent.css`.

## Not Managed
- `places.sqlite` is not managed because it stores bookmarks and history as machine-local runtime state.
- `cookies.sqlite` is not managed because cookies are runtime state.
- `logins.json` and `key4.db` are not managed because they contain secrets.
- `sessionstore` data is not managed because it is session runtime state.
- `cache2`, `storage/`, and other caches are not managed because they are machine-local runtime state.
- Cross-device bookmark and history sync is handled by Floorp/Firefox Sync, not git.

## Profile Paths
- macOS profile root: `$HOME/Library/Application Support/Floorp`.
- Linux profile root: `$HOME/.floorp`.
- The managed profile is the fixed `default` profile on both platforms.
- Browser binary installation is unchanged: macOS uses the Homebrew cask, and Linux uses the `floorp-bin` nixpkg.

## Migration
- Existing bookmarks and history in an old random-hash profile are not auto-migrated.
- To migrate once, launch Floorp with the old profile, export bookmarks or use Floorp/Firefox Sync, then import or sync them into the `default` profile.
- After migration, keep runtime data out of git and let Floorp maintain it locally.
