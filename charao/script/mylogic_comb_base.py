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
# def get_code_primitive():
#  Returns the comb-base primitive code (lr_mux).
#  User-defined primitive code may override this via mylogic_user.py specified in ARGS.
#
###############################################################################
from .myExpectCell import MyExpectCell

###############################################################################
def get_logic_dict():
  return {
    "ANTENNA":{"logic_type":"comb",
           "functions":{},
           "expect":
           [#--- passive power
             MyExpectCell(pin_oirc=["","i0","i0",""],ival={"o":[""],"i":["0"]},mondrv_oirc=["","1","1",""],meas_types=["passive"],tmg_sense="non",arc_oirc=["","r","r",""], tmg_when="", specify=""),
             MyExpectCell(pin_oirc=["","i0","i0",""],ival={"o":[""],"i":["1"]},mondrv_oirc=["","0","0",""],meas_types=["passive"],tmg_sense="non",arc_oirc=["","f","f",""], tmg_when="", specify=""),
             #--- leakage
             MyExpectCell(pin_oirc=["","i0","i0",""],ival={"o":[""],"i":["0"]},mondrv_oirc=["","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["","s","s",""], tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["","i0","i0",""],ival={"o":[""],"i":["1"]},mondrv_oirc=["","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["","s","s",""], tmg_when="i0" , specify=""),
            ]
    },

    "TIE1":{"logic_type":"comb",
           "functions":{"o0":"1"},
           "expect":
           [
             #--- leakage
             MyExpectCell(pin_oirc=["o0","","",""],ival={"o":["1"],"i":[""]},mondrv_oirc=["1","","",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="o0", specify=""),
            ]
    },

    "TIE0":{"logic_type":"comb",
           "functions":{"o0":"0"},
           "expect":
           [
             #--- leakage
             MyExpectCell(pin_oirc=["o0","","",""],ival={"o":["0"],"i":[""]},mondrv_oirc=["0","","",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""], tmg_when="!o0", specify=""),
            ]
    },

    "BUF":{"logic_type":"comb",
           "functions":{"o0":"i0"},
           "expect":
           [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="", specify=""),
            MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="", specify="(i0 => o0) = (0,0);"),
             #--- leakage
            MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0", specify=""),
            MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0", specify=""),
            ]
    },

    "DEL":{"logic_type":"comb",
           "functions":{"o0":"i0"},
           "expect":
           [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="", specify=""),
            MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="", specify="(i0 => o0) = (0,0);"),
             #--- leakage
            MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0", specify=""),
            MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0", specify=""),
            ]
    },
    
    "INV":{"logic_type":"comb",
           "functions":{"o0":"!i0"},
           "expect":
           [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="", specify=""),
            MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="", specify="(i0 => o0) = (0,0);"),
             #--- leakage
            MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0", specify=""),
            MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0", specify=""),
            ]
    },
    
    "AND2":{"logic_type":"comb",
            "functions":{"o0":"i0&i1"},
            "expect":                                                     
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i1", specify="(i0 => o0) = (0,0);;", timing_default=True),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i0", specify="(i1 => o0) = (0,0);;", timing_default=True),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0", specify=""),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1", specify=""),
             ]
    },
    "AND3":{"logic_type":"comb",
            "functions":{"o0":"i0&i1&i2"},
            "expect":
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i1&i2", specify="(i0 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i0&i2", specify="(i1 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i0&i1", specify="(i2 => o0) = (0,0);;", timing_default=True),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1", specify=""),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2", specify=""),
             ]
    },
    "AND4":{"logic_type":"comb",
            "functions":{"o0":"i0&i1&i2&i3"},
            "expect":
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i1&i2&i3", specify="(i0 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i0&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i0&i2&i3", specify="(i1 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","1","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i0&i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i0&i1&i3", specify="(i2 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i0&i1&i2", specify="(i3 => o0) = (0,0);;", timing_default=True),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","1","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1&!i2", specify=""),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","1","0"]},mondrv_oirc=["0","1","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2&i3", specify=""),
             ]
    },
    
    "OR2":{"logic_type":"comb",
           "functions":{"o0":"i0|i1"},
           "expect":
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i1", specify="(i0 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i0", specify="(i1 => o0) = (0,0);;", timing_default=True),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0", specify=""),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1", specify=""),
             ]
    },
    "OR3":{"logic_type":"comb",
           "functions":{"o0":"i0|i1|i2"},
           "expect":                                                     
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i1&!i2", specify="(i0 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i0&!i2", specify="(i1 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i0&!i1", specify="(i2 => o0) = (0,0);;", timing_default=True),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1", specify=""),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2", specify=""),
             ]
    },
    "OR4":{"logic_type":"comb",
           "functions":{"o0":"i0|i1|i2|i3"},
           "expect":
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i1&!i2&!i3", specify="(i0 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i0&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i0&!i2&!i3", specify="(i1 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i0&!i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i0&!i1&!i3", specify="(i2 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i0&!i1&!i2", specify="(i3 => o0) = (0,0);;", timing_default=True),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","0","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1&i2", specify=""),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","1","0"]},mondrv_oirc=["1","1","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2&i3", specify=""),
             ]
    },
    
    "NAND2":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1)"},
             "expect":                                                     
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i1", specify="(i0 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i0", specify="(i1 => o0) = (0,0);;", timing_default=True),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0", specify=""),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1", specify=""),
             ]
    },
    "NAND3":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1&i2)"},
             "expect":                                                     
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","1"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1","1"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i1&i2", specify="(i0 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","1"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1","1"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i0&i2", specify="(i1 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","0"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","1","1"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i0&i1", specify="(i2 => o0) = (0,0);;", timing_default=True),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1", specify=""),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2", specify=""),
             ]
    },
    "NAND4":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1&i2&i3)"},
             "expect":                                                     
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","1","1"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i1&i2&i3", specify="(i0 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","1","1"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i0&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i0&i2&i3", specify="(i1 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","0","1"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i0&i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i0&i1&i3", specify="(i2 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","1","1","0"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i0&i1&i2", specify="(i3 => o0) = (0,0);;", timing_default=True),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","0","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","0","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","0","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["1","1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1&!i2", specify=""),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","1","0"]},mondrv_oirc=["1","1","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2&i3", specify=""),
             ]
    },

    "NOR2":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1)"},
            "expect":
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i1", specify="(i0 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i0", specify="(i1 => o0) = (0,0);;", timing_default=True),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0", specify=""),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1", specify=""),
             ]
    },
    "NOR3":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1|i2)"},
            "expect":                                                     
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0","0"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","0"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i1&!i2", specify="(i0 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0","0"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","0"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i0&!i2", specify="(i1 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","0","0"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","1"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i0&!i1", specify="(i2 => o0) = (0,0);;", timing_default=True),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1", specify=""),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2", specify=""),
             ]
    },
    "NOR4":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1|i2|i3)"},
            "expect":                                                     
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","0","0"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i1&!i2&!i3", specify="(i0 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i0&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","0","0"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i0&!i2&!i3", specify="(i1 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i0&!i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","1","0"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i0&!i1&!i3", specify="(i2 => o0) = (0,0);;", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","0","0","1"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i0&!i1&!i2", specify="(i3 => o0) = (0,0);;", timing_default=True),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","1","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","1","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["0","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","1","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i3","i3",""],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1&i2", specify=""),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","1","0"]},mondrv_oirc=["0","1","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2&i3", specify=""),
             ]
    },


    "XOR2":{"logic_type":"comb",
            "functions":{"o0":"i0^i1"},
            "expect":                                                     
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i1", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i0", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i1", specify="(i0 => o0) = (0,0);", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i0", specify="(i1 => o0) = (0,0);", timing_default=True),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1", specify=""),
            ]
    },

    "XNOR2":{"logic_type":"comb",
             "functions":{"o0":"!(i0^i1)"},
             "expect":                                                     
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i1", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i0", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i0", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i1", specify="(i0 => o0) = (0,0);", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i0", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i0", specify="(i1 => o0) = (0,0);", timing_default=True),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1", specify=""),
            ]
    },

    "MUX2":{"logic_type":"comb",
            "functions":{"o0":"(i0&!i2)|(i1&i2)"},  #--- o0 = (i2)? i1 : i0
            "expect":                                                     
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i2", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i2", specify="(i1 => o0) = (0,0);", timing_default=True),

             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i0&i1", specify="(i2 => o0) = (0,0);"),

             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","0"]},mondrv_oirc=["0","0","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","1"]},mondrv_oirc=["1","1","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i0&!i1", specify="(i2 => o0) = (0,0);", timing_default=True),
             #--- power_tin (input pin internal_power, output stable state)
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","r","r",""],tmg_when="i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["power_tin"],tmg_sense="non",arc_oirc=["s","f","f",""],tmg_when="i0&i1", specify=""),
             #--- leakage
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2", specify=""),
            ]
    },

    "XOR3":{"logic_type":"comb",
            "functions":{"o0":"i0^i1^i2"},
            "expect":
            #--- i0 arcs (4 sensitizations × 2 directions = 8 entries) ---
            #--- !i1 & !i2  (others_xor=0 → pos) ---
            [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i1&!i2", specify="(i0 => o0) = (0,0);"),
             #--- !i1 & i2  (others_xor=1 → neg) ---
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i1&i2", specify="(i0 => o0) = (0,0);", timing_default=True),
             #--- i1 & !i2  (others_xor=1 → neg) ---
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i1&!i2", specify="(i0 => o0) = (0,0);", timing_default=True),
             #--- i1 & i2  (others_xor=0 → pos) ---
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i1&i2", specify="(i0 => o0) = (0,0);", timing_default=True),

             #--- i1 arcs ---
             #--- !i0 & !i2  (others_xor=0 → pos) ---
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i0&!i2", specify="(i1 => o0) = (0,0);"),
             #--- !i0 & i2  (others_xor=1 → neg) ---
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i0&i2", specify="(i1 => o0) = (0,0);", timing_default=True),
             #--- i0 & !i2  (others_xor=1 → neg) ---
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i0&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i0&!i2", specify="(i1 => o0) = (0,0);", timing_default=True),
             #--- i0 & i2  (others_xor=0 → pos) ---
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i0&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i0&i2", specify="(i1 => o0) = (0,0);", timing_default=True),

             #--- i2 arcs ---
             #--- !i0 & !i1  (others_xor=0 → pos) ---
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i0&!i1", specify="(i2 => o0) = (0,0);"),
             #--- !i0 & i1  (others_xor=1 → neg) ---
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i0&i1", specify="(i2 => o0) = (0,0);", timing_default=True),
             #--- i0 & !i1  (others_xor=1 → neg) ---
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i0&!i1", specify="(i2 => o0) = (0,0);", timing_default=True),
             #--- i0 & i1  (others_xor=0 → pos) ---
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i0&i1", specify=""),
             MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i0&i1", specify="(i2 => o0) = (0,0);", timing_default=True),

             #--- leakage (2^3 = 8 input combinations) ---
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2", specify=""),
            ]
    },

    "XNOR3":{"logic_type":"comb",
             "functions":{"o0":"!(i0^i1^i2)"},
             "expect":
             #--- i0 arcs (XOR3 から sense pos↔neg / ival[o] / mondrv_oirc[0] / arc_oirc[0] 反転) ---
             #--- !i1 & !i2  (others_xor=0 → neg) ---
             [MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i1&!i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i1&!i2", specify="(i0 => o0) = (0,0);"),
              #--- !i1 & i2  (others_xor=1 → pos) ---
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i1&i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i1&i2", specify="(i0 => o0) = (0,0);", timing_default=True),
              #--- i1 & !i2  (others_xor=1 → pos) ---
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i1&!i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i1&!i2", specify="(i0 => o0) = (0,0);", timing_default=True),
              #--- i1 & i2  (others_xor=0 → neg) ---
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["1"],"i":["0","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i1&i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["0"],"i":["1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i1&i2", specify="(i0 => o0) = (0,0);", timing_default=True),

              #--- i1 arcs ---
              #--- !i0 & !i2  (others_xor=0 → neg) ---
              MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i0&!i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","1","0"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i0&!i2", specify="(i1 => o0) = (0,0);"),
              #--- !i0 & i2  (others_xor=1 → pos) ---
              MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["0","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i0&i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i0&i2", specify="(i1 => o0) = (0,0);", timing_default=True),
              #--- i0 & !i2  (others_xor=1 → pos) ---
              MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i0&!i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i0&!i2", specify="(i1 => o0) = (0,0);", timing_default=True),
              #--- i0 & i2  (others_xor=0 → neg) ---
              MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["1"],"i":["1","0","1"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i0&i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i1","i1",""],ival={"o":["0"],"i":["1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i0&i2", specify="(i1 => o0) = (0,0);", timing_default=True),

              #--- i2 arcs ---
              #--- !i0 & !i1  (others_xor=0 → neg) ---
              MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="!i0&!i1", specify=""),
              MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","0","1"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="!i0&!i1", specify="(i2 => o0) = (0,0);"),
              #--- !i0 & i1  (others_xor=1 → pos) ---
              MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["0","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="!i0&i1", specify=""),
              MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["0","1","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="!i0&i1", specify="(i2 => o0) = (0,0);", timing_default=True),
              #--- i0 & !i1  (others_xor=1 → pos) ---
              MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","0","0"]},mondrv_oirc=["1","1","1",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["r","r","r",""],tmg_when="i0&!i1", specify=""),
              MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["delay","power_tout"],tmg_sense="pos",arc_oirc=["f","f","f",""],tmg_when="i0&!i1", specify="(i2 => o0) = (0,0);", timing_default=True),
              #--- i0 & i1  (others_xor=0 → neg) ---
              MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["1"],"i":["1","1","0"]},mondrv_oirc=["0","1","1",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["f","r","r",""],tmg_when="i0&i1", specify=""),
              MyExpectCell(pin_oirc=["o0","i2","i2",""],ival={"o":["0"],"i":["1","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["delay","power_tout"],tmg_sense="neg",arc_oirc=["r","f","f",""],tmg_when="i0&i1", specify="(i2 => o0) = (0,0);", timing_default=True),

              #--- leakage (2^3 = 8 input combinations、XNOR=1 のとき u、XNOR=0 のとき d) ---
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","0","0"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&!i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","0","1"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&!i1&i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["0","1","0"]},mondrv_oirc=["0","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&!i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["0","1","1"]},mondrv_oirc=["1","0","0",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="!i0&i1&i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","0","0"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&!i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","0","1"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&!i1&i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["u"],"i":["1","1","0"]},mondrv_oirc=["1","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&!i2", specify=""),
              MyExpectCell(pin_oirc=["o0","i0","i0",""],ival={"o":["d"],"i":["1","1","1"]},mondrv_oirc=["0","1","1",""],meas_types=["leakage"],tmg_sense="non",arc_oirc=["s","s","s",""],tmg_when="i0&i1&i2", specify=""),
             ]
    },
  }

###############################################################################
def get_code_primitive():
    return '''
primitive lr_mux (q, d0, d1, s);
   output q;
   input s, d0, d1;
`protect
   table
   // d0  d1  s   : q 
      0   ?   0   : 0 ;
      1   ?   0   : 1 ;
      ?   0   1   : 0 ;
      ?   1   1   : 1 ;
      0   0   x   : 0 ;
      1   1   x   : 1 ;
   endtable
`endprotect
endprimitive

'''
