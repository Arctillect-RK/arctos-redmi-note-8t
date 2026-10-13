# Установка ArctOS на Redmi Note 8T — рабочий метод по шагам

Это «чистый» путь, который точно работает, без тупиков, что были в процессе.
Время: ~2–3 часа, большую часть — сборка.

## 0. Что нужно

- **Redmi Note 8T (willow)** с **разблокированным загрузчиком** (официально, через Mi Unlock).
  Redmi Note 8 (ginkgo) очень похож, но DTB и прошивка Wi-Fi там другие — инструкция проверена только на willow.
- **Родная прошивка-основа MIUI 12.5 (Android 11)** — разделы modem/bluetooth/dsp/vendor/persist должны быть
  стоковыми: из них скрипт достанет прошивки устройства.
- ПК с Linux или Windows + WSL2 (Ubuntu), ~60 ГБ места.
- **Свежие platform-tools (adb/fastboot ≥ 35)**: <https://developer.android.com/tools/releases/platform-tools>.
  ⚠️ Старый `fastboot` (2016–2018 годов) «успешно» шьёт sparse-образ userdata, но записывает только первые
  мегабайты — система потом не находится.
- USB-кабель. Для отладки очень удобно, что телефон по USB поднимает сеть `172.16.42.1` и SSH.

> ⚠️ Установка стирает все данные телефона (раздел userdata). Сделайте бэкап.

## 1. Собрать образ postmarketOS

```sh
pip install --user pmbootstrap          # или из https://gitlab.postmarketos.org/postmarketOS/pmbootstrap
pmbootstrap init                        # channel: edge, vendor: xiaomi, device: willow, UI: phosh, systemd: yes
pmbootstrap install                     # задайте пароль пользователя user
pmbootstrap export                      # /tmp/postmarketOS-export/xiaomi-willow.img и boot.img
```

Подсказки для WSL: если не работает DNS — в `%USERPROFILE%\.wslconfig` поставьте `networkingMode=mirrored`
и `dnsTunneling=true`; если мало места на C: — `wsl --manage <дистрибутив> --move D:\wsl`.

## 2. Собрать boot-образ ArctOS

Готовый DTB лежит в репозитории: `dts/sm6125-xiaomi-willow-arctos.dtb`
(исходник — `dts/sm6125-xiaomi-willow-arctos.dts`, все отличия от оригинала — `dts/willow-original-to-arctos.diff`).

```sh
pip install zstandard
python3 tools/make-arctos-boot.py /tmp/postmarketOS-export/boot.img \
        dts/sm6125-xiaomi-willow-arctos.dtb arctos-boot.img
```

Скрипт подставляет DTB, патчит initramfs (поиск системы на userdata) и добавляет нужные параметры ядра.

Пустой dtbo (обязателен, иначе загрузчик Xiaomi накладывает свои оверлеи и отказывается грузить ядро):

```sh
dd if=/dev/zero of=dtbo-empty.img bs=1M count=24
```

## 3. Собрать модули ядра

Ядро ставит сам postmarketOS (`linux-nura-qcom-sm61x5` 7.2.3), его не меняем — собираем только модули,
**тем же clang**, что и ядро (в ядре включены CFI и Shadow Call Stack). Удобнее всего в native-chroot pmbootstrap:

```sh
pmbootstrap chroot -- apk add clang lld llvm make flex bison perl elfutils-dev openssl openssl-dev \
    linux-headers python3 bc findutils pahole zstd diffutils gcc musl-dev
# исходники того же ядра + конфиг из pmaports
wget https://codeberg.org/sm61x5-mainline/linux/archive/v7.2.3-r0.tar.gz
# распакуйте в chroot (например /home/pmos/k/linux), положите config-nura-qcom-sm61x5.aarch64 как .config
cd linux
patch -p1 < patches/kernel/0001-drm-msm-dpu-sm6125-video-mode-panel.patch
patch -p1 < patches/kernel/0002-soc-qcom-pd-mapper-add-sm6125.patch
patch -p1 < patches/kernel/0003-ath10k-wcn3990-wlan-hl3x-fixes.patch
make ARCH=arm64 LLVM=1 olddefconfig
make ARCH=arm64 LLVM=1 KBUILD_BUILD_VERSION=1-nura-qcom-sm61x5 -j$(nproc)   # нужен Module.symvers
```

