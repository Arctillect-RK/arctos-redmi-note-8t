import re,sys
src,dst=sys.argv[1],sys.argv[2]
t=open(src).read()
i=t.index('spi@4a88000 {'); j=t.index('};',i)+2
node=t[i:j]
n=node.replace('pinctrl-1 = <0x35>;','pinctrl-1 = <0x34>;')
n=re.sub(r'\n\t*dmas = <[^>]*>;','',n); n=re.sub(r'\n\t*dma-names = [^;]*;','',n)
n=n.replace('status = "disabled";\n\t\t\t};','''status = "okay";

				touchscreen@0 {
					compatible = "novatek,NVT-ts-spi";
					reg = <0x00>;
					spi-max-frequency = <0x7a1200>;
					novatek,irq-gpio = <0x13 0x58 0x00>;
					novatek,swrst-n8-addr = <0x3f0fe>;
					novatek,spi-rd-fast-addr = <0x3f310>;
				};
			};''')
assert 'touchscreen@0' in n and 'dmas' not in n and '0x35' not in n
open(dst,'w').write(t[:i]+n+t[j:])
print(n)
