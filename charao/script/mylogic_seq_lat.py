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
           "vcode":"wire mgm_d0; wire iq1; not (mgm_d0, i0); udp_iq_latch_n inst (iq1, 1'b0, 1'b0, c0, mgm_d0, ); not (o0, iq1);",
           "expect":
           [
             #--- rising_edge (E rise -> Q) + power_tout
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["1","1","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"]}, mondrv_oirc=["0","0","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- combinational (D -> Q while E=1, transparent latch) - charao auto: islatch + clk_role="nouse" → clk_init="stable"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}, mondrv_oirc=["1","1","1","0"]
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["r","r","r","s"], tmg_when="", specify="(i0 => o0) = (0,0);"),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"]}, mondrv_oirc=["0","0","0","0"]
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["f","f","f","s"], tmg_when="", specify=""),
             #--- power_tin pin(E) when:"!D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(E) when:"D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!E"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["d","1","1","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1"],"b":[],"c":["0"]}, mondrv_oirc=["d","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"E"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0"],"b":[],"c":["1"]}, mondrv_oirc=["d","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1"],"b":[],"c":["1"]}, mondrv_oirc=["d","0","0","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="c0", specify=""),
             #--- setup_falling (D vs E fall edge)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold_falling
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- passive (data)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (E)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             #--- min_pulse_width_high (E) -- H pulse 計測
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             # min_pulse_width_low (E) は orig latq lib に無いため削除
             #--- leakage (4 conditions: !D&!E / !D&E / D&!E / D&E)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"]},mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"]},mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"]},mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"]},mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0", specify=""),
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
           "vcode":"wire c_int; wire iq2; not (c_int, r0); udp_iq_latch_n inst (iq2, c_int, 1'b0, c0, i0, ); buf (o0, iq2);",
           "expect":
           [
             #--- rising_edge (E rise -> Q) -- RN=1
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- combinational (D -> Q while E=1) - charao auto: islatch + clk_role="nouse" → clk_init="stable"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["1","1","1","0"]
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["r","r","r","s"], tmg_when="", specify="(i0 => o0) = (0,0);"),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["f","f","f","s"], tmg_when="", specify=""),
             #--- power_tin pin(E) when:"!D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(E) when:"D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!E"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["d","1","1","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["d","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"E"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["d","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["d","0","0","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="c0", specify=""),
             #--- clear (RN fall -> Q fall)
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","s","f","s"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- setup_falling
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold_falling
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- recovery_falling (RN rise -> E fall)
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["1"],"r":["0"]}, mondrv_oirc=["1","1","0","0"]
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["r","r","f","f"], tmg_when="", specify="$recovery(posedge r0, negedge c0, 0, notifier);"),
             #--- removal_falling
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["1"],"r":["0"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["s","r","f","f"], tmg_when="", specify="$removal(posedge r0, negedge c0, 0, notifier);"),
             #--- passive (data)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (reset)
             MyExpectCell(pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             #--- passive (E)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             #--- min_pulse_width_high (E)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_width_low (RN)  -- RN L pulse
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","s","f","s"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- leakage (8 conditions: i0 x c0 x r0)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["0"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&r0", specify=""),
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
           "vcode":"wire p_int; wire iq2; not (p_int, s0); udp_iq_latch_n inst (iq2, 1'b0, p_int, c0, i0, ); buf (o0, iq2);",
           "expect":
           [
             #--- rising_edge -- SETN=1
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- combinational (D -> Q while E=1) - charao auto: islatch + clk_role="nouse" → clk_init="stable"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","0"]
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["r","r","r","s"], tmg_when="", specify="(i0 => o0) = (0,0);"),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["f","f","f","s"], tmg_when="", specify=""),
             #--- power_tin pin(E) when:"!D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(E) when:"D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!E"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["d","1","1","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["d","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"E"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["d","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["d","0","0","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="c0", specify=""),
             #--- preset (SETN fall -> Q rise)
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","s","f","s"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup_falling
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold_falling
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- recovery_falling (SETN rise -> E fall)
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"s":["0"]}, mondrv_oirc=["0","1","0","0"]
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["f","r","f","f"], tmg_when="", specify="$recovery(posedge s0, negedge c0, 0, notifier);"),
             #--- removal_falling
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"s":["0"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["s","r","f","f"], tmg_when="", specify="$removal(posedge s0, negedge c0, 0, notifier);"),
             #--- passive (data)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (set)
             MyExpectCell(pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (E)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             #--- min_pulse_width_high (E)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_width_low (SETN)
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","s","f","s"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (8 conditions)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"s":["0"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"s":["0"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&s0", specify=""),
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
           "vcode":"wire c_int; wire p_int; wire iq2; not (c_int, r0); not (p_int, s0); udp_iq_latch_hn inst (iq2, c_int, p_int, c0, i0, ); buf (o0, iq2);",
           "expect":
           [
             #--- rising_edge -- RN=1, SETN=1
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- combinational (D -> Q while E=1) - charao auto: islatch + clk_role="nouse" → clk_init="stable"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","0"]
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["r","r","r","s"], tmg_when="", specify="(i0 => o0) = (0,0);"),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                         ,meas_types=["delay","power_tout"] ,tmg_sense="pos",arc_oirc=["f","f","f","s"], tmg_when="", specify=""),
             #--- power_tin pin(E) when:"!D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(E) when:"D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!E"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["d","1","1","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["d","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"E"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["d","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["d","0","0","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="c0", specify=""),
             #--- clear (RN fall -> Q fall)
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","s","f","s"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- preset (SETN fall -> Q rise)
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","s","f","s"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup_falling
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold_falling
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- recovery_falling reset
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["1"],"r":["0"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["r","r","f","f"], tmg_when="", specify="$recovery(posedge r0, negedge c0, 0, notifier);"),
             #--- recovery_falling set
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["0"]}, mondrv_oirc=["0","1","0","0"]
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["f","r","f","f"], tmg_when="", specify="$recovery(posedge s0, negedge c0, 0, notifier);"),
             #--- removal_falling reset
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["1"],"r":["0"],"s":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["s","r","f","f"], tmg_when="", specify="$removal(posedge r0, negedge c0, 0, notifier);"),
             #--- removal_falling set
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["s","r","f","f"], tmg_when="", specify="$removal(posedge s0, negedge c0, 0, notifier);"),
             #--- passive (data)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (reset)
             MyExpectCell(pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             #--- passive (set)
             MyExpectCell(pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (E)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             #--- min_pulse_width_high (E)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_width_low (RN)
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","s","f","s"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- min_pulse_width_low (SETN)
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","s","f","s"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (16 conditions: i0 x c0 x r0 x s0)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&r0&s0", specify=""),
           ]
    },
  }

###############################################################################
def get_code_primitive():
  # LATCH uses udp_iq_latch_n / udp_iq_latch_hn from mylogic_seq_ff.py (no new primitives).
  return ""