Из дерева ядра возьмите: `drivers/gpu/drm/msm/msm.ko`, `drivers/net/wireless/ath/ath10k/ath10k_core.ko`,
`ath10k_snoc.ko`, `drivers/soc/qcom/qcom_pd_mapper.ko`. Внешние модули из `drivers/`:

```sh
for m in nt36xxx-willow panel-xiaomi-willow-tianma pmi632-qg; do
  make -C /path/to/linux ARCH=arm64 LLVM=1 M=$PWD/drivers/$m modules
done
```

Сложите все 7 `.ko` в одну папку — она понадобится на шаге 6.

## 4. Прошить

Телефон в fastboot (питание + громкость вниз):

```sh
fastboot erase misc                         # сбрасывает флаг «после неудачной загрузки — сразу в fastboot»
fastboot flash dtbo dtbo-empty.img
# vbmeta с отключённой проверкой: проще всего `pmbootstrap flasher flash_vbmeta`
# (нужен пакет android-tools-avbtool в chroot), или вручную:
#   avbtool make_vbmeta_image --flags 2 --padding_size 4096 --output vbmeta-disabled.img
fastboot flash vbmeta vbmeta-disabled.img
fastboot flash userdata /tmp/postmarketOS-export/xiaomi-willow.img
fastboot flash boot arctos-boot.img
fastboot reboot
```

Первая загрузка ~1 минута. На экране должна появиться Phosh. По USB поднимется сеть:

```sh
ssh user@172.16.42.1
```

Сенсор, Wi-Fi и звук на этом этапе ещё не работают — это нормально.

## 5. Достать прошивки устройства (на телефоне)

Скопируйте репозиторий на телефон (`scp -r`), затем:

```sh
sudo sh scripts/arctos-extract-firmware.sh
```

Скрипт берёт из **собственных стоковых разделов телефона**: прошивки модема, ADSP и Wi-Fi DSP
(раздел modem), калибровку антенны `bdf_c3x.bin`, BT `crbtfw21/crnv21` (bluetooth), GPU zap,
IPA GSI и прошивку тачскрина (vendor), конфиги и заводскую калибровку датчиков (vendor + persist),
библиотеки ADSP (dsp). Плюс `a630_sqe.fw` и `firmware-5.bin` из linux-firmware.

## 6. Поставить ArctOS

```sh
sudo sh scripts/install-arctos.sh /path/to/ko-files
sh scripts/build-phosh.sh            # ~6 минут на телефоне, нужен Wi-Fi или USB-интернет
sudo reboot
```

Тема иконок: сгенерируйте её на ПК (`python3 theme/make_icons.py <папка с белыми глифами> theme/ArctOS`,
подробности в docstring) или пропустите — будет стандартная Adwaita.

PIN экрана блокировки: длина задаётся в `/etc/environment.d/90-arctos.conf` (`PHOSH_PIN_LENGTH`).

## 7. Проверка

| Что | Команда / признак |
|---|---|
| Дисплей | `dmesg | grep "panel init complete"`, в Phosh нет «телевизионной» копии кадра |
| Тачскрин | `dmesg | grep "Update firmware success"`, `NVTCapacitiveTouchScreen` в `/proc/bus/input/devices` |
| GPU | `journalctl -t phoc | grep "GL renderer: FD610"` |
| Частота CPU | `cat /sys/devices/system/cpu/cpufreq/policy*/scaling_driver` → `qcom-cpufreq-hw` |
| Батарея | `cat /sys/class/power_supply/qcom-battery/capacity` |
| Модем | `cat /sys/class/remoteproc/*/state` → `running` |
| Wi-Fi | `nmcli dev wifi list` |
| Bluetooth | `bluetoothctl show` |
| Датчики | `monitor-sensor --accel` |
| Модем в ModemManager | `mmcli -L` |

## Если что-то пошло не так

- **Телефон сразу возвращается в fastboot** → `fastboot erase misc`; проверьте, что dtbo пустой.
- **«failed to mount subpartitions»** → boot собран не через `make-arctos-boot.py`, или userdata
  записан старым fastboot (сверьте контрольные суммы блоков на телефоне и в образе).
- **Зависание при перезагрузке** → проверьте, что `rmtfs` запущен **без** `-r` (`rootfs/etc/systemd/system/rmtfs.service`).
- Вернуться на Android — [BACK-TO-ANDROID.md](BACK-TO-ANDROID.md).
