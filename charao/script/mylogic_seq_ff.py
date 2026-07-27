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
    # DFF_PC: D + posedge CLK + Q (no reset/set, single Q output).
    #   GF180 target: dffq_1/2/4. Verilog primitive: udp_iq_ff_n (Q, C=0, P=0, CK, D, N).
    #   Pin mapping (charao internal logic ports):
    #     o0 = Q   (output)
    #     i0 = D   (data input)
    #     c0 = CLK (clock, posedge)
    #   ports_dict example: {"D":"i0","CLK":"c0","Q":"o0",...}
    "DFF_PC":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"i0",
                 "clocked_on":"c0"},
           "vcode":"reg notifier; udp_iq_ff_n inst (o0, 1'b0, 1'b0, c0, i0, notifier);",
           "expect":
           [
             #--- q delay (clk -> q) + power_tout  #ISS-00135: CLK-on-VREL 複製廃止（dffrsnq 新方式に統一）
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);", timing_default=True),
             #--- power_tin pin(CLK) when:"!D" - CLK 変化、 D=0 stable、 Q=0 stable
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D" - CLK 変化、 D=1 stable、 Q=1 stable
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK" - D 変化、 CLK=0 stable、 Q 不変
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK" - D 変化、 CLK=1 stable、 Q 不変
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["r"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0", specify=""),
             #--- setup
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["r"],"b":[],"c":["p"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","f","","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["f"],"b":[],"c":["p"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","r","","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- passive power (data)  -- CLK 静止 L
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="", specify=""),
             #--- passive power (clk)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             #--- min_pulse (clk)  #ISS-00135: dffrsnq 新方式（単一 entry、 when 分割は ISS-00082）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_low (clk)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"]}
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","r","","n"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- leakage (4 conditions: !D&!CLK / !D&CLK / D&!CLK / D&CLK)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["p"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["r"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["p"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["r"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0", specify="", power_default=True),
           ]
    },
    #---------------------------------------------------------------------------------------
    # DFF_NC: D + negedge CLKN + Q (no reset/set, single Q output).
    #   GF180 target: dffnq_1/2/4.
    #   Pin mapping (charao internal logic ports):
    #     o0 = Q    (output)
    #     i0 = D    (data input)
    #     c0 = CLKN (clock, negedge — internally inverted then fed to udp_iq_ff_n)
    #   ports_dict example: {"D":"i0","CLKN":"c0","Q":"o0",...}
    # GF180 target: dffnq_1/2/4.
    # Internal: CLKN -> not -> CLK_int -> udp_iq_ff_n (posedge primitive), D -> not -> D_int,
    #           udp_iq_ff_n outputs iq1 (= !D), then not gate -> Q (= D).
    "DFF_NC":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"i0",
                 "clocked_on":"(!c0)"},
           "vcode":"reg notifier; wire clkn_int; wire d_int; wire iq1; not (clkn_int, c0); not (d_int, i0); udp_iq_ff_n inst (iq1, 1'b0, 1'b0, clkn_int, d_int, notifier); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clkn negedge -> q) + power_tout  #ISS-00135: CLK-on-VREL 複製廃止（dffrsnq 新方式に統一）
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"]}
                         ,meas_types=["falling_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"]}
                         ,meas_types=["falling_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="", specify="(negedge c0 => (o0 +: i0)) =(0,0);", timing_default=True),
             #--- power_tin pin(CLKN) when:"!D" - CLKN 変化、 D=0 stable、 Q=0 stable
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLKN) when:"D" - CLKN 変化、 D=1 stable、 Q=1 stable
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLKN" - D 変化、 CLKN=0 stable、 Q 不変
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLKN" - D 変化、 CLKN=1 stable、 Q 不変
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","n"], tmg_when="c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","n"], tmg_when="c0", specify=""),
             #--- setup
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["r"],"b":[],"c":["n"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["r","f","","f"], tmg_when="", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["f"],"b":[],"c":["n"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["f","r","","f"], tmg_when="", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- passive power (data) -- CLKN 静止 H
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="", specify=""),
             #--- passive power (clkn)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             #--- min_pulse (clkn)  #ISS-00135: dffrsnq 新方式（単一 entry、 when 分割は ISS-00082）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_low (clkn)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"]}
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","r","","n"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- leakage (4 conditions: !D&CLKN / !D&!CLKN / D&CLKN / D&!CLKN)  (CLKN polarity reversed vs CLK)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["n"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["f"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["n"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["f"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0", specify="", power_default=True),
           ]
    },
    #---------------------------------------------------------------------------------------
    # DFF_PC_NR: D + posedge CLK + active-low reset RN + Q (single Q output).
    #   GF180 target: dffrnq_1/2/4.
    #   Pin mapping (charao internal logic ports):
    #     o0 = Q   (output)
    #     i0 = D   (data input)
    #     c0 = CLK (clock, posedge)
    #     r0 = RN  (reset, active-low — Q=0 when RN=0)
    #   ports_dict example: {"D":"i0","RN":"r0","CLK":"c0","Q":"o0",...}
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
           "vcode":"reg notifier; wire p_int; wire d_int; wire iq1; not (p_int, r0); not (d_int, i0); udp_iq_ff_n inst (iq1, 1'b0, p_int, c0, d_int, notifier); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clk -> q) -- RN=1 (non-reset) + power_tout  #ISS-00135: CLK-on-VREL 複製廃止（dffrsnq 新方式に統一）
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);", timing_default=True),
             #--- power_tin pin(CLK) when:"!D" - CLK 変化、 D=0 stable、 Q=0 stable (RN inactive)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D"
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK" - D 変化、 CLK=0 stable
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0", specify=""),
             #--- clear (RN fall -> Q fall, async)
             MyExpectCell(pin_tr=["o0","r0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","1","f","0"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- setup (D -> CLK rising edge)
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="r0", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="r0", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["r"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","f","","r"], tmg_when="r0", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["f"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","r","","r"], tmg_when="r0", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery (RN rise -> CLK rise)  #ISS-00135: rel=r0 / VIN=i0(D) 駆動（dffrsnq 方式）
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["r","1","r","r"], tmg_when="", specify="$recovery(posedge r0, posedge c0, 0, notifier);"),
             #--- removal (CLK rise after RN rise, arc same as recovery)
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["r","1","r","r"], tmg_when="", specify="$removal(posedge r0, posedge c0, 0, notifier);"),
             #--- passive power (data) -- CLK static L, RN=1
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="", specify=""),
             #--- passive power (reset)
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","0"], tmg_when="", specify=""),
             #--- passive power (clk)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             #--- min_pulse (clk)  #ISS-00135: dffrsnq 新方式（単一 entry、 when 分割は ISS-00082）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_low (clk)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"r":["1"]}
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","r","","n"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (reset) -- RN L pulse
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","1","n","0"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- leakage (8 conditions: i0 x c0 x r0)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["p"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["p"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["r"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["r"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"c":["p"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","0"],tmg_when="i0&!c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["p"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"c":["r"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","1"],tmg_when="i0&c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["r"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&r0", specify="", power_default=True),
           ]
    },
    #---------------------------------------------------------------------------------------
    # DFF_PC_NS: D + posedge CLK + active-low set SETN + Q (single Q output).
    #   GF180 target: dffsnq_1/2/4.
    #   Pin mapping (charao internal logic ports):
    #     o0 = Q    (output)
    #     i0 = D    (data input)
    #     c0 = CLK  (clock, posedge)
    #     s0 = SETN (set, active-low — Q=1 when SETN=0)
    #   ports_dict example: {"D":"i0","SETN":"s0","CLK":"c0","Q":"o0",...}
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
           "vcode":"reg notifier; wire c_int; wire d_int; wire iq1; not (c_int, s0); not (d_int, i0); udp_iq_ff_n inst (iq1, c_int, 1'b0, c0, d_int, notifier); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clk -> q) -- SETN=1 (non-set)  #ISS-00135: CLK-on-VREL 複製廃止（dffrsnq 新方式に統一）
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"s":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);", timing_default=True),
             #--- power_tin pin(CLK) when:"!D" (SETN inactive)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D"
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0", specify=""),
             #--- preset (SETN fall -> Q rise, async)
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","0","f","0"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="s0", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="s0", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["r"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","f","","r"], tmg_when="s0", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["f"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","r","","r"], tmg_when="s0", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery (SETN rise -> CLK rise)  #ISS-00135: rel=s0 / VIN=i0(D) 駆動（dffrsnq 方式）
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["p"],"s":["0"]}
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["f","0","r","r"], tmg_when="", specify="$recovery(posedge s0, posedge c0, 0, notifier);"),
             #--- removal
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["p"],"s":["0"]}
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["f","0","r","r"], tmg_when="", specify="$removal(posedge s0, posedge c0, 0, notifier);"),
             #--- passive (data) -- CLK static L, SETN=1
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="", specify=""),
             #--- passive (set)
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"s":["0"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","r","r","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","f","0"], tmg_when="", specify=""),
             #--- passive (clk)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             #--- min_pulse (clk)  #ISS-00135: dffrsnq 新方式（単一 entry、 when 分割は ISS-00082）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_low (clk)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","r","","n"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (set)
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","0","n","0"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (8 conditions: i0 x c0 x s0)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"c":["p"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","0"],tmg_when="!i0&!c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["p"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"c":["r"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","1"],tmg_when="!i0&c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["r"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["p"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["p"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["r"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["r"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&s0", specify="", power_default=True),
           ]
    },
    #---------------------------------------------------------------------------------------
    # DFF_NC_NR: D + negedge CLKN + active-low reset RN + Q (single Q output).
    #   GF180 target: dffnrnq_1/2/4.
    #   Pin mapping (charao internal logic ports):
    #     o0 = Q    (output)
    #     i0 = D    (data input)
    #     c0 = CLKN (clock, negedge)
    #     r0 = RN   (reset, active-low — Q=0 when RN=0)
    #   ports_dict example: {"D":"i0","RN":"r0","CLKN":"c0","Q":"o0",...}
    # GF180 target: dffnrnq_1/2/4.
    "DFF_NC_NR":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"i0",
                 "clocked_on":"(!c0)",
                 "clear":"(!r0)"},
           "vcode":"reg notifier; wire clkn_int; wire p_int; wire d_int; wire iq1; not (clkn_int, c0); not (p_int, r0); not (d_int, i0); udp_iq_ff_n inst (iq1, 1'b0, p_int, clkn_int, d_int, notifier); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clkn neg -> q) + power_tout  #ISS-00135: CLK-on-VREL 複製廃止（dffrsnq 新方式に統一）
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"]}
                         ,meas_types=["falling_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"]}
                         ,meas_types=["falling_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="", specify="(negedge c0 => (o0 +: i0)) =(0,0);", timing_default=True),
             #--- power_tin pin(CLKN) when:"!D" (RN inactive)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLKN) when:"D"
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLKN"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLKN"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","n"], tmg_when="c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","n"], tmg_when="c0", specify=""),
             #--- clear
             MyExpectCell(pin_tr=["o0","r0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","1","f","1"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- setup
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="r0", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="r0", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["r"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["r","f","","f"], tmg_when="r0", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["f"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["f","r","","f"], tmg_when="r0", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- recovery (RN rise -> CLKN fall)  #ISS-00135: rel=r0 / VIN=i0(D) 駆動（dffrsnq 方式）
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["n"],"r":["0"]}
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["r","1","r","f"], tmg_when="", specify="$recovery(posedge r0, negedge c0, 0, notifier);"),
             #--- removal
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["n"],"r":["0"]}
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["r","1","r","f"], tmg_when="", specify="$removal(posedge r0, negedge c0, 0, notifier);"),
             #--- passive (data) -- CLKN static H, RN=1
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="", specify=""),
             #--- passive (reset)
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["0"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","1"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","1"], tmg_when="", specify=""),
             #--- passive (clkn)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             #--- min_pulse_high (clkn)  #ISS-00135: dffrsnq 新方式（単一 entry、 when 分割は ISS-00082）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse (clkn) -- L pulse 完了で H 終了
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","r","","n"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (reset)
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","1","n","1"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- leakage (8 conditions: i0 x c0 x r0)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["n"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["n"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["f"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["f"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"c":["n"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","1"],tmg_when="i0&c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["n"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"c":["f"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","0"],tmg_when="i0&!c0&!r0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["f"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&r0", specify="", power_default=True),
           ]
    },
    #---------------------------------------------------------------------------------------
    # DFF_NC_NS: D + negedge CLKN + active-low set SETN + Q (single Q output).
    #   GF180 target: dffnsnq_1/2/4.
    #   Pin mapping (charao internal logic ports):
    #     o0 = Q    (output)
    #     i0 = D    (data input)
    #     c0 = CLKN (clock, negedge)
    #     s0 = SETN (set, active-low — Q=1 when SETN=0)
    #   ports_dict example: {"D":"i0","SETN":"s0","CLKN":"c0","Q":"o0",...}
    # GF180 target: dffnsnq_1/2/4.
    "DFF_NC_NS":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"i0",
                 "clocked_on":"(!c0)",
                 "preset":"(!s0)"},
           "vcode":"reg notifier; wire clkn_int; wire c_int; wire d_int; wire iq1; not (clkn_int, c0); not (c_int, s0); not (d_int, i0); udp_iq_ff_n inst (iq1, c_int, 1'b0, clkn_int, d_int, notifier); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clkn neg -> q) + power_tout  #ISS-00135: CLK-on-VREL 複製廃止（dffrsnq 新方式に統一）
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"s":["1"]}
                         ,meas_types=["falling_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"s":["1"]}
                         ,meas_types=["falling_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="", specify="(negedge c0 => (o0 +: i0)) =(0,0);", timing_default=True),
             #--- power_tin pin(CLKN) when:"!D" (SETN inactive)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLKN) when:"D"
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLKN"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLKN"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","n"], tmg_when="c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","n"], tmg_when="c0", specify=""),
             #--- preset
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","0","f","1"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="s0", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="s0", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["r"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["r","f","","f"], tmg_when="s0", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["f"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["f","r","","f"], tmg_when="s0", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- recovery (SETN rise -> CLKN fall)  #ISS-00135: rel=s0 / VIN=i0(D) 駆動（dffrsnq 方式）
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["n"],"s":["0"]}
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["f","0","r","f"], tmg_when="", specify="$recovery(posedge s0, negedge c0, 0, notifier);"),
             #--- removal
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["n"],"s":["0"]}
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["f","0","r","f"], tmg_when="", specify="$removal(posedge s0, negedge c0, 0, notifier);"),
             #--- passive (data) -- CLKN static H, SETN=1
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="", specify=""),
             #--- passive (set)
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"s":["0"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","r","r","1"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","f","1"], tmg_when="", specify=""),
             #--- passive (clkn)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             #--- min_pulse_high (clkn)  #ISS-00135: dffrsnq 新方式（単一 entry、 when 分割は ISS-00082）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"s":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse (clkn)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","r","","n"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (set)
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","0","n","1"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (8 conditions: i0 x c0 x s0)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"c":["n"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","1"],tmg_when="!i0&c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["n"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"c":["f"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","0"],tmg_when="!i0&!c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["f"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["n"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["n"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["f"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["f"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&s0", specify="", power_default=True),
           ]
    },
    #---------------------------------------------------------------------------------------
    # DFF_PC_NR_NS: D + posedge CLK + active-low reset RN + active-low set SETN + Q.
    #   GF180 target: dffrsnq_1/2/4. Verilog primitive: udp_iq_ff_hn.
    #   Pin mapping (charao internal logic ports):
    #     o0 = Q    (output)
    #     i0 = D    (data input)
    #     c0 = CLK  (clock, posedge)
    #     r0 = RN   (reset, active-low — Q=0 when RN=0; reset has priority over set)
    #     s0 = SETN (set,   active-low — Q=1 when SETN=0)
    #   ports_dict example: {"D":"i0","RN":"r0","SETN":"s0","CLK":"c0","Q":"o0",...}
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
           "vcode":"reg notifier; wire p_int; wire c_int; wire d_int; wire iq1; not (p_int, r0); not (c_int, s0); not (d_int, i0); udp_iq_ff_hn inst (iq1, c_int, p_int, c0, d_int, notifier); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clk -> q) -- RN=1, SETN=1 + power_tout  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                         ,meas_types=["rising_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);", timing_default=True),
             #--- power_tin pin(CLK) when:"!D" (RN/SETN inactive)  #ISS-00101: mondrv_oirc 省略 / ISS-00127: pin_tr=[c0,""] 明示（target=CLK）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D"
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK"  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0", specify=""),
             #--- clear (RN fall)  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["o0","r0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","1","f","0"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- preset (SETN fall)  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","0","f","0"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="r0&s0", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="r0&s0", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["r"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["r","f","","r"], tmg_when="r0&s0", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["f"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oirc=["f","r","","r"], tmg_when="r0&s0", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery reset  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["p"],"r":["0"],"s":["1"]}
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["r","1","r","r"], tmg_when="s0", specify="$recovery(posedge r0, posedge c0, 0, notifier);"),
             #--- recovery set
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["p"],"r":["1"],"s":["0"]}
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oirc=["f","0","r","r"], tmg_when="r0", specify="$recovery(posedge s0, posedge c0, 0, notifier);"),
             #--- removal reset  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["p"],"r":["0"],"s":["1"]}
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["r","1","r","r"], tmg_when="s0", specify="$removal(posedge r0, posedge c0, 0, notifier);"),
             #--- removal set
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["p"],"r":["1"],"s":["0"]}
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oirc=["f","0","r","r"], tmg_when="r0", specify="$removal(posedge s0, posedge c0, 0, notifier);"),
             #--- passive (data) -- CLK static L, RN=1, SETN=1  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="", specify=""),
             #--- passive (reset) -- RN toggles (output static), SETN=1
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["0"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","0"], tmg_when="", specify=""),
             #--- passive (set) -- SETN toggles (output static), RN=1
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"],"s":["0"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","r","r","0"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","f","0"], tmg_when="", specify=""),
             #--- passive (clk) -- CLK toggles (output static)  #ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             #--- min_pulse (clk)  #ISS-00101: mondrv_oirc 省略、 ival[c]=p / arc[r,c]=p,p で CLK H pulse 表現 / ISS-00127: pin_tr=[c0,""]
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse_low (clk)  #ISS-00101: mondrv_oirc 省略、 ival[c]=r / arc[r,c]=n,n で CLK L pulse 表現 / ISS-00127: pin_tr=[c0,""]
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"],tmg_sense="non",arc_oirc=["r","r","","n"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (reset)  #ISS-00101: mondrv_oirc 省略、 ival[c]=p（init で CLK pulse 内部状態確立）/ arc[r,c]=n,0 / ISS-00127: pin_tr=[r0,""]
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","1","n","0"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- min_pulse (set)   #ISS-00101: mondrv_oirc 省略、 ival[c]=p / arc[r,c]=n,0 / ISS-00127: pin_tr=[s0,""]
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","0","n","0"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (16: r=0[Q=L,8] / r=1&s=0[Q=H,4] / r=1&s=1[Q=i0,4])
             #     #ISS-00101: mondrv_oirc 省略、 ival[c]: c0=0→p (init pulse), c0=1→r (init rise) / arc[c]: c0=0→0, c0=1→1
             # Group 1: r=0 (reset active, Q=L)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["p"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!r0&!s0&!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["r"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!r0&!s0&!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"c":["p"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","0"],tmg_when="!r0&!s0&i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"c":["r"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","1"],tmg_when="!r0&!s0&i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["p"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!r0&s0&!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["r"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!r0&s0&!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"c":["p"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","0"],tmg_when="!r0&s0&i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"c":["r"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","1"],tmg_when="!r0&s0&i0&c0", specify=""),
             # Group 2: r=1, s=0 (set active, Q=H)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"c":["p"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","0"],tmg_when="r0&!s0&!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"c":["r"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","1"],tmg_when="r0&!s0&!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["p"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="r0&!s0&i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["r"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="r0&!s0&i0&c0", specify=""),
             # Group 3: r=1, s=1 (hold, Q=i0)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="r0&s0&!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="r0&s0&!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["p"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="r0&s0&i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["r"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="r0&s0&i0&c0", specify="", power_default=True),
           ]
    },

    #---------------------------------------------------------------------------------------
    # DFF_NC_NR_NS: D + negedge CLKN + active-low reset RN + active-low set SETN + Q.
    #   GF180 target: dffnrsnq_1/2/4. Verilog primitive: udp_iq_ff_hn.
    #   Pin mapping (charao internal logic ports):
    #     o0 = Q    (output)
    #     i0 = D    (data input)
    #     c0 = CLKN (clock, negedge)
    #     r0 = RN   (reset, active-low — Q=0 when RN=0; reset has priority over set)
    #     s0 = SETN (set,   active-low — Q=1 when SETN=0)
    #   ports_dict example: {"D":"i0","RN":"r0","SETN":"s0","CLKN":"c0","Q":"o0",...}
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
           "vcode":"reg notifier; wire clkn_int; wire p_int; wire c_int; wire d_int; wire iq1; not (clkn_int, c0); not (p_int, r0); not (c_int, s0); not (d_int, i0); udp_iq_ff_hn inst (iq1, c_int, p_int, clkn_int, d_int, notifier); not (o0, iq1);",
           "expect":
           [
             #--- q delay (clkn neg -> q) + power_tout  #ISS-00135: CLK-on-VREL 複製廃止（dffrsnq 新方式に統一）
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                         ,meas_types=["falling_edge","power_tout"] ,tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                         ,meas_types=["falling_edge","power_tout"] ,tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="", specify="(negedge c0 => (o0 +: i0)) =(0,0);", timing_default=True),
             #--- power_tin pin(CLKN) when:"!D" (RN/SETN inactive)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLKN) when:"D"
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLKN"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLKN"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["0","r","","n"], tmg_when="c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["1","f","","n"], tmg_when="c0", specify=""),
             #--- clear
             MyExpectCell(pin_tr=["o0","r0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oirc=["f","1","f","1"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- preset
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oirc=["r","0","f","1"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- setup
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["r","r","","f"], tmg_when="r0&s0", specify="$setup(posedge i0, negedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["setup_falling"] ,tmg_sense="non",arc_oirc=["f","f","","f"], tmg_when="r0&s0", specify="$setup(negedge i0, negedge c0, 0, notifier);"),
             #--- hold
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["r"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["r","f","","f"], tmg_when="r0&s0", specify="$hold(negedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["f"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["hold_falling"],tmg_sense="non",arc_oirc=["f","r","","f"], tmg_when="r0&s0", specify="$hold(negedge c0, posedge i0, 0, notifier);"),
             #--- recovery reset  #ISS-00135: rel=r0 / VIN=i0(D) 駆動（dffrsnq 方式）
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["n"],"r":["0"],"s":["1"]}
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["r","1","r","f"], tmg_when="s0", specify="$recovery(posedge r0, negedge c0, 0, notifier);"),
             #--- recovery set
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["n"],"r":["1"],"s":["0"]}
                       ,meas_types=["recovery_falling"],tmg_sense="pos",arc_oirc=["f","0","r","f"], tmg_when="r0", specify="$recovery(posedge s0, negedge c0, 0, notifier);"),
             #--- removal reset
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["n"],"r":["0"],"s":["1"]}
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["r","1","r","f"], tmg_when="s0", specify="$removal(posedge r0, negedge c0, 0, notifier);"),
             #--- removal set
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["n"],"r":["1"],"s":["0"]}
                        ,meas_types=["removal_falling"],tmg_sense="non",arc_oirc=["f","0","r","f"], tmg_when="r0", specify="$removal(posedge s0, negedge c0, 0, notifier);"),
             #--- passive (data) -- CLKN static H, RN=1, SETN=1
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="", specify=""),
             #--- passive (reset) -- RN toggles (output static), SETN=1
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["0"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","1"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","r0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","r","r","1"], tmg_when="", specify=""),
             #--- passive (set) -- SETN toggles (output static), RN=1
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"],"s":["0"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","r","r","1"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","s0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["1","f","f","1"], tmg_when="", specify=""),
             #--- passive (clkn) -- CLKN toggles (output static)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="", specify=""),
             #--- min_pulse_high (clkn)  #ISS-00135: dffrsnq 新方式（単一 entry、 when 分割は ISS-00082）
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse (clkn)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","r","","n"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             #--- min_pulse (reset)
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["f","1","n","1"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- min_pulse (set)
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oirc=["r","0","n","1"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             #--- leakage (16 conditions: i0 x c0 x r0 x s0)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["n"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["n"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"c":["n"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!i0&c0&r0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["f"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["f"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["0"],"c":["f"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["0"],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!i0&!c0&r0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"c":["n"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"c":["n"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["n"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["n"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="i0&c0&r0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"c":["f"],"r":["0"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&!r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0"],"i":["1"],"c":["f"],"r":["0"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&!r0&s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["f"],"r":["1"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&r0&!s0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1"],"i":["1"],"c":["f"],"r":["1"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="i0&!c0&r0&s0", specify="", power_default=True),
           ]
    },

  #==========================================================================================================================================================
  #Q,QB
    #---------------------------------------------------------------------------------------
    # DFFB_PC_PR: D + posedge CLK + active-high reset R + Q + QB (differential output).
    #   Pin mapping (charao internal logic ports):
    #     o0 = Q   (output, normal)
    #     o1 = QB  (output, inverted)
    #     i0 = D   (data input)
    #     c0 = CLK (clock, posedge)
    #     r0 = R   (reset, active-high — Q=0, QB=1 when R=1)
    #   ports_dict example: {"D":"i0","R":"r0","CLK":"c0","Q":"o0","QB":"o1",...}
    "DFFB_PC_PR":{
           "logic_type":"seq",
           "functions":{"o0":"Io0","o1":"Io1"},
           "ff":{"out":"Io0,Io1",
                 "next_state":"i0",
                 "clocked_on":"c0",
                 "clear":"(r0)"},
           "expect":
           [
             #--- q delay (clk -> o0/o1) -- R inactive (active-high R=L)  #ISS-00135: CLK-on-VREL 複製廃止（dffrsnq 新方式に統一）
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["rising_edge"], tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["rising_edge"], tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);", timing_default=True),
             MyExpectCell(pin_tr=["o1","c0"], pin_oirc=["o1","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["rising_edge"], tmg_sense="non",arc_oirc=["r","f","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o1","c0"], pin_oirc=["o1","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["rising_edge"], tmg_sense="non",arc_oirc=["f","r","","r"], tmg_when="", specify="(posedge c0 => (o1 +: i0)) =(0,0);", timing_default=True),
             #--- power_tin pin(CLK) when:"!D" (R inactive)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["r"],"r":["0"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D"
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["r"],"r":["0"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["r"],"r":["0"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["r"],"r":["0"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0", specify=""),
             #--- clear (R rise, active-high) -- o0=Q fall
             MyExpectCell(pin_tr=["o0","r0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["clear"], tmg_sense="neg",arc_oirc=["f","1","r","0"], tmg_when="", specify="(posedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- preset (同じ R rise で o1=QB rise、 Q の補集合)
             MyExpectCell(pin_tr=["o1","r0"], pin_oirc=["o1","i0","r0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["preset"], tmg_sense="pos",arc_oirc=["r","1","r","0"], tmg_when="", specify="(posedge r0 => (o1 +: 1'b1)) = (0,0);"),

             #--- setup (D vs CLK constraint)、 o0/o1 並列  #ISS-00135: 新方式 + when=async inactive
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["setup_rising"], tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="!r0", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["setup_rising"], tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="!r0", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o1","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["setup_rising"], tmg_sense="non",arc_oirc=["f","r","","r"], tmg_when="!r0", specify=""),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o1","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["setup_rising"], tmg_sense="non",arc_oirc=["r","f","","r"], tmg_when="!r0", specify=""),

             #--- hold (D vs CLK constraint)、 o0/o1 並列  #ISS-00135: 新方式（hold は ival/arc を D 状態で入替）
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["r"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["hold_rising"], tmg_sense="non",arc_oirc=["r","f","","r"], tmg_when="!r0", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["f"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["hold_rising"], tmg_sense="non",arc_oirc=["f","r","","r"], tmg_when="!r0", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o1","i0","","c0"], ival={"o":["0","1"],"i":["r"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["hold_rising"], tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="!r0", specify=""),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o1","i0","","c0"], ival={"o":["1","0"],"i":["f"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["hold_rising"], tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="!r0", specify=""),
             #--- recovery (R inactiv = fall, active-high R)、 o0/o1 並列  #ISS-00135: rel=r0 / VIN=i0(D) 駆動（dffrsnq 方式）
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0","1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["recovery_rising"], tmg_sense="pos",arc_oirc=["r","1","f","r"], tmg_when="", specify="$recovery(negedge r0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o1","i0","r0","c0"], ival={"o":["0","1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["recovery_rising"], tmg_sense="pos",arc_oirc=["f","1","f","r"], tmg_when="", specify=""),
             #--- removal (R inactiv = fall, active-high R、 arc は recovery と同型)、 o0/o1 並列
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o0","i0","r0","c0"], ival={"o":["0","1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["removal_rising"], tmg_sense="non",arc_oirc=["r","1","f","r"], tmg_when="", specify="$removal(negedge r0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["r0","c0"], pin_oirc=["o1","i0","r0","c0"], ival={"o":["0","1"],"i":["1"],"b":[],"c":["p"],"r":["1"]}
                        ,meas_types=["removal_rising"], tmg_sense="non",arc_oirc=["f","1","f","r"], tmg_when="", specify=""),

             #--- passive 削除（ISS-00120：output ありセルは他 measure 副産物で c_in 取得、 SPEC_measure.md §9 方針）
             #--- min_pulse_width_high (CLK high)、 o0/o1 並列  #ISS-00135: 新方式
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["min_pulse_width_high"], tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o1","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["min_pulse_width_high"], tmg_sense="non",arc_oirc=["f","r","","p"], tmg_when="", specify=""),
             #--- min_pulse_width_low (CLK low)、 o0/o1 並列
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["1"],"b":[],"c":["r"],"r":["0"]}
                        ,meas_types=["min_pulse_width_low"], tmg_sense="non",arc_oirc=["r","r","","n"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o1","i0","","c0"], ival={"o":["0","1"],"i":["1"],"b":[],"c":["r"],"r":["0"]}
                        ,meas_types=["min_pulse_width_low"], tmg_sense="non",arc_oirc=["f","r","","n"], tmg_when="", specify=""),
             #--- min_pulse_width_high (R high、 active-high R の clear pulse)、 o0/o1 並列
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o0","i0","r0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["min_pulse_width_high"], tmg_sense="non",arc_oirc=["f","1","p","0"], tmg_when="", specify="$width(posedge r0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["r0",""], pin_oirc=["o1","i0","r0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"r":["0"]}
                        ,meas_types=["min_pulse_width_high"], tmg_sense="non",arc_oirc=["r","1","p","0"], tmg_when="", specify=""),
             #--- leakage (R/D/CLK 3 bit = 8 state、 出力 2 個維持、 R active-high)  #ISS-00135: slot2 複製廃止
             # Group 1: R=0 (R inactive、 Q=D 値)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"c":["p"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="!r0&!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"c":["r"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="!r0&!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"c":["p"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="!r0&i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"c":["r"],"r":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="!r0&i0&c0", specify=""),
             # Group 2: R=1 (R active = Q clear、 Q=L 強制)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"c":["p"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="r0&!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"c":["r"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="r0&!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["1"],"c":["p"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","0"],tmg_when="r0&i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["1"],"c":["r"],"r":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","1","","1"],tmg_when="r0&i0&c0", specify="", power_default=True),
           ]
    },

    #---------------------------------------------------------------------------------------
    # DFFB_PC_NS: D + posedge CLK + active-low set SETN + Q + QB (differential output).
    #   Pin mapping (charao internal logic ports):
    #     o0 = Q    (output, normal)
    #     o1 = QB   (output, inverted)
    #     i0 = D    (data input)
    #     c0 = CLK  (clock, posedge)
    #     s0 = SETN (set, active-low — Q=1, QB=0 when SETN=0)
    #   ports_dict example: {"D":"i0","SETN":"s0","CLK":"c0","Q":"o0","QB":"o1",...}
    "DFFB_PC_NS":{
           "logic_type":"seq",
           "functions":{"o0":"Io0","o1":"Io1"},
           "ff":{"out":"Io0,Io1",
                 "next_state":"i0",
                 "clocked_on":"c0",
                 "preset":"(!s0)"},
           "expect":
           [
             #--- q delay (clk -> o0/o1) -- SETN inactive (active-low SETN=H)  #ISS-00135: CLK-on-VREL 複製廃止（dffrsnq 新方式に統一）
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["rising_edge"], tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["rising_edge"], tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);", timing_default=True),
             MyExpectCell(pin_tr=["o1","c0"], pin_oirc=["o1","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["rising_edge"], tmg_sense="non",arc_oirc=["r","f","","r"], tmg_when="", specify=""),
             MyExpectCell(pin_tr=["o1","c0"], pin_oirc=["o1","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["rising_edge"], tmg_sense="non",arc_oirc=["f","r","","r"], tmg_when="", specify="(posedge c0 => (o1 +: i0)) =(0,0);", timing_default=True),
             #--- power_tin pin(CLK) when:"!D" (SETN inactive)
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["0","0","","r"], tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["0","0","","f"], tmg_when="!i0", specify=""),
             #--- power_tin pin(CLK) when:"D"
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["1","1","","r"], tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["1","1","","f"], tmg_when="i0", specify=""),
             #--- power_tin pin(D) when:"!CLK"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["0","r","","0"], tmg_when="!c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["1","f","","0"], tmg_when="!c0", specify=""),
             #--- power_tin pin(D) when:"CLK"
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["0","r","","1"], tmg_when="c0", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["power_tin"], tmg_sense="non",arc_oirc=["1","f","","1"], tmg_when="c0", specify=""),

             #--- preset (SETN fall, active-low SETN) -- o0=Q rise
             MyExpectCell(pin_tr=["o0","s0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["preset"], tmg_sense="neg",arc_oirc=["r","0","f","0"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             #--- clear (同じ SETN fall で o1=QB fall、 Q の補集合)
             MyExpectCell(pin_tr=["o1","s0"], pin_oirc=["o1","i0","s0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["clear"], tmg_sense="pos",arc_oirc=["f","0","f","0"], tmg_when="", specify="(negedge s0 => (o1 +: 1'b0)) = (0,0);"),

             #--- setup (D vs CLK constraint)、 o0/o1 並列  #ISS-00135: 新方式 + when=async inactive
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["setup_rising"], tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="s0", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["setup_rising"], tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="s0", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o1","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["setup_rising"], tmg_sense="non",arc_oirc=["f","r","","r"], tmg_when="s0", specify=""),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o1","i0","","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["setup_rising"], tmg_sense="non",arc_oirc=["r","f","","r"], tmg_when="s0", specify=""),

             #--- hold (D vs CLK constraint)、 o0/o1 並列  #ISS-00135: 新方式（hold は ival/arc を D 状態で入替）
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["r"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["hold_rising"], tmg_sense="non",arc_oirc=["r","f","","r"], tmg_when="s0", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["f"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["hold_rising"], tmg_sense="non",arc_oirc=["f","r","","r"], tmg_when="s0", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o1","i0","","c0"], ival={"o":["0","1"],"i":["r"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["hold_rising"], tmg_sense="non",arc_oirc=["f","f","","r"], tmg_when="s0", specify=""),
             MyExpectCell(pin_tr=["i0","c0"], pin_oirc=["o1","i0","","c0"], ival={"o":["1","0"],"i":["f"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["hold_rising"], tmg_sense="non",arc_oirc=["r","r","","r"], tmg_when="s0", specify=""),

             #--- recovery (SETN rise = inactivation, active-low SETN)、 o0/o1 並列  #ISS-00135: rel=s0 / VIN=i0(D) 駆動（dffrsnq 方式）
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1","0"],"i":["0"],"b":[],"c":["p"],"s":["0"]}
                        ,meas_types=["recovery_rising"], tmg_sense="pos",arc_oirc=["f","0","r","r"], tmg_when="", specify="$recovery(posedge s0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o1","i0","s0","c0"], ival={"o":["1","0"],"i":["0"],"b":[],"c":["p"],"s":["0"]}
                        ,meas_types=["recovery_rising"], tmg_sense="pos",arc_oirc=["r","0","r","r"], tmg_when="", specify=""),
             #--- removal (SETN rise = inactivation、 arc は recovery と同型)、 o0/o1 並列
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o0","i0","s0","c0"], ival={"o":["1","0"],"i":["0"],"b":[],"c":["p"],"s":["0"]}
                        ,meas_types=["removal_rising"], tmg_sense="non",arc_oirc=["f","0","r","r"], tmg_when="", specify="$removal(posedge s0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_tr=["s0","c0"], pin_oirc=["o1","i0","s0","c0"], ival={"o":["1","0"],"i":["0"],"b":[],"c":["p"],"s":["0"]}
                        ,meas_types=["removal_rising"], tmg_sense="non",arc_oirc=["r","0","r","r"], tmg_when="", specify=""),

             #--- passive 削除（ISS-00120：output ありセルは他 measure 副産物で c_in 取得、 SPEC_measure.md §9 方針）
             #--- min_pulse_width_high (CLK high)、 o0/o1 並列  #ISS-00135: 新方式
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["min_pulse_width_high"], tmg_sense="non",arc_oirc=["r","r","","p"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o1","i0","","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["min_pulse_width_high"], tmg_sense="non",arc_oirc=["f","r","","p"], tmg_when="", specify=""),
             #--- min_pulse_width_low (CLK low)、 o0/o1 並列
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["1"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"], tmg_sense="non",arc_oirc=["r","r","","n"], tmg_when="", specify="$width(negedge c0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["c0",""], pin_oirc=["o1","i0","","c0"], ival={"o":["0","1"],"i":["1"],"b":[],"c":["r"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"], tmg_sense="non",arc_oirc=["f","r","","n"], tmg_when="", specify=""),
             #--- min_pulse_width_low (SETN low、 active-low SETN の preset pulse)、 o0/o1 並列
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o0","i0","s0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"], tmg_sense="non",arc_oirc=["r","0","n","0"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             MyExpectCell(pin_tr=["s0",""], pin_oirc=["o1","i0","s0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["p"],"s":["1"]}
                        ,meas_types=["min_pulse_width_low"], tmg_sense="non",arc_oirc=["f","0","n","0"], tmg_when="", specify=""),

             #--- leakage (S/D/CLK 3 bit = 8 state、 出力 2 個維持、 SETN active-low)  #ISS-00135: slot2 複製廃止
             # Group 1: S=0 (SETN active = preset、 Q=H 強制)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["0"],"c":["p"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","0"],tmg_when="!s0&!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["0"],"c":["r"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","0","","1"],tmg_when="!s0&!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"c":["p"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="!s0&i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"c":["r"],"s":["0"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="!s0&i0&c0", specify=""),
             # Group 2: S=1 (SETN inactive、 Q=D 値)
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"c":["p"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","0"],tmg_when="s0&!i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["0","1"],"i":["0"],"c":["r"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","0","","1"],tmg_when="s0&!i0&c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"c":["p"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","0"],tmg_when="s0&i0&!c0", specify=""),
             MyExpectCell(pin_tr=["",""], pin_oirc=["o0","i0","","c0"], ival={"o":["1","0"],"i":["1"],"c":["r"],"s":["1"]}
                        ,meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","1","","1"],tmg_when="s0&i0&c0", specify="", power_default=True),

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
