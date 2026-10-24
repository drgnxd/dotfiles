#!/bin/bash
set -euo pipefail

script_dir="$(dirname "${BASH_SOURCE[0]}")"
test_dir="$(mktemp -d "${TMPDIR:-/tmp}/spotlight-app-launchers.XXXXXXXX")"
trap 'rm -rf "$test_dir"' EXIT

source_apps="$test_dir/home/Applications/Home Manager Apps"
applications_dir="$test_dir/home/Applications"
first_target="$test_dir/target-one/TestAlias.app"
second_target="$test_dir/target-two/TestAlias.app"
mkdir -p "$source_apps" "$first_target/Contents/Resources" "$second_target/Contents/Resources"

printf '%s\n' first-icon >"$first_target/Contents/Resources/icon.icns"
printf '%s\n' second-icon >"$second_target/Contents/Resources/icon.icns"

for info_plist in "$first_target/Contents/Info.plist" "$second_target/Contents/Info.plist"; do
  printf '%s\n' \
    '<?xml version="1.0" encoding="UTF-8"?>' \
    '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">' \
    '<plist version="1.0"><dict>' \
    '<key>CFBundleIdentifier</key><string>org.example.testapp</string>' \
    '<key>CFBundleName</key><string>Test Alias</string>' \
    '<key>CFBundleDisplayName</key><string>Test Alias</string>' \
    '<key>CFBundleIconFile</key><string>icon.icns</string>' \
    '</dict></plist>' >"$info_plist"
done

ln -s "$first_target" "$source_apps/TestAlias.app"
bash "$script_dir/spotlight_app_launchers.sh" "$source_apps" "$applications_dir"

launcher="$applications_dir/TestAlias.app"
test -d "$launcher" && ! test -L "$launcher"
test "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$launcher/Contents/Info.plist")" = org.nixos.home-manager.spotlight.org.example.testapp
test "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleDisplayName' "$launcher/Contents/Info.plist")" = 'Test Alias'
test "$(/usr/libexec/PlistBuddy -c 'Print :LSUIElement' "$launcher/Contents/Info.plist")" = true
test "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIconFile' "$launcher/Contents/Info.plist")" = icon.icns
test "$(/bin/cat "$launcher/Contents/Resources/home-manager-spotlight-target")" = "$(printf '%s\n%s\n%s\n%s' "$first_target" org.example.testapp 'Test Alias' 2)"
/usr/bin/cmp -s "$first_target/Contents/Resources/icon.icns" "$launcher/Contents/Resources/icon.icns"
/usr/bin/codesign --verify --deep --strict "$launcher"

mkdir -p "$applications_dir/Collision.app/Contents/Resources"
printf '%s\n' preserved >"$applications_dir/Collision.app/Contents/Resources/user-file"
ln -s "$first_target" "$source_apps/Collision.app"
bash "$script_dir/spotlight_app_launchers.sh" "$source_apps" "$applications_dir" 2>"$test_dir/stderr"
test "$(/bin/cat "$applications_dir/Collision.app/Contents/Resources/user-file")" = preserved

ln -sfn "$second_target" "$source_apps/TestAlias.app"
bash "$script_dir/spotlight_app_launchers.sh" "$source_apps" "$applications_dir"
test "$(/bin/cat "$launcher/Contents/Resources/home-manager-spotlight-target")" = "$(printf '%s\n%s\n%s\n%s' "$second_target" org.example.testapp 'Test Alias' 2)"
/usr/bin/cmp -s "$second_target/Contents/Resources/icon.icns" "$launcher/Contents/Resources/icon.icns"
