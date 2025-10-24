#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
# This file is part of charao.
#
# Based on OriginalProject (https://github.com/snishizawa/libretto)
# Original copyright (C) 2022-2025 Original Author
# Modified by MATSUDA Masahiro, 2025
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
import sys, inspect 
import math

def my_exit():
  frame = inspect.currentframe().f_back
  path = frame.f_code.co_filename.split('/')
  print("file:"+path[-1] +" in:"+frame.f_code.co_name+", line:"+str(frame.f_lineno))
  sys.exit()

def startup():
  print("  ")
  print("  ------------------------------------")
  print("  charao: Cell library characterizer")
  print("  Version: 0.7")
  print("  https://github.com/MatsudaLogicResearch/charao_prj")
  print("  ")

def history():
  print("  ------------------------------------")
  #print("  Version: 0.6")
  #print("  + rename to charao")
  #print("  + Support three_state.")
  #print("  Version: 0.5")
  #print("  + Support multi template in cell.")
  #print("  + Use jonc format files for configuration.")
  #print("  + Use jinja2 file for testbench.")
  #print("  Version: 0.2")
  #print("  + Support multiple slope load conditions")
  #print("  Version: 0.1")
  #print("  + Very basic version")
  #print("  + Support combinational cells")
  #print("  +++ Propagation delay, transition delay")
  #print("  +++ Dynamic power, leakage power")
  #print("  + Support sequential cells")
  #print("  ++ D-Flip-Flops, include both pos-neg edge clock, asyncronous set reset")
  #print("  +++ C2Q delay, setup, hold, recovery, removal")
  #print("  +++ Setup is defined by minimum D2Q, hold is defined by minimum D2Q")
  
def f2s_ceil(f: float, sigdigs: int=2) -> str:
  if f == 0.0:
    return "0"

  abs_f = abs(f)
  exponent = math.floor(math.log10(abs_f))
  factor = 10 ** (sigdigs - 1 - exponent)

  # 2.34 -> 2.4, -2.34 -> -2.3
  rounded = math.ceil(f * factor) / factor
  
  # format
  format_str = f"{{:.{sigdigs}g}}"
  s = format_str.format(rounded)

  # 1E3  --> 1000
  if 'e' in s or 'E' in s:
    digits_after_dot = max(0, sigdigs - math.floor(math.log10(abs(rounded))) - 1)
    s = f"{rounded:.{digits_after_dot}f}"

  #
  return s
