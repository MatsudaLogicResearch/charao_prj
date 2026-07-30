#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
# This file is part of charao.
#
# Copyright (C) 2025-2026 MATSUDA Masahiro
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
###############################################################################
###############################################################################
# def get_logic_dict():
#  Returns scan-FF (SDFF) Logic definitions. Internal MUX2: next_state = (SE)? SI : D.
#  Primitives (udp_iq_ff_n / udp_iq_ff_hn) are supplied by <target>/primitives.v
#  (ISS-00172, see docs/SPEC_primitives.md).
#  User-defined Logic entries may be added via mylogic_user.py specified in ARGS.
#
# Characterization mode (Phase B, ISS-00086):
#  SE=0 (functional mode) で D->Q timing/power を計測。 SI/SE は ival で "0" 固定
#  → set_stable_inport 経由で VLOW にバインド。 expect 群は DFF_PC* pattern を継承し、
#    ival["i"] を 3 要素化 ([D値,"0","0"]) するのが基本差分。
#  vcode は orig sdff*_func 準拠 (MUX2 OR-of-3-ANDs + udp_iq_ff_n/hn + Q invert)。
#  Phase A (orig 互角化、 SE/SI 別 when 計測) は将来 ISS-00086B 候補で対応。
#
# 新方式展開 (2026-07-06、 seq_ff a23 新方式の移植):
#  - slot2(VREL) 複製廃止 (ISS-00135、 pin_oirc は同一ピンの重複指定不可)
#  - hold の ival i=r/f 化＋arc 入替 (ISS-00101)、 recovery/removal の VIN=i0(D) 駆動＋async-on-VREL
#  - const (setup/hold/recovery/removal) に代表 1 when を付与:
#    Phase B ハーネス (SE=0/SI=0、 rec/rem は D 駆動) に一致する orig entry の when
#    (例: sdffrsnq setup = "RN&!SE&SETN&!SI" ⇔ tmg_when="r0&!i2&s0&!i1"、
#     orig のアルファベット順並びに合わせて記述)。 SE/SI 全分解は ISS-00086B (A4)。
#
###############################################################################
from .myExpectCell import MyExpectCell

