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
#  Returns tri-state / bus-keeper logic definitions (special std cells with
#  three_state attribute or bus-hold inout pin).
#  Targeted issues:
#    - ISS-00069: HOLD (bus keeper, 1 cell)         [implemented]
#    - ISS-00066: BUFZ / INVZ (tri-state, 14 cells) [pending]
#
# def get_code_primitive():
#  No additional primitive (Verilog built-in `buf (weak0,weak1)` is used).
#
###############################################################################
from .myExpectCell import MyExpectCell

###############################################################################
def get_logic_dict():
  return {
    #---------------------------------------------------------------------------------------
    # HOLD (bus keeper, std cell). orig liberty structure (gf180 hold):
    #   pin(Z) direction:inout, three_state:"1", function:"Z", driver_type:bus_hold
    #   leakage_power : 3 entries (when="!Z" / "Z" / default)
    #   internal_power on biport : 1D template (pwr_tin_10), no related_pin, no when
    #     (input slope x value, fall_power + rise_power)
    #---------------------------------------------------------------------------------------
    # BUFZ (tri-state buffer, std cell). orig liberty structure (gf180 bufz_*):
    #   pin(Z) direction:output, three_state:"(!EN)", function:"I"
    #   leakage_power: 4 conditions (!EN&!I, !EN&I, EN&!I, EN&I) + default
    #   timing(related:I, combinational, when:"EN") + power_tout(related:I, when:"EN")
    #   [A1.b/A2 後回し: power_tin EN/I, three_state_enable/disable timing, power_tout related:EN]
    #   Pin mapping (charao internal logic ports):
    #     o0 = Z  (output, tri-state — Hi-Z when EN=0)
    #     i0 = I  (data input)
    #     i1 = EN (enable, active-high — output drives when EN=1)
    #   ports_dict example: {"I":"i0","EN":"i1","Z":"o0",...}
    "BUFZ":{
      "logic_type":"comb",
      "three_state":"(!i1)",
      "functions":{"o0":"i0"},
      "vcode":'bufif1 (o0, i0, i1);',
      "expect":
             [
               #--- delay + power_tout (related:I=i0, when:EN=i1=1)
               MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["0"],"i":["0","1"]}, mondrv_oirc=["1","1","1",""]
                           ,meas_types=["delay","power_tout"], tmg_sense="pos", arc_oirc=["r","r","r",""], tmg_when="i1", specify=""),
               MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["1"],"i":["1","1"]}, mondrv_oirc=["0","0","0",""]
                           ,meas_types=["delay","power_tout"], tmg_sense="pos", arc_oirc=["f","f","f",""], tmg_when="i1", specify="(i0 => o0) = (0,0);"),
               #--- three_state_enable arc (EN rise -> Z to active value, no when, fall/rise pair)
               # I=1: ext drive 0 -> internal 1 (Z rise)
               MyExpectCell(pin_oirc=["o0","i0","i1",""], ival={"o":["0"],"i":["1","0"]}, mondrv_oirc=["1","1","1",""]
                           ,meas_types=["three_state_enable","power_tout"], tmg_sense="pos", arc_oirc=["r","s","r",""], tmg_when="", specify=""),
               # I=0: ext drive 1 -> internal 0 (Z fall)
               MyExpectCell(pin_oirc=["o0","i0","i1",""], ival={"o":["1"],"i":["0","0"]}, mondrv_oirc=["0","0","1",""]
                           ,meas_types=["three_state_enable","power_tout"], tmg_sense="pos", arc_oirc=["f","s","r",""], tmg_when="", specify=""),
               #--- three_state_disable arc (EN fall -> Z to Hi-Z, oe_infos SW for initial pull)
               # I=0: DUT was driving Z=0; EN fall releases; ext pull-up -> Z rise
               MyExpectCell(pin_oirc=["o0","i0","i1",""], ival={"o":["0"],"i":["0","1"]}, mondrv_oirc=["1","0","0",""]
                           ,meas_types=["three_state_disable"], tmg_sense="neg", arc_oirc=["r","s","f",""], tmg_when="", specify=""),
               # I=1: DUT was driving Z=1; EN fall releases; ext pull-down -> Z fall
               MyExpectCell(pin_oirc=["o0","i0","i1",""], ival={"o":["1"],"i":["1","1"]}, mondrv_oirc=["0","1","0",""]
                           ,meas_types=["three_state_disable"], tmg_sense="neg", arc_oirc=["f","s","f",""], tmg_when="", specify=""),
               #--- power_tin pin(EN) when:"!I" (i0=0): EN rise/fall, I=0 stable
               MyExpectCell(pin_oirc=["o0","i1","i1",""], ival={"o":["0"],"i":["0","0"]}, mondrv_oirc=["0","1","1",""]
                           ,meas_types=["power_tin"], tmg_sense="non", arc_oirc=["s","r","r",""], tmg_when="!i0", specify=""),
               MyExpectCell(pin_oirc=["o0","i1","i1",""], ival={"o":["0"],"i":["0","1"]}, mondrv_oirc=["0","0","0",""]
                           ,meas_types=["power_tin"], tmg_sense="non", arc_oirc=["s","f","f",""], tmg_when="!i0", specify=""),
               #--- power_tin pin(EN) when:"I" (i0=1): EN rise/fall, I=1 stable
               MyExpectCell(pin_oirc=["o0","i1","i1",""], ival={"o":["1"],"i":["1","0"]}, mondrv_oirc=["1","1","1",""]
                           ,meas_types=["power_tin"], tmg_sense="non", arc_oirc=["s","r","r",""], tmg_when="i0", specify=""),
               MyExpectCell(pin_oirc=["o0","i1","i1",""], ival={"o":["1"],"i":["1","1"]}, mondrv_oirc=["1","0","0",""]
                           ,meas_types=["power_tin"], tmg_sense="non", arc_oirc=["s","f","f",""], tmg_when="i0", specify=""),
               #--- power_tin pin(I) when:"!EN" (i1=0, output Hi-Z): I rise/fall in disabled state
               MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["b"],"i":["0","0"]}, mondrv_oirc=["b","1","1",""]
                           ,meas_types=["power_tin"], tmg_sense="non", arc_oirc=["s","r","r",""], tmg_when="!i1", specify=""),
               MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["b"],"i":["1","0"]}, mondrv_oirc=["b","0","0",""]
                           ,meas_types=["power_tin"], tmg_sense="non", arc_oirc=["s","f","f",""], tmg_when="!i1", specify=""),
               #--- leakage (4 conditions: !EN&!I / !EN&I / EN&!I / EN&I)
               MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["d"],"i":["0","0"]}, mondrv_oirc=["0","0","0",""]
                           ,meas_types=["leakage"], tmg_sense="non", arc_oirc=["s","s","s",""], tmg_when="!i0&!i1", specify=""),
               MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["d"],"i":["1","0"]}, mondrv_oirc=["0","0","0",""]
                           ,meas_types=["leakage"], tmg_sense="non", arc_oirc=["s","s","s",""], tmg_when="i0&!i1", specify=""),
               MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["d"],"i":["0","1"]}, mondrv_oirc=["0","1","1",""]
                           ,meas_types=["leakage"], tmg_sense="non", arc_oirc=["s","s","s",""], tmg_when="!i0&i1", specify=""),
               MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["u"],"i":["1","1"]}, mondrv_oirc=["1","1","1",""]
                           ,meas_types=["leakage"], tmg_sense="non", arc_oirc=["s","s","s",""], tmg_when="i0&i1", specify=""),
             ]
    },
    #---------------------------------------------------------------------------------------
    # INVZ (tri-state inverter, std cell). orig liberty structure (gf180 invz_*):
    #   pin(ZN) direction:output, three_state:"(!EN)", function:"!I"
    #   timing(related:I, combinational, when:"EN") sense:negative_unate
    #   timing(related:EN, three_state_enable, sense:positive_unate)
    #   timing(related:EN, three_state_disable, sense:negative_unate)
    #   Pin mapping (charao internal logic ports):
    #     o0 = ZN (output, tri-state, inverted — Hi-Z when EN=0)
    #     i0 = I  (data input)
    #     i1 = EN (enable, active-high — output drives when EN=1)
    #   ports_dict example: {"I":"i0","EN":"i1","ZN":"o0",...}
    "INVZ":{
      "logic_type":"comb",
      "three_state":"(!i1)",
      "functions":{"o0":"!i0"},
      "vcode":'notif1 (o0, i0, i1);',
      "expect":
             [
               #--- delay + power_tout (related:I=i0, when:EN=i1=1, sense=neg)
               MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["1"],"i":["0","1"]}, mondrv_oirc=["1","0","0",""]
                           ,meas_types=["delay","power_tout"], tmg_sense="neg", arc_oirc=["f","r","r",""], tmg_when="i1", specify=""),
               MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["0"],"i":["1","1"]}, mondrv_oirc=["0","1","1",""]
                           ,meas_types=["delay","power_tout"], tmg_sense="neg", arc_oirc=["r","f","f",""], tmg_when="i1", specify="(i0 => o0) = (0,0);"),
               #--- three_state_enable arc (EN rise -> ZN to active value, sense=pos)
               # I=1: ZN=0 (ext drive 1 -> internal 0, ZN fall)
               MyExpectCell(pin_oirc=["o0","i0","i1",""], ival={"o":["1"],"i":["1","0"]}, mondrv_oirc=["0","1","1",""]
                           ,meas_types=["three_state_enable","power_tout"], tmg_sense="pos", arc_oirc=["f","s","r",""], tmg_when="", specify=""),
               # I=0: ZN=1 (ext drive 0 -> internal 1, ZN rise)
               MyExpectCell(pin_oirc=["o0","i0","i1",""], ival={"o":["0"],"i":["0","0"]}, mondrv_oirc=["1","0","1",""]
                           ,meas_types=["three_state_enable","power_tout"], tmg_sense="pos", arc_oirc=["r","s","r",""], tmg_when="", specify=""),
               #--- three_state_disable arc (EN fall -> ZN to Hi-Z, sense=neg)
               # I=1: ZN was 0 -> ext pull-up -> ZN rise
               MyExpectCell(pin_oirc=["o0","i0","i1",""], ival={"o":["0"],"i":["1","1"]}, mondrv_oirc=["1","1","0",""]
                           ,meas_types=["three_state_disable"], tmg_sense="neg", arc_oirc=["r","s","f",""], tmg_when="", specify=""),
               # I=0: ZN was 1 -> ext pull-down -> ZN fall
               MyExpectCell(pin_oirc=["o0","i0","i1",""], ival={"o":["1"],"i":["0","1"]}, mondrv_oirc=["0","0","0",""]
                           ,meas_types=["three_state_disable"], tmg_sense="neg", arc_oirc=["f","s","f",""], tmg_when="", specify=""),
               #--- leakage (4 conditions: !EN&!I / EN&!I / !EN&I / EN&I)
               MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["d"],"i":["0","0"]}, mondrv_oirc=["0","0","0",""]
                           ,meas_types=["leakage"], tmg_sense="non", arc_oirc=["s","s","s",""], tmg_when="!i0&!i1", specify=""),
               MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["d"],"i":["1","0"]}, mondrv_oirc=["0","0","0",""]
                           ,meas_types=["leakage"], tmg_sense="non", arc_oirc=["s","s","s",""], tmg_when="i0&!i1", specify=""),
               MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["u"],"i":["0","1"]}, mondrv_oirc=["1","0","1",""]
                           ,meas_types=["leakage"], tmg_sense="non", arc_oirc=["s","s","s",""], tmg_when="!i0&i1", specify=""),
               MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["d"],"i":["1","1"]}, mondrv_oirc=["0","1","1",""]
                           ,meas_types=["leakage"], tmg_sense="non", arc_oirc=["s","s","s",""], tmg_when="i0&i1", specify=""),
             ]
    },
    #---------------------------------------------------------------------------------------
    # HOLD: bus keeper (bidirectional pin Z, weak driver maintains last value).
    #   Pin mapping (charao internal logic ports):
    #     b0 = Z (bidirectional, bus_hold driver_type — weak0/weak1 self-loop)
    #   ports_dict example: {"Z":"b0",...}
    "HOLD":{
      "logic_type":"comb",
      "three_state":"1",
      "driver_type":"bus_hold",
      "functions":{"b0":"b0"},
      "vcode":'''
      buf (weak0,weak1) MGM_BG_0(b0_w, b0);
      buf MGM_BG_1(b0, b0_w);
      ''',
      "expect":
             [
               #--- power_tin (biport internal_power, 1D, no when)
               MyExpectCell(pin_oirc=["b0","b0","b0",""], ival={"o":[],"i":[],"b":["0"]}, mondrv_oirc=["1","1","1",""]
                           ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["r","r","r",""], tmg_when="", specify=""),
               MyExpectCell(pin_oirc=["b0","b0","b0",""], ival={"o":[],"i":[],"b":["1"]}, mondrv_oirc=["0","0","0",""]
                           ,meas_types=["power_tin"] ,tmg_sense="non",arc_oirc=["f","f","f",""], tmg_when="", specify=""),
               #--- leakage (when="!b0" / "b0"; default block emitted by Liberty exporter via timing_default convention)
               MyExpectCell(pin_oirc=["b0","b0","b0",""], ival={"o":[],"i":[],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                           ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!b0", specify=""),
               MyExpectCell(pin_oirc=["b0","b0","b0",""], ival={"o":[],"i":[],"b":["1"]}, mondrv_oirc=["1","1","1",""]
                           ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="b0", specify=""),
             ]
    },
  }


###############################################################################
def get_code_primitive():
    return ""
