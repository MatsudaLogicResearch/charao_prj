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
#  Primitives (udp_iq_ff_n / udp_iq_ff_hn) are shared with mylogic_seq_ff.py.
#  User-defined Logic entries may be added via mylogic_user.py specified in ARGS.
#
# def get_code_primitive():
#  Returns empty string (no SDFF-specific primitives, see mylogic_seq_ff.py).
#
# Characterization mode (Phase B, ISS-00086):
#  SE=0 (functional mode) で D->Q timing/power を計測。 SI/SE は ival で "0" 固定
#  → set_stable_inport 経由で VLOW にバインド。 expect 群は DFF_PC* pattern を継承し、
#    ival["i"] を 3 要素化 ([D値,"0","0"]) するのみが差分。
#  vcode は orig sdff*_func 準拠 (MUX2 OR-of-3-ANDs + udp_iq_ff_n/hn + Q invert)。
#  Phase A (orig 互角化、 SE/SI 別 when 計測) は将来 ISS-00086B 候補で対応。
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
           "vcode":"wire d_inv; wire se_inv; wire si_inv; wire row1; wire row2; wire row3; wire mgm_d0; wire iq1; not (d_inv, i0); not (se_inv, i2); and (row1, d_inv, se_inv); not (si_inv, i1); and (row2, d_inv, si_inv); and (row3, si_inv, i2); or (mgm_d0, row1, row2, row3); udp_iq_ff_n inst (iq1, 1'b0, 1'b0, c0, mgm_d0, ); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clk -> q) + power_tout
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["1","1","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["0","0","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- power_tin pin(CLK) when:"!D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["d","1","1","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["d","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0","0","0"],"b":[],"c":["1"]}, mondrv_oirc=["d","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1","0","0"],"b":[],"c":["1"]}, mondrv_oirc=["d","0","0","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="c0", specify=""),
             #--- setup
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- passive power (data)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive power (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             #--- min_pulse_width_high
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_width_low
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","r","r","f"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- leakage (4 conditions)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"]},mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"]},mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"]},mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"]},mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0", specify=""),
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
           "vcode":"wire d_inv; wire se_inv; wire si_inv; wire row1; wire row2; wire row3; wire mgm_d0; wire iq1; wire p_int; not (d_inv, i0); not (se_inv, i2); and (row1, d_inv, se_inv); not (si_inv, i1); and (row2, d_inv, si_inv); and (row3, si_inv, i2); or (mgm_d0, row1, row2, row3); not (p_int, r0); udp_iq_ff_n inst (iq1, 1'b0, p_int, c0, mgm_d0, ); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clk -> q) -- RN=1 + power_tout
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- power_tin pin(CLK) when:"!D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["d","1","1","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["d","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0","0","0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["d","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1","0","0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["d","0","0","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="c0", specify=""),
             #--- clear (RN fall)
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","s","f","s"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- setup
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1","0","0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["1","1","1","1"]
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["r","r","r","r"], tmg_when="", specify="$recovery(posedge r0, posedge c0, 0, notifier);"),
             #--- removal
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1","0","0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="", specify="$removal(posedge r0, posedge c0, 0, notifier);"),
             #--- passive power (data)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive power (reset)
             MyExpectCell(pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             #--- passive power (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             #--- min_pulse (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","r","r","f"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (reset)
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","s","f","s"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- leakage (8 conditions: i0 x c0 x r0)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"r":["0"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"r":["0"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"r":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"r":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&r0", specify=""),
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
           "vcode":"wire d_inv; wire se_inv; wire si_inv; wire row1; wire row2; wire row3; wire mgm_d0; wire iq1; wire c_int; not (d_inv, i0); not (se_inv, i2); and (row1, d_inv, se_inv); not (si_inv, i1); and (row2, d_inv, si_inv); and (row3, si_inv, i2); or (mgm_d0, row1, row2, row3); not (c_int, s0); udp_iq_ff_n inst (iq1, c_int, 1'b0, c0, mgm_d0, ); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clk -> q) -- SETN=1
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- power_tin pin(CLK) when:"!D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["d","1","1","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["d","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0","0","0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["d","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1","0","0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["d","0","0","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="c0", specify=""),
             #--- preset (SETN fall)
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","s","f","s"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0","0","0"],"b":[],"c":["0"],"s":["0"]}, mondrv_oirc=["0","1","1","1"]
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["f","r","r","r"], tmg_when="", specify="$recovery(posedge s0, posedge c0, 0, notifier);"),
             #--- removal
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0","0","0"],"b":[],"c":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="", specify="$removal(posedge s0, posedge c0, 0, notifier);"),
             #--- passive (data)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (set)
             MyExpectCell(pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             #--- min_pulse (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","r","r","f"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (set)
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","s","f","s"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (8 conditions)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"s":["0"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"s":["0"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&s0", specify=""),
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
           "vcode":"wire d_inv; wire se_inv; wire si_inv; wire row1; wire row2; wire row3; wire mgm_d0; wire iq1; wire p_int; wire c_int; not (d_inv, i0); not (se_inv, i2); and (row1, d_inv, se_inv); not (si_inv, i1); and (row2, d_inv, si_inv); and (row3, si_inv, i2); or (mgm_d0, row1, row2, row3); not (p_int, r0); not (c_int, s0); udp_iq_ff_hn inst (iq1, c_int, p_int, c0, mgm_d0, ); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clk -> q) -- RN=1, SETN=1
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- power_tin pin(CLK) when:"!D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D"
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["d","1","1","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["d","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK"
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0","0","0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["d","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1","0","0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["d","0","0","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="c0", specify=""),
             #--- clear (RN fall)
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","s","f","s"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- preset (SETN fall)
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","s","f","s"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery reset
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1","0","0"],"b":[],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["r","r","r","r"], tmg_when="", specify="$recovery(posedge r0, posedge c0, 0, notifier);"),
             #--- recovery set
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["0","1","1","1"]
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["f","r","r","r"], tmg_when="", specify="$recovery(posedge s0, posedge c0, 0, notifier);"),
             #--- removal reset
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1","0","0"],"b":[],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="", specify="$removal(posedge r0, posedge c0, 0, notifier);"),
             #--- removal set
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="", specify="$removal(posedge s0, posedge c0, 0, notifier);"),
             #--- passive (data)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (reset)
             MyExpectCell(pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             #--- passive (set)
             MyExpectCell(pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             #--- min_pulse (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","r","r","f"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (reset)
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","s","f","s"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- min_pulse (set)
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0","0","0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","s","f","s"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (16 conditions: i0 x c0 x r0 x s0)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0","0","0"],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1","0","0"],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&r0&s0", specify=""),
           ]
    },
  }

###############################################################################
def get_code_primitive():
  # SDFF uses udp_iq_ff_n / udp_iq_ff_hn from mylogic_seq_ff.py (no new primitives).
  return ""
