# Основа, благодарности и лицензии

## На чём основано

- **[ginkgo-mainline-linux](https://github.com/Huabin1010/ginkgo-mainline-linux)** (Huabin1010) — mainline Linux
  на Redmi Note 8 (ginkgo): тот же SoC SM6125, та же панель Tianma NT36672A и тот же тачскрин. Их отчёты были
  главной картой по дисплею (prog_fetch INTF_1, частота MDP), тачскрину (SPI_MODE_0, выравнивание структуры,
  передача по 32 байта, sleep-pinctrl), Wi-Fi (MSA 1 МБ, порядок vdev-start, quiet mode, chainmask), GPU (zap и
  SQE) и cpufreq. Драйвер `drivers/pmi632-qg/qcom-pmi632-qg.c` взят у них без изменений.
- **[postmarketOS](https://postmarketos.org/)** — дистрибутив, pmbootstrap, initramfs, порт `xiaomi-willow`.
- **[sm61x5-mainline](https://codeberg.org/sm61x5-mainline/linux)** (Barnabas Czeman) — ядро
  `linux-nura-qcom-sm61x5` с поддержкой SM6125.
- **[Phosh](https://gitlab.gnome.org/World/Phosh/phosh)** — мобильная оболочка (GPL-3.0-or-later).
- **[gmobile](https://gitlab.gnome.org/World/Phosh/gmobile)** — геометрия выреза (используется профиль `xiaomi,lavender`).
- **Adwaita icon theme** — символические глифы для генератора иконок (CC BY-SA 3.0).
- Android-ядро и DT Xiaomi для ginkgo/willow (trinket) — источник таймингов панели, параметров SMP2P/GLINK/IPA/BT
  и драйвера Novatek NT36xxx.

## Лицензии

| Часть | Лицензия |
|---|---|
| `patches/kernel/*`, `drivers/*`, `dts/*` | GPL-2.0 (как ядро Linux; DTS — по лицензии исходного DT) |
| `patches/phosh/*` | GPL-3.0-or-later (как Phosh) |
| `patches/initramfs/*`, `tools/*`, `scripts/*`, `rootfs/*` | GPL-3.0-or-later |
| `theme/*.py`, `theme/gtk.css`, `theme/wallpapers/*` | GPL-3.0-or-later |
| сгенерированные иконки | CC BY-SA 3.0 (из-за глифов Adwaita) |

Проприетарные прошивки Qualcomm/Xiaomi в репозиторий не входят и не распространяются.

Иконки и обои ArctOS — оригинальная графика в духе iOS 4–6; это не материалы Apple.
