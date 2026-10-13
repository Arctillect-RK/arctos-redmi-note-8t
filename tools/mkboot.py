import struct,sys,hashlib
base,dtb,out=sys.argv[1:4]
d=open(base,'rb').read()
ksz,kaddr,rsz,raddr,ssz,saddr,taddr,pg,hv=struct.unpack_from("<9I",d,8)
al=lambda n:((n+pg-1)//pg)*pg
k=d[pg:pg+ksz]; rd=d[pg+al(ksz):pg+al(ksz)+rsz]
p=k.rfind(b"\xd0\x0d\xfe\xed"); assert p+struct.unpack(">I",k[p+4:p+8])[0]==len(k)
k=k[:p]+open(dtb,'rb').read()
hdr=bytearray(d[:pg]); struct.pack_into("<I",hdr,8,len(k))
o=bytes(hdr)+k+b'\0'*(al(len(k))-len(k))+rd+b'\0'*(al(rsz)-rsz)
open(out,'wb').write(o); print(out,len(o),hashlib.md5(o).hexdigest())
