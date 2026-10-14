#!/usr/bin/env bash
# Legt einen Eintrag "SparteNet Manager" im Anwendungsmenü (KDE/GNOME) an.
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
chmod +x "$DIR/SparteNet_starten.sh"
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/spartenet-manager.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=SparteNet Manager
Comment=UniFi Cloud Gateway für Kleingartensparten verwalten
Exec="$DIR/SparteNet_starten.sh"
Path=$DIR
Icon=$DIR/sparteNet_icon.png
Terminal=true
Categories=Network;Utility;
DESK
chmod +x "$HOME/.local/share/applications/spartenet-manager.desktop"
update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1
echo "Fertig. „SparteNet Manager“ steht jetzt im Anwendungsmenü."
