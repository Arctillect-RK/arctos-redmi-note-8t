import sys,re
src,dst=sys.argv[1],sys.argv[2]
t=open(src,encoding='latin1').read()
def node_span(head):
    i=t.index(head); depth=0; k=t.index('{',i)
    while True:
        a=t.find('{',k+1); b=t.find('}',k+1)
        if a!=-1 and a<b: depth+=1; k=a
        else:
            if depth==0: return i,b
            depth-=1; k=b
def set_okay(head):
    global t
    i,j=node_span(head)
    # only the node's own status (first level): find 'status = "disabled";' before first child '{' after header
    first_child=t.find('{',t.index('{',i)+1)
    s=t.find('status = "disabled";',i,j)
    if s==-1: print('no disabled status',head); return
    t=t[:s]+'status = "okay";'+t[s+len('status = "disabled";'):]
    print('enabled',head)
set_okay('display-subsystem@5e00000 {')
set_okay('phy@5e94400 {')
i,j=node_span('clock-controller@5f00000 {')
if 'status = "disabled";' in t[i:j]: set_okay('clock-controller@5f00000 {')
set_okay('dsi@5e94000 {')
# L18 phandle
t=t.replace('\t\t\t\t\tl18 {\n\t\t\t\t\t\tregulator-min-microvolt = <0x124f80>;\n\t\t\t\t\t\tregulator-max-microvolt = <0x134980>;\n\t\t\t\t\t\tregulator-allow-set-load;\n',
            '\t\t\t\t\tl18 {\n\t\t\t\t\t\tregulator-min-microvolt = <0x124f80>;\n\t\t\t\t\t\tregulator-max-microvolt = <0x134980>;\n\t\t\t\t\t\tregulator-allow-set-load;\n\t\t\t\t\t\tphandle = <0x1f2>;\n',1)
assert 'phandle = <0x1f2>;' in t
i,j=node_span('dsi@5e94000 {')
d=t[i:j]
d=d.replace('phy-names = "dsi";','phy-names = "dsi";\n\t\t\t\tvdda-supply = <0x1f2>;',1)
d=d.replace('''					port@1 {
						reg = <0x01>;

						endpoint {
						};''','''					port@1 {
						reg = <0x01>;

						endpoint {
							remote-endpoint = <0x1f0>;
							data-lanes = <0x00 0x01 0x02 0x03>;
							phandle = <0x1f1>;
						};''',1)
assert 'remote-endpoint = <0x1f0>' in d, d[-800:]
panel='''
				panel@0 {
					compatible = "xiaomi,willow-tianma-nt36672a";
					reg = <0x00>;
					reset-gpios = <0x13 0x5a 0x01>;

					port {
						endpoint {
							remote-endpoint = <0x1f1>;
							phandle = <0x1f0>;
						};
					};
				};
'''
k=d.index('\t\t\t\tports {')
d=d[:k]+panel.lstrip('\n')+'\n'+d[k:]
t=t[:i]+d+t[j:]
open(dst,'w',encoding='latin1').write(t)
i,j=node_span('dsi@5e94000 {'); print(t[i:i+1800])
