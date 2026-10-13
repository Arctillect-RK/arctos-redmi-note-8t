import re
import sys

src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='latin1').read()

PH = {'l8': 0x210, 'l16': 0x211, 'l17': 0x212, 'l23': 0x213,
      'modem_mem': 0x214, 'wlan_msa': 0x215, 'smp2p_out': 0x216, 'smp2p_in': 0x217,
      'rmtfs': 0x218}
for v in PH.values():
    assert 'phandle = <0x%x>;' % v not in t


def add_phandle_to_regulator(name, ph):
    global t
    m = re.search(r'(\n\t{5}%s \{\n(?:\t{6}[^\n]*\n)*?)(\t{5}\};)' % name, t)
    assert m, name
    t = t[:m.end(1)] + '\t\t\t\t\t\tphandle = <0x%x>;\n' % ph + t[m.end(1):]


for r in ('l8', 'l16', 'l17', 'l23'):
    add_phandle_to_regulator(r, PH[r])

# modem PIL region: add phandle
old = '\t\tmemory@4b000000 {\n\t\t\treg = <0x00 0x4b000000 0x00 0x7e00000>;\n\t\t\tno-map;\n'
assert t.count(old) == 1
t = t.replace(old, old + '\t\t\tphandle = <0x%x>;\n' % PH['modem_mem'])

# WLAN MSA: downstream icnss uses 1 MB (the second MB is a guard); 2 MB crashes the FW
old = '\t\tmemory@53300000 {\n\t\t\treg = <0x00 0x53300000 0x00 0x200000>;\n\t\t\tno-map;\n'
assert t.count(old) == 1
t = t.replace(old, '\t\tmemory@53300000 {\n\t\t\treg = <0x00 0x53300000 0x00 0x100000>;\n\t\t\tno-map;\n'
              '\t\t\tphandle = <0x%x>;\n' % PH['wlan_msa'])

# rmtfs shared memory (modemst1/2 are served from here by the rmtfs daemon)
i = t.index('\treserved-memory {')
j = t.index('\n\t};', i)
rmtfs = '''
		rmtfs@89b01000 {
			compatible = "qcom,rmtfs-mem";
			reg = <0x00 0x89b01000 0x00 0x200000>;
			no-map;
			qcom,client-id = <0x01>;
			qcom,vmid = <0x0f>;
			phandle = <0x%x>;
		};
''' % PH['rmtfs']
t = t[:j] + rmtfs + t[j:]

# smp2p to the modem (downstream trinket.dtsi qcom,smp2p-modem)
smp2p = '''
	smp2p-mpss {
		compatible = "qcom,smp2p";
		qcom,smem = <0x1b3 0x1ac>;
		interrupts = <0x00 0x46 0x01>;
		mboxes = <0x0e 0x0e>;
		qcom,local-pid = <0x00>;
		qcom,remote-pid = <0x01>;

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
''' % (PH['smp2p_out'], PH['smp2p_in'])
i = t.index('\tsmem {')
t = t[:i] + smp2p.lstrip('\n') + '\n' + t[i:]

# MPSS remoteproc + WCN3990 inside soc@0
soc_nodes = '''
		remoteproc@6080000 {
			compatible = "qcom,sm6115-mpss-pas";
			reg = <0x00 0x6080000 0x00 0x10000>;
			interrupts-extended = <0x01 0x00 0x133 0x01 0x%(in)x 0x00 0x01 0x%(in)x 0x01 0x01 0x%(in)x 0x02 0x01 0x%(in)x 0x03 0x01 0x%(in)x 0x07 0x01>;
			interrupt-names = "wdog\\0fatal\\0ready\\0handover\\0stop-ack\\0shutdown-ack";
			clocks = <0x14 0x00>;
			clock-names = "xo";
			power-domains = <0x22 0x00>;
			memory-region = <0x%(mm)x>;
			qcom,smem-states = <0x%(out)x 0x00>;
			qcom,smem-state-names = "stop";
			firmware-name = "qcom/sm6125/xiaomi/willow/modem.mdt";
			status = "okay";

			glink-edge {
				interrupts = <0x00 0x44 0x01>;
				label = "mpss";
				qcom,remote-pid = <0x01>;
				mboxes = <0x0e 0x0c>;
			};
		};

		wifi@c800000 {
			compatible = "qcom,wcn3990-wifi";
			reg = <0x00 0xc800000 0x00 0x800000>;
			reg-names = "membase";
			memory-region = <0x%(msa)x>;
			interrupts = <0x00 0x166 0x04 0x00 0x167 0x04 0x00 0x168 0x04 0x00 0x169 0x04 0x00 0x16a 0x04 0x00 0x16b 0x04 0x00 0x16c 0x04 0x00 0x16d 0x04 0x00 0x16e 0x04 0x00 0x16f 0x04 0x00 0x170 0x04 0x00 0x171 0x04>;
			iommus = <0x21 0x80 0x01>;
			vdd-0.8-cx-mx-supply = <0x%(l8)x>;
			vdd-1.8-xo-supply = <0x%(l16)x>;
			vdd-1.3-rfa-supply = <0x%(l17)x>;
			vdd-3.3-ch0-supply = <0x%(l23)x>;
			vdd-3.3-ch1-supply = <0x%(l23)x>;
			qcom,calibration-variant = "Xiaomi_willow";
			status = "okay";
		};
''' % {'in': PH['smp2p_in'], 'out': PH['smp2p_out'], 'mm': PH['modem_mem'], 'msa': PH['wlan_msa'],
       'l8': PH['l8'], 'l16': PH['l16'], 'l17': PH['l17'], 'l23': PH['l23']}
i = t.index('\tsoc@0 {')
k = t.index('compatible = "simple-bus";', i)
k = t.index('\n', k) + 1
t = t[:k] + soc_nodes + t[k:]

open(dst, 'w', encoding='latin1').write(t)
print('ok')
