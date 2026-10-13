#!/usr/bin/env python3
"""Turn the boot.img produced by pmbootstrap for xiaomi-willow into an ArctOS boot image.

  python3 make-arctos-boot.py <pmos-boot.img> <sm6125-xiaomi-willow-arctos.dtb> <out-boot.img>

What it does (header v0 Android boot image with an appended DTB, as pmOS builds it):
  1. replaces the DTB appended to the kernel with the ArctOS one;
  2. patches the initramfs (`init_functions.sh`): the rootfs image uses 4096-byte sectors while
     the eMMC has 512-byte ones, so `fdisk -l` cannot count the subpartitions inside userdata and
     pmOS never tries `losetup --sector-size 4096` -> "failed to mount subpartitions";
  3. drops `quiet splash`, adds the kernel options the bring-up needs.

Requires: pip install zstandard   (pmOS initramfs is zstd-compressed)
"""
import io
import struct
import sys

import zstandard

EXTRA_CMDLINE = ('clk_ignore_unused pd_ignore_unused fw_devlink=permissive '
                 'fw_devlink.sync_state=disabled console=tty0')
FDISK_OLD = '\t\t\tif [ "$part_count" -eq 2 ]; then\n'
FDISK_NEW = ('\t\t\t# willow: 4K-sector image on 512-byte eMMC, fdisk cannot count it\n'
             '\t\t\tif [ "$part_count" -eq 2 ] || '
             '[ "$(readlink -f /dev/disk/by-partlabel/userdata)" = "$partition" ]; then\n')


def cpio_parse(b):
    out, p = [], 0
    while True:
        h = b[p:p + 110]
        assert h[:6] in (b'070701', b'070702'), h[:6]
        f = [int(h[6 + 8 * i:14 + 8 * i], 16) for i in range(13)]
        ns, fs = f[11], f[6]
        name = b[p + 110:p + 110 + ns - 1]
        p2 = (p + 110 + ns + 3) & ~3
        data = b[p2:p2 + fs]
        p = (p2 + fs + 3) & ~3
        if name == b'TRAILER!!!':
            return out
        out.append([h, name, data])


def cpio_build(entries):
    o = bytearray()
    trailer = [b'070701' + b'0' * 104, b'TRAILER!!!', b'']
    for h, name, data in entries + [trailer]:
        f = [int(h[6 + 8 * i:14 + 8 * i], 16) for i in range(13)]
        f[6], f[11] = len(data), len(name) + 1
        if name == b'TRAILER!!!':
            f[4] = 1  # nlink
        o += b'070701' + b''.join(b'%08X' % x for x in f) + name + b'\0'
        o += b'\0' * ((-len(o)) % 4)
        o += data
        o += b'\0' * ((-len(o)) % 4)
    return bytes(o)


def main(src, dtb_path, dst):
    d = open(src, 'rb').read()
    assert d[:8] == b'ANDROID!', 'not an Android boot image'
    ksz, _kaddr, rsz, _raddr, _ssz, _saddr, _taddr, pg, _hv = struct.unpack_from('<9I', d, 8)
    al = lambda n: ((n + pg - 1) // pg) * pg  # noqa: E731

    kernel = d[pg:pg + ksz]
    ramdisk = d[pg + al(ksz):pg + al(ksz) + rsz]

    # 1. DTB
    p = kernel.rfind(b'\xd0\x0d\xfe\xed')
    assert p > 0 and p + struct.unpack('>I', kernel[p + 4:p + 8])[0] == len(kernel), 'no appended DTB'
    kernel = kernel[:p] + open(dtb_path, 'rb').read()

    # 2. initramfs
    entries = cpio_parse(zstandard.ZstdDecompressor().stream_reader(io.BytesIO(ramdisk)).read())
    for e in entries:
        if e[1] == b'init_functions.sh':
            text = e[2].decode()
            if FDISK_NEW not in text:
                assert text.count(FDISK_OLD) == 1, 'init_functions.sh changed upstream, patch by hand'
                text = text.replace(FDISK_OLD, FDISK_NEW)
            e[2] = text.encode()
    ramdisk = zstandard.ZstdCompressor(level=19).compress(cpio_build(entries))

    # 3. cmdline (header bytes 64..576)
    hdr = bytearray(d[:pg])
    cmd = bytes(hdr[64:576]).split(b'\0')[0].decode()
    words = [w for w in cmd.split() if w not in ('quiet', 'splash')]
    for w in EXTRA_CMDLINE.split():
        if w not in words:
            words.append(w)
    cmd = ' '.join(words)
    assert len(cmd) < 512
    hdr[64:576] = cmd.encode().ljust(512, b'\0')
    hdr[576:608] = b'\0' * 32  # id/sha, not checked by the willow bootloader
    struct.pack_into('<I', hdr, 8, len(kernel))
    struct.pack_into('<I', hdr, 16, len(ramdisk))

    out = (bytes(hdr) + kernel + b'\0' * (al(len(kernel)) - len(kernel))
           + ramdisk + b'\0' * (al(len(ramdisk)) - len(ramdisk)))
    open(dst, 'wb').write(out)
    print('written', dst, len(out), 'bytes\ncmdline:', cmd)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
