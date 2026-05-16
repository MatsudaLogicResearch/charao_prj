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
#  Returns the IO Logic definitions.
#  (IO cells: P_VDD, P_VSS, P_ANA1, P_I[X|A|P|N]_SMT[...]_PU[...]_PD[...]_O[...]_SLW[...]_HD[...]_LD[...])
#  User-defined Logic entries may be added via mylogic_user.py specified in ARGS.
#
# def get_code_primitive():
#  Returns the IO primitive code (currently empty).
#  User-defined primitive code may override this via mylogic_user.py specified in ARGS.
#
###############################################################################
from .myExpectCell import MyExpectCell

###############################################################################
def get_logic_dict():
  return {
  #==========================================================================================================================================================
  #P_I[X|A|P|N]_SMT[X|A|S]_PU[X|A|P|N]_PD[X|A|P|N]_R[nm]_O[X|A|P|N]_SLW[X|S]_HD[X|P|N]_LD[X|P|N]_DUMP[nm]_DRV[nn]
  #
  #  I: input 
  #    IX: no function
  #    IA: always (no enable pin)
  #    IP: controled by enable(active High)
  #    IN: controled by enable(active Low)
  #  SMT: schumit
  #    SMTX: no function
  #    SMTA: always (no enable pin)
  #    SMTS: on/off by select pin
  #  PU: input pull-up 
  #    PUX: no function
  #    PUA: always (no enable pin)
  #    PUP: controled by enable(active High)
  #    PUN: controled by enable(active Low)
  #  PD: input pull-down
  #    PDX: no function
  #    PDA: always (no enable pin)
  #    PDP: controled by enable(active High)
  #    PDN: controled by enable(active Low)
  #  R: input registor
  #    R12: 100 Ohm (= n x 10^m)
  #  O: output
  #    OX: no function
  #    OA: always (no enable pin)
  #    OP: controled by enable(active High)
  #    ON: controled by enable(active Low)
  #  SLW: slew rate control
  #    SLWX: no function
  #    SLWS: change by select pin
  #  HD: output driver for High level
  #    HDX: no driver
  #    HDP: use PMOS driver
  #    HDN: use NMOS driver
  #  LD: output driver for Low level
  #    LDX: no driver
  #    LDP: use PMOS driver
  #    LDN: use NMOS driver
  #  DUMP: output dumping resistor
  #    DUMP51 : 50 Ohm(=n x 10^m)
  #  DRV: output driving current in mA
  #    DRV04: 4mA
  #
  #==========================================================================================================================================================
  # io-cell
  # P_I[X|A|P|N]_SMT[X|A|S]_PU[X|A|P|N]_PD[X|A|P|N]_O[X|A|P|N]_SLW[X|S]_HD[X|P|N]_LD[X|P|N]

  #---------------------------------------------------------------------------------------
  # P_VDD: power pad (PAD tied to VDD). No logic-level pins; no spice simulation needed.
  #   Pin mapping: (no logic pins — VDD-only)
  "P_VDD":{
    "logic_type":"io",
    "functions":{},
    "vcode":"",
    "expect":
           [
             #--- no spice simulation
           ]
  },
  #---------------------------------------------------------------------------------------
  # P_VSS: ground pad (PAD tied to VSS). No logic-level pins; no spice simulation needed.
  #   Pin mapping: (no logic pins — VSS-only)
  "P_VSS":{
    "logic_type":"io",
    "functions":{},
    "vcode":"",
    "expect":
           [
             #--- no spice simulation
           ]
  },
  #---------------------------------------------------------------------------------------
  # P_ANA1: analog pad (single bidirectional PAD pin; no digital function).
  #   Pin mapping (charao internal logic ports):
  #     b0 = PAD (bidirectional analog pin)
  #   ports_dict example: {"PAD":"b0",...}
  "P_ANA1":{
    "logic_type":"io",
    "functions":{},
    "vcode":"",
    "expect":
           [
             #--- leakage
             MyExpectCell(pin_oirc=["b0","b0","b0",""], ival={"o":[],"i":[],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!b0", specify=""),
             MyExpectCell(pin_oirc=["b0","b0","b0",""], ival={"o":[],"i":[],"b":["1"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="b0", specify=""),
           ]
  },
  #---------------------------------------------------------------------------------------
  # P_IP_SMTX_PUN_PDP_OX_SLWX_HDX_LDX: input pad (PIC).
  #   PAD -> CORE direction, with input-enable, pull-up(active-low) and pull-down(active-high).
  #   Pin mapping (charao internal logic ports):
  #     b0 = PAD  (bidirectional pad)
  #     o0 = C    (core-side output, = IE & PAD)
  #     i0 = IE   (input enable, active-high)
  #     i1 = PU_N (pull-up enable, active-low)
  #     i2 = PD_P (pull-down enable, active-high)
  #   ports_dict example: {"PAD":"b0","C":"o0","IE":"i0","PU_N":"i1","PD_P":"i2",...}
  "P_IP_SMTX_PUN_PDP_OX_SLWX_HDX_LDX":{
    "logic_type":"io",
    "functions":{"o0":"i0&b0"},
    "vcode":'''
      wire pp,PAD_i,c_in,c_buf;
      bufif0(weak0,weak1)(PAD_i,1'B1,i1);
      bufif1(weak0,weak1)(PAD_i,1'B0,i2);
      buf(o0,c_in);
      and(c_in,c_buf,i0);
      pmos(c_buf,b0,1'B0);
      pmos(pp,PAD_i,1'B0);
      pmos(b0,pp,1'B0);
    ''',
    "expect":
           [
             #--- PAD to CORE
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["1","1","0"],"b":["0"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["delay_i2c"] ,tmg_sense="pos",arc_oirc=["r","r","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["1"],"i":["1","1","0"],"b":["1"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["delay_i2c"] ,tmg_sense="pos",arc_oirc=["f","f","f",""], tmg_when="", specify="(b0 => o0)=(0,0);"),
             #--- IE to CORE
             MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["0"],"i":["0","1","0"],"b":["1"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["delay_c2c"] ,tmg_sense="pos",arc_oirc=["r","s","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["1"],"i":["1","1","0"],"b":["1"]}, mondrv_oirc=["0","1","0",""]
                         ,meas_types=["delay_c2c"] ,tmg_sense="pos",arc_oirc=["f","s","f",""], tmg_when="", specify="(i0 => o0)=(0,0);"),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["0","0","0"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&!i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["0","0","0"],"b":["1"]}, mondrv_oirc=["0","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&!i1&!i2&b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["0","1","0"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["0","1","0"],"b":["1"]}, mondrv_oirc=["0","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&!i2&b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["0","1","1"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&i2&!b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["0","1","1"],"b":["1"]}, mondrv_oirc=["0","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&i2&b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["1","0","0"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="i0&!i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["1","0","0"],"b":["1"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="i0&!i1&!i2&b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["1","1","0"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="i0&i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["1","1","0"],"b":["1"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="i0&i1&!i2&b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["1","1","1"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="i0&i1&i2&!b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["1","1","1"],"b":["1"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="i0&i1&i2&b0", specify=""),
           ]
  },
  #---------------------------------------------------------------------------------------
  # P_IP_SMTA_PUN_PDP_OX_SLWX_HDX_LDX: input pad with Schmitt trigger (always on; PICS).
  #   Same pin set as PIC; SMTA = Schmitt always enabled.
  #   Pin mapping (charao internal logic ports):
  #     b0 = PAD  (bidirectional pad)
  #     o0 = C    (core-side output, = IE & PAD)
  #     i0 = IE   (input enable, active-high)
  #     i1 = PU_N (pull-up enable, active-low)
  #     i2 = PD_P (pull-down enable, active-high)
  #   ports_dict example: {"PAD":"b0","C":"o0","IE":"i0","PU_N":"i1","PD_P":"i2",...}
  "P_IP_SMTA_PUN_PDP_OX_SLWX_HDX_LDX":{
    "logic_type":"io",
    "functions":{"o0":"i0&b0"},
    "vcode":'''
      wire pp,PAD_i,c_in,c_buf;
      bufif0(weak0,weak1)(PAD_i,1'B1,i1);
      bufif1(weak0,weak1)(PAD_i,1'B0,i2);
      buf(o0,c_in);
      and(c_in,c_buf,i0);
      pmos(c_buf,b0,1'B0);
      pmos(pp,PAD_i,1'B0);
      pmos(b0,pp,1'B0);
    ''',
    "expect":
           [
             #--- PAD to CORE
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["1","1","0"],"b":["0"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["delay_i2c"] ,tmg_sense="pos",arc_oirc=["r","r","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["1"],"i":["1","1","0"],"b":["1"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["delay_i2c"] ,tmg_sense="pos",arc_oirc=["f","f","f",""], tmg_when="", specify="(b0 => o0)=(0,0);"),
             #--- IE to CORE
             MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["0"],"i":["0","1","0"],"b":["1"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["delay_c2c"] ,tmg_sense="pos",arc_oirc=["r","s","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""], ival={"o":["1"],"i":["1","1","0"],"b":["1"]}, mondrv_oirc=["0","1","0",""]
                         ,meas_types=["delay_c2c"] ,tmg_sense="pos",arc_oirc=["f","s","f",""], tmg_when="", specify="(i0 => o0)=(0,0);"),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["0","0","0"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&!i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["0","0","0"],"b":["1"]}, mondrv_oirc=["0","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&!i1&!i2&b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["0","1","0"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["0","1","0"],"b":["1"]}, mondrv_oirc=["0","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&!i2&b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["0","1","1"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&i2&!b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["0","1","1"],"b":["1"]}, mondrv_oirc=["0","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&i2&b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["1","0","0"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&!i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["1","0","0"],"b":["1"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&!i1&!i2&b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["1","1","0"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["1","1","0"],"b":["1"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&!i2&b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["1","1","1"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&i2&!b0", specify=""),
             MyExpectCell(pin_oirc=["o0","b0","b0",""], ival={"o":["0"],"i":["1","1","1"],"b":["1"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&i2&b0", specify=""),
           ]
  },
  #---------------------------------------------------------------------------------------
  # P_IX_SMTX_PUN_PDP_ON_SLWX_HDA_LDA: output pad with tri-state output enable (POC).
  #   CORE -> PAD direction, with active-low OEN, pull-up(active-low) and pull-down(active-high).
  #   Pin mapping (charao internal logic ports):
  #     b0 = PAD  (bidirectional pad; output driver active when OEN=0)
  #     i0 = OEN  (output enable, active-low — PAD drives when OEN=0, Hi-Z when OEN=1)
  #     i1 = PU_N (pull-up enable, active-low)
  #     i2 = PD_P (pull-down enable, active-high)
  #     i3 = I    (core-side data input, driven to PAD when enabled)
  #   ports_dict example: {"PAD":"b0","OEN":"i0","PU_N":"i1","PD_P":"i2","I":"i3",...}
  "P_IX_SMTX_PUN_PDP_ON_SLWX_HDA_LDA":{
    "logic_type":"io",
    "functions":{"b0":"i3"},
    "vcode":'''
      wire pp,PAD_i,PAD_q;
      bufif0(weak0,weak1)(PAD_i,1'B1,i1);
      bufif1(weak0,weak1)(PAD_i,1'B0,i2);
      bufif0(PAD_q,i3,i0);
      pmos(pp,PAD_q,1'B0);
      pmos(pp,PAD_i,1'B0);
      pmos(b0,pp,1'B0);
    ''',
    "expect":
           [
             #--- I to PAD
             MyExpectCell(pin_oirc=["b0","i3","i3",""], ival={"o":[],"i":["0","1","0","0"],"b":["0"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["delay_c2i"] ,tmg_sense="pos",arc_oirc=["r","r","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["b0","i3","i3",""], ival={"o":[],"i":["0","1","0","1"],"b":["1"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["delay_c2i"] ,tmg_sense="pos",arc_oirc=["f","f","f",""], tmg_when="", specify="(i3 => b0)=(0,0);"),
             #--- OE to PAD(enable)
             MyExpectCell(pin_oirc=["b0","i3","i0",""], ival={"o":[],"i":["1","1","0","1"],"b":["0"]}, mondrv_oirc=["1","1","0",""]
                         ,meas_types=["three_state_enable_c2i"] ,tmg_sense="neg",arc_oirc=["r","s","f",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["b0","i3","i0",""], ival={"o":[],"i":["1","1","0","0"],"b":["1"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["three_state_enable_c2i"] ,tmg_sense="neg",arc_oirc=["f","s","f",""], tmg_when="", specify=""),
             #--- OE to PAD(disable)
             MyExpectCell(pin_oirc=["b0","i3","i0",""], ival={"o":[],"i":["0","1","0","0"],"b":["0"]}, mondrv_oirc=["1","0","1",""]
                         ,meas_types=["three_state_disable_c2i"] ,tmg_sense="pos",arc_oirc=["r","s","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["b0","i3","i0",""], ival={"o":[],"i":["0","1","0","1"],"b":["1"]}, mondrv_oirc=["0","1","1",""]
                         ,meas_types=["three_state_disable_c2i"] ,tmg_sense="pos",arc_oirc=["f","s","r",""], tmg_when="", specify="(i0 => b0)=(0,0,0,0,0,0);"),
             #--- leakage
             MyExpectCell(pin_oirc=["b0","i3","i3",""], ival={"o":[]  ,"i":["0","0","0","0"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["b0","i3","i3",""], ival={"o":[]  ,"i":["0","0","0","1"],"b":["1"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["b0","i3","i3",""], ival={"o":[]  ,"i":["0","1","0","0"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["b0","i3","i3",""], ival={"o":[]  ,"i":["0","1","0","1"],"b":["1"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["b0","i3","i3",""], ival={"o":[]  ,"i":["0","1","1","0"],"b":["0"]}, mondrv_oirc=["0","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["b0","i3","i3",""], ival={"o":[]  ,"i":["0","1","1","1"],"b":["1"]}, mondrv_oirc=["1","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!i0&i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["b0","i3","i3",""], ival={"o":[]  ,"i":["1","0","0","0"],"b":["u"]}, mondrv_oirc=["u","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["b0","i3","i3",""], ival={"o":[]  ,"i":["1","0","0","1"],"b":["u"]}, mondrv_oirc=["u","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["b0","i3","i3",""], ival={"o":[]  ,"i":["1","1","0","0"],"b":["z"]}, mondrv_oirc=["z","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["b0","i3","i3",""], ival={"o":[]  ,"i":["1","1","0","1"],"b":["z"]}, mondrv_oirc=["z","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["b0","i3","i3",""], ival={"o":[]  ,"i":["1","1","1","0"],"b":["d"]}, mondrv_oirc=["d","0","0",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["b0","i3","i3",""], ival={"o":[]  ,"i":["1","1","1","1"],"b":["d"]}, mondrv_oirc=["d","1","1",""]
                         ,meas_types=["leakage"] ,tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="i0&i1&i2&i3", specify=""),
           ]
  }
  }

###############################################################################
def get_code_primitive():
    return ""
