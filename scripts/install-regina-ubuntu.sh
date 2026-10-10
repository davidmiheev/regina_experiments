#!/usr/bin/env bash
# Install Regina (https://regina-normal.github.io) from the official Ubuntu apt
# repository, following https://regina-normal.github.io/install/ubuntu.html.
#
# Idempotent: exits early if Regina is already installed (use --force to redo).
# Supported releases: Ubuntu 24.04 (noble), 25.04 (plucky), 25.10 (questing).
#
# Usage:  scripts/install-regina-ubuntu.sh [--with-doc] [--with-dev] [--force]
set -euo pipefail

WITH_DOC=0
WITH_DEV=0
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --with-doc) WITH_DOC=1 ;;
    --with-dev) WITH_DEV=1 ;;
    --force)    FORCE=1 ;;
    -h|--help)  sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

if [[ $FORCE -eq 0 ]] && command -v regina-python >/dev/null 2>&1; then
  echo "Regina already installed: $(regina-engine-config --version 2>/dev/null || echo '?')"
  exit 0
fi

if [[ $EUID -eq 0 ]]; then SUDO=""; else SUDO="sudo"; fi

. /etc/os-release
CODENAME="${VERSION_CODENAME:-}"
case "$CODENAME" in
  noble|plucky|questing) ;;
  *) echo "Unsupported Ubuntu release '$CODENAME' (need noble, plucky or questing)." >&2
     echo "See https://regina-normal.github.io/install/ for other options." >&2
     exit 1 ;;
esac

export DEBIAN_FRONTEND=noninteractive

echo ">> Installing signing keys (debian-keyring)"
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq debian-keyring curl ca-certificates >/dev/null

echo ">> Adding Regina apt source for $CODENAME"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fsSL -o "$TMP/regina-$CODENAME.sources" \
  "https://regina-normal.github.io/repos/regina-$CODENAME.sources"
$SUDO cp "$TMP/regina-$CODENAME.sources" /etc/apt/sources.list.d/

echo ">> Installing regina-normal"
$SUDO apt-get update -qq
PKGS=(regina-normal)
[[ $WITH_DOC -eq 1 ]] && PKGS+=(regina-normal-doc)
[[ $WITH_DEV -eq 1 ]] && PKGS+=(regina-normal-dev)
# --no-install-recommends keeps the install lean on headless machines;
# the GUI (regina-gui) is still part of the package.
$SUDO apt-get install -y -qq --no-install-recommends "${PKGS[@]}" >/dev/null

echo ">> Installed: $(regina-engine-config --version 2>/dev/null || dpkg-query -W -f='${Version}' regina-normal)"
