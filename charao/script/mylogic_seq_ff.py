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
#  Returns the seq Logic definitions (sequential cells: DFF, LATCH, etc.).
#  User-defined Logic entries may be added via mylogic_user.py specified in ARGS.
#
# def get_code_primitive():
#  Returns the seq primitive code (lr_dff).
#  User-defined primitive code may override this via mylogic_user.py specified in ARGS.
#
###############################################################################
from .myExpectCell import MyExpectCell

###############################################################################
def get_logic_dict():
  return {
    #---------------------------------------------------------------------------------------
    # DFF_PC (D + posedge CLK + Q, no reset/set, single Q output).
    # GF180 target: dffq_1/2/4. Verilog primitive: udp_iq_ff_n (Q, C=0, P=0, CK, D, N).
    "DFF_PC":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"i0",
                 "clocked_on":"c0"},
           "vcode":"udp_iq_ff_n inst (o0, 1'b0, 1'b0, c0, i0, );",
           "expect":
           [
             #--- q delay (clk -> q) + power_tout
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["1","1","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"]}, mondrv_oirc=["0","0","1","1"]
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- power_tin pin(CLK) when:"!D" - CLK 変化、 D=0 stable、 Q=0 stable
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D" - CLK 変化、 D=1 stable、 Q=1 stable
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK" - D 変化、 CLK=0 stable、 Q 不変
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["d","1","1","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1"],"b":[],"c":["0"]}, mondrv_oirc=["d","0","0","0"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK" - D 変化、 CLK=1 stable、 Q 不変
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["0"],"b":[],"c":["1"]}, mondrv_oirc=["d","1","1","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d"],"i":["1"],"b":[],"c":["1"]}, mondrv_oirc=["d","0","0","1"]
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="c0", specify=""),
             #--- setup
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- passive power (data)  -- CLK 静止 L
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive power (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             #--- min_pulse (clk) -- H pulse 完了で L 終了
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_low (clk) -- L pulse 計測 (init H -> fall -> L -> rise)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","r","r","f"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- leakage (4 conditions: !D&!CLK / !D&CLK / D&!CLK / D&CLK)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"]},mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"]},mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"]},mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"]},mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0", specify=""),
           ]
    },
    #---------------------------------------------------------------------------------------
    # DFF_NC (D + negedge CLKN + Q, no reset/set, single Q output).
    # GF180 target: dffnq_1/2/4.
    # Internal: CLKN -> not -> CLK_int -> udp_iq_ff_n (posedge primitive), D -> not -> D_int,
    #           udp_iq_ff_n outputs iq1 (= !D), then not gate -> Q (= D).
    "DFF_NC":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"i0",
                 "clocked_on":"(!c0)"},
           "vcode":"wire clkn_int; wire d_int; wire iq1; not (clkn_int, c0); not (d_int, i0); udp_iq_ff_n inst (iq1, 1'b0, 1'b0, clkn_int, d_int, ); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clkn negedge -> q)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}, mondrv_oirc=["1","1","0","0"]
                         ,meas_types=["falling_edge"] ,tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"]}, mondrv_oirc=["0","0","0","0"]
                         ,meas_types=["falling_edge"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="(negedge c0 => (o0 +: i0)) =(0,0);"),
             #--- setup
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- passive power (data) -- CLKN 静止 H
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive power (clkn)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             #--- min_pulse (clkn) -- L pulse 完了で H 終了
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- leakage (4 conditions: !D&CLKN / !D&!CLKN / D&CLKN / D&!CLKN)  (CLKN polarity reversed vs CLK)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"]},mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"]},mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="!i0&!c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"]},mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"]},mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="i0&!c0", specify=""),
           ]
    },
    #---------------------------------------------------------------------------------------
    # DFF_PC_NR (D + posedge CLK + active-low reset RN + Q, single Q output).
    # GF180 target: dffrnq_1/2/4.
    # Internal: RN -> not -> p_int (active high), D -> not -> d_int,
    #           udp_iq_ff_n(iq1, 0, p_int, CLK, d_int, N), then not -> Q.
    # Skeleton: rising_edge x2 + clear x1 + leakage x8. (TODO: setup/hold/recovery/removal/passive/min_pulse)
    "DFF_PC_NR":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"i0",
                 "clocked_on":"c0",
                 "clear":"(!r0)"},
           "vcode":"wire p_int; wire d_int; wire iq1; not (p_int, r0); not (d_int, i0); udp_iq_ff_n inst (iq1, 1'b0, p_int, c0, d_int, ); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clk -> q) -- RN=1 (non-reset)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                         ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","1","1"]
                         ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- clear (RN fall -> Q fall, async)
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","s","f","s"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- setup (D -> CLK rising edge)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery (RN rise -> CLK rise)
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["1","1","1","1"]
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["r","r","r","r"], tmg_when="", specify="$recovery(posedge r0, posedge c0, 0, notifier);"),
             #--- removal (CLK rise after RN rise, arc same as recovery)
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="", specify="$removal(posedge r0, posedge c0, 0, notifier);"),
             #--- passive power (data) -- CLK static L, RN=1
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive power (reset)
             MyExpectCell(pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             #--- passive power (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             #--- min_pulse (clk) -- H pulse 完了で L 終了
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse (reset) -- RN L pulse
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","s","f","s"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- leakage (8 conditions: i0 x c0 x r0)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&r0", specify=""),
           ]
    },
    #---------------------------------------------------------------------------------------
    # DFF_PC_NS (D + posedge CLK + active-low set SETN + Q).
    # GF180 target: dffsnq_1/2/4.
    # Internal: SETN -> not -> c_int (active high), D -> not -> d_int,
    #           udp_iq_ff_n(iq1, c_int, 0, CLK, d_int, N), then not -> Q.
    "DFF_PC_NS":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"i0",
                 "clocked_on":"c0",
                 "preset":"(!s0)"},
           "vcode":"wire c_int; wire d_int; wire iq1; not (c_int, s0); not (d_int, i0); udp_iq_ff_n inst (iq1, c_int, 1'b0, c0, d_int, ); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clk -> q) -- SETN=1 (non-set)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                         ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                         ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- preset (SETN fall -> Q rise, async)
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","s","f","s"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery (SETN rise -> CLK rise)
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"s":["0"]}, mondrv_oirc=["0","1","1","1"]
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["f","r","r","r"], tmg_when="", specify="$recovery(posedge s0, posedge c0, 0, notifier);"),
             #--- removal
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="", specify="$removal(posedge s0, posedge c0, 0, notifier);"),
             #--- passive (data) -- CLK static L, SETN=1
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (set)
             MyExpectCell(pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             #--- min_pulse (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse (set)
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","s","f","s"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (8 conditions: i0 x c0 x s0)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"s":["0"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&!c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"s":["0"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&s0", specify=""),
           ]
    },
    #---------------------------------------------------------------------------------------
    # DFF_NC_NR (D + negedge CLKN + active-low reset RN + Q).
    # GF180 target: dffnrnq_1/2/4.
    "DFF_NC_NR":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"i0",
                 "clocked_on":"(!c0)",
                 "clear":"(!r0)"},
           "vcode":"wire clkn_int; wire p_int; wire d_int; wire iq1; not (clkn_int, c0); not (p_int, r0); not (d_int, i0); udp_iq_ff_n inst (iq1, 1'b0, p_int, clkn_int, d_int, ); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clkn neg -> q)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["1","1","0","0"]
                         ,meas_types=["falling_edge"] ,tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                         ,meas_types=["falling_edge"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="(negedge c0 => (o0 +: i0)) =(0,0);"),
             #--- clear
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["0","1","0","1"]
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","s","f","s"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- setup
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- recovery (RN rise -> CLKN fall)
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["1"],"r":["0"]}, mondrv_oirc=["1","1","0","0"]
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["r","r","f","f"], tmg_when="", specify="$recovery(posedge r0, negedge c0, 0, notifier);"),
             #--- removal
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["1"],"r":["0"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["s","r","f","f"], tmg_when="", specify="$removal(posedge r0, negedge c0, 0, notifier);"),
             #--- passive (data) -- CLKN static H, RN=1
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (reset)
             MyExpectCell(pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["0"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             #--- passive (clkn)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             #--- min_pulse (clkn) -- L pulse 完了で H 終了
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (reset)
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"]}, mondrv_oirc=["0","1","0","1"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","s","f","s"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- leakage (8 conditions: i0 x c0 x r0)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["0"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["0"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="!i0&!c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="!i0&!c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="i0&!c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="i0&!c0&r0", specify=""),
           ]
    },
    #---------------------------------------------------------------------------------------
    # DFF_NC_NS (D + negedge CLKN + active-low set SETN + Q).
    # GF180 target: dffnsnq_1/2/4.
    "DFF_NC_NS":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"i0",
                 "clocked_on":"(!c0)",
                 "preset":"(!s0)"},
           "vcode":"wire clkn_int; wire c_int; wire d_int; wire iq1; not (clkn_int, c0); not (c_int, s0); not (d_int, i0); udp_iq_ff_n inst (iq1, c_int, 1'b0, clkn_int, d_int, ); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clkn neg -> q)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                         ,meas_types=["falling_edge"] ,tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                         ,meas_types=["falling_edge"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="(negedge c0 => (o0 +: i0)) =(0,0);"),
             #--- preset
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","s","f","s"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- recovery (SETN rise -> CLKN fall)
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"s":["0"]}, mondrv_oirc=["0","1","0","0"]
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["f","r","f","f"], tmg_when="", specify="$recovery(posedge s0, negedge c0, 0, notifier);"),
             #--- removal
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"s":["0"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["s","r","f","f"], tmg_when="", specify="$removal(posedge s0, negedge c0, 0, notifier);"),
             #--- passive (data) -- CLKN static H, SETN=1
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (set)
             MyExpectCell(pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f","s"], tmg_when="", specify=""),
             #--- passive (clkn)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             #--- min_pulse (clkn)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (set)
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","s","f","s"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (8 conditions: i0 x c0 x s0)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"s":["0"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"s":["0"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="!i0&!c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="!i0&!c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="i0&!c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="i0&!c0&s0", specify=""),
           ]
    },
    #---------------------------------------------------------------------------------------
    # DFF_PC_NR_NS (D + posedge CLK + active-low reset RN + active-low set SETN + Q).
    # GF180 target: dffrsnq_1/2/4. Uses udp_iq_ff_hn (P dominates over C).
    "DFF_PC_NR_NS":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"i0",
                 "clocked_on":"c0",
                 "clear":"(!r0)",
                 "preset":"(!s0)",
                 "clear_preset_var1":"L",
                 "clear_preset_var2":"H"},
           "vcode":"wire p_int; wire c_int; wire d_int; wire iq1; not (p_int, r0); not (c_int, s0); not (d_int, i0); udp_iq_ff_hn inst (iq1, c_int, p_int, c0, d_int, ); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clk -> q) -- RN=1, SETN=1
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                         ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                         ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- clear (RN fall)
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","s","f","s"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- preset (SETN fall)
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","s","f","s"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","f","r","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery reset
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["r","r","r","r"], tmg_when="", specify="$recovery(posedge r0, posedge c0, 0, notifier);"),
             #--- recovery set
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["0","1","1","1"]
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["f","r","r","r"], tmg_when="", specify="$recovery(posedge s0, posedge c0, 0, notifier);"),
             #--- removal reset
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="", specify="$removal(posedge r0, posedge c0, 0, notifier);"),
             #--- removal set
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["s","r","r","r"], tmg_when="", specify="$removal(posedge s0, posedge c0, 0, notifier);"),
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
             #--- passive (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","s","f","f"], tmg_when="", specify=""),
             #--- min_pulse (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse (reset)
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","s","f","s"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- min_pulse (set)
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
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="!i0&c0&r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&!c0&r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","r"],tmg_when="i0&c0&r0&s0", specify=""),
           ]
    },

    #---------------------------------------------------------------------------------------
    # DFF_NC_NR_NS (D + negedge CLKN + active-low reset RN + active-low set SETN + Q).
    # GF180 target: dffnrsnq_1/2/4. Uses udp_iq_ff_hn (P dominates over C).
    "DFF_NC_NR_NS":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"i0",
                 "clocked_on":"(!c0)",
                 "clear":"(!r0)",
                 "preset":"(!s0)",
                 "clear_preset_var1":"L",
                 "clear_preset_var2":"H"},
           "vcode":"wire clkn_int; wire p_int; wire c_int; wire d_int; wire iq1; not (clkn_int, c0); not (p_int, r0); not (c_int, s0); not (d_int, i0); udp_iq_ff_hn inst (iq1, c_int, p_int, clkn_int, d_int, ); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clkn neg -> q)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                         ,meas_types=["falling_edge"] ,tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                         ,meas_types=["falling_edge"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="(negedge c0 => (o0 +: i0)) =(0,0);"),
             #--- clear
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","0","1"]
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","s","f","s"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- preset
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","s","f","s"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup/hold
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["r","r","f","f"], tmg_when="", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- recovery/removal reset
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["1"],"r":["0"],"s":["1"]}, mondrv_oirc=["1","1","0","0"]
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["r","r","f","f"], tmg_when="", specify="$recovery(posedge r0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","r0","c0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["1"],"r":["0"],"s":["1"]}, mondrv_oirc=["0","1","0","0"]
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["s","r","f","f"], tmg_when="", specify="$removal(posedge r0, negedge c0, 0, notifier);"),
             #--- recovery/removal set
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["0"]}, mondrv_oirc=["0","1","0","0"]
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["f","r","f","f"], tmg_when="", specify="$recovery(posedge s0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","s0","c0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","1","0","0"]
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["s","r","f","f"], tmg_when="", specify="$removal(posedge s0, negedge c0, 0, notifier);"),
             #--- min_pulse (clkn)
             MyExpectCell(pin_oirc=["o0","i0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","f","f","f"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (reset)
             MyExpectCell(pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","1","0","1"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","s","f","s"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- min_pulse (set)
             MyExpectCell(pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","s","f","s"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (16 conditions: i0 x c0 x r0 x s0)
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="!i0&c0&r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="!i0&!c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["0"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="!i0&!c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="!i0&!c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["d","u"],"i":["0"],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["0","0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="!i0&!c0&r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","s"],tmg_when="i0&c0&r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["0"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="i0&!c0&!r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["0"],"s":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="i0&!c0&!r0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["1"],"s":["0"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="i0&!c0&r0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0","c0"], ival={"o":["u","d"],"i":["1"],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oirc=["1","1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s","f"],tmg_when="i0&!c0&r0&s0", specify=""),
           ]
    },

  #==========================================================================================================================================================
  #Q,QB
    "DFFB_PC_PR":{
           "logic_type":"seq",
           "functions":{"o0":"Io0","o1":"Io1"},
           "ff":{"out":"Io0,Io1",
                 "next_state":"i0",
                 "clocked_on":"c0",
                 "clear":"(r0)"},
           "expect":
           [
             #--- q delay (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["1","1","1",""]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oirc=["r","r","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0",""], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","0","1",""]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oirc=["f","f","r",""], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             
             MyExpectCell(pin_oirc=["o1","i0","c0",""], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["1","0","1",""]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oirc=["r","f","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o1","i0","c0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","1","1",""]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oirc=["f","r","r",""], tmg_when="", specify="(posedge c0 => (o1 +: i0)) =(0,0);"),
             #--- clear(q)
             MyExpectCell(pin_oirc=["o0","i0","r0",""], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","1","1",""]
                       ,meas_types=["clear"]       ,tmg_sense="neg",arc_oirc=["f","s","r",""], tmg_when="", specify="(posedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- clear(q)-->preset(qb)
             MyExpectCell(pin_oirc=["o1","i0","r0",""], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["1","1","1",""]
                       ,meas_types=["preset"]       ,tmg_sense="pos",arc_oirc=["r","s","r",""], tmg_when="", specify="(posedge r0 => (o1 +: 1'b1)) = (0,0);"),
             
             #--- setup
             MyExpectCell(pin_oirc=["o0","i0","c0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["1","1","1",""]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","r",""], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0",""], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","0","1",""]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","r",""], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),

             #--- hold (arc_oirc is same as setup)
             MyExpectCell(pin_oirc=["o0","i0","c0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["1","1","1",""]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","r","r",""], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0",""], ival={"o":["1","1"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","0","1",""]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","f","r",""], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery reset
             MyExpectCell(pin_oirc=["o0","r0", "c0"], ival={"o":["0","1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["1","0","1",""]
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["r","f","r",""], tmg_when="", specify="$recovery(negedge r0, posedge c0, 0, notifier);"),
             #--- removal reset(arc_oirc is same as recovery)
             MyExpectCell(pin_oirc=["o0","r0", "c0"], ival={"o":["0","1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","1",""]
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["r","f","r",""], tmg_when="", specify="$removal(negedge r0, posedge c0, 0, notifier);"),
             
             #--- passive power(data)
             MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","1","1",""]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["1","0","0",""]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f",""], tmg_when="", specify=""),
             #--- passive power(reset)
             MyExpectCell(pin_oirc=["o0","r0","r0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","1","1",""]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","r0","r0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oirc=["0","0","0",""]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r",""], tmg_when="", specify=""),
             
             #--- passive power(clk)
             MyExpectCell(pin_oirc=["o0","c0","c0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","1","1",""]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0",""], ival={"o":["0","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","0","0",""]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f",""], tmg_when="", specify=""),
             #--- min_pulse(clk)
             MyExpectCell(pin_oirc=["o0","i0","c0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["1","1","1",""]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","r",""], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse(reset)
             MyExpectCell(pin_oirc=["o0","i0","r0",""], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oirc=["0","1","1",""]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["f","s","r",""], tmg_when="", specify="$width(posedge r0, 0, 0, notifier);"),
             #--- leakage(clock->inputport & mondrv_oirc[1]=clock value )
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"]},mondrv_oirc=["0","0","0",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["1"]},mondrv_oirc=["0","0","0",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"]},mondrv_oirc=["0","1","0",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","r","s",""],tmg_when="!i0&c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["1"]},mondrv_oirc=["0","1","0",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","r","s",""],tmg_when="!i0&c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"]},mondrv_oirc=["1","0","1",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["d","u"],"i":["1"],"c":["0"],"r":["1"]},mondrv_oirc=["0","0","1",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!c0&r0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"]},mondrv_oirc=["1","1","1",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","r","s",""],tmg_when="i0&c0&!r0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["d","u"],"i":["1"],"c":["0"],"r":["1"]},mondrv_oirc=["0","1","1",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","r","s",""],tmg_when="i0&c0&r0", specify=""),
           ]
    },

    "DFFB_PC_NS":{
           "logic_type":"seq",
           "functions":{"o0":"Io0","o1":"Io1"},
           "ff":{"out":"Io0,Io1",
                 "next_state":"i0",
                 "clocked_on":"c0",
                 "preset":"(!s0)"},
           "expect":
           [
             #--- q delay (clk)
             MyExpectCell(pin_oirc=["o0","i0","c0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1",""]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oirc=["r","r","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","c0",""], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","1",""]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oirc=["f","f","r",""], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             
             MyExpectCell(pin_oirc=["o1","i0","c0",""], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","1",""]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oirc=["r","f","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o1","i0","c0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","1","1",""]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oirc=["f","r","r",""], tmg_when="", specify="(posedge c0 => (o1 +: i0)) =(0,0);"),
             
             #--- preset(q)
             MyExpectCell(pin_oirc=["o0","i0","s0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0",""]
                       ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","s","f",""], tmg_when="", specify="(negedge s0 => (o0 +: 1'b1)) = (0,0);"),
             #--- preset(q)-->clear(qb)
             MyExpectCell(pin_oirc=["o1","i0","s0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","1","0",""]
                       ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","s","f",""], tmg_when="", specify="(negedge s0 => (o1 +: 1'b0)) = (0,0);"),
             
             #--- setup
             MyExpectCell(pin_oirc=["o0","i0","c0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1",""]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","r",""], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0",""], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","1",""]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","r",""], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             
             #--- hold (arc_oirc is same as setup)
             MyExpectCell(pin_oirc=["o0","i0","c0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1",""]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","r","r",""], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oirc=["o0","i0","c0",""], ival={"o":["1","1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","1",""]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","f","r",""], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),

             #--- recovery preset
             MyExpectCell(pin_oirc=["o0","s0", "c0"], ival={"o":["1","0"],"i":["0"],"b":[],"c":["0"],"s":["0"]}, mondrv_oirc=["0","1","1",""]
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["f","r","r",""], tmg_when="", specify="$recovery(posedge s0, posedge c0, 0, notifier);"),
             #--- removal preset(arc_oirc is same as recovery)
             MyExpectCell(pin_oirc=["o0","s0", "c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["0"]}, mondrv_oirc=["0","1","1",""]
                        ,meas_types=["removal_rising"],tmg_sense="pos",arc_oirc=["f","r","r",""], tmg_when="", specify="$removal(posedge s0, posedge c0, 0, notifier);"),
             
             #--- passive power(data)
             MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","1","1",""]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0",""]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f",""], tmg_when="", specify=""),
             #--- passive power(preset)
             MyExpectCell(pin_oirc=["o0","s0","s0",""], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["0"]}, mondrv_oirc=["1","1","1",""]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","s0","s0",""], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0",""]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f",""], tmg_when="", specify=""),
             
             #--- passive power(clk)
             MyExpectCell(pin_oirc=["o0","c0","c0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","1","1",""]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","r","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","c0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["0","0","0",""]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["s","f","f",""], tmg_when="", specify=""),
             
             #--- min_pulse(clk)
             MyExpectCell(pin_oirc=["o0","i0","c0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","1","1",""]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","r",""], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse(preset)
             MyExpectCell(pin_oirc=["o0","i0","s0",""], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oirc=["1","0","0",""]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","s","f",""], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             
             #--- leakage(clock->inputport & mondrv_oirc[1]=clock value )
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["u","d"],"i":["0"],"c":["0"],"s":["0"]},mondrv_oirc=["1","0","0",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["d","s"],"i":["0"],"c":["0"],"s":["1"]},mondrv_oirc=["0","0","0",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["u","d"],"i":["0"],"c":["0"],"s":["0"]},mondrv_oirc=["1","1","0",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","r","s",""],tmg_when="!i0&c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["u","d"],"i":["0"],"c":["0"],"s":["1"]},mondrv_oirc=["1","1","0",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","r","s",""],tmg_when="!i0&c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["0"]},mondrv_oirc=["1","0","1",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["1"]},mondrv_oirc=["1","0","1",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!c0&s0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["0"]},mondrv_oirc=["1","1","1",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","r","s",""],tmg_when="i0&c0&!s0", specify=""),
             MyExpectCell(pin_oirc=["o0","c0","i0",""], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["1"]},mondrv_oirc=["1","1","1",""]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","r","s",""],tmg_when="i0&c0&s0", specify=""),

           ]
    },
  }

###############################################################################
def get_code_primitive():
    return '''
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
//
// Note: charao 4-primitive set (udp_iq_ff_hn / udp_iq_latch_hn / udp_iq_ff_n /
//       udp_iq_latch_n) is adapted from GF180MCU PDK primitives by
//       GlobalFoundries (gf180mcu_fd_sc_mcu7t5v0__udp_*_iq_*).
//       Pin order is preserved: (Q, C, P, CK, D, N).
//       `hn` = P (preset) dominates over C (clear)
//       `n`  = C (clear) dominates over P (preset)  (normal)

primitive udp_iq_ff_hn ( Q, C, P, CK, D, N );
output Q;
reg Q;
input C, P, CK, D, N;
table
// C  P  CK D  N  :  Q  :  Q
   0  0  n  ?  ?  :  ?  :  -;
   ?  0  r  0  ?  :  ?  :  0;
   ?  0  p  0  ?  :  0  :  0;
   1  0  ?  ?  ?  :  ?  :  0;
   0  ?  r  1  ?  :  ?  :  1;
   0  ?  p  1  ?  :  1  :  1;
   ?  1  ?  ?  ?  :  ?  :  1;
   0  0  ?  *  ?  :  ?  :  -;
   ?  ?  ?  ?  *  :  ?  :  x;
   0  n  ?  ?  ?  :  ?  :  -;
   n  0  ?  ?  ?  :  ?  :  -;
   0  p  ?  ?  ?  :  ?  :  -;
endtable
endprimitive

primitive udp_iq_ff_n ( Q, C, P, CK, D, N );
output Q;
reg Q;
input C, P, CK, D, N;
table
// C  P  CK D  N  :  Q  :  Q
   0  0  n  ?  ?  :  ?  :  -;
   ?  0  r  0  ?  :  ?  :  0;
   ?  0  p  0  ?  :  0  :  0;
   1  0  ?  ?  ?  :  ?  :  0;
   0  ?  r  1  ?  :  ?  :  1;
   0  ?  p  1  ?  :  1  :  1;
   0  1  ?  ?  ?  :  ?  :  1;
   ?  ?  ?  ?  *  :  ?  :  x;
   0  0  ?  *  ?  :  ?  :  -;
   0  n  ?  ?  ?  :  ?  :  -;
   n  0  ?  ?  ?  :  ?  :  -;
   0  p  ?  ?  ?  :  ?  :  -;
endtable
endprimitive

primitive udp_iq_latch_hn ( Q, C, P, CK, D, N );
output Q;
reg Q;
input C, P, CK, D, N;
table
// C    P    CK   D    N  :  Q  :  Q
   0    0    0    *    ?  :  ?  :  -;
   0    0    (?0) ?    ?  :  ?  :  -;
   0    (?0) 0    ?    ?  :  ?  :  -;
   (?0) 0    0    ?    ?  :  ?  :  -;
   ?    0    1    0    ?  :  ?  :  0;
   ?    0    ?    (?0) ?  :  0  :  0;
   ?    (?0) ?    0    ?  :  0  :  0;
   1    0    ?    ?    ?  :  ?  :  0;
   0    ?    1    1    ?  :  ?  :  1;
   0    ?    ?    (?1) ?  :  1  :  1;
   (?0) ?    ?    1    ?  :  1  :  1;
   ?    1    ?    ?    ?  :  ?  :  1;
   ?    ?    ?    ?    *  :  ?  :  x;
endtable
endprimitive

primitive udp_iq_latch_n ( Q, C, P, CK, D, N );
output Q;
reg Q;
input C, P, CK, D, N;
table
// C    P    CK   D    N  :  Q  :  Q
   0    0    0    *    ?  :  ?  :  -;
   0    0    (?0) ?    ?  :  ?  :  -;
   0    (?0) 0    ?    ?  :  ?  :  -;
   (?0) 0    0    ?    ?  :  ?  :  -;
   ?    0    1    0    ?  :  ?  :  0;
   ?    0    ?    (?0) ?  :  0  :  0;
   ?    (?0) ?    0    ?  :  0  :  0;
   1    0    ?    ?    ?  :  ?  :  0;
   0    ?    1    1    ?  :  ?  :  1;
   0    ?    ?    (?1) ?  :  1  :  1;
   (?0) ?    ?    1    ?  :  1  :  1;
   0    1    ?    ?    ?  :  ?  :  1;
   ?    ?    ?    ?    *  :  ?  :  x;
endtable
endprimitive

'''
