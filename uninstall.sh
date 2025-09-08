#!/usr/bin/env bash
set -euo pipefail

# SimpleBooth uninstaller
# Removes services, virtual environment and configuration files created by setup.sh

if [[ $EUID -ne 0 ]]; then
  echo "Ce script doit être exécuté en tant que root" >&2
  exit 1
fi

INSTALL_USER=${SUDO_USER:-$USER}
HOME_DIR=$(eval echo "~$INSTALL_USER")
APP_DIR="$(cd "$(dirname "$0")" && pwd)"

printf 'Suppression du service systemd...\n'
systemctl disable --now simplebooth-kiosk.service 2>/dev/null || true
rm -f /etc/systemd/system/simplebooth-kiosk.service
systemctl daemon-reload || true

printf 'Suppression de l\'autostart...\n'
rm -f "$HOME_DIR/start_simplebooth.sh"
rm -f "$HOME_DIR/.config/autostart/simplebooth.desktop"

printf 'Suppression de l\'autologin...\n'
rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf 2>/dev/null || true
rmdir /etc/systemd/system/getty@tty1.service.d 2>/dev/null || true

printf 'Suppression de l\'environnement virtuel et des données...\n'
rm -rf "$APP_DIR/venv" "$APP_DIR/photos" "$APP_DIR/effet" "$APP_DIR/config.json"

printf 'Désinstallation terminée.\n'
