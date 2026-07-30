**===================================================================
** This file is associated with the charao project.
** Copyright (C) 2025 MATSUDA Masahiro
** 
** This configuration file is licensed under the MIT License.
**===================================================================

** PATH は sim の CWD（work/<cell>/<meas>/<arc>/）からの相対。 model 内の .inc は
** charao が絶対パス化しないため 4 階層戻す（gf180 の .model_gf180_TT.sp と同じ規約）
.inc '../../../../sample_src/OSU035/SS/nmos.sp'
.inc '../../../../sample_src/OSU035/SS/pmos.sp'

* .TEMP 125

