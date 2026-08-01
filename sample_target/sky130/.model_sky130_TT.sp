**===================================================================
** This file is associated with the charao project.
** Copyright (C) 2026 MATSUDA Masahiro
**
** This configuration file is licensed under the MIT License.
**===================================================================
** SkyWater SKY130 PDK (sky130A) - TT corner
** Source: ciel (旧 volare) f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7
**
** 【ISS-00184】 sky130.lib.spice の .lib tt を丸ごと読むと 1 sim あたり 28 秒を
**   モデル読込に費やす（.model 1,019 個 / .param 14,071 個 / 265,330 行 / 6.79MB）。
**   過渡解析そのものは 0.0075 秒なので、 99.97% が読込オーバーヘッドだった。
**
**   sc_hd の netlist を全 grep した結果、 実際に使うデバイスは以下だけ：
**     nfet_01v8(3973) / pfet_01v8_hvt(4165) / special_nfet_01v8(209) / special_pfet_01v8_hvt(2)
**     res_generic_po(2) / diode_pw2nd_05v5(1)  ← decap / fill / tap のみ
**   pfet_01v8・lvt・g5v0・esd・rf・npn/pnp・cap_vpp・sonos は 1 個も使っていない。
**   → 必要な 4 ファイルだけを直接 include する（.param は 14,071 → 74 個）。
**   実測: 1 sim あたり 28.044 秒 → 0.098 秒（286 倍）。 .lib の値は完全一致。
**
**   r+c は .param を 8,909 個（配線寄生容量 mcp1f_*）引き込むため rc セクションに分離した。
**   decap / fill / tap だけが cell_info で "model_section":["mos","rc"] を指定する。
**
** 【重要】 charao は .lib <file> <section> でこのファイルを読む（ISS-00184）。
**   .inc で読むと **非選択セクションも素通しで読まれる**（スキップされるのは
**   .lib <file> <section> で入ったときだけ）ため、 subckt が二重定義されて
**   parse error になる。 実測確認済み。
**
** PATH は sim の CWD（work/<cell>/<meas>/<arc>/）からの相対。 charao が
** モデル内の PATH を絶対化しないため 4 階層戻す（gf180 の .model_gf180_TT.sp と同じ規約）。

** ==================================================================
** mos : 論理セル用（sc_hd が使う 2 デバイスのみ）
** ==================================================================
.lib mos
** --- all.spice が設定していた scale。 直接 include に切り替えたので明示する ---
**     sky130 の cell netlist は w=650000u のような値で書かれており必須。
.option scale=1.0u

** --- sky130.lib.spice の .lib tt が設定していた MC スイッチ（0 = 非モンテカルロ）---
**     mismatch.corner.spice が参照するため必要。
.param mc_mm_switch=0
.param mc_pr_switch=0

** --- sc_hd が使う 2 デバイス（special_* も同じファイル内で定義される）---
.include "../../../../sample_src/sky130A/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8__tt.pm3.spice"
.include "../../../../sample_src/sky130A/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8__mismatch.corner.spice"
.include "../../../../sample_src/sky130A/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__pfet_01v8_hvt__tt.pm3.spice"
.include "../../../../sample_src/sky130A/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__pfet_01v8_hvt__mismatch.corner.spice"
.endl mos

** ==================================================================
** rc : decap / fill / tap 用（res_generic_po / diode_pw2nd_05v5）
**      mos に追加して読む（"model_section":["mos","rc"]）。
** ==================================================================
.lib rc
.include "../../../../sample_src/sky130A/libs.tech/ngspice/r+c/res_typical__cap_typical.spice"
.include "../../../../sample_src/sky130A/libs.tech/ngspice/r+c/res_typical__cap_typical__lin.spice"
.endl rc
