import sys
src,dst=sys.argv[1],sys.argv[2]
t=open(src,encoding='latin1').read()
OUT,IN=0x21d,0x21e
for v in (OUT,IN): assert 'phandle = <0x%x>;'%v not in t
i=t.index('\tsmp2p-mpss {'); j=t.index('\t\tslave-kernel {',i)
ent='''		ipa-ap-to-modem {
			qcom,entry-name = "ipa";
			#qcom,smem-state-cells = <0x01>;
			phandle = <0x%x>;
		};

		ipa-modem-to-ap {
			qcom,entry-name = "ipa";
			interrupt-controller;
			#interrupt-cells = <0x02>;
			phandle = <0x%x>;
		};

'''%(OUT,IN)
t=t[:j]+ent+t[j:]
ipa='''
		ipa@5840000 {
			compatible = "qcom,sc7180-ipa";
			iommus = <0x21 0xe0 0x00 0x21 0xe2 0x00>;
			reg = <0x00 0x5840000 0x00 0x7000 0x00 0x5847000 0x00 0x2000 0x00 0x5804000 0x00 0x2c000>;
			reg-names = "ipa-reg\0ipa-shared\0gsi";
			interrupts-extended = <0x01 0x00 0x101 0x01 0x01 0x00 0x103 0x04 0x%(in)x 0x00 0x01 0x%(in)x 0x01 0x01>;
			interrupt-names = "ipa\0gsi\0ipa-clock-query\0ipa-setup-ready";
			clocks = <0x14 0x44>;
			clock-names = "core";
			qcom,smem-states = <0x%(out)x 0x00 0x%(out)x 0x01>;
			qcom,smem-state-names = "ipa-clock-enabled-valid\0ipa-clock-enabled";
			qcom,gsi-loader = "modem";
			status = "okay";
		};
'''%{'in':IN,'out':OUT}
i=t.index('\t\tremoteproc@6080000 {')
t=t[:i]+ipa.lstrip('\n')+'\n'+t[i:]
open(dst,'w',encoding='latin1').write(t); print('ok')
