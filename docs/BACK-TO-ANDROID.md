# Вернуться на Android (LineageOS)

Проверено: официальная **LineageOS 23.2** для ginkgo/willow (одна сборка на оба телефона).
Нужна родная основа MIUI 12.5 (Android 11) — она остаётся нетронутой, ArctOS её не трогает.

## Файлы

С <https://download.lineageos.org/devices/ginkgo/builds> одной и той же даты:
`lineage-23.2-…-ginkgo-signed.zip`, `recovery.img`, `dtbo.img`, `vbmeta.img`. Сверьте SHA-256 со страницы.

## Шаги

1. Телефон в fastboot (питание + громкость вниз). Используйте **свежий** platform-tools.
   ```sh
   fastboot erase misc
   fastboot flash dtbo dtbo.img          # обязательно: после ArctOS там пустой dtbo
   fastboot flash vbmeta vbmeta.img
   fastboot flash recovery recovery.img
   fastboot format:ext4 cache            # см. «грабли» ниже
   fastboot reboot recovery
   ```
2. В Lineage Recovery: **Factory reset → Format data / factory reset**.
3. **Apply update → Apply from ADB**, на ПК:
   ```sh
   adb sideload lineage-23.2-…-ginkgo-signed.zip
   ```
   Успех — `Total xfer: 1.00x` (индикатор может остановиться на ~47%, это нормально).
4. **Reboot system now**. Первая загрузка 3–5 минут.

## Грабли

| Симптом | Причина | Решение |
|---|---|---|
| `adb sideload` сразу пишет `Total xfer: 0.00x`, на экране «Installation aborted», «Failed to mount /cache» | раздел /cache после ArctOS испорчен, recovery не может писать служебные файлы | `fastboot format:ext4 cache`, повторить sideload |
| Первая загрузка: экран восстановления с `init_user0_failed` | userdata остался в старом формате (от Linux), Android не может создать зашифрованные данные | в этом же экране **Factory data reset** (или recovery → Format data) и перезагрузка |
| Recovery не грузится, телефон возвращается в fastboot | пустой dtbo от ArctOS | прошить `dtbo.img` от LineageOS |
| Старый `adb` пишет `unauthorized` в recovery | очень старая версия adb | свежий platform-tools |
