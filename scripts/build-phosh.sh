#!/bin/sh
# Build the ArctOS-patched Phosh 0.57.0 natively on the phone (8 cores: ~6 min) and install it.
# Run ON the phone as the normal user from the repository root:  sh scripts/build-phosh.sh
# Needs Wi-Fi (downloads build dependencies and the Phosh tarball).
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
VER=0.57.0
WORK=$HOME/src

sudo apk add build-base meson appstream-dev callaudiod-dev systemd-dev evince-dev \
  evolution-data-server-dev feedbackd-dev gcr-dev gettext-dev glib-dev gmobile-dev \
  gnome-bluetooth-dev gnome-desktop-dev gtk+3.0-dev libadwaita-dev libgudev-dev \
  libhandy1-dev libsecret-dev linux-pam-dev modemmanager-dev networkmanager-dev \
  polkit-dev pulseaudio-dev qrcodegen-dev upower-dev wayland-dev wayland-protocols

mkdir -p "$WORK" && cd "$WORK"
[ -f phosh-$VER.tar.xz ] || wget https://sources.phosh.mobi/releases/phosh/phosh-$VER.tar.xz
[ -d phosh-$VER ] || tar -xf phosh-$VER.tar.xz
cd phosh-$VER
patch -p1 --forward < "$REPO/patches/phosh/0001-arctos-phosh-$VER.patch" || true

[ -d build ] || meson setup build --prefix=/usr --libexecdir=/usr/libexec --buildtype=release \
  -Dphoc_tests=disabled -Dman=false -Dtests=false
# Long build: if you run this over SSH, start it with
#   sudo systemd-run --uid=$(id -un) --gid=$(id -gn) --working-directory=$PWD meson compile -C build
# (background jobs die with the SSH session; never run two ninja builds at once)
meson compile -C build

sudo cp -n /usr/libexec/phosh /usr/libexec/phosh.orig 2>/dev/null || true
sudo install -m755 build/src/phosh /usr/libexec/phosh
echo "installed — reboot to start the patched Phosh (original kept as /usr/libexec/phosh.orig)"
