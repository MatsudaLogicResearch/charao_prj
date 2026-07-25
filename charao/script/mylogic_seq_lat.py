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
#  Returns level-sensitive latch (LATCH) Logic definitions.
#  logic_type:"seq_lat" で myLogicCell.add_latch() が呼ばれる (charao.py 分岐)。
#  Liberty 出力は ff block ではなく latch block (myExportLib.py で islatch 分岐)。
#  Primitives (udp_iq_latch_n / udp_iq_latch_hn) は mylogic_seq_ff.py から共有。
#
# def get_code_primitive():
#  Returns empty string (no LATCH-specific primitives, see mylogic_seq_ff.py).
#
# Characterization (Phase B0+B1, ISS-00070 LAT):
#  rising_edge   : E rise → Q transition (DFF_PC 同型 harness)
#  combinational : D → Q while E=1 (LAT 固有 transparent path)
#  setup_falling : D vs E fall edge (latch closure 直前の D 安定)
#  hold_falling  : D vs E fall edge (latch closure 直後の D 静止)
#  recovery_falling / removal_falling : RN/SETN release vs E fall
#  min_pulse_width_high (E)   : E H pulse 最小幅
#  min_pulse_width_low (RN/SETN) : RN/SETN L pulse 最小幅
#  ※ min_pulse_width_low (E) は orig latq lib に無いため計測しない
#  ※ non_seq_setup/hold_rising (RN vs SETN, latrsnq 固有) は Phase A 範囲で別途
#
###############################################################################
from .myExpectCell import MyExpectCell

