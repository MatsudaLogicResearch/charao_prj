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
#  Returns the comb-base Logic definitions (basic combinational gates).
#  User-defined Logic entries may be added via mylogic_user.py specified in ARGS.
#
#  (ISS-00172) primitive code is supplied by <target>/primitives.v.
#              see docs/SPEC_primitives.md
#
###############################################################################
from .myExpectCell import MyExpectCell

###############################################################################
def get_logic_dict():
  return {
    #---------------------------------------------------------------------------------------
    # ANTENNA: antenna diode cell (single input, no output).
    #   Pin mapping (charao internal logic ports):
    #     i0 = A (input, antenna pin)
    #   ports_dict example: {"A":"i0",...}
    "ANTENNA":{"logic_type":"comb",
           "functions":{},
           "expect":
           [#--- passive power
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["","","i0",""],ival={"o":[""],"i":["0"]},meas_types=["passive"],tmg_sense="non",arc_oirc=["","","r",""], tmg_when="", specify=""), #ISS-00135: passive は inport 必須のため新ルール非適用、 ISS-00101: mondrv_oirc 省略
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["","","i0",""],ival={"o":[""],"i":["1"]},meas_types=["passive"],tmg_sense="non",arc_oirc=["","","f",""], tmg_when="", specify=""),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["","","i0",""],ival={"o":[""],"i":["0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["","","0",""], tmg_when="!i0", specify=""), #ISS-00135: 上記同様 passive と整合
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["","","i0",""],ival={"o":[""],"i":["1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["","","1",""], tmg_when="i0" , specify="", power_default=True),
            ]
    },

    #---------------------------------------------------------------------------------------
    # TIE1: constant-1 tie cell (output fixed to VDD; no input).
    #   Pin mapping (charao internal logic ports):
    #     o0 = Y (output, tied to 1)
    #   ports_dict example: {"Y":"o0",...}
    "TIE1":{"logic_type":"comb",
           "functions":{"o0":"1"},
           "expect":
           [
             #--- leakage
             MyExpectCell(pin_tr=["o0",""], pin_oirc=["o0","","",""],ival={"o":["1"],"i":[""]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","",""], tmg_when="", specify=""), #ISS-00101: mondrv_oirc 省略、 arc=s→0/1。 ISS-00116: TIE は 1 state cell のため tmg_when="" + power_default 削除（orig は when なし 1 entry のみ）
            ]
    },

    #---------------------------------------------------------------------------------------
    # TIE0: constant-0 tie cell (output fixed to VSS; no input).
    #   Pin mapping (charao internal logic ports):
    #     o0 = Y (output, tied to 0)
    #   ports_dict example: {"Y":"o0",...}
    "TIE0":{"logic_type":"comb",
           "functions":{"o0":"0"},
           "expect":
           [
             #--- leakage
             MyExpectCell(pin_tr=["o0",""], pin_oirc=["o0","","",""],ival={"o":["0"],"i":[""]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","",""], tmg_when="", specify=""), #ISS-00101: mondrv_oirc 省略、 arc=s→0/1。 ISS-00116: TIE は 1 state cell のため tmg_when="" + power_default 削除（orig は when なし 1 entry のみ）
            ]
    },

    #---------------------------------------------------------------------------------------
    # BUF: non-inverting buffer (o0 = i0).
    #   Pin mapping (charao internal logic ports):
    #     o0 = Y (output)
    #     i0 = A (data input)
    #   ports_dict example: {"A":"i0","Y":"o0",...}
    "BUF":{"logic_type":"comb",
           "functions":{"o0":"i0"},
           "expect":
           [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="", specify=""),
            MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="", specify="(i0 => o0) = (0,0);"),
             #--- leakage
            MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0", specify=""),
            MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0", specify="", power_default=True),
            ]
    },

    #---------------------------------------------------------------------------------------
    # DEL: delay buffer (o0 = i0; same logic as BUF but timing-optimized cell).
    #   Pin mapping (charao internal logic ports):
    #     o0 = Y (output)
    #     i0 = A (data input)
    #   ports_dict example: {"A":"i0","Y":"o0",...}
    "DEL":{"logic_type":"comb",
           "functions":{"o0":"i0"},
           "expect":
           [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="", specify=""),
            MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="", specify="(i0 => o0) = (0,0);"),
             #--- leakage
            MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0", specify=""),
            MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0", specify="", power_default=True),
            ]
    },
    
    #---------------------------------------------------------------------------------------
    # INV: inverter (o0 = !i0).
    #   Pin mapping (charao internal logic ports):
    #     o0 = Y (output, inverted)
    #     i0 = A (data input)
    #   ports_dict example: {"A":"i0","Y":"o0",...}  (also ZN/YN depending on tech)
    "INV":{"logic_type":"comb",
           "functions":{"o0":"!i0"},
           "expect":
           [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="", specify=""), #ISS-00135 (pin_oirc[i]="" / pin_oirc[r]=i0): VIN 省略、 VREL のみ駆動
            MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="", specify="(i0 => o0) = (0,0);"),
             #--- leakage
            MyExpectCell(pin_tr=["i0",""],     pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0", specify=""), #ISS-00135 (pin_oirc[i]="" / pin_oirc[r]=i0), ISS-00127: leakage は cell-level
            MyExpectCell(pin_tr=["i0",""],     pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0", specify="", power_default=True),
            ]
    },
    
    #---------------------------------------------------------------------------------------
    # AND2: 2-input AND (o0 = i0 & i1).
    #   Pin mapping (charao internal logic ports):
    #     o0 = Y (output)
    #     i0 = A (data input 0)
    #     i1 = B (data input 1)
    #   ports_dict example: {"A":"i0","B":"i1","Y":"o0",...}
    "AND2":{"logic_type":"comb",
            "functions":{"o0":"i0&i1"},
            "expect":                                                     
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i1", specify="(i0 => o0) = (0,0);;"),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i0", specify="(i1 => o0) = (0,0);;"),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0", specify=""),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1", specify="", power_default=True),
             ]
    },
    #---------------------------------------------------------------------------------------
    # AND3: 3-input AND (o0 = i0 & i1 & i2).
    #   Pin mapping (charao internal logic ports):
    #     o0 = Y, i0 = A, i1 = B, i2 = C
    #   ports_dict example: {"A":"i0","B":"i1","C":"i2","Y":"o0",...}
    "AND3":{"logic_type":"comb",
            "functions":{"o0":"i0&i1&i2"},
            "expect":
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i1&i2", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i0&i2", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i0&i2", specify="(i1 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i0&i1", specify=""),
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i0&i1", specify="(i2 => o0) = (0,0);;"),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i1", specify=""),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&i2", specify="", power_default=True),
             ]
    },
    #---------------------------------------------------------------------------------------
    # AND4: 4-input AND (o0 = i0 & i1 & i2 & i3).
    #   Pin mapping (charao internal logic ports):
    #     o0 = Y, i0 = A, i1 = B, i2 = C, i3 = D
    #   ports_dict example: {"A":"i0","B":"i1","C":"i2","D":"i3","Y":"o0",...}
    "AND4":{"logic_type":"comb",
            "functions":{"o0":"i0&i1&i2&i3"},
            "expect":
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i1&i2&i3", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i0&i2&i3", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i0&i2&i3", specify="(i1 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","1","0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i0&i1&i3", specify=""),
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i0&i1&i3", specify="(i2 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i3"], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","1","1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["o0","i3"], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i0&i1&i2", specify="(i3 => o0) = (0,0);;"),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&!i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&!i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&i1&!i2", specify=""),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&i2&i3", specify="", power_default=True),
             ]
    },
    
    #---------------------------------------------------------------------------------------
    # OR2: 2-input OR (o0 = i0 | i1).
    #   Pin mapping: o0 = Y, i0 = A, i1 = B
    #   ports_dict example: {"A":"i0","B":"i1","Y":"o0",...}
    "OR2":{"logic_type":"comb",
           "functions":{"o0":"i0|i1"},
           "expect":
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i1", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i0", specify="(i1 => o0) = (0,0);;"),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0", specify=""),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1", specify="", power_default=True),
             ]
    },
    #---------------------------------------------------------------------------------------
    # OR3: 3-input OR (o0 = i0 | i1 | i2).
    #   Pin mapping: o0 = Y, i0 = A, i1 = B, i2 = C
    #   ports_dict example: {"A":"i0","B":"i1","C":"i2","Y":"o0",...}
    "OR3":{"logic_type":"comb",
           "functions":{"o0":"i0|i1|i2"},
           "expect":                                                     
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i1&!i2", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i0&!i2", specify="(i1 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i0&!i1", specify="(i2 => o0) = (0,0);;"),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&i2", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&i1", specify=""),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&i2", specify="", power_default=True),
             ]
    },
    #---------------------------------------------------------------------------------------
    # OR4: 4-input OR (o0 = i0 | i1 | i2 | i3).
    #   Pin mapping: o0 = Y, i0 = A, i1 = B, i2 = C, i3 = D
    #   ports_dict example: {"A":"i0","B":"i1","C":"i2","D":"i3","Y":"o0",...}
    "OR4":{"logic_type":"comb",
           "functions":{"o0":"i0|i1|i2|i3"},
           "expect":
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i1&!i2&!i3", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i0&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i0&!i2&!i3", specify="(i1 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i0&!i1&!i3", specify=""),
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","0","1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i0&!i1&!i3", specify="(i2 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i3"], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["o0","i3"], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","0","0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i0&!i1&!i2", specify="(i3 => o0) = (0,0);;"),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&i1&i3", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&i1&i2", specify=""),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&i2&i3", specify="", power_default=True),
             ]
    },
    
    #---------------------------------------------------------------------------------------
    # NAND2: 2-input NAND (o0 = !(i0 & i1)).
    #   Pin mapping: o0 = Y (often ZN), i0 = A, i1 = B
    #   ports_dict example: {"A":"i0","B":"i1","Y":"o0",...}
    "NAND2":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1)"},
             "expect":                                                     
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i1", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i0", specify="(i1 => o0) = (0,0);;"),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0", specify=""),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1", specify="", power_default=True),
             ]
    },
    #---------------------------------------------------------------------------------------
    # NAND3: 3-input NAND (o0 = !(i0 & i1 & i2)).
    #   Pin mapping: o0 = Y, i0 = A, i1 = B, i2 = C
    #   ports_dict example: {"A":"i0","B":"i1","C":"i2","Y":"o0",...}
    "NAND3":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1&i2)"},
             "expect":                                                     
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i1&i2", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i0&i2", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i0&i2", specify="(i1 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i0&i1", specify=""),
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i0&i1", specify="(i2 => o0) = (0,0);;"),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i1", specify=""),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1&i2", specify="", power_default=True),
             ]
    },
    #---------------------------------------------------------------------------------------
    # NAND4: 4-input NAND (o0 = !(i0 & i1 & i2 & i3)).
    #   Pin mapping: o0 = Y, i0 = A, i1 = B, i2 = C, i3 = D
    #   ports_dict example: {"A":"i0","B":"i1","C":"i2","D":"i3","Y":"o0",...}
    "NAND4":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1&i2&i3)"},
             "expect":                                                     
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i1&i2&i3", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i0&i2&i3", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i0&i2&i3", specify="(i1 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i0&i1&i3", specify=""),
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i0&i1&i3", specify="(i2 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i3"], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","1","1","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["o0","i3"], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i0&i1&i2", specify="(i3 => o0) = (0,0);;"),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&!i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&!i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["1","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&i1&!i2", specify=""),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1&i2&i3", specify="", power_default=True),
             ]
    },

    #---------------------------------------------------------------------------------------
    # NOR2: 2-input NOR (o0 = !(i0 | i1)).
    #   Pin mapping: o0 = Y, i0 = A, i1 = B
    #   ports_dict example: {"A":"i0","B":"i1","Y":"o0",...}
    "NOR2":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1)"},
            "expect":
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i1", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i0", specify="(i1 => o0) = (0,0);;"),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0", specify=""),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1", specify="", power_default=True),
             ]
    },
    #---------------------------------------------------------------------------------------
    # NOR3: 3-input NOR (o0 = !(i0 | i1 | i2)).
    #   Pin mapping: o0 = Y, i0 = A, i1 = B, i2 = C
    #   ports_dict example: {"A":"i0","B":"i1","C":"i2","Y":"o0",...}
    "NOR3":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1|i2)"},
            "expect":                                                     
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i1&!i2", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i0&!i2", specify="(i1 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i0&!i1", specify="(i2 => o0) = (0,0);;"),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&i2", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&i1", specify=""),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1&i2", specify="", power_default=True),
             ]
    },
    #---------------------------------------------------------------------------------------
    # NOR4: 4-input NOR (o0 = !(i0 | i1 | i2 | i3)).
    #   Pin mapping: o0 = Y, i0 = A, i1 = B, i2 = C, i3 = D
    #   ports_dict example: {"A":"i0","B":"i1","C":"i2","D":"i3","Y":"o0",...}
    "NOR4":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1|i2|i3)"},
            "expect":                                                     
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i1&!i2&!i3", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i0&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i0&!i2&!i3", specify="(i1 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i0&!i1&!i3", specify=""),
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","1","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i0&!i1&!i3", specify="(i2 => o0) = (0,0);;"),

             MyExpectCell(pin_tr=["o0","i3"], pin_oirc=["o0","","i3",""],ival={"o":["1"],"i":["0","0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["o0","i3"], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","0","0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i0&!i1&!i2", specify="(i3 => o0) = (0,0);;"),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&i1&i3", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&i1&i3", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["0","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i3",""], pin_oirc=["o0","","i3",""],ival={"o":["0"],"i":["1","1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="i0&i1&i2", specify=""),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1&i2&i3", specify="", power_default=True),
             ]
    },


    #---------------------------------------------------------------------------------------
    # XOR2: 2-input XOR (o0 = i0 ^ i1).
    #   Pin mapping: o0 = Y, i0 = A, i1 = B
    #   ports_dict example: {"A":"i0","B":"i1","Y":"o0",...}
    "XOR2":{"logic_type":"comb",
            "functions":{"o0":"i0^i1"},
            "expect":                                                     
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i1", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i0", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i1", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i0", specify="(i1 => o0) = (0,0);"),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1", specify="", power_default=True),
            ]
    },

    #---------------------------------------------------------------------------------------
    # XNOR2: 2-input XNOR (o0 = !(i0 ^ i1)).
    #   Pin mapping: o0 = Y, i0 = A, i1 = B
    #   ports_dict example: {"A":"i0","B":"i1","Y":"o0",...}
    "XNOR2":{"logic_type":"comb",
             "functions":{"o0":"!(i0^i1)"},
             "expect":                                                     
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i1", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i0", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i0", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i1", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i0", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i0", specify="(i1 => o0) = (0,0);"),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1", specify="", power_default=True),
            ]
    },

    #---------------------------------------------------------------------------------------
    # MUX2: 2-to-1 multiplexer (o0 = (i2)? i1 : i0 — i2 is the select).
    #   Pin mapping (charao internal logic ports):
    #     o0 = Y  (output)
    #     i0 = A  (data input 0, selected when S=0)
    #     i1 = B  (data input 1, selected when S=1)
    #     i2 = S0 (select, 0 -> A, 1 -> B)
    #   ports_dict example: {"A":"i0","B":"i1","S0":"i2","Y":"o0",...}
    "MUX2":{"logic_type":"comb",
            "functions":{"o0":"(i0&!i2)|(i1&i2)"},  #--- o0 = (i2)? i1 : i0
            "expect":
            [#--- ISS-00106: MUX2 の I0→Z / I1→Z arc を I1 / I0 別 when で 2 分割（orig 互換、 冗長 arc 追加）
             # I0→Z (S=0), I1=0
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i2&!i1", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i2&!i1", specify="(i0 => o0) = (0,0);"),
             # I0→Z (S=0), I1=1
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i2&i1", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i2&i1", specify="(i0 => o0) = (0,0);;", timing_default=True),

             # I1→Z (S=1), I0=0
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i2&!i0", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i2&!i0", specify="(i1 => o0) = (0,0);"),
             # I1→Z (S=1), I0=1
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i2&i0", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i2&i0", specify="(i1 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i0&i1", specify="(i2 => o0) = (0,0);"),

             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i0&!i1", specify="(i2 => o0) = (0,0);", timing_default=True),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i1",""], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","r",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["0","","f",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","0"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","r",""],tmg_when="i0&i1", specify=""),
             MyExpectCell(pin_tr=["i2",""], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","1"]},meas_types=["power_tin"],tmg_sense="non",arc_oirc=["1","","f",""],tmg_when="i0&i1", specify=""),
             #--- leakage
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&i2", specify="", power_default=True),
            ]
    },

    #---------------------------------------------------------------------------------------
    # XOR3: 3-input XOR (o0 = i0 ^ i1 ^ i2).
    #   Pin mapping: o0 = Y, i0 = A, i1 = B, i2 = C
    #   ports_dict example: {"A":"i0","B":"i1","C":"i2","Y":"o0",...}
    "XOR3":{"logic_type":"comb",
            "functions":{"o0":"i0^i1^i2"},
            "expect":
            #--- i0 arcs (4 sensitizations × 2 directions = 8 entries) ---
            #--- !i1 & !i2  (others_xor=0 → pos) ---
            [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i1&!i2", specify="(i0 => o0) = (0,0);"),
             #--- !i1 & i2  (others_xor=1 → neg) ---
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i1&i2", specify="(i0 => o0) = (0,0);"),
             #--- i1 & !i2  (others_xor=1 → neg) ---
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i1&!i2", specify="(i0 => o0) = (0,0);"),
             #--- i1 & i2  (others_xor=0 → pos) ---
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i1&i2", specify="(i0 => o0) = (0,0);", timing_default=True),

             #--- i1 arcs ---
             #--- !i0 & !i2  (others_xor=0 → pos) ---
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i0&!i2", specify="(i1 => o0) = (0,0);"),
             #--- !i0 & i2  (others_xor=1 → neg) ---
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i0&i2", specify="(i1 => o0) = (0,0);"),
             #--- i0 & !i2  (others_xor=1 → neg) ---
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i0&!i2", specify="(i1 => o0) = (0,0);"),
             #--- i0 & i2  (others_xor=0 → pos) ---
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i0&i2", specify=""),
             MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i0&i2", specify="(i1 => o0) = (0,0);", timing_default=True),

             #--- i2 arcs ---
             #--- !i0 & !i1  (others_xor=0 → pos) ---
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i0&!i1", specify="(i2 => o0) = (0,0);"),
             #--- !i0 & i1  (others_xor=1 → neg) ---
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i0&i1", specify="(i2 => o0) = (0,0);"),
             #--- i0 & !i1  (others_xor=1 → neg) ---
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i0&!i1", specify="(i2 => o0) = (0,0);"),
             #--- i0 & i1  (others_xor=0 → pos) ---
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i0&i1", specify=""),
             MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i0&i1", specify="(i2 => o0) = (0,0);", timing_default=True),

             #--- leakage (2^3 = 8 input combinations) ---
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&i2", specify="", power_default=True),
            ]
    },

    #---------------------------------------------------------------------------------------
    # XNOR3: 3-input XNOR (o0 = !(i0 ^ i1 ^ i2)).
    #   Pin mapping: o0 = Y, i0 = A, i1 = B, i2 = C
    #   ports_dict example: {"A":"i0","B":"i1","C":"i2","Y":"o0",...}
    "XNOR3":{"logic_type":"comb",
             "functions":{"o0":"!(i0^i1^i2)"},
             "expect":
             #--- i0 arcs (XOR3 から sense pos↔neg / ival[o] / mondrv_oirc[0] / arc_oirc[0] 反転) ---
             #--- !i1 & !i2  (others_xor=0 → neg) ---
             [MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i1&!i2", specify=""),
              MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i1&!i2", specify="(i0 => o0) = (0,0);"),
              #--- !i1 & i2  (others_xor=1 → pos) ---
              MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i1&i2", specify=""),
              MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i1&i2", specify="(i0 => o0) = (0,0);"),
              #--- i1 & !i2  (others_xor=1 → pos) ---
              MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["0","1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i1&!i2", specify=""),
              MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["1","1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i1&!i2", specify="(i0 => o0) = (0,0);"),
              #--- i1 & i2  (others_xor=0 → neg) ---
              MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["1"],"i":["0","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i1&i2", specify=""),
              MyExpectCell(pin_tr=["o0","i0"], pin_oirc=["o0","","i0",""],ival={"o":["0"],"i":["1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i1&i2", specify="(i0 => o0) = (0,0);", timing_default=True),

              #--- i1 arcs ---
              #--- !i0 & !i2  (others_xor=0 → neg) ---
              MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i0&!i2", specify=""),
              MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","1","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i0&!i2", specify="(i1 => o0) = (0,0);"),
              #--- !i0 & i2  (others_xor=1 → pos) ---
              MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["0","0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i0&i2", specify=""),
              MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["0","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i0&i2", specify="(i1 => o0) = (0,0);"),
              #--- i0 & !i2  (others_xor=1 → pos) ---
              MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i0&!i2", specify=""),
              MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i0&!i2", specify="(i1 => o0) = (0,0);"),
              #--- i0 & i2  (others_xor=0 → neg) ---
              MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["1"],"i":["1","0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i0&i2", specify=""),
              MyExpectCell(pin_tr=["o0","i1"], pin_oirc=["o0","","i1",""],ival={"o":["0"],"i":["1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i0&i2", specify="(i1 => o0) = (0,0);", timing_default=True),

              #--- i2 arcs ---
              #--- !i0 & !i1  (others_xor=0 → neg) ---
              MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","0","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="!i0&!i1", specify=""),
              MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","0","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="!i0&!i1", specify="(i2 => o0) = (0,0);"),
              #--- !i0 & i1  (others_xor=1 → pos) ---
              MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["0","1","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="!i0&i1", specify=""),
              MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["0","1","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="!i0&i1", specify="(i2 => o0) = (0,0);"),
              #--- i0 & !i1  (others_xor=1 → pos) ---
              MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","0","0"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","","r",""],tmg_when="i0&!i1", specify=""),
              MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","0","1"]},meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","","f",""],tmg_when="i0&!i1", specify="(i2 => o0) = (0,0);"),
              #--- i0 & i1  (others_xor=0 → neg) ---
              MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["1"],"i":["1","1","0"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","","r",""],tmg_when="i0&i1", specify=""),
              MyExpectCell(pin_tr=["o0","i2"], pin_oirc=["o0","","i2",""],ival={"o":["0"],"i":["1","1","1"]},meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","","f",""],tmg_when="i0&i1", specify="(i2 => o0) = (0,0);", timing_default=True),

              #--- leakage (2^3 = 8 input combinations、XNOR=1 のとき u、XNOR=0 のとき d) ---
              MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&!i1&!i2", specify=""),
              MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&!i1&i2", specify=""),
              MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["0","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","0",""],tmg_when="!i0&i1&!i2", specify=""),
              MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["0","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","0",""],tmg_when="!i0&i1&i2", specify=""),
              MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","0","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&!i1&!i2", specify=""),
              MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","0","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&!i1&i2", specify=""),
              MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["u"],"i":["1","1","0"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["1","","1",""],tmg_when="i0&i1&!i2", specify=""),
              MyExpectCell(pin_tr=["i0",""], pin_oirc=["o0","","i0",""],ival={"o":["d"],"i":["1","1","1"]},meas_types=["leakage"],tmg_sense="non",arc_oirc=["0","","1",""],tmg_when="i0&i1&i2", specify="", power_default=True),
             ]
    },
  }
