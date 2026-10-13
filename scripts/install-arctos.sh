#!/bin/sh
# ArctOS overlay installer. Run ON the phone as root from the repository root:
#   sudo sh scripts/install-arctos.sh /path/to/modules
# <modules> = directory with the built .ko files (see docs/INSTALL.md, step 3):
#   nt36xxx_willow.ko panel-xiaomi-willow-tianma.ko qcom-pmi632-qg.ko
#   msm.ko ath10k_core.ko ath10k_snoc.ko qcom_pd_mapper.ko
set -eu

MODS=${1:?usage: install-arctos.sh <dir with .ko files>}
REPO=$(cd "$(dirname "$0")/.." && pwd)
KVER=$(uname -r)
USER_HOME=/home/user

[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }

echo "== packages"
apk add rmtfs tqftpserv qrtr hexagonrpcd libssc iio-sensor-proxy font-liberation grim rsvg-convert

echo "== kernel modules"
install -Dm644 "$MODS/nt36xxx_willow.ko"             /lib/modules/$KVER/extra/nt36xxx_willow.ko
install -Dm644 "$MODS/panel-xiaomi-willow-tianma.ko" /lib/modules/$KVER/extra/panel-xiaomi-willow-tianma.ko
install -Dm644 "$MODS/qcom-pmi632-qg.ko"             /lib/modules/$KVER/extra/qcom-pmi632-qg.ko
for m in msm ath10k_core ath10k_snoc qcom_pd_mapper; do
  install -Dm644 "$MODS/$m.ko" /lib/modules/$KVER/updates/$m.ko
done
depmod -a

echo "== system configuration"
cp -r "$REPO/rootfs/etc/." /etc/
rm -f /etc/phosh/phoc.ini.append
install -Dm755 "$REPO/rootfs/usr/local/sbin/arctos-modem" /usr/local/sbin/arctos-modem
for f in /etc/phosh/phoc.ini /etc/phrog/phoc.ini; do
  mkdir -p "$(dirname $f)"; [ -f $f ] || cp /usr/share/phosh/phoc.ini $f
  grep -q '^\[output:DSI-1\]' $f || printf '\n[output:DSI-1]\nscale = 3\n' >> $f
done
# autologin into Phosh (greetd initial_session)
G=/etc/phrog/greetd-config.toml
if [ -f $G ] && ! grep -q '^\[initial_session\]' $G; then
  printf '\n[initial_session]\ncommand = "systemd-cat phosh-session"\nuser = "user"\n' >> $G
fi
mkdir -p /etc/dconf/profile
[ -f /etc/dconf/profile/user ] || printf 'user-db:user\nsystem-db:local\n' > /etc/dconf/profile/user
dconf update
hostnamectl set-hostname arctos || true
systemctl daemon-reload
systemctl enable rmtfs.service tqftpserv.service arctos-modem.service \
  hexagonrpcd-adsp-rootpd.service hexagonrpcd-adsp-sensorspd.service

echo "== theme, icons, wallpapers app"
install -Dm644 "$REPO/theme/gtk.css" $USER_HOME/.config/gtk-3.0/gtk.css
mkdir -p /usr/share/wallpapers/arctos
cp "$REPO"/theme/wallpapers/*.png /usr/share/wallpapers/arctos/
install -Dm755 "$REPO/theme/arctos-wallpapers.py" /usr/bin/arctos-wallpapers
install -Dm644 "$REPO/theme/os.arctos.Wallpapers.desktop" /usr/share/applications/os.arctos.Wallpapers.desktop
if [ -d "$REPO/theme/ArctOS" ]; then
  rm -rf /usr/share/icons/ArctOS; cp -r "$REPO/theme/ArctOS" /usr/share/icons/ArctOS
  gtk-update-icon-cache -f /usr/share/icons/ArctOS
fi
# hide utility apps from the home grid
D=$USER_HOME/.local/share/applications; mkdir -p $D
for a in org.freedesktop.IBus.Setup cups org.freedesktop.MalcontentControl rygel-preferences mobi.phosh.PhoshTour; do
  f=/usr/share/applications/$a.desktop; [ -f $f ] || continue
  { echo "[Desktop Entry]"; echo "NoDisplay=true"; grep -v '^\[Desktop Entry\]\|^NoDisplay=' $f; } > $D/$a.desktop
done
chown -R user:user $USER_HOME/.config $USER_HOME/.local

echo "done — now build the patched Phosh (scripts/build-phosh.sh) and reboot"
