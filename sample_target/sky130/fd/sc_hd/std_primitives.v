//===========================================================================
// This file is part of charao.
//
// Copyright (C) 2026 MATSUDA Masahiro / Logic Research Co., Ltd.
//
// This file is licensed under the MIT License.
//===========================================================================
// Verilog primitives for the SKY130 target (sky130_fd_sc_hd).
//
// charao の生成する .v は、 下の 4 つを固定端子 (Q, C, P, CK, D, N) で
// インスタンス化する。 契約は docs/SPEC_primitives.md を参照。
//
//   udp_iq_ff_n     : posedge FF    / C と P の同時アサートは未定義 (x)
//   udp_iq_ff_hn    : posedge FF    / 同時アサートは P が勝つ
//   udp_iq_latch_n  : level latch   / C と P の同時アサートは未定義 (x)
//   udp_iq_latch_hn : level latch   / 同時アサートは P が勝つ
//
//   C  : clear  (active High)
//   P  : preset (active High)
//   CK : FF はクロック(posedge) / LATCH は enable(active High)
//   D  : データ
//   N  : notifier (タイミングチェック違反で Q を x にする)
//
// 【重要】 優先度は「表」ではなく「配線」で作る (docs/SPEC_primitives.md §5)
//   実セルがリセット優先でも、 新しい UDP は不要。 優先させたい信号を P へ渡し、
//   出力を IQ1 で受けてその反転を Q に出せばよい。 SKY130 の DFF 系セルは
//   ISS-00181 で tools/gen_udp.py により実測して確認する（未実施なら要検証）。
//   表の内容は gf180 / OSU035 と同一（FF/latch の真理値表は回路構成によらず一意）。
//
//
// 本ファイルは charao 契約に合わせて新規記述したものであり、
// 特定 PDK のコードを複製していない。
//===========================================================================

primitive udp_iq_ff_n ( Q, C, P, CK, D, N, VPWR, VGND );
output Q;
reg Q;
input C, P, CK, D, N, VPWR, VGND;
table
// C  P  CK D  N  VPWR VGND :  Q  :  Q
   0  0  n  ?  ?  1    0   :  ?  :  -;
   ?  0  r  0  ?  1    0   :  ?  :  0;
   ?  0  p  0  ?  1    0   :  0  :  0;
   1  0  ?  ?  ?  1    0   :  ?  :  0;
   0  ?  r  1  ?  1    0   :  ?  :  1;
   0  ?  p  1  ?  1    0   :  1  :  1;
   0  1  ?  ?  ?  1    0   :  ?  :  1;
   ?  ?  ?  ?  *  1    0   :  ?  :  x;
   0  0  ?  *  ?  1    0   :  ?  :  -;
   0  n  ?  ?  ?  1    0   :  ?  :  -;
   n  0  ?  ?  ?  1    0   :  ?  :  -;
   0  p  ?  ?  ?  1    0   :  ?  :  -;
//--- 電源が変化したら Q は不定（パワーカット時の x 伝播）
   ?  ?  ?  ?  ?  *  ?  :  ?  :  x;
   ?  ?  ?  ?  ?  ?  *  :  ?  :  x;
endtable
endprimitive

primitive udp_iq_ff_hn ( Q, C, P, CK, D, N, VPWR, VGND );
output Q;
reg Q;
input C, P, CK, D, N, VPWR, VGND;
table
// C  P  CK D  N  VPWR VGND :  Q  :  Q
   0  0  n  ?  ?  1    0   :  ?  :  -;
   ?  0  r  0  ?  1    0   :  ?  :  0;
   ?  0  p  0  ?  1    0   :  0  :  0;
   1  0  ?  ?  ?  1    0   :  ?  :  0;
   0  ?  r  1  ?  1    0   :  ?  :  1;
   0  ?  p  1  ?  1    0   :  1  :  1;
   ?  1  ?  ?  ?  1    0   :  ?  :  1;
   0  0  ?  *  ?  1    0   :  ?  :  -;
   ?  ?  ?  ?  *  1    0   :  ?  :  x;
   0  n  ?  ?  ?  1    0   :  ?  :  -;
   n  0  ?  ?  ?  1    0   :  ?  :  -;
   0  p  ?  ?  ?  1    0   :  ?  :  -;
//--- 電源が変化したら Q は不定（パワーカット時の x 伝播）
   ?  ?  ?  ?  ?  *  ?  :  ?  :  x;
   ?  ?  ?  ?  ?  ?  *  :  ?  :  x;
endtable
endprimitive

primitive udp_iq_latch_n ( Q, C, P, CK, D, N, VPWR, VGND );
output Q;
reg Q;
input C, P, CK, D, N, VPWR, VGND;
table
// C    P    CK   D    N  VPWR VGND :  Q  :  Q
   0    0    0    *    ?  1    0   :  ?  :  -;
   0    0    (?0) ?    ?  1    0   :  ?  :  -;
   0    (?0) 0    ?    ?  1    0   :  ?  :  -;
   (?0) 0    0    ?    ?  1    0   :  ?  :  -;
   ?    0    1    0    ?  1    0   :  ?  :  0;
   ?    0    ?    (?0) ?  1    0   :  0  :  0;
   ?    (?0) ?    0    ?  1    0   :  0  :  0;
   1    0    ?    ?    ?  1    0   :  ?  :  0;
   0    ?    1    1    ?  1    0   :  ?  :  1;
   0    ?    ?    (?1) ?  1    0   :  1  :  1;
   (?0) ?    ?    1    ?  1    0   :  1  :  1;
   0    1    ?    ?    ?  1    0   :  ?  :  1;
   ?    ?    ?    ?    *  1    0   :  ?  :  x;
//--- 電源が変化したら Q は不定（パワーカット時の x 伝播）
   ?  ?  ?  ?  ?  *  ?  :  ?  :  x;
   ?  ?  ?  ?  ?  ?  *  :  ?  :  x;
endtable
endprimitive

primitive udp_iq_latch_hn ( Q, C, P, CK, D, N, VPWR, VGND );
output Q;
reg Q;
input C, P, CK, D, N, VPWR, VGND;
table
// C    P    CK   D    N  VPWR VGND :  Q  :  Q
   0    0    0    *    ?  1    0   :  ?  :  -;
   0    0    (?0) ?    ?  1    0   :  ?  :  -;
   0    (?0) 0    ?    ?  1    0   :  ?  :  -;
   (?0) 0    0    ?    ?  1    0   :  ?  :  -;
   ?    0    1    0    ?  1    0   :  ?  :  0;
   ?    0    ?    (?0) ?  1    0   :  0  :  0;
   ?    (?0) ?    0    ?  1    0   :  0  :  0;
   1    0    ?    ?    ?  1    0   :  ?  :  0;
   0    ?    1    1    ?  1    0   :  ?  :  1;
   0    ?    ?    (?1) ?  1    0   :  1  :  1;
   (?0) ?    ?    1    ?  1    0   :  1  :  1;
   ?    1    ?    ?    ?  1    0   :  ?  :  1;
   ?    ?    ?    ?    *  1    0   :  ?  :  x;
//--- 電源が変化したら Q は不定（パワーカット時の x 伝播）
   ?  ?  ?  ?  ?  *  ?  :  ?  :  x;
   ?  ?  ?  ?  ?  ?  *  :  ?  :  x;
endtable
endprimitive
