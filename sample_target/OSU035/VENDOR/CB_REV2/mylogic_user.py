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
# def get_logic_dict():
#  Returns Uesr-define Logic definitions.
#  Add to mylogic_base.py.
#
#  (ISS-00172) get_code_primitive() は廃止した。
#              primitive は <target>/primitives.v が供給する。
#              see docs/SPEC_primitives.md
#
###############################################################################
from charao.script.myExpectCell import MyExpectCell

###############################################################################
def get_logic_dict():
  return {}
#  return {
#    "INV":{"logic_type":"comb",
#           "functions":{"o0":"!i0"},
#           "expect":
#           [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0"]},mondrv_oir=["0","1","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
#            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1"]},mondrv_oir=["1","0","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),
#             #--- leakage
#            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0", specify=""),
#            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0", specify=""),
#            ]
#        },
#  }

###############################################################################
#--- (ISS-00172) get_code_primitive() は廃止。 primitive は primitives.v で供給する。
