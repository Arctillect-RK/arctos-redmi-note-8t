import zstandard,sys,io
def parse(b):
    out=[];p=0
    while True:
        h=b[p:p+110]; assert h[:6] in (b'070701',b'070702'),h[:6]
        f=[int(h[6+8*i:14+8*i],16) for i in range(13)]
        ns,fs=f[11],f[6]
        name=b[p+110:p+110+ns-1]; p2=(p+110+ns+3)&~3
        data=b[p2:p2+fs]; p=(p2+fs+3)&~3
        if name==b'TRAILER!!!': break
        out.append([h,name,data])
    return out
def build(ents):
    o=bytearray()
    for h,name,data in ents+[[b'07070100000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000',b'TRAILER!!!',b'']]:
        f=[int(h[6+8*i:14+8*i],16) for i in range(13)]
        f[6]=len(data); f[11]=len(name)+1
        o+=b'070701'+b''.join(b'%08X'%x for x in f)+name+b'\0'
        o+=b'\0'*((-len(o))%4); o+=data; o+=b'\0'*((-len(o))%4)
    return bytes(o)
