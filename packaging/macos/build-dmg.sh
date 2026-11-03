#!/usr/bin/env bash
# Construit gsColorName.app et l'image disque .dmg (à lancer sur macOS).
# Prérequis : Python 3.10+ (python.org ou Homebrew), Xcode Command Line Tools.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
VERSION="$(python3 -c 'import version; print(version.__version__)')"
ARCH="$(uname -m)"            # arm64 (Apple Silicon) ou x86_64 (Intel)
mkdir -p dist

python3 -m venv .venv-build
.venv-build/bin/pip install -q --upgrade pip
.venv-build/bin/pip install -q -r requirements.txt pyinstaller
rm -rf build dist/gsColorName.app dist/gscolorname
.venv-build/bin/pyinstaller packaging/gscolorname.spec --noconfirm --distpath dist --workpath build

APP="dist/gsColorName.app"
# Signature ad hoc (obligatoire sur Apple Silicon ; remplacer « - » par une identité Developer ID si disponible)
codesign --force --deep --sign "${MAC_SIGN_IDENTITY:--}" "$APP"
codesign --verify --deep --strict "$APP"

# Image disque : l'app + un raccourci vers /Applications
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
DMG="dist/gsColorName-${VERSION}-macos-${ARCH}.dmg"
rm -f "$DMG"
hdiutil create -volname "gsColorName ${VERSION}" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
echo "OK : $DMG"
