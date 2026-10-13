import re,sys
src,dst=sys.argv[1],sys.argv[2]
t=open(src).read()
PH='0x1fe'
assert 'phandle = <%s>;'%PH not in t
for cpu,dom in [('0',0),('1',0),('2',0),('3',0),('100',1),('101',1),('102',1),('103',1)]:
    m=re.search(r'(\t\tcpu@%s \{\n(?:\t\t\t[^\n]*\n)*?)(\t\t\tphandle = )'%cpu,t)
    assert m,cpu
    ins='\t\t\tqcom,freq-domain = <%s 0x%x>;\n\t\t\tclocks = <%s 0x%x>;\n'%(PH,dom,PH,dom)
    t=t[:m.start(2)]+ins+t[m.start(2):]
node='''
		cpufreq@f521000 {
			compatible = "qcom,sm6115-cpufreq-hw\0qcom,cpufreq-hw";
			reg = <0x00 0xf521000 0x00 0x1000 0x00 0xf523000 0x00 0x1000>;
			reg-names = "freq-domain0\0freq-domain1";
			clocks = <0x14 0x00 0x16 0x06>;
			clock-names = "xo\0alternate";
			#freq-domain-cells = <0x01>;
			#clock-cells = <0x01>;
			phandle = <%s>;
		};
'''%PH
i=t.index('\tsoc@0 {'); j=t.index('ranges',i); j=t.index('\n',t.index('compatible = "simple-bus";',i))+1
t=t[:j]+node+t[j:]
open(dst,'w').write(t)
print(t[t.index('cpu@100 {')-10:t.index('cpu@100 {')+420])
