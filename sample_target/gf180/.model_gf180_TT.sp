**===================================================================
** This file is associated with the charao project.
** Copyright (C) 2025 MATSUDA Masahiro
**
** This configuration file is licensed under the MIT License.
**===================================================================
** GF180MCU PDK (gf180mcuC) - TT corner
** Source: volare 0fe599b2afb6708d281543108caf8310912f54af (2024.08.17)

** ISS-00184: charao は .lib <file> <section> でこのファイルを読む。
**   セクション名は config_lib.jsonc の model_section（既定 ["mos"]）で指定する。
**   セル個別に変えたい場合は cell_info の "model_section" が優先される。
**   gf180 は分割の必要が無い（モデル全体で .param 164 個 / 8,229 行、 読込 0.024 秒）
**   ため 1 セクションにまとめる。 分割の機構は 2026-07-31 に mos / rc の 2 分割で
**   動作確認済み（inv_1=["mos"] / nand2_1=["mos","rc"] とも参照値と完全一致）。
.lib mos
.inc '../../../../sample_src/gf180mcuC/libs.tech/ngspice/design.ngspice'
.lib '../../../../sample_src/gf180mcuC/libs.tech/ngspice/sm141064.ngspice' typical
.lib '../../../../sample_src/gf180mcuC/libs.tech/ngspice/sm141064.ngspice' diode_typical
.endl mos
