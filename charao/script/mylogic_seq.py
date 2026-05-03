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
           "expect":
           [
             #--- q delay (clk)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","1","1"]
                         ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","0","1"]
                         ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- clear
             MyExpectCell(pin_oir=["o0","i0","r0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","1","0"]
                        ,meas_types=["clear"]       ,tmg_sense="pos",arc_oir=["f","s","f"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- preset
             MyExpectCell(pin_oir=["o0","i0","s0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_types=["preset"]      ,tmg_sense="neg",arc_oir=["r","s","f"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             
             #--- setup
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","0","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold (arc_oir is same as setup)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","0","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery reset
             MyExpectCell(pin_oir=["o0","r0", "c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oir=["1","1","1"]
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oir=["r","r","r"], tmg_when="", specify="$recovery(posedge r0, posedge c0, 0, notifier);"),
             #--- recovery set
             MyExpectCell(pin_oir=["o0","s0", "c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oir=["0","1","1"]
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oir=["f","r","r"], tmg_when="", specify="$recovery(posedge s0, posedge c0, 0, notifier);"),
             #--- removal reset(arc_oir is same as recovery)
             MyExpectCell(pin_oir=["o0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oir=["0","1","1"]
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oir=["s","r","r"], tmg_when="", specify="$removal(posedge r0, posedge c0, 0, notifier);"),
             #--- removal set(arc_oir is same as recovery)
             MyExpectCell(pin_oir=["o0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oir=["1","0","1"]
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oir=["s","r","r"], tmg_when="", specify="$removal(posedge s0, posedge c0, 0, notifier);"),
             
             #--- passive power(data)
             MyExpectCell(pin_oir=["o0","i0","i0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","f","f"], tmg_when="", specify=""),
             #--- passive power(reset)
             MyExpectCell(pin_oir=["o0","r0","r0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oir=["0","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","r0","r0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","r","r"], tmg_when="", specify=""),
             #--- passive power(set)
             MyExpectCell(pin_oir=["o0","s0","s0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oir=["1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","s0","s0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","f","f"], tmg_when="", specify=""),
             #--- passive power(clk)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","s","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","s","f"], tmg_when="", specify=""),
             #--- min_pulse(clk)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse(reset)
             MyExpectCell(pin_oir=["o0","i0","r0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","1","0"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oir=["f","s","f"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- min_pulse(set)
             MyExpectCell(pin_oir=["o0","i0","s0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oir=["r","s","f"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
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
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["1","1","1"]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","0","1"]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             
             MyExpectCell(pin_oir=["o1","i0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["1","0","1"]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oir=["r","f","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o1","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","1","1"]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oir=["f","r","r"], tmg_when="", specify="(posedge c0 => (o1 +: i0)) =(0,0);"),
             #--- clear(q)
             MyExpectCell(pin_oir=["o0","i0","r0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","1","1"]
                       ,meas_types=["clear"]       ,tmg_sense="neg",arc_oir=["f","s","r"], tmg_when="", specify="(posedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- clear(q)-->preset(qb)
             MyExpectCell(pin_oir=["o1","i0","r0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["1","1","1"]
                       ,meas_types=["preset"]       ,tmg_sense="pos",arc_oir=["r","s","r"], tmg_when="", specify="(posedge r0 => (o1 +: 1'b1)) = (0,0);"),
             
             #--- setup
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["1","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","0","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),

             #--- hold (arc_oir is same as setup)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["1","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1","1"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","0","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery reset
             MyExpectCell(pin_oir=["o0","r0", "c0"], ival={"o":["0","1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oir=["1","0","1"]
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oir=["r","f","r"], tmg_when="", specify="$recovery(negedge r0, posedge c0, 0, notifier);"),
             #--- removal reset(arc_oir is same as recovery)
             MyExpectCell(pin_oir=["o0","r0", "c0"], ival={"o":["0","1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oir=["0","0","1"]
                        ,meas_types=["removal_rising"],tmg_sense="non",arc_oir=["r","f","r"], tmg_when="", specify="$removal(negedge r0, posedge c0, 0, notifier);"),
             
             #--- passive power(data)
             MyExpectCell(pin_oir=["o0","i0","i0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["1","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","f","f"], tmg_when="", specify=""),
             #--- passive power(reset)
             MyExpectCell(pin_oir=["o0","r0","r0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","f","f"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","r0","r0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oir=["0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","r","r"], tmg_when="", specify=""),
             
             #--- passive power(clk)
             MyExpectCell(pin_oir=["o0","c0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","c0","c0"], ival={"o":["0","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","f","f"], tmg_when="", specify=""),
             #--- min_pulse(clk)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["1","1","1"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse(reset)
             MyExpectCell(pin_oir=["o0","i0","r0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","1","1"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oir=["f","s","r"], tmg_when="", specify="$width(posedge r0, 0, 0, notifier);"),
             #--- leakage(clock->inputport & mondrv_oir[1]=clock value )
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"]},mondrv_oir=["0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!c0&!r0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["1"]},mondrv_oir=["0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!c0&r0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"]},mondrv_oir=["0","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","r","s"],tmg_when="!i0&c0&!r0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["1"]},mondrv_oir=["0","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","r","s"],tmg_when="!i0&c0&r0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"]},mondrv_oir=["1","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!c0&!r0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["d","u"],"i":["1"],"c":["0"],"r":["1"]},mondrv_oir=["0","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!c0&r0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"]},mondrv_oir=["1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","r","s"],tmg_when="i0&c0&!r0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["d","u"],"i":["1"],"c":["0"],"r":["1"]},mondrv_oir=["0","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","r","s"],tmg_when="i0&c0&r0", specify=""),
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
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","0","1"]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             
             MyExpectCell(pin_oir=["o1","i0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","0","1"]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oir=["r","f","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o1","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","1","1"]
                        ,meas_types=["rising_edge"] ,tmg_sense="non",arc_oir=["f","r","r"], tmg_when="", specify="(posedge c0 => (o1 +: i0)) =(0,0);"),
             
             #--- preset(q)
             MyExpectCell(pin_oir=["o0","i0","s0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","0","0"]
                       ,meas_types=["preset"]      ,tmg_sense="neg",arc_oir=["r","s","f"], tmg_when="", specify="(negedge s0 => (o0 +: 1'b1)) = (0,0);"),
             #--- preset(q)-->clear(qb)
             MyExpectCell(pin_oir=["o1","i0","s0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","1","0"]
                       ,meas_types=["clear"]       ,tmg_sense="pos",arc_oir=["f","s","f"], tmg_when="", specify="(negedge s0 => (o1 +: 1'b0)) = (0,0);"),
             
             #--- setup
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","0","1"]
                        ,meas_types=["setup_rising"] ,tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             
             #--- hold (arc_oir is same as setup)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1","1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","0","1"]
                        ,meas_types=["hold_rising"],tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),

             #--- recovery preset
             MyExpectCell(pin_oir=["o0","s0", "c0"], ival={"o":["1","0"],"i":["0"],"b":[],"c":["0"],"s":["0"]}, mondrv_oir=["0","1","1"]
                       ,meas_types=["recovery_rising"],tmg_sense="pos",arc_oir=["f","r","r"], tmg_when="", specify="$recovery(posedge s0, posedge c0, 0, notifier);"),
             #--- removal preset(arc_oir is same as recovery)
             MyExpectCell(pin_oir=["o0","s0", "c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["0"]}, mondrv_oir=["0","1","1"]
                        ,meas_types=["removal_rising"],tmg_sense="pos",arc_oir=["f","r","r"], tmg_when="", specify="$removal(posedge s0, posedge c0, 0, notifier);"),
             
             #--- passive power(data)
             MyExpectCell(pin_oir=["o0","i0","i0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","f","f"], tmg_when="", specify=""),
             #--- passive power(preset)
             MyExpectCell(pin_oir=["o0","s0","s0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["0"]}, mondrv_oir=["1","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","s0","s0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","f","f"], tmg_when="", specify=""),
             
             #--- passive power(clk)
             MyExpectCell(pin_oir=["o0","c0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","1","1"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","c0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","0","0"]
                        ,meas_types=["passive"]      ,tmg_sense="non",arc_oir=["s","f","f"], tmg_when="", specify=""),
             
             #--- min_pulse(clk)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_types=["min_pulse_width_high"],tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse(preset)
             MyExpectCell(pin_oir=["o0","i0","s0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_types=["min_pulse_width_low"] ,tmg_sense="non",arc_oir=["r","s","f"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             
             #--- leakage(clock->inputport & mondrv_oir[1]=clock value )
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["0"],"c":["0"],"s":["0"]},mondrv_oir=["1","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!c0&!s0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["d","s"],"i":["0"],"c":["0"],"s":["1"]},mondrv_oir=["0","0","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!c0&s0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["0"],"c":["0"],"s":["0"]},mondrv_oir=["1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","r","s"],tmg_when="!i0&c0&!s0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["0"],"c":["0"],"s":["1"]},mondrv_oir=["1","1","0"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","r","s"],tmg_when="!i0&c0&s0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["0"]},mondrv_oir=["1","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!c0&!s0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["1"]},mondrv_oir=["1","0","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!c0&s0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["0"]},mondrv_oir=["1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","r","s"],tmg_when="i0&c0&!s0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["1"]},mondrv_oir=["1","1","1"]
                        ,meas_types=["leakage"],tmg_sense="non",arc_oir=["s","r","s"],tmg_when="i0&c0&s0", specify=""),

           ]
    },
  }

###############################################################################
def get_code_primitive():
    return '''
primitive lr_dff (q, d, cp, cdn, sdn, notifier);
`protect
   output q;
   input d, cp, cdn, sdn, notifier;
   reg q;

   table
      ?   ?   0   ?   ? : ? : 0 ; // CDN dominate SDN
      ?   ?   1   0   ? : ? : 1 ; // SDN is set
      ?   ?   1   x   ? : 0 : x ; // SDN affect Q

      0 (01)  ?   1   ? : ? : 0 ; // Latch 0
      0   *   ?   1   ? : 0 : 0 ; // Keep 0 (D==Q)

      1 (01)  1   ?   ? : ? : 1 ; // Latch 1
      1   *   1   ?   ? : 1 : 1 ; // Keep 1 (D==Q)

      ? (1?)  1   1   ? : ? : - ; // ignore negative edge of clock
      ? (?0)  1   1   ? : ? : - ; // ignore negative edge of clock
      ?   ? (?1)  ?   ? : ? : - ; // ignore positive edge of CDN
      ?   ?   ? (?1)  ? : ? : - ; // ignore posative edge of SDN
      *   ?   ?   ?   ? : ? : - ; // ignore data change on steady clock

      ?   ?   ?   ?   * : ? : x ; // timing check violation
   endtable
`endprotect
endprimitive

'''
