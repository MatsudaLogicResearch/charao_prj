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
#  Returns the physical (non-functional) cell definitions.
#  (filler / decap-filler / endcap / filltie: no signal pin, no timing arc)
#  User-defined Logic entries may be added via mylogic_user.py specified in ARGS.
#
#  (ISS-00172) primitive code is supplied by <target>/primitives.v.
#              see docs/SPEC_primitives.md
#
###############################################################################
# ISS-00165: 物理セル（fill/fillcap/endcap/filltie）対応。
#   - 信号ピンを持たず（power/well ピンのみ）、 timing arc も持たない
#   - SPICE subckt が空（Tr 0）or decap のみのため sim では leakage=0 → measure は行わない
#     （orig の leakage 5e-05 は sim で再現できない一律成分であり sim 由来ではない）
#   - cell_leakage_power は config_lib.jsonc の leakage_offset（嵩上げ値）で出力される
#     （myLogicCell.set_max_pleak が offset で初期化、 harness 空ならその値がそのまま残る）
#   - logic_type="physical"：comb ではないため mylogic_comb_* から分離（2026-07-24 ダーマツ判断）
###############################################################################

def get_logic_dict():
  return {
    #---------------------------------------------------------------------------------------
    # PHYSICAL: filler / decap-filler / endcap / filltie cells.
    #   No signal port (power/well pins only), no function, no timing arc, no measure.
    #   ports_dict example: {"VDD":"vdd","VNW":"vnw","VPW":"vpw","VSS":"vss"}
    #                       {"VDD":"vdd","VSS":"vss"}  (endcap / filltie)
    "PHYSICAL":{"logic_type":"physical",
           "functions":{},
           "expect":[]
    },
  }