###############################################################################
def get_logic_dict():
  return {
    #---------------------------------------------------------------------------------------
    # LATCH_PE: D + pos-level Enable E + Q (no reset/set).
    #   GF180 target: latq_1/2/4. Internal: not + udp_iq_latch_n + not (IQ1 polarity = !D).
    #   Pin mapping: o0=Q, i0=D, c0=E (pos-level enable)
    #   ports_dict example: {"D":"i0","E":"c0","Q":"o0",...}
    "LATCH_PE":{
           "logic_type":"seq_lat",
           "functions":{"o0":"Io0"},
           "latch":{"out":"Io0,IQB",
                    "enable":"c0",
                    "data_in":"(!i0)"},
           "vcode":"reg notifier; wire mgm_d0; wire iq1; not (mgm_d0, i0); udp_iq_latch_n inst (iq1, 1'b0, 1'b0, c0, mgm_d0, notifier); not (o0, iq1);",
           "expect":
           [
             #--- rising_edge (E rise -> Q) + power_tout
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- combinational (D -> Q while E=1, transparent latch) - charao auto: islatch + clk_role="nouse" → clk_init="stable"
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["r","","r","1"], tmg_when="", specify="(i0 => o0) = (0,0);"),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"]}
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["f","","f","1"], tmg_when="", specify=""),
             #--- power_tin pin(E) when:"!D"
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(E) when:"D"
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!E"（orig latq は !E のみ。 E=1 は D 透過中で出力変化のため power_tin 非対象、 ISS-00100 D0）
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","f","","0"], tmg_when="!c0", specify=""),
             #--- setup_falling (D vs E fall edge)
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold_falling
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["1","f","","f"], tmg_when="", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["0","r","","f"], tmg_when="", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- passive (data)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="", specify=""),
             #--- passive (E)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             #--- min_pulse_width_high (E) -- H pulse 計測。D 2 分割（when:!D/D）。!D 側は t_init で D=1→Q=1 を作り t_in で D=0
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["f","f","","p"], tmg_when="!i0", specify="$width(posedge c0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="i0", specify="$width(posedge c0, 0, 0, notifier);"),
             # min_pulse_width_low (E) は orig latq lib に無いため削除
             #--- leakage (4 conditions: !D&!E / !D&E / D&!E / D&E)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d","u"],"i":["0"],"c":["p"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d","u"],"i":["0"],"c":["r"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["u","d"],"i":["1"],"c":["p"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["u","d"],"i":["1"],"c":["r"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0", specify="", power_default=True),
           ]
    },
    #---------------------------------------------------------------------------------------
    # LATCH_PE_NR: D + pos-level Enable E + active-low reset RN + Q.
    #   GF180 target: latrnq_1/2/4. Internal: not + udp_iq_latch_n + buf (IQ2 polarity = D, C=!RN).
    "LATCH_PE_NR":{
           "logic_type":"seq_lat",
           "functions":{"o0":"Io0"},
           "latch":{"out":"Io0,IQB",
                    "enable":"c0",
                    "data_in":"i0",
                    "clear":"(!r0)"},
           "vcode":"reg notifier; wire c_int; wire iq2; not (c_int, r0); udp_iq_latch_n inst (iq2, c_int, 1'b0, c0, i0, notifier); buf (o0, iq2);",
           "expect":
           [
             #--- rising_edge (E rise -> Q) -- RN=1
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- combinational (D -> Q while E=1) - charao auto: islatch + clk_role="nouse" → clk_init="stable"
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"]}
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["r","","r","1"], tmg_when="", specify="(i0 => o0) = (0,0);"),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"]}
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["f","","f","1"], tmg_when="", specify=""),
             #--- power_tin pin(E) -- D x RN の 4 when（orig latrnq: !D&!RN / !D&RN / D&!RN / D&RN）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0&!r0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"r":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0&!r0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0&r0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0&r0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","1","","r"], tmg_when="i0&!r0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["r"],"r":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","1","","f"], tmg_when="i0&!r0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0&r0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0&r0", specify=""),
             #--- power_tin pin(D) -- E x RN の 3 when（orig latrnq: !E&!RN / !E&RN / E&!RN。E&RN は D 透過で出力変化のため除外）
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d"],"i":["0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0&!r0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","f","","0"], tmg_when="!c0&!r0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0&r0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","f","","0"], tmg_when="!c0&r0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d"],"i":["0"],"b":[],"c":["r"],"r":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0&!r0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d"],"i":["1"],"b":[],"c":["r"],"r":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","f","","1"], tmg_when="c0&!r0", specify=""),
             #--- power_tin pin(RN) -- D x E の 3 when（orig latrnq: !D&!E / !D&E / D&!E。D&E は RN で出力変化のため除外）
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","r","0"], tmg_when="!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","f","0"], tmg_when="!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"r":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","r","1"], tmg_when="!i0&c0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","f","1"], tmg_when="!i0&c0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","1","r","0"], tmg_when="i0&!c0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","1","f","0"], tmg_when="i0&!c0", specify=""),
             #--- clear (RN fall -> Q fall) -- D x E の 3 when + ifnone(timing_default)。orig latrnq: !D&!E / D&!E / D&E + ifnone
             #     全 entry ival[i]=1（t_init で D=1 を取り込み内部状態 IQ2=1→Q=1 を作る）。 mondrv_oirc[1] が t_in(=when) の D 値
             MyExpectCell(pin_tr=["o0","r0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","f","f","0"], tmg_when="!i0&!c0", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             MyExpectCell(pin_tr=["o0","r0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","1","f","0"], tmg_when="i0&!c0", timing_default=True, specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);;"),
             MyExpectCell(pin_tr=["o0","r0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","1","f","1"], tmg_when="i0&c0", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- setup_falling -- when:RN（RN inactive 前提、 orig latrnq）
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="r0", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="r0", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold_falling -- when:RN
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["0","r","","f"], tmg_when="r0", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["1","f","","f"], tmg_when="r0", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- recovery_falling (RN rise -> E fall)
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["1"],"r":["0"]}
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["r","1","r","f"], tmg_when="", specify="$recovery(posedge r0, negedge c0, 0, notifier);"),
             #--- removal_falling
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["1"],"r":["0"]}
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["r","1","r","f"], tmg_when="", specify="$removal(posedge r0, negedge c0, 0, notifier);"),
             #--- passive (data)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="", specify=""),
             #--- passive (reset)
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","0"], tmg_when="", specify=""),
             #--- passive (E)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             #--- min_pulse_width_high (E) -- D 2 分割（when:!D&RN/D&RN）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["f","f","","p"], tmg_when="!i0&r0", specify="$width(posedge c0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="i0&r0", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_width_low (RN)  -- RN L pulse。D 2 分割（when:!D&!E/D&!E）
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","f","n","0"], tmg_when="!i0&!c0", specify="$width(negedge r0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","1","n","0"], tmg_when="i0&!c0", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- leakage (8 conditions: i0 x c0 x r0)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d","u"],"i":["0"],"c":["p"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d","u"],"i":["0"],"c":["r"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","0"],tmg_when="i0&!c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["u","d"],"i":["1"],"c":["p"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","1"],tmg_when="i0&c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["u","d"],"i":["1"],"c":["r"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&r0", specify="", power_default=True),
           ]
    },
    #---------------------------------------------------------------------------------------
    # LATCH_PE_NS: D + pos-level Enable E + active-low set SETN + Q.
    #   GF180 target: latsnq_1/2/4. Internal: not + udp_iq_latch_n + buf (IQ2 polarity = D, P=!SETN).
    "LATCH_PE_NS":{
           "logic_type":"seq_lat",
           "functions":{"o0":"Io0"},
           "latch":{"out":"Io0,IQB",
                    "enable":"c0",
                    "data_in":"i0",
                    "preset":"(!s0)"},
           "vcode":"reg notifier; wire p_int; wire iq2; not (p_int, s0); udp_iq_latch_n inst (iq2, 1'b0, p_int, c0, i0, notifier); buf (o0, iq2);",
           "expect":
           [
             #--- rising_edge -- SETN=1
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"s":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"s":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- combinational (D -> Q while E=1) - charao auto: islatch + clk_role="nouse" → clk_init="stable"
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["r","","r","1"], tmg_when="", specify="(i0 => o0) = (0,0);"),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["1"]}
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["f","","f","1"], tmg_when="", specify=""),
             #--- power_tin pin(E) -- D x SETN の 4 when（orig latsnq: !D&!SETN / !D&SETN / D&!SETN / D&SETN）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["f"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","","r"], tmg_when="!i0&!s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","","f"], tmg_when="!i0&!s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0&s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0&s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0&!s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0&!s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0&s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0&s0", specify=""),
             #--- power_tin pin(D) -- E x SETN の 3 when（orig latsnq: !E&!SETN / !E&SETN / E&!SETN。E&SETN は D 透過で除外）
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","r","","0"], tmg_when="!c0&!s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0&!s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0&s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","f","","0"], tmg_when="!c0&s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","r","","1"], tmg_when="c0&!s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0&!s0", specify=""),
             #--- power_tin pin(SETN) -- D x E の 3 when（orig latsnq: !D&!E / D&!E / D&E。!D&E は SETN で出力変化のため除外）
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","r","0"], tmg_when="!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","f","0"], tmg_when="!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","r","0"], tmg_when="i0&!c0", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","f","0"], tmg_when="i0&!c0", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","r","1"], tmg_when="i0&c0", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","f","1"], tmg_when="i0&c0", specify=""),
             #--- preset (SETN fall -> Q rise) -- D x E の 3 when + ifnone(timing_default)。orig latsnq: !D&!E / !D&E / D&!E + ifnone
             #     全 entry ival[i]=0（t_init で D=0 を取り込み内部状態 IQ2=0→Q=0 を作る）。 mondrv_oirc[1] が t_in(=when) の D 値
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","0","f","0"], tmg_when="!i0&!c0", timing_default=True, specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);;"),
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","0","f","1"], tmg_when="!i0&c0", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","r","f","0"], tmg_when="i0&!c0", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup_falling -- when:SETN（SETN inactive 前提、 orig latsnq）
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="s0", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="s0", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold_falling -- when:SETN
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["0","r","","f"], tmg_when="s0", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["1","f","","f"], tmg_when="s0", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- recovery_falling (SETN rise -> E fall)
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"s":["0"]}
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["f","0","r","f"], tmg_when="", specify="$recovery(posedge s0, negedge c0, 0, notifier);"),
             #--- removal_falling
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"s":["0"]}
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["f","0","r","f"], tmg_when="", specify="$removal(posedge s0, negedge c0, 0, notifier);"),
             #--- passive (data)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="", specify=""),
             #--- passive (set)
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["0"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","r","r","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","f","0"], tmg_when="", specify=""),
             #--- passive (E)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             #--- min_pulse_width_high (E) -- D 2 分割（when:!D&SETN/D&SETN）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"s":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["f","f","","p"], tmg_when="!i0&s0", specify="$width(posedge c0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"s":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="i0&s0", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_width_low (SETN) -- D 2 分割（when:!D&!E/D&!E）
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","0","n","0"], tmg_when="!i0&!c0", specify="$width(negedge s0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","r","n","0"], tmg_when="i0&!c0", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (8 conditions)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"c":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","0"],tmg_when="!i0&!c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["p"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"c":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","1"],tmg_when="!i0&c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["r"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["p"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["r"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&s0", specify="", power_default=True),
           ]
    },
    #---------------------------------------------------------------------------------------
    # LATCH_PE_NR_NS: D + pos-level Enable E + active-low RN + active-low SETN + Q.
    #   GF180 target: latrsnq_1/2/4. Internal: not*2 + udp_iq_latch_hn + buf.
    "LATCH_PE_NR_NS":{
           "logic_type":"seq_lat",
           "functions":{"o0":"Io0"},
           "latch":{"out":"Io0,IQB",
                    "enable":"c0",
                    "data_in":"i0",
                    "clear":"(!r0)",
                    "preset":"(!s0)",
                    "clear_preset_var1":"L",
                    "clear_preset_var2":"H"},
           "vcode":"reg notifier; wire c_int; wire p_int; wire iq2; not (c_int, r0); not (p_int, s0); udp_iq_latch_hn inst (iq2, c_int, p_int, c0, i0, notifier); buf (o0, iq2);",
           "expect":
           [
             #--- rising_edge -- RN=1, SETN=1  #ISS-00101: ival[c]=f で init 内 CLK H→L (D を latch)、 計測中 arc[3]=r で CLK L→H (transparent 化 → Q に新 D 反映)、 mondrv_oirc 省略  #ISS-00127: pin_tr=["o0","c0"] (target=Q, related=E)
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- combinational (D -> Q while E=1)  #ISS-00101: arc[3]=s→1 (E=1 stable transparent)、 mondrv_oirc 省略  #ISS-00127: pin_tr=["o0","i0"] (target=Q, related=D)
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["r","","r","1"], tmg_when="", specify="(i0 => o0) = (0,0);"),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["f","","f","1"], tmg_when="", specify=""),
             #--- power_tin pin(E) -- D x RN x SETN の 8 when（orig latrsnq）  #ISS-00101: mondrv_oirc 省略、 arc[0]=s→ival[o]、 ival[c]=f/1 (arc[3]=r/f)、 pin_oirc[1]=c0 維持（VIN=E、 charao の target_inport は pin_oirc[1] で識別、 i0 にすると pin(D) entry と混在し pin(E) の internal_power が出力されなくなる）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["f"],"r":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","","r"], tmg_when="!i0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"r":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","","f"], tmg_when="!i0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["f"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","","r"], tmg_when="!i0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","","f"], tmg_when="!i0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0&r0&s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0&r0&s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["f"],"r":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","1","","r"], tmg_when="i0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["1"],"r":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","1","","f"], tmg_when="i0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0&r0&s0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0&r0&s0", specify=""),
             #--- power_tin pin(D) -- E x RN x SETN の 7 when（orig latrsnq、E&RN&SETN は D 透過で除外）
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0&r0&s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0&r0&s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0&r0&!s0", specify=""),
             #--- power_tin pin(RN) -- D x E x SETN の 7 when（orig latrsnq、D&E&SETN は RN で出力変化のため除外）
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","r","0"], tmg_when="!i0&!c0&!s0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","f","0"], tmg_when="!i0&!c0&!s0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","r","0"], tmg_when="!i0&!c0&s0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","f","0"], tmg_when="!i0&!c0&s0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"r":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","r","1"], tmg_when="!i0&c0&!s0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","f","1"], tmg_when="!i0&c0&!s0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","r","1"], tmg_when="!i0&c0&s0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","f","1"], tmg_when="!i0&c0&s0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","r","0"], tmg_when="i0&!c0&!s0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","f","0"], tmg_when="i0&!c0&!s0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","1","r","0"], tmg_when="i0&!c0&s0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","1","f","0"], tmg_when="i0&!c0&s0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["0"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","r","1"], tmg_when="i0&c0&!s0", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","f","1"], tmg_when="i0&c0&!s0", specify=""),
             #--- power_tin pin(SETN) -- D x E の 3 when（RN=1 固定。orig latrsnq: !D&!E&RN / D&!E&RN / D&E&RN）
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","r","0"], tmg_when="!i0&!c0&r0", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","f","0"], tmg_when="!i0&!c0&r0", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","r","0"], tmg_when="i0&!c0&r0", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","f","0"], tmg_when="i0&!c0&r0", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["0"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","r","1"], tmg_when="i0&c0&r0", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","f","1"], tmg_when="i0&c0&r0", specify=""),
             #--- clear (RN fall -> Q fall) -- D x E の 3 when + ifnone(timing_default)。orig latrsnq: !D&!E / D&!E / D&E + ifnone
             #     全 entry ival[i]=1（t_init で D=1 を取り込み内部状態 IQ2=1→Q=1 を作る）。 mondrv_oirc[1] が t_in(=when) の D 値
             MyExpectCell(pin_tr=["o0","r0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","f","f","0"], tmg_when="!i0&!c0", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             MyExpectCell(pin_tr=["o0","r0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","1","f","0"], tmg_when="i0&!c0", timing_default=True, specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);;"),
             MyExpectCell(pin_tr=["o0","r0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","1","f","1"], tmg_when="i0&c0", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- preset (SETN fall -> Q rise) -- D x E x RN の 7 when + ifnone(timing_default)。orig latrsnq: D&E&RN を除く 7 + ifnone
             #     全 entry ival[i]=0（t_init で D=0 を取り込み内部状態 IQ2=0→Q=0 を作る）。 mondrv_oirc[1] が t_in(=when) の D 値
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["0"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","0","f","0"], tmg_when="!i0&!c0&!r0", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","0","f","0"], tmg_when="!i0&!c0&r0", timing_default=True, specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);;"),
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["0"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","0","f","1"], tmg_when="!i0&c0&!r0", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","0","f","1"], tmg_when="!i0&c0&r0", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["0"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","r","f","0"], tmg_when="i0&!c0&!r0", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","r","f","0"], tmg_when="i0&!c0&r0", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["0"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","r","f","1"], tmg_when="i0&c0&!r0", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup_falling -- when:RN&SETN（RN/SETN inactive 前提、 orig latrsnq）
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="r0&s0", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="r0&s0", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold_falling -- when:RN&SETN  #ISS-00101+ hold 探索想定: E↓で旧 D 値 latched → Q stable (変化なし) が成功状態。 setup と D 方向同じだが ival[o] が旧 D 値で stable
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["1","f","","f"], tmg_when="r0&s0", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["0","r","","f"], tmg_when="r0&s0", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- recovery_falling reset  #ISS-00143: async-on-VREL 化（ISS-00133 jp2 の TRIG v(VREL)=async 前提に整合、 seq_ff NR_NS 同型）。 tmg_when は orig latrsnq 実測（RN entry: when="SETN"）
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["1"],"r":["0"],"s":["1"]}
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["r","1","r","f"], tmg_when="s0", specify="$recovery(posedge r0, negedge c0, 0, notifier);"),
             #--- recovery_falling set  #ISS-00143: 同上（SETN entry: when="RN"）
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["0"]}
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["f","0","r","f"], tmg_when="r0", specify="$recovery(posedge s0, negedge c0, 0, notifier);"),
             #--- removal_falling reset  #ISS-00143: async-on-VREL 化（arc は recovery と同一、 seq_ff 同型）
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["1"],"r":["0"],"s":["1"]}
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["r","1","r","f"], tmg_when="s0", specify="$removal(posedge r0, negedge c0, 0, notifier);"),
             #--- removal_falling set  #ISS-00143: 同上
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["0"]}
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["f","0","r","f"], tmg_when="r0", specify="$removal(posedge s0, negedge c0, 0, notifier);"),
             #--- passive (data)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="", specify=""),
             #--- passive (reset)
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","0"], tmg_when="", specify=""),
             #--- passive (set)
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["0"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","r","r","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","f","0"], tmg_when="", specify=""),
             #--- passive (E)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             #--- min_pulse_width_high (E) -- D 2 分割（when:!D&RN&SETN/D&RN&SETN）  #ISS-00127: pin_tr=[c0,""] target=E  #ISS-00101: ival[c]=f (init 内 E 1→0 fall、 init 後半 latched), arc[r,c]=p,p で t_in 内 E pos pulse
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["f","f","","p"], tmg_when="!i0&r0&s0", specify="$width(posedge c0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="i0&r0&s0", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_width_low (RN) -- D 2 分割（when:!D&!E&SETN/D&!E&SETN）  #ISS-00127: pin_tr=[r0,""] target=RN  #ISS-00101: ival[c]=f で init E 1→0 fall、 arc[r]=n で RN neg pulse、 ival[o,i]=1,1 で init Q=1 → RN active で Q clear 0 を観測
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","f","n","0"], tmg_when="!i0&!c0&s0", specify="$width(negedge r0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","1","n","0"], tmg_when="i0&!c0&s0", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- min_pulse_width_low (SETN) -- D 2 分割（when:!D&!E&RN/D&!E&RN）  #ISS-00127: pin_tr=[s0,""] target=SETN  #ISS-00101: ival[c]=f で init E 1→0 fall、 arc[r]=n で SETN neg pulse、 ival[o,i]=0,0 で init Q=0 → SETN active で Q preset 1 を観測
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","0","n","0"], tmg_when="!i0&!c0&r0", specify="$width(negedge s0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","r","n","0"], tmg_when="i0&!c0&r0", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (16 conditions: i0 x c0 x r0 x s0)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d","u"],"i":["0"],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&r0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["d","u"],"i":["0"],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&r0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["u","d"],"i":["1"],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&r0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["u","d"],"i":["1"],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&r0&s0", specify="", power_default=True),
           ]
    },
    #---------------------------------------------------------------------------------------
    # ICG_PC: Integrated Clock Gating, posedge (latch + AND). ISS-00070 ICG (2026-07-07).
    #   GF180 target: icgtp_1/2/4. orig func: D0=E|TE -> udp_n_iq_latch(IQ2, EN=!CLK, D0) -> Q=CLK&IQ2.
    #   Pin mapping: o0=Q, i0=E (enable), i1=TE (test enable), c0=CLK (posedge)。
    #   const (E/TE vs CLK rise) は orig 同様 when なし。 delay/power_tout/min_pulse は
    #   代表 when "i0&!i1"(=E&!TE, functional mode) で orig 群と照合（他 when は分解差＝既知扱い）。
    #   負エッジ側 const は「Q 遷移なしが成功」= arc[0] stable（LAT hold と同じ流儀）。
    "ICG_PC":{
           "logic_type":"seq_lat",
           "functions":{"o0":"(c0&Io0)"},
           "latch":{"out":"Io0,IQB",
                    "enable":"(!c0)",
                    "data_in":"(i0|i1)"},
           "vcode":"reg notifier; wire mgm_d0; wire mgm_en0; wire iq2; or (mgm_d0, i0, i1); not (mgm_en0, c0); udp_iq_latch_n inst (iq2, 1'b0, 1'b0, mgm_en0, mgm_d0, notifier); and (o0, c0, iq2);",
           "expect":
           [
             #--- delay (CLK -> Q, comb 型) + power_tout -- when E&!TE（functional mode 代表）
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0"],"b":[],"c":["f"]}
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["r","1","","r"], tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0"],"b":[],"c":["r"]}
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["f","1","","f"], tmg_when="i0&!i1", specify="(c0 => o0) = (0,0);", timing_default=True),
             #--- setup E (vs CLK rise、 when なし=orig 一致)。 負エッジ側は latched=0 -> Q 遷移なし = arc[0] stable
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0"],"b":[],"c":["p"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold E
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["r","0"],"b":[],"c":["p"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["f","0"],"b":[],"c":["p"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- setup/hold TE（E=0 固定、 同型）
             MyExpectCell(pin_tr=["i1","c0"], pin_oirc=["o0","i1","","c0"], ival={"o":["0"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify="$setup(posedge i1, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i1","c0"], pin_oirc=["o0","i1","","c0"], ival={"o":["0"],"i":["0","1"],"b":[],"c":["p"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="$setup(negedge i1, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i1","c0"], pin_oirc=["o0","i1","","c0"], ival={"o":["0"],"i":["0","r"],"b":[],"c":["p"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="$hold(posedge c0, negedge i1, 0, notifier);"),
             MyExpectCell(pin_tr=["i1","c0"], pin_oirc=["o0","i1","","c0"], ival={"o":["0"],"i":["0","f"],"b":[],"c":["p"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify="$hold(posedge c0, posedge i1, 0, notifier);"),
             #--- power_tin pin(E) -- when CLK×(!TE) の代表 2 状態 × r/f
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","f","","0"], tmg_when="!c0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0&!i1", specify=""),
             #--- power_tin pin(TE)
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","i1","","c0"], ival={"o":["0"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0&!i0", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","i1","","c0"], ival={"o":["0"],"i":["0","1"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","f","","0"], tmg_when="!c0&!i0", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","i1","","c0"], ival={"o":["0"],"i":["0","0"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0&!i0", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","i1","","c0"], ival={"o":["1"],"i":["0","1"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0&!i0", specify=""),
             #--- power_tin pin(CLK) -- ゲート閉（!E&!TE）で CLK r/f、 Q=0 不変
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0&!i1", specify=""),
             #--- min_pulse (CLK) -- when E&!TE（有効時のみ Q にパルスが通る）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0"],"b":[],"c":["p"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","1","","p"], tmg_when="i0&!i1", specify="$width(posedge c0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0"],"b":[],"c":["r"]}
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","1","","n"], tmg_when="i0&!i1", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- passive (E/TE/CLK)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","f","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","i1","","c0"], ival={"o":["0"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","i1","","c0"], ival={"o":["0"],"i":["0","1"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","f","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             #--- leakage (8 states: CLK x E x TE、 Q = CLK&(E|TE))
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0"],"c":["p"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!c0&!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","1"],"c":["p"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!c0&!i0&i1", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0"],"c":["p"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","0"],tmg_when="!c0&i0&!i1", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","1"],"c":["p"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","0"],tmg_when="!c0&i0&i1", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","0"],"c":["r"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="c0&!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","1"],"c":["r"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","1"],tmg_when="c0&!i0&i1", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0"],"c":["r"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="c0&i0&!i1", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","1"],"c":["r"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="c0&i0&i1", specify="", power_default=True),
           ]
    },
    #---------------------------------------------------------------------------------------
    # ICG_NC: Integrated Clock Gating, negedge (latch + OR). ISS-00070 ICG (2026-07-07).
    #   GF180 target: icgtn_1/2/4. orig func: D0=E|TE -> udp_n_iq_latch(IQ3, EN=CLKN, D0) -> Q=CLKN|!IQ3.
    #   Pin mapping: o0=Q, i0=E, i1=TE, c0=CLKN (negedge)。 CLKN=1 で透過、 CLKN fall で E を latch。
    #   有効時（latched=1）: Q は CLKN に追従。 無効時: Q=1 固定（negedge FF は発火しない）。
    "ICG_NC":{
           "logic_type":"seq_lat",
           "functions":{"o0":"(c0|(!Io0))"},
           "latch":{"out":"Io0,IQB",
                    "enable":"c0",
                    "data_in":"(i0|i1)"},
           "vcode":"reg notifier; wire mgm_d0; wire iq3; wire iq3n; or (mgm_d0, i0, i1); udp_iq_latch_n inst (iq3, 1'b0, 1'b0, c0, mgm_d0, notifier); not (iq3n, iq3); or (o0, c0, iq3n);",
           "expect":
           [
             #--- delay (CLKN -> Q) + power_tout -- when E&!TE
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0"],"b":[],"c":["1"]}
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["f","1","","f"], tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0"],"b":[],"c":["f"]}
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["r","1","","r"], tmg_when="i0&!i1", specify="(c0 => o0) = (0,0);", timing_default=True),
             #--- setup E (vs CLKN fall)。 負エッジ側は latched=0 -> Q=1 のまま = arc[0] stable
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","0"],"b":[],"c":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0"],"b":[],"c":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold E
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["r","0"],"b":[],"c":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["f","0"],"b":[],"c":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- setup/hold TE
             MyExpectCell(pin_tr=["i1","c0"], pin_oirc=["o0","i1","","c0"], ival={"o":["1"],"i":["0","0"],"b":[],"c":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="", specify="$setup(posedge i1, negedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i1","c0"], pin_oirc=["o0","i1","","c0"], ival={"o":["1"],"i":["0","1"],"b":[],"c":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="", specify="$setup(negedge i1, negedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i1","c0"], pin_oirc=["o0","i1","","c0"], ival={"o":["1"],"i":["0","r"],"b":[],"c":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="", specify="$hold(negedge c0, negedge i1, 0, notifier);"),
             MyExpectCell(pin_tr=["i1","c0"], pin_oirc=["o0","i1","","c0"], ival={"o":["1"],"i":["0","f"],"b":[],"c":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="", specify="$hold(negedge c0, posedge i1, 0, notifier);"),
             #--- power_tin pin(E) -- CLKN=0: opaque（Q=!latched 固定）/ CLKN=1: 透過（Q=1 固定）
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","r","","0"], tmg_when="!c0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","f","","0"], tmg_when="!c0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","0"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","r","","1"], tmg_when="c0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0&!i1", specify=""),
             #--- power_tin pin(TE)
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","i1","","c0"], ival={"o":["1"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","r","","0"], tmg_when="!c0&!i0", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","i1","","c0"], ival={"o":["0"],"i":["0","1"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","f","","0"], tmg_when="!c0&!i0", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","i1","","c0"], ival={"o":["1"],"i":["0","0"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","r","","1"], tmg_when="c0&!i0", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","i1","","c0"], ival={"o":["1"],"i":["0","1"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0&!i0", specify=""),
             #--- power_tin pin(CLKN) -- ゲート閉（!E&!TE、 latched=0 -> Q=1 固定）で CLKN r/f
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","","r"], tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","0"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","0","","f"], tmg_when="!i0&!i1", specify=""),
             #--- min_pulse (CLKN) -- when E&!TE
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0"],"b":[],"c":["p"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","1","","p"], tmg_when="i0&!i1", specify="$width(posedge c0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0"],"b":[],"c":["r"]}
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","1","","n"], tmg_when="i0&!i1", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- passive (E/TE/CLKN)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","f","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","i1","","c0"], ival={"o":["1"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","i1","","c0"], ival={"o":["0"],"i":["0","1"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","f","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","0","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","0","","f"], tmg_when="", specify=""),
             #--- leakage (8 states: CLKN x E x TE、 Q = CLKN | !(E|TE))
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","0"],"c":["p"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","0"],tmg_when="!c0&!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0","1"],"c":["p"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!c0&!i0&i1", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","0"],"c":["p"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","0"],tmg_when="!c0&i0&!i1", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1","1"],"c":["p"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","0"],tmg_when="!c0&i0&i1", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","0"],"c":["r"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","1"],tmg_when="c0&!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0","1"],"c":["r"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","1"],tmg_when="c0&!i0&i1", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","0"],"c":["r"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="c0&i0&!i1", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1","1"],"c":["r"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="c0&i0&i1", specify="", power_default=True),
           ]
    },
  }

###############################################################################
def get_code_primitive():
  # LATCH uses udp_iq_latch_n / udp_iq_latch_hn from mylogic_seq_ff.py (no new primitives).
  return ""
