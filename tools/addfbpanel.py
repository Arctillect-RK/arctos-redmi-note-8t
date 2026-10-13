import sys,re
src,dst=sys.argv[1],sys.argv[2]
t=open(src,encoding='latin1').read()
m=re.search(r'(\n(\t+)framebuffer(@[0-9a-f]+)? \{\n\t+compatible = "simple-framebuffer";\n)',t)
assert m, 'no fb'
t=t[:m.end()]+m.group(2)+'\tpanel = <0x1f3>;\n'+t[m.end():]
k=t.rindex('\n};')  # end of root node? find root '/ {' end: insert as last child of root
root_end=t.index('\n};\n', t.index('/ {'))
node='\n\tframebuffer-panel {\n\t\twidth-mm = <0x43>;\n\t\theight-mm = <0x91>;\n\t\tphandle = <0x1f3>;\n\t};\n'
t=t[:root_end]+node+t[root_end:]
open(dst,'w',encoding='latin1').write(t)
i=t.index('compatible = "simple-framebuffer"'); print(t[i-60:i+300])
