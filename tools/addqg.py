import sys
src,dst=sys.argv[1],sys.argv[2]
t=open(src).read()
i=t.index('pmic@2 {'); j=t.index('typec@1500 {',i); j=t.rindex('\n',0,j)+1
ind=t[j:t.index('typec@1500',j)]
node=ind+'qgauge@4800 {\n'+ind+'\tcompatible = "qcom,pmi632-qg";\n'+ind+'\treg = <0x4800>;\n'+ind+'};\n\n'
assert 'qgauge@4800' not in t
t=t[:j]+node+t[j:]
open(dst,'w').write(t); print(t[i:i+700])