###############################################################################
def get_logic_dict():
  return {
    #---------------------------------------------------------------------------------------
    # SDFF_PC: D + SI + SE + posedge CLK + Q (no reset/set, single Q output).
    #   GF180 target: sdffq_1/2/4. Internal: MUX2(D, SI, SE) -> udp_iq_ff_n.
    #   Pin mapping (charao internal logic ports):
    #     o0 = Q   (output)
    #     i0 = D   (data input)
    #     i1 = SI  (scan input,  bound to VLOW via set_stable_inport in Phase B)
    #     i2 = SE  (scan enable, bound to VLOW via set_stable_inport in Phase B)
    #     c0 = CLK (clock, posedge)
    #   ports_dict example: {"D":"i0","SE":"i2","SI":"i1","CLK":"c0","Q":"o0",...}
    "SDFF_PC":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"(i2)?i1:i0",
                 "clocked_on":"c0"},
           "vcode":"reg notifier; wire d_inv; wire se_inv; wire si_inv; wire row1; wire row2; wire row3; wire mgm_d0; wire iq1; not (d_inv, i0); not (se_inv, i2); and (row1, d_inv, se_inv); not (si_inv, i1); and (row2, d_inv, si_inv); and (row3, si_inv, i2); or (mgm_d0, row1, row2, row3); udp_iq_ff_n inst (iq1, 1'b0, 1'b0, c0, mgm_d0, notifier, vdd, vss); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clk -> q) + power_tout  #ISS-00135: CLK-on-VREL 複製廃止（dffrsnq 新方式に統一）
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);", timing_default=True),
             #--- power_tin pin(CLK) when:"!D" - CLK 変化、 D=0 stable、 Q=0 stable
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D" - CLK 変化、 D=1 stable、 Q=1 stable
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK" - D 変化、 CLK=0 stable、 Q 不変
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK" - D 変化、 CLK=1 stable、 Q 不変
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0", specify=""),
             #--- setup
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="!i2&!i1", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="!i2&!i1", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["r","0","0"],"b":[],"c":["p"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","f","","r"], tmg_when="!i2&!i1", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["f","0","0"],"b":[],"c":["p"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","r","","r"], tmg_when="!i2&!i1", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- passive power (data)  -- CLK 静止 L
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="", specify=""),
             #--- passive power (clk)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             #--- min_pulse (clk)  #ISS-00135: dffrsnq 新方式（単一 entry、 when 分割は ISS-00082）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_low (clk)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["r"]}
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","r","","n"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- leakage (4 conditions: !D&!CLK / !D&CLK / D&!CLK / D&CLK)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"c":["p"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"c":["r"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"c":["p"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"c":["r"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0", specify="", power_default=True),
           ]
    },
    #---------------------------------------------------------------------------------------
    # SDFF_PC_NR: D + SI + SE + posedge CLK + active-low reset RN + Q.
    #   GF180 target: sdffrnq_1/2/4. Internal: MUX2 + udp_iq_ff_n with P=!RN.
    #   ports_dict example: {"D":"i0","RN":"r0","SE":"i2","SI":"i1","CLK":"c0","Q":"o0",...}
    "SDFF_PC_NR":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"(i2)?i1:i0",
                 "clocked_on":"c0",
                 "clear":"(!r0)"},
           "vcode":"reg notifier; wire d_inv; wire se_inv; wire si_inv; wire row1; wire row2; wire row3; wire mgm_d0; wire iq1; wire p_int; not (d_inv, i0); not (se_inv, i2); and (row1, d_inv, se_inv); not (si_inv, i1); and (row2, d_inv, si_inv); and (row3, si_inv, i2); or (mgm_d0, row1, row2, row3); not (p_int, r0); udp_iq_ff_n inst (iq1, 1'b0, p_int, c0, mgm_d0, notifier, vdd, vss); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clk -> q) -- RN=1 (non-reset) + power_tout  #ISS-00135: CLK-on-VREL 複製廃止（dffrsnq 新方式に統一）
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);", timing_default=True),
             #--- power_tin pin(CLK) when:"!D" - CLK 変化、 D=0 stable、 Q=0 stable (RN inactive)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D"
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK" - D 変化、 CLK=0 stable
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0", specify=""),
             #--- clear (RN fall -> Q fall, async)
             MyExpectCell(pin_tr=["o0","r0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","1","f","0"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- setup (D -> CLK rising edge)
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="r0&!i2&!i1", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="r0&!i2&!i1", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["r","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","f","","r"], tmg_when="r0&!i2&!i1", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["f","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","r","","r"], tmg_when="r0&!i2&!i1", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery (RN rise -> CLK rise)  #ISS-00135: rel=r0 / VIN=i0(D) 駆動（dffrsnq 方式）
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1","0","0"],"b":[],"c":["p"],"r":["0"]}
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["r","1","r","r"], tmg_when="i0&!i2&!i1", specify="$recovery(posedge r0, posedge c0, 0, notifier);"),
             #--- removal (CLK rise after RN rise, arc same as recovery)
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1","0","0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["r","1","r","r"], tmg_when="i0&!i2&!i1", specify="$removal(posedge r0, posedge c0, 0, notifier);"),
             #--- passive power (data) -- CLK static L, RN=1
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="", specify=""),
             #--- passive power (reset)
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","0"], tmg_when="", specify=""),
             #--- passive power (clk)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             #--- min_pulse (clk)  #ISS-00135: dffrsnq 新方式（単一 entry、 when 分割は ISS-00082）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_low (clk)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","r","","n"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (reset) -- RN L pulse
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","1","n","0"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- leakage (8 conditions: i0 x c0 x r0)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"c":["p"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"c":["p"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"c":["r"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"c":["r"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0","0"],"c":["p"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","0"],tmg_when="i0&!c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"c":["p"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0","0"],"c":["r"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","1"],tmg_when="i0&c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"c":["r"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&r0", specify="", power_default=True),
           ]
    },
    #---------------------------------------------------------------------------------------
    # SDFF_PC_NS: D + SI + SE + posedge CLK + active-low set SETN + Q.
    #   GF180 target: sdffsnq_1/2/4. Internal: MUX2 + udp_iq_ff_n with C=!SETN.
    #   ports_dict example: {"D":"i0","SE":"i2","SETN":"s0","SI":"i1","CLK":"c0","Q":"o0",...}
    "SDFF_PC_NS":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"(i2)?i1:i0",
                 "clocked_on":"c0",
                 "preset":"(!s0)"},
           "vcode":"reg notifier; wire d_inv; wire se_inv; wire si_inv; wire row1; wire row2; wire row3; wire mgm_d0; wire iq1; wire c_int; not (d_inv, i0); not (se_inv, i2); and (row1, d_inv, se_inv); not (si_inv, i1); and (row2, d_inv, si_inv); and (row3, si_inv, i2); or (mgm_d0, row1, row2, row3); not (c_int, s0); udp_iq_ff_n inst (iq1, c_int, 1'b0, c0, mgm_d0, notifier, vdd, vss); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clk -> q) -- SETN=1 (non-set)  #ISS-00135: CLK-on-VREL 複製廃止（dffrsnq 新方式に統一）
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"s":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"s":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);", timing_default=True),
             #--- power_tin pin(CLK) when:"!D" (SETN inactive)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D"
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0", specify=""),
             #--- preset (SETN fall -> Q rise, async)
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","0","f","0"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="!i2&s0&!i1", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="!i2&s0&!i1", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["r","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","f","","r"], tmg_when="!i2&s0&!i1", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["f","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","r","","r"], tmg_when="!i2&s0&!i1", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery (SETN rise -> CLK rise)  #ISS-00135: rel=s0 / VIN=i0(D) 駆動（dffrsnq 方式）
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0","0","0"],"b":[],"c":["p"],"s":["0"]}
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["f","0","r","r"], tmg_when="!i0&!i2&!i1", specify="$recovery(posedge s0, posedge c0, 0, notifier);"),
             #--- removal
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0","0","0"],"b":[],"c":["p"],"s":["0"]}
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["f","0","r","r"], tmg_when="!i0&!i2&!i1", specify="$removal(posedge s0, posedge c0, 0, notifier);"),
             #--- passive (data) -- CLK static L, SETN=1
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="", specify=""),
             #--- passive (set)
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"s":["0"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","r","r","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","f","0"], tmg_when="", specify=""),
             #--- passive (clk)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             #--- min_pulse (clk)  #ISS-00135: dffrsnq 新方式（単一 entry、 when 分割は ISS-00082）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_low (clk)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","r","","n"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (set)
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","0","n","0"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (8 conditions: i0 x c0 x s0)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","0","0"],"c":["p"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","0"],tmg_when="!i0&!c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"c":["p"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","0","0"],"c":["r"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","1"],tmg_when="!i0&c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"c":["r"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"c":["p"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"c":["p"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"c":["r"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"c":["r"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&s0", specify="", power_default=True),
           ]
    },
    #---------------------------------------------------------------------------------------
    # SDFF_PC_NR_NS: D + SI + SE + posedge CLK + active-low RN + active-low SETN + Q.
    #   GF180 target: sdffrsnq_1/2/4. Internal: MUX2 + udp_iq_ff_hn with C=!SETN, P=!RN.
    #   ports_dict example: {"D":"i0","RN":"r0","SE":"i2","SETN":"s0","SI":"i1","CLK":"c0","Q":"o0",...}
    "SDFF_PC_NR_NS":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"(i2)?i1:i0",
                 "clocked_on":"c0",
                 "clear":"(!r0)",
                 "preset":"(!s0)",
                 "clear_preset_var1":"L",
                 "clear_preset_var2":"H"},
           "vcode":"reg notifier; wire d_inv; wire se_inv; wire si_inv; wire row1; wire row2; wire row3; wire mgm_d0; wire iq1; wire p_int; wire c_int; not (d_inv, i0); not (se_inv, i2); and (row1, d_inv, se_inv); not (si_inv, i1); and (row2, d_inv, si_inv); and (row3, si_inv, i2); or (mgm_d0, row1, row2, row3); not (p_int, r0); not (c_int, s0); udp_iq_ff_hn inst (iq1, c_int, p_int, c0, mgm_d0, notifier, vdd, vss); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clk -> q) -- RN=1, SETN=1 + power_tout  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);", timing_default=True),
             #--- power_tin pin(CLK) when:"!D" (RN/SETN inactive)  #ISS-00101: mondrv_oirc 省略 / ISS-00127: pin_tr=[c0,""] 明示（target=CLK）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D"
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK"  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0", specify=""),
             #--- clear (RN fall)  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["o0","r0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","1","f","0"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- preset (SETN fall)  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","0","f","0"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="r0&!i2&s0&!i1", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="r0&!i2&s0&!i1", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["r","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","f","","r"], tmg_when="r0&!i2&s0&!i1", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["f","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","r","","r"], tmg_when="r0&!i2&s0&!i1", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery reset  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1","0","0"],"b":[],"c":["p"],"r":["0"],"s":["1"]}
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["r","1","r","r"], tmg_when="i0&!i2&s0&!i1", specify="$recovery(posedge r0, posedge c0, 0, notifier);"),
             #--- recovery set
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"],"s":["0"]}
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["f","0","r","r"], tmg_when="!i0&r0&!i2&!i1", specify="$recovery(posedge s0, posedge c0, 0, notifier);"),
             #--- removal reset  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1","0","0"],"b":[],"c":["p"],"r":["0"],"s":["1"]}
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["r","1","r","r"], tmg_when="i0&!i2&s0&!i1", specify="$removal(posedge r0, posedge c0, 0, notifier);"),
             #--- removal set
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"],"s":["0"]}
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["f","0","r","r"], tmg_when="!i0&r0&!i2&!i1", specify="$removal(posedge s0, posedge c0, 0, notifier);"),
             #--- passive (data) -- CLK static L, RN=1, SETN=1  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="", specify=""),
             #--- passive (reset) -- RN toggles (output static), SETN=1
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["0"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","0"], tmg_when="", specify=""),
             #--- passive (set) -- SETN toggles (output static), RN=1
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"],"s":["0"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","r","r","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","f","0"], tmg_when="", specify=""),
             #--- passive (clk) -- CLK toggles (output static)  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             #--- min_pulse (clk)  #ISS-00101: mondrv_oirc 省略、 ival[c]=p / arc[r,c]=p,p で CLK H pulse 表現 / ISS-00127: pin_tr=[c0,""]
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_low (clk)  #ISS-00101: mondrv_oirc 省略、 ival[c]=r / arc[r,c]=n,n で CLK L pulse 表現 / ISS-00127: pin_tr=[c0,""]
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","r","","n"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (reset)  #ISS-00101: mondrv_oirc 省略、 ival[c]=p（init で CLK pulse 内部状態確立）/ arc[r,c]=n,0 / ISS-00127: pin_tr=[r0,""]
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","1","n","0"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- min_pulse (set)   #ISS-00101: mondrv_oirc 省略、 ival[c]=p / arc[r,c]=n,0 / ISS-00127: pin_tr=[s0,""]
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","0","n","0"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (16: r=0[Q=L,8] / r=1&s=0[Q=H,4] / r=1&s=1[Q=i0,4])
             #     #ISS-00101: mondrv_oirc 省略、 ival[c]: c0=0→p (init pulse), c0=1→r (init rise) / arc[c]: c0=0→0, c0=1→1
             # Group 1: r=0 (reset active, Q=L)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"c":["p"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!r0&!s0&!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"c":["r"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!r0&!s0&!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0","0"],"c":["p"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","0"],tmg_when="!r0&!s0&i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0","0"],"c":["r"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","1"],tmg_when="!r0&!s0&i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"c":["p"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!r0&s0&!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"c":["r"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!r0&s0&!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0","0"],"c":["p"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","0"],tmg_when="!r0&s0&i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0","0"],"c":["r"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","1"],tmg_when="!r0&s0&i0&c0", specify=""),
             # Group 2: r=1, s=0 (set active, Q=H)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","0","0"],"c":["p"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","0"],tmg_when="r0&!s0&!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","0","0"],"c":["r"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","1"],tmg_when="r0&!s0&!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"c":["p"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="r0&!s0&i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"c":["r"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="r0&!s0&i0&c0", specify=""),
             # Group 3: r=1, s=1 (hold, Q=i0)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="r0&s0&!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0","0"],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="r0&s0&!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="r0&s0&i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0","0"],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="r0&s0&i0&c0", specify="", power_default=True),
           ]
    },
  }
