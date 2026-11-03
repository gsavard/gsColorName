#!/usr/bin/env bash
# Ajoute gsColorName au menu des applications (GNOME/KDE)
DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/gscolorname.desktop <<DESK
[Desktop Entry]
Type=Application
Name=gsColorName
Comment=Nom et codes d'une couleur (HEX, RGB, CMJN…), pipette et IA
Exec=$DIR/run.sh
Icon=$DIR/assets/gscolorname.svg
Terminal=false
Categories=Graphics;Utility;
StartupWMClass=gscolorname
DESK
update-desktop-database ~/.local/share/applications 2>/dev/null || true
echo "Installé : ~/.local/share/applications/gscolorname.desktop"
