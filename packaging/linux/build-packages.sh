#!/usr/bin/env bash
# Construit les paquets .deb et .rpm de gsColorName (exécutable autonome PyInstaller).
# Usage : packaging/linux/build-packages.sh [deb] [rpm]   (par défaut : les deux)
# Prérequis : python3 (+ venv), dpkg-deb (pour .deb), rpmbuild (pour .rpm)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
VERSION="$(python3 -c 'import version; print(version.__version__)')"
ARCH_DEB="amd64"; ARCH_RPM="x86_64"
[ "$(uname -m)" = "aarch64" ] && { ARCH_DEB="arm64"; ARCH_RPM="aarch64"; }
TARGETS="${*:-deb rpm}"
mkdir -p dist

# 1) exécutable autonome
if [ ! -x dist/gscolorname/gscolorname ] || [ "${REBUILD:-1}" = "1" ]; then
  python3 -m venv .venv-build
  .venv-build/bin/pip install -q --upgrade pip
  .venv-build/bin/pip install -q -r requirements.txt pyinstaller
  .venv-build/bin/pyinstaller packaging/gscolorname.spec --noconfirm --distpath dist --workpath build
fi

# 2) arborescence commune
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
install -d "$STAGE/opt/gscolorname" "$STAGE/usr/bin" "$STAGE/usr/share/applications" \
  "$STAGE/usr/share/icons/hicolor/256x256/apps" "$STAGE/usr/share/icons/hicolor/scalable/apps" \
  "$STAGE/usr/share/doc/gscolorname"
cp -a dist/gscolorname/. "$STAGE/opt/gscolorname/"
ln -s /opt/gscolorname/gscolorname "$STAGE/usr/bin/gscolorname"
install -m644 packaging/linux/gscolorname.desktop "$STAGE/usr/share/applications/"
install -m644 assets/gscolorname.png "$STAGE/usr/share/icons/hicolor/256x256/apps/gscolorname.png"
install -m644 assets/gscolorname.svg "$STAGE/usr/share/icons/hicolor/scalable/apps/gscolorname.svg"
install -m644 README.md LICENSE "$STAGE/usr/share/doc/gscolorname/"
SIZE_KB="$(du -sk "$STAGE" | cut -f1)"

DESC_SHORT="Nom et codes d'une couleur (HEX, RGB, CMJN, Lab...), pipette et IA"
DESC_LONG="Application de bureau Qt : convertit une couleur dans plus de 20 formats, trouve son nom
 parmi 32 000 noms (CIEDE2000), pipette ecran (Wayland/X11) et assistant IA via LM Studio ou OpenRouter."

# 3) .deb
if [[ " $TARGETS " == *" deb "* ]]; then
  DEB="$(mktemp -d)"
  cp -a "$STAGE/." "$DEB/"
  install -d "$DEB/DEBIAN"
  cat > "$DEB/DEBIAN/control" <<CTRL
Package: gscolorname
Version: $VERSION
Section: graphics
Priority: optional
Architecture: $ARCH_DEB
Maintainer: gsavard <https://github.com/gsavard>
Homepage: https://github.com/gsavard/gsColorName
Installed-Size: $SIZE_KB
Depends: libc6 (>= 2.31), libgl1, libegl1, libxkbcommon0, libxkbcommon-x11-0, libfontconfig1, libdbus-1-3, libxcb-cursor0, libxcb-icccm4, libxcb-keysyms1, libxcb-shape0
Recommends: xdg-desktop-portal
Description: $DESC_SHORT
 $DESC_LONG
CTRL
  printf '#!/bin/sh\nset -e\ncommand -v update-desktop-database >/dev/null && update-desktop-database -q /usr/share/applications || true\ncommand -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q -t /usr/share/icons/hicolor || true\n' > "$DEB/DEBIAN/postinst"
  cp "$DEB/DEBIAN/postinst" "$DEB/DEBIAN/postrm"
  chmod 755 "$DEB/DEBIAN/postinst" "$DEB/DEBIAN/postrm"
  dpkg-deb --root-owner-group --build "$DEB" "dist/gscolorname_${VERSION}_${ARCH_DEB}.deb"
  rm -rf "$DEB"
fi

# 4) .rpm
if [[ " $TARGETS " == *" rpm "* ]]; then
  TOP="$(mktemp -d)"
  mkdir -p "$TOP"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
  tar -C "$STAGE" -czf "$TOP/SOURCES/stage.tar.gz" .
  sed -e "s/@VERSION@/$VERSION/" packaging/linux/gscolorname.rpm.spec > "$TOP/SPECS/gscolorname.spec"
  rpmbuild --define "_topdir $TOP" --target "$ARCH_RPM" -bb "$TOP/SPECS/gscolorname.spec"
  cp "$TOP"/RPMS/*/gscolorname-*.rpm dist/
  rm -rf "$TOP"
fi
ls -lh dist/*.deb dist/*.rpm 2>/dev/null || true
