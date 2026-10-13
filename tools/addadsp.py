import re
import sys

src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='latin1').read()

PH = {'adsp_mem': 0x21a, 'out': 0x21b, 'in': 0x21c}
for v in PH.values():
    assert 'phandle = <0x%x>;' % v not in t

old = '\t\tadsp-pil-mem@55300000 {\n\t\t\treg = <0x00 0x55300000 0x00 0x2200000>;\n\t\t\tno-map;\n'
assert t.count(old) == 1
t = t.replace(old, old + '\t\t\tphandle = <0x%x>;\n' % PH['adsp_mem'])

# smp2p to the ADSP (downstream trinket.dtsi qcom,smp2p-adsp)
smp2p = '''
	smp2p-adsp {
		compatible = "qcom,smp2p";
		qcom,smem = <0x1bb 0x1ad>;
		interrupts = <0x00 0x189 0x01>;
		mboxes = <0x0e 0x0a>;
		qcom,local-pid = <0x00>;
		qcom,remote-pid = <0x02>;

		master-kernel {
			qcom,entry-name = "master-kernel";
			#qcom,smem-state-cells = <0x01>;
			phandle = <0x%x>;
		};

		slave-kernel {
			qcom,entry-name = "slave-kernel";
			interrupt-controller;
			#interrupt-cells = <0x02>;
			phandle = <0x%x>;
		};
	};
''' % (PH['out'], PH['in'])
i = t.index('\tsmp2p-mpss {')
t = t[:i] + smp2p.lstrip('\n') + '\n' + t[i:]

adsp = '''
		remoteproc@ab00000 {
			compatible = "qcom,sm6115-adsp-pas";
			reg = <0x00 0xab00000 0x00 0x100>;
			interrupts-extended = <0x01 0x00 0x18c 0x01 0x%(in)x 0x00 0x01 0x%(in)x 0x01 0x01 0x%(in)x 0x02 0x01 0x%(in)x 0x03 0x01>;
			interrupt-names = "wdog\\0fatal\\0ready\\0handover\\0stop-ack";
			clocks = <0x14 0x00>;
			clock-names = "xo";
			power-domains = <0x22 0x00>;
			memory-region = <0x%(mem)x>;
			qcom,smem-states = <0x%(out)x 0x00>;
			qcom,smem-state-names = "stop";
			firmware-name = "qcom/sm6125/xiaomi/willow/adsp.mdt";
			status = "okay";

			glink-edge {
				interrupts = <0x00 0x187 0x01>;
				label = "lpass";
				qcom,remote-pid = <0x02>;
				mboxes = <0x0e 0x08>;

				fastrpc {
					compatible = "qcom,fastrpc";
					qcom,glink-channels = "fastrpcglink-apps-dsp";
					label = "adsp";
					qcom,non-secure-domain;
					#address-cells = <0x01>;
					#size-cells = <0x00>;

					compute-cb@3 {
						compatible = "qcom,fastrpc-compute-cb";
						reg = <0x03>;
						iommus = <0x21 0x43 0x00>;
					};

					compute-cb@4 {
						compatible = "qcom,fastrpc-compute-cb";
						reg = <0x04>;
						iommus = <0x21 0x44 0x00>;
					};
				};
			};
		};
''' % {'in': PH['in'], 'out': PH['out'], 'mem': PH['adsp_mem']}
i = t.index('\t\tremoteproc@6080000 {')
t = t[:i] + adsp.lstrip('\n') + '\n' + t[i:]

open(dst, 'w', encoding='latin1').write(t)
print('ok')
