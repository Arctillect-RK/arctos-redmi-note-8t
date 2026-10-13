# Что откуда взято и куда кладётся

## Из этого репозитория

| Файл в репозитории | Происхождение | Куда на телефоне / как используется |
|---|---|---|
| `dts/sm6125-xiaomi-willow-arctos.dts/.dtb` | DTB postmarketOS `sm6125-xiaomi-willow` + наши правки | внутри `arctos-boot.img` (через `tools/make-arctos-boot.py`) |
| `dts/willow-original-to-arctos.diff` | разница с оригинальным DTB | для чтения / переноса на новую версию ядра |
| `patches/kernel/0001-…dpu…patch` | наш, по находкам ginkgo-mainline | ядро → `msm.ko` → `/lib/modules/$(uname -r)/updates/` |
| `patches/kernel/0002-…pd-mapper…patch` | наш | `qcom_pd_mapper.ko` → `updates/` |
| `patches/kernel/0003-…ath10k…patch` | наш, по находкам ginkgo-mainline | `ath10k_core.ko`, `ath10k_snoc.ko` → `updates/` |
| `patches/initramfs/…patch` | наш (initramfs postmarketOS) | применяется `tools/make-arctos-boot.py` |
| `patches/phosh/0001-arctos-phosh-0.57.0.patch` | наш (Phosh 0.57.0) | `scripts/build-phosh.sh` → `/usr/libexec/phosh` |
| `drivers/nt36xxx-willow/` | драйвер Novatek из Android-ядра Xiaomi, портирован нами | `nt36xxx_willow.ko` → `/lib/modules/…/extra/` |
| `drivers/panel-xiaomi-willow-tianma/` | наш, тайминги/команды из Android DT | `panel-xiaomi-willow-tianma.ko` → `extra/` |
| `drivers/pmi632-qg/` | ginkgo-mainline-linux (без изменений) | `qcom-pmi632-qg.ko` → `extra/` |
| `rootfs/etc/systemd/system/*.service` | наши | `/etc/systemd/system/` |
| `rootfs/usr/local/sbin/arctos-modem` | наш | `/usr/local/sbin/` |
| `rootfs/etc/udev/rules.d/81-arctos-accel-mount.rules` | наш | `/etc/udev/rules.d/` |
| `rootfs/etc/sysctl.d/90-arctos-panic.conf` | наш | `/etc/sysctl.d/` |
| `rootfs/etc/environment.d/90-arctos.conf` | наш | `/etc/environment.d/` |
| `rootfs/etc/dconf/db/local.d/10-arctos` | наш | `/etc/dconf/db/local.d/` + `dconf update` |
| `rootfs/etc/os-release` | наш (имя ArctOS) | `/etc/os-release` (вместо ссылки) |
| `theme/gtk.css` | наш | `~/.config/gtk-3.0/gtk.css` |
| `theme/make_icons.py` | наш; глифы — Adwaita symbolic (CC BY-SA) | генерирует тему `ArctOS` → `/usr/share/icons/ArctOS` |
| `theme/arctos-wallpapers.py` + `.desktop` | наш | `/usr/bin/arctos-wallpapers`, `/usr/share/applications/` |
| `theme/wallpapers/*.png` | наши (сгенерированы) | `/usr/share/wallpapers/arctos/` |
| `tools/make-arctos-boot.py` | наш | на ПК: boot.img pmbootstrap → `arctos-boot.img` |
| `tools/add*.py` | наши | скрипты правки DTS по шагам (для переноса на новые версии) |

## С самого телефона (скрипт `scripts/arctos-extract-firmware.sh`)

Не распространяются — достаются из стоковых разделов вашего же телефона.

| Что | Раздел-источник | Куда |
|---|---|---|
| `modem.mdt` + `modem.bNN` | modem (vfat) `image/` | `/lib/firmware/qcom/sm6125/xiaomi/willow/` |
| `adsp.mdt` + `adsp.bNN` | modem `image/` | там же |
| `wlanmdsp.mbn` (WLAN.HL.3.0.2-00656) | modem `image/` | там же (модем берёт через tqftpserv) |
| `bdf_c3x.bin` (калибровка антенны 8T) | modem `image/` | `/lib/firmware/ath10k/WCN3990/hw1.0/board.bin` |
| `crbtfw21.tlv`, `crnv21.bin` | bluetooth (vfat) `image/` | `/lib/firmware/qca/` |
| `a610_zap.mdt/.b00-.b02` (подписан под устройство) | vendor `/firmware` | `/lib/firmware/qcom/sm6125/xiaomi/willow/` |
| `ipa_fws.mdt/.b00-.b04` | vendor `/firmware` | там же |
| `novatek_ts_tianma_fw.bin` | vendor `/firmware` | `/lib/firmware/` |
| конфиги датчиков `nicobar_*.json` | vendor `/etc/sensors/config` | `/usr/share/qcom/sm6125/xiaomi/willow/sensors/config/` |
| заводская калибровка датчиков | persist `/sensors/registry` | `…/sensors/registry/` |
| библиотеки ADSP | dsp (ext4) | `/usr/share/qcom/sm6125/xiaomi/willow/dsp/` |

## Из открытых источников

| Что | Откуда | Куда |
|---|---|---|
| ядро `linux-nura-qcom-sm61x5` 7.2.3 | postmarketOS / sm61x5-mainline | ставит pmbootstrap |
| исходники ядра для модулей | codeberg.org/sm61x5-mainline/linux, тег `v7.2.3-r0` | сборка на ПК |
| `a630_sqe.fw` (версия ≥ 0x190) | linux-firmware | `/lib/firmware/qcom/` |
| `ath10k/WCN3990/hw1.0/firmware-5.bin` | linux-firmware | `/lib/firmware/ath10k/WCN3990/hw1.0/` |
| `rmtfs`, `tqftpserv`, `qrtr`, `hexagonrpcd`, `libssc` | репозитории Alpine/postmarketOS | `apk add` |
| Phosh 0.57.0 | sources.phosh.mobi | собирается на телефоне с нашим патчем |
