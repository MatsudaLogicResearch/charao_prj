// Copyright 2022 GlobalFoundries PDK Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// ---------------------------------------------------------------------------
// NOTICE OF MODIFICATION (Apache License 2.0, Section 4(b))
//
// This file has been modified for the charao project (2026) by
// MATSUDA Masahiro / Logic Research Co., Ltd.
//
//   Source : open_pdks gf180mcu
//            (0fe599b2afb6708d281543108caf8310912f54af)
//            libs.ref/gf180mcu_fd_sc_mcu7t5v0/verilog/primitives.v
//
//   Change : the four primitives were renamed to the charao naming convention.
//            gf180mcu_fd_sc_mcu7t5v0__udp_hn_iq_ff    -> udp_iq_ff_hn
//            gf180mcu_fd_sc_mcu7t5v0__udp_hn_iq_latch -> udp_iq_latch_hn
//            gf180mcu_fd_sc_mcu7t5v0__udp_n_iq_ff     -> udp_iq_ff_n
//            gf180mcu_fd_sc_mcu7t5v0__udp_n_iq_latch  -> udp_iq_latch_n
//
//   No other change: the UDP tables, the pin order (Q, C, P, CK, D, N) and the
//   include guards are identical to the original.
//
// This file remains licensed under the Apache License, Version 2.0.
// A copy of the License is provided at sample_target/gf180/LICENSE-Apache-2.0.txt
// ---------------------------------------------------------------------------

`ifndef GF180MCU_FD_SC_MCU7T5V0__UDP_HN_IQ_FF_V
`define GF180MCU_FD_SC_MCU7T5V0__UDP_HN_IQ_FF_V

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

`endif // GF180MCU_FD_SC_MCU7T5V0__UDP_HN_IQ_FF_V


//--------EOF---------

// Copyright 2022 GlobalFoundries PDK Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

`ifndef GF180MCU_FD_SC_MCU7T5V0__UDP_HN_IQ_LATCH_V
`define GF180MCU_FD_SC_MCU7T5V0__UDP_HN_IQ_LATCH_V

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

`endif // GF180MCU_FD_SC_MCU7T5V0__UDP_HN_IQ_LATCH_V


//--------EOF---------

// Copyright 2022 GlobalFoundries PDK Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

`ifndef GF180MCU_FD_SC_MCU7T5V0__UDP_N_IQ_FF_V
`define GF180MCU_FD_SC_MCU7T5V0__UDP_N_IQ_FF_V

primitive udp_iq_ff_n ( Q, C, P, CK, D, N, VPWR, VGND );
output Q;
reg Q;
input C, P, CK, D, N, VPWR, VGND;
table
// C  P  CK  D  N  VPWR VGND :  Q  :  Q
   0  0  n   ?  ?  1    0   :  ?  :  -;
   ?  0  r   0  ?  1    0   :  ?  :  0;
   ?  0  p   0  ?  1    0   :  0  :  0;
   1  0  ?   ?  ?  1    0   :  ?  :  0;
   0  ?  r   1  ?  1    0   :  ?  :  1;
   0  ?  p   1  ?  1    0   :  1  :  1;
   0  1  ?   ?  ?  1    0   :  ?  :  1;
   ?  ?  ?   ?  *  1    0   :  ?  :  x;
   0  0  ?   *  ?  1    0   :  ?  :  -;
   0  n  ?   ?  ?  1    0   :  ?  :  -;
   n  0  ?   ?  ?  1    0   :  ?  :  -;
   0  p  ?   ?  ?  1    0   :  ?  :  -;

//--- 電源が変化したら Q は不定（パワーカット時の x 伝播）
   ?  ?  ?  ?  ?  *  ?  :  ?  :  x;
   ?  ?  ?  ?  ?  ?  *  :  ?  :  x;
endtable
endprimitive

`endif // GF180MCU_FD_SC_MCU7T5V0__UDP_N_IQ_FF_V


//--------EOF---------

// Copyright 2022 GlobalFoundries PDK Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

`ifndef GF180MCU_FD_SC_MCU7T5V0__UDP_N_IQ_LATCH_V
`define GF180MCU_FD_SC_MCU7T5V0__UDP_N_IQ_LATCH_V

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

`endif // GF180MCU_FD_SC_MCU7T5V0__UDP_N_IQ_LATCH_V


//--------EOF---------

