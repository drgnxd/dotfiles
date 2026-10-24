#!/bin/sh
set -eu

source_apps=$1
applications_dir=$2

[ -d "$source_apps" ] || exit 0

/bin/mkdir -p "$applications_dir"
temporary_dir=$(/usr/bin/mktemp -d "$applications_dir/.spotlight-launchers.XXXXXXXX")
trap '/bin/rm -rf "$temporary_dir"' EXIT

for app in "$source_apps"/*.app; do
  [ -L "$app" ] || continue
  [ -d "$app" ] || continue

  app_file=${app##*/}
  app_name=${app_file%.app}
  info_plist="$app/Contents/Info.plist"
  bundle_id=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$info_plist" 2>/dev/null || true)
  case "$bundle_id" in
  '' | *[!A-Za-z0-9.-]*)
    printf 'warning: skipping %s; it has no usable bundle identifier\n' "$app" >&2
    continue
    ;;
  esac

  display_name=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleDisplayName' "$info_plist" 2>/dev/null || true)
  if [ -z "$display_name" ]; then
    display_name=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleName' "$info_plist" 2>/dev/null || true)
  fi
  [ -n "$display_name" ] || display_name=$app_name

  destination="$applications_dir/$app_name.app"
  marker="$destination/Contents/Resources/home-manager-spotlight-target"
  desired_marker="$temporary_dir/target"
  printf '%s\n%s\n%s\n%s\n' "$(/usr/bin/readlink "$app")" "$bundle_id" "$display_name" 3 >"$desired_marker"

  if [ -e "$destination" ] || [ -L "$destination" ]; then
    if [ -L "$destination" ] || [ ! -f "$marker" ]; then
      printf 'warning: preserving existing application at %s\n' "$destination" >&2
      continue
    fi
    if /usr/bin/cmp -s "$marker" "$desired_marker"; then
      continue
    fi
  fi

  launcher="$temporary_dir/$app_name.app"
  script="$temporary_dir/$app_name.applescript"
  launcher_bundle_id="org.nixos.home-manager.spotlight.$bundle_id"
  escaped_app=$(
    printf '%s' "$app" | /usr/bin/sed 's/\\/\\\\/g; s/"/\\"/g'
  )
  printf 'do shell script "/usr/bin/open " & quoted form of "%s"\n' "$escaped_app" >"$script"
  /usr/bin/osacompile -o "$launcher" "$script"
  if ! /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier $launcher_bundle_id" "$launcher/Contents/Info.plist" 2>/dev/null; then
    /usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string $launcher_bundle_id" "$launcher/Contents/Info.plist"
  fi
  /usr/bin/defaults write "$launcher/Contents/Info" CFBundleName "$display_name"
  /usr/bin/defaults write "$launcher/Contents/Info" CFBundleDisplayName "$display_name"
  /usr/bin/defaults write "$launcher/Contents/Info" LSUIElement -bool true
  /bin/mkdir -p "$launcher/Contents/Resources"
  icon_file=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIconFile' "$info_plist" 2>/dev/null || true)
  if [ -n "$icon_file" ]; then
    icon_file=${icon_file##*/}
    case "$icon_file" in
    *.icns) ;;
    *) icon_file="$icon_file.icns" ;;
    esac
    source_icon="$app/Contents/Resources/$icon_file"
    if [ -f "$source_icon" ]; then
      /bin/cp "$source_icon" "$launcher/Contents/Resources/$icon_file"
      /usr/bin/defaults write "$launcher/Contents/Info" CFBundleIconFile "$icon_file"
      if /usr/libexec/PlistBuddy -c 'Print :CFBundleIconName' "$launcher/Contents/Info.plist" >/dev/null 2>&1; then
        /usr/libexec/PlistBuddy -c 'Delete :CFBundleIconName' "$launcher/Contents/Info.plist"
      fi
    fi
  fi
  /bin/cp "$desired_marker" "$launcher/Contents/Resources/home-manager-spotlight-target"
  /usr/bin/codesign --force --deep --sign - "$launcher"

  previous="$temporary_dir/previous.app"
  if [ -e "$destination" ]; then
    /bin/mv "$destination" "$previous"
  fi
  if ! /bin/mv "$launcher" "$destination"; then
    if [ -e "$previous" ]; then
      /bin/mv "$previous" "$destination"
    fi
    exit 1
  fi
done
