import re,sys
src,dst=sys.argv[1],sys.argv[2]
t=open(src,encoding='latin1').read()
L9=0x219
assert 'phandle = <0x219>;' not in t
m=re.search(r'(\n\t{5}l9 \{\n(?:\t{6}[^\n]*\n)*?)(\t{5}\};)',t); assert m
t=t[:m.end(1)]+'\t\t\t\t\t\tphandle = <0x219>;\n'+t[m.end(1):]
i=t.index('\t\t\tspi@4c90000 {')
node='''			serial@4c90000 {
				compatible = "qcom,geni-uart";
				reg = <0x00 0x4c90000 0x00 0x4000>;
				clocks = <0x16 0x9b>;
				clock-names = "se";
				interrupts = <0x00 0x138 0x04>;
				pinctrl-0 = <0x4c>;
				pinctrl-names = "default";
				status = "okay";

				bluetooth {
					compatible = "qcom,wcn3990-bt";
					vddio-supply = <0x219>;
					vddxo-supply = <0x211>;
					vddrf-supply = <0x212>;
					vddch0-supply = <0x213>;
					max-speed = <0x30d400>;
				};
			};

'''
t=t[:i]+node+t[i:]
open(dst,'w',encoding='latin1').write(t); print('ok')
