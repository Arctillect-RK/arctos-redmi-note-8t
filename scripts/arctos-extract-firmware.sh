#!/bin/sh
# ArctOS: copy the device-specific firmware out of the phone's OWN stock partitions.
# Run ON the phone as root (sudo), after the first boot of the pmOS/ArctOS image.
# The stock modem/bluetooth/dsp/vendor/persist partitions are untouched by ArctOS
# (only boot, dtbo, vbmeta and userdata are rewritten), so everything is still there.
# Nothing proprietary is shipped in the repository.
set -eu

DEV=/dev/disk/by-partlabel
FW=/lib/firmware/qcom/sm6125/xiaomi/willow
ATH=/lib/firmware/ath10k/WCN3990/hw1.0
QCA=/lib/firmware/qca
SHARE=/usr/share/qcom/sm6125/xiaomi/willow
M=/tmp/arctos-fw-mnt

[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }
command -v debugfs >/dev/null || apk add e2fsprogs-extra
mkdir -p $M/modem $M/bt $FW $ATH $QCA $SHARE/sensors $SHARE/dsp

echo "== modem partition (vfat): modem, ADSP, WLAN DSP"
mount -o ro "$DEV/modem" $M/modem
cp $M/modem/image/modem.mdt $M/modem/image/modem.b* $FW/
cp $M/modem/image/adsp.mdt  $M/modem/image/adsp.b*  $FW/
cp $M/modem/image/wlanmdsp.mbn $FW/
# Wi-Fi board data: the Redmi Note 8T uses bdf_c3x (Redmi Note 8 / ginkgo: bdf_c3j)
cp $M/modem/image/bdf_c3x.bin $ATH/board.bin
umount $M/modem

echo "== bluetooth partition (vfat): WCN3990 BT"
mount -o ro "$DEV/bluetooth" $M/bt
cp $M/bt/image/crbtfw21.tlv $M/bt/image/crnv21.bin $QCA/
umount $M/bt

echo "== vendor partition (ext4, read with debugfs): GPU zap, IPA GSI, touch, sensor configs"
V="$DEV/vendor"
for f in a610_zap.mdt a610_zap.b00 a610_zap.b01 a610_zap.b02; do debugfs -R "dump /firmware/$f $FW/$f" "$V"; done
for f in ipa_fws.mdt ipa_fws.b00 ipa_fws.b01 ipa_fws.b02 ipa_fws.b03 ipa_fws.b04; do debugfs -R "dump /firmware/$f $FW/$f" "$V"; done
debugfs -R "dump /firmware/novatek_ts_tianma_fw.bin /lib/firmware/novatek_ts_tianma_fw.bin" "$V"
(cd $SHARE/sensors && debugfs -R "rdump /etc/sensors/config ." "$V" && debugfs -R "dump /etc/sensors/sns_reg_config sns_reg.conf" "$V")

echo "== persist partition: factory sensor calibration registry"
(cd $SHARE/sensors && debugfs -R "rdump /sensors/registry ." "$DEV/persist")

echo "== dsp partition: ADSP shared libraries for the sensors PD"
(cd $SHARE/dsp && debugfs -R "rdump / ." "$DEV/dsp")
ln -sfn xiaomi /usr/share/qcom/sm6125/Xiaomi

echo "== firmware from linux-firmware (not on the phone)"
echo "   a630_sqe.fw (Adreno SQE >= 0x190) and ath10k firmware-5.bin come from linux-firmware:"
apk add linux-firmware-qcom linux-firmware-ath10k >/dev/null 2>&1 || true
[ -f /lib/firmware/qcom/a630_sqe.fw ] || [ -f /lib/firmware/qcom/a630_sqe.fw.zst ] || echo "   !! install a630_sqe.fw manually"
[ -f $ATH/firmware-5.bin ] || [ -f $ATH/firmware-5.bin.zst ] || echo "   !! install ath10k/WCN3990/hw1.0/firmware-5.bin manually"

rmdir $M/modem $M/bt $M 2>/dev/null || true
echo "done"
