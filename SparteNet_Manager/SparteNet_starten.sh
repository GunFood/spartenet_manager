#!/usr/bin/env bash
# SparteNet Manager (Cloud) – Start für Linux (Nobara/Fedora/Ubuntu). Braucht nur Python 3.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 fehlt. Installieren mit:  sudo dnf install python3"; read -rp "Enter"; exit 1
fi
exec python3 SparteNet_Manager.py
