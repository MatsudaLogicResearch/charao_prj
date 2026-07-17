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
import argparse, re, os, shutil, subprocess
import numpy as np
import statistics as st
import threading

from pydantic import BaseModel, model_validator, Field, PrivateAttr
from typing import Any, Dict, List, DefaultDict,Annotated,Literal, Optional
from collections import defaultdict


from .myExpectCell     import MyExpectCell as Mec
from .myLibrarySetting import MyLibrarySetting as Mls 
from .myLogicCell      import MyLogicCell      as Mlc
from .myItem           import MyItemTemplate
from .myFunc import my_exit, f2s_ceil

#DictKey=Literal["prop","trans","setup_hold",
#                "eintl","ein","cin", "pleak"]
#DictKey=Literal["prop","trans","setup_hold",
#                "eintl","ein","cin"]
DictKey=Literal["prop","trans","setup_hold","setup_hold_raw","min_pulse",
                "eintl","cin","crel","cclk",
                "c_in","c_rel","c_clk","slew_in","slew_rel","slew_clk","load_out"]

#LutKey = Literal["prop","trans","setup_hold","eintl","ein"]
LutKey = Literal["prop","trans","setup_hold","min_pulse","eintl"]

NestedDefaultDict = Annotated[
    DefaultDict[float, float],  # slope -> value
    Field(default_factory=lambda: defaultdict(float))
]

Level2Dict = Annotated[
    DefaultDict[float, NestedDefaultDict],  # load -> (slope -> value)
    Field(default_factory=lambda: defaultdict(lambda: defaultdict(float)))
]

Level3Dict = Annotated[
    DefaultDict[DictKey, Level2Dict],  #Level3Dict["prop"][index_2][index_1] = 1.234
    Field(default_factory=lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))
]

# ISS-00135 reorg: arc(極性) → Liberty 完成形キーワード文字列 の変換を 1 箇所に集約。
#   各 category(prop/tran/power/constraint) は同じ極性(rise/fall/stable)を別キーワードで表すだけ。
#   passive_power は power 列(rise_power/fall_power/stable)を流用する。
_DIR_LIB = {
  "rise":   {"prop":"cell_rise", "tran":"rise_transition", "power":"rise_power", "constraint":"rise_constraint"},
  "fall":   {"prop":"cell_fall", "tran":"fall_transition", "power":"fall_power", "constraint":"fall_constraint"},
  "stable": {"prop":"stable",    "tran":"stable",          "power":"stable",     "constraint":"stable"},
  "":       {"prop":"",          "tran":"",                "power":"",           "constraint":""},
}

def _arc_pol(arc):
  #-- arc → 極性。 0/1/z は stable。 p/n は min_pulse 専用で direction_in_lib 未使用→""。 '' はスロット無し→""。
  #   's'(旧 static, 廃止) は未知扱い(None)=エラー。 既存 's' は別の高優先課題で 0/1/z へ移行する。
  if arc == "r": return "rise"
  if arc == "f": return "fall"
  if arc in ("0", "1", "z"): return "stable"
  if arc in ("p", "n", ""):  return ""
  return None   #-- unknown ('s' 含む) → my_exit


class MyConditionsAndResults(BaseModel):
  #=====================================
  # class variable
  
  #=====================================
  # instance variable by BaseModel
  #self.instance = None          ## instance name

  #-- reference
  mls: Optional[Mls]=None
  mlc: Optional[Mlc]=None
  
  #-- for myExpectLogic
  mec: Mec = Field(default_factory=Mec)

  template_kind    : str = ""
  template         : MyItemTemplate = None
  #template_timing  : MyItemTemplate = None
  #template_energy  : MyItemTemplate = None
  
  measure_type   : str = ""
  timing_type    : str = ""
  timing_sense   : str = ""
  #timing_unate   : str = ""
  timing_when    : str = ""
  #-- ISS-00135 reorg: direction_prop/tran/power + constraint + passive_power を 1 dict に集約。
  #   key=category(prop/tran/power/constraint/passive_power) -> Liberty 完成形キーワード文字列。
  direction_in_lib : dict[str,str] = Field(
    default_factory=lambda: {"prop":"","tran":"","power":"","constraint":"","passive_power":""}
  )

  target_inport         : str = ""
  target_inport_val     : str = ""
  target_relport        : str = ""
  target_relport_val    : str = ""
  target_outport        : str = ""
  target_outport_val    : str = ""
  target_clkport        : str = ""
  target_clkport_val    : str = ""

  #-- ISS-00127: Liberty 出力用 pin 識別（pin_tr ベース、 自動推定 logic 込み）
  #   spice 制御用の target_*port とは分離して、 .lib export で参照する
  lib_target_pin        : str = ""    # `pin (X){}` の X（Liberty 出力用）
  lib_related_pin       : str = ""    # `related_pin (Y)` の Y（Liberty 出力用）

  clk_role              : str = "nouse"
  clk_init              : str = "pulse"   # pulse (default) or stable (for LAT combinational arc; auto-detect by islatch + clk_role="nouse")
  stable_inport_val      : dict[str,str] = Field(default_factory=dict); ## {"i0":"1"}
  nontarget_outport      : list[str] = Field(default_factory=list)

  #-- hold result from spice simulation ([load][slope])
  dict_list2: Level3Dict  ; # initial value is set in Level3Dict
  pleak: float = 0.0
  
  #
  lut: dict[LutKey, list[float]] = Field(
    default_factory=lambda: {key: [] for key in LutKey.__args__}
  )

  lut_min2max: dict[LutKey, list[float]] = Field(
    default_factory=lambda: {key: [] for key in LutKey.__args__}
  )

  #
#  avg: dict[AvgKey, float] = Field(
#    default_factory=lambda: {key: [] for key in AvgKey.__args__}
#  )

  min_pulse_width : float = 0.0

  # lock はモデルフィールドにしない（検証やシリアライズ対象に含めない）
  _lock: threading.Lock = PrivateAttr(default_factory=threading.Lock)
    
  #def __init__ (self):

  #@property
  #def mls(self) -> Mls:
  #  return self._mls;  #--- no setter
  #
  #@property
  #def mlc(self) -> Mlc:
  #  return self._mlc;  #--- no setter
  
  def set_update(self):
    self.set_measure_type()
    self.set_timing_type()
    self.set_timing_sense()
    self.set_timing_when()
    self.set_direction()
    self.set_target_port()
    self.set_stable_inport()
    self.set_nontarget_outport()
    
  def set_direction(self):

    arc_out = self.mec.arc_oirc[0]
    # ISS-00135 reorg: 入力方向(constraint/passive_power)は pin_tr[t] が在る pin_oirc 位置の arc を見る。
    #   setup/hold/recovery/removal→[1]、 passive→[2]、 clear/preset/delay(pin_tr[t]=o0)→[0]。
    #   出力方向(prop/tran/power)は arc_oirc[0]。 min_pulse(p/n) は direction_in_lib 未使用→""。
    _pt = self.mec.pin_tr[0] if self.mec.pin_tr else ""
    arc_in = next((self.mec.arc_oirc[k] for k in range(4)
                   if _pt and self.mec.pin_oirc[k] == _pt), "")

    po = _arc_pol(arc_out)
    pi = _arc_pol(arc_in)

    #-- unknown arc('s' 含む)はエラー。 ANTENNA は output 専用なので arc_out unknown を許容し "" 扱い。
    if po is None:
      if self.mlc.logic not in ["ANTENNA"]:
        print(f"{self.mlc.logic}")
        print(f"[Error] unknown arc_out={arc_out}(output).")
        my_exit()
      po = ""
    if pi is None:
      print(f"[Error] unknown arc_in={arc_in}(input).")
      my_exit()

    #-- 1 dict に集約（prop/tran/power=出力極性 po、 constraint/passive_power=入力極性 pi）
    self.direction_in_lib = {
      "prop":          _DIR_LIB[po]["prop"],
      "tran":          _DIR_LIB[po]["tran"],
      "power":         _DIR_LIB[po]["power"],
      "constraint":    _DIR_LIB[pi]["constraint"],
      "passive_power": _DIR_LIB[pi]["power"],
    }
      
  def set_measure_type(self):
    if self.mec.meas_type in ["rising_edge","falling_edge",
                              "setup_rising","setup_falling","hold_rising","hold_falling",
                              "removal_rising","removal_falling","recovery_rising","recovery_falling",
                              "clear", "preset",
                              "min_pulse_width_low", "min_pulse_width_high",
                              "passive"]:
      self.measure_type = self.mec.meas_type
    elif self.mec.meas_type in ["delay","delay_c2c", "delay_i2c", "delay_c2i", "delay_i2i",
                                "power_tout","power_tin","power_c2c", "power_i2c", "power_c2i", "power_i2i"]:
      self.measure_type = self.mec.meas_type
    elif self.mec.meas_type.startswith("three_state_"):
      self.measure_type = self.mec.meas_type
    elif self.mec.meas_type in ["leakage"]:
      self.measure_type = self.mec.meas_type
    else:
      print(f"[Error] unkown meas_type={self.mec.meas_type}")
      my_exit()

      
  def set_timing_type(self):
    if self.mec.meas_type in ["min_pulse_width_low","min_pulse_width_high","passive"]:
      self.timing_type = "no_type"
    elif self.mec.meas_type.startswith("delay"):
      self.timing_type = "combinational"
    elif self.mec.meas_type.startswith("power"):
      self.timing_type = "power"
    elif self.mec.meas_type.startswith("three_state_enable"):
      self.timing_type = "three_state_enable"
    elif self.mec.meas_type.startswith("three_state_disable"):
      self.timing_type = "three_state_disable"
    else:
      self.timing_type = self.mec.meas_type

  def set_timing_sense(self):
    if(self.mec.tmg_sense== 'pos'):
      self.timing_sense = "positive_unate"
    elif(self.mec.tmg_sense== 'neg'):
      self.timing_sense = "negative_unate"
    elif(self.mec.tmg_sense == 'non'):
      self.timing_sense = "non_unate"
    else:
      print("Illegal input: " + self.mec.tmg_sense+", check tmg_sense.")
      my_exit()
      
  def set_timing_when(self):
    self.timing_when = self.mec.tmg_when

  def set_function(self):
    self.function = self.mec.function 

  def set_target_port(self):
    self.set_target_outport()
    self.set_target_inport()
    self.set_target_relport()
    self.set_target_clkport()
    self.set_lib_target_related()  # ISS-00127: Liberty 出力用 pin 識別を pin_tr or 自動推定で設定


  def set_lib_target_related(self):
    """ISS-00127: Liberty 出力用 pin 識別を mylogic の pin_tr から設定。
    pin_tr は mylogic で **全 entry に必須記載**（charao 内の自動推定は実装しない）。
    詳細は docs/SPEC_pin_oirc.md §5。"""
    pin_tr = self.mec.pin_tr
    if not pin_tr or len(pin_tr) < 1:
      print(f"[Error] ISS-00127: pin_tr is mandatory for all mylogic entries. meas_type={self.mec.meas_type}, pin_oirc={self.mec.pin_oirc}, tmg_when='{self.mec.tmg_when}'")
      my_exit()
    self.lib_target_pin  = pin_tr[0]
    self.lib_related_pin = pin_tr[1] if len(pin_tr) >= 2 else ""
    # ISS-00135 reorg(#3): pin_tr[0] 非空必須。 例外: leakage で input なし(pin_oirc[2]="")は
    #   cell-level で pin 非紐付けのため空白可（ISS-00136 で再検討）
    if self.lib_target_pin == "":
      is_leak_noinput = (self.mec.meas_type == "leakage" and self.mec.pin_oirc[2] == "")
      if not is_leak_noinput:
        print(f"[Error] ISS-00135: pin_tr[0] (target) must be non-empty. meas_type={self.mec.meas_type}, pin_oirc={self.mec.pin_oirc}, pin_tr={pin_tr}")
        my_exit()


  def set_target_outport(self):
    
    pin_pos=self.mec.pin_oirc[0]

    #-- CELL without output
    if not pin_pos:
      self.target_outport      = ""
      self.target_outport_val  = ""
      return

    
    #-- get pin name & pin position
    flag=re.match(r"([a-zA-Z]+)(\d+)", pin_pos)
    if flag:
      pin=flag.group(1)
      pos=int(flag.group(2))
    else:
      print(f"  [Error] out port name={pin_pos} is illegal name.")
      my_exit()


    #-- get pin value
    ival = self.mec.ival;          #initial value dict
    val0 = ival[pin][pos] if (pin in ival and pos < len(ival[pin])) else ""

    #if val0 and  nval:
    #  self.target_outport      = pin_pos
    #  self.target_outport_val  = val0 + nval
    if val0 :
      self.target_outport      = pin_pos
      self.target_outport_val  = val0
    else :
      print(f"Error out port value error(ival={val0}).")
      my_exit();

  def set_target_inport(self):

    pin_pos=self.mec.pin_oirc[1]
    
    #-- CELL without input
    if not pin_pos:
      self.target_inport      = ""
      self.target_inport_val  = ""
      return
    
    #-- get pin name & pin position
    flag=re.match(r"([a-zA-Z]+)(\d+)", pin_pos)
    if flag:
      pin=flag.group(1)
      pos=int(flag.group(2))
    else:
      print(f"  [Error] target port name={pin_pos} is illegal name.")
      my_exit()

    #-- get pin value
    ival = self.mec.ival;          #initial value dict
    val0 = ival[pin][pos] if (pin in ival and pos < len(ival[pin])) else ""

    #if val0 and  nval:
    #  self.target_inport      = pin_pos
    #  self.target_inport_val  = val0 + nval
    if val0 :
      self.target_inport      = pin_pos
      self.target_inport_val  = val0
    else :
      print(f"Error target port value error(ival={val0}).")
      my_exit();

  def set_target_relport(self):

    pin_pos=self.mec.pin_oirc[2]
    
    #-- CELL without relport
    if not pin_pos:
      self.target_relport      = ""
      self.target_relport_val  = ""
      return
    
    #-- get pin name & pin position
    flag=re.match(r"([a-zA-Z]+)(\d+)", pin_pos)
    if flag:
      pin=flag.group(1)
      pos=int(flag.group(2))
      
    #elif pin_pos == "":
    #  #-- no clock/latch port
    #  pin_pos=None
    #  val0 = "x"

    else:
      print(f"  [Error] related port name={pin_pos} is illegal name.")
      my_exit()

    #-- get pin value
    ival = self.mec.ival;          #initial value dict
    val0 = ival[pin][pos] if (pin in ival and pos < len(ival[pin])) else ""
      
    #-- 
    if val0:
      self.target_relport      = pin_pos
      self.target_relport_val  = val0
    else :
      print(f"Error related port value error(ival={val0}).")
      my_exit();

  def set_target_clkport(self):

    #----val
    if self.mlc.clock != None:
      
      #-- get pin name & pin position
      #pin_pos=self.mec.pin_oirc[2]
      pin_pos= self.mlc.clock
      flag=re.match(r"([a-zA-Z]+)(\d+)", pin_pos)
      if flag:
        pin=flag.group(1)
        pos=int(flag.group(2))
      else:
        print(f"  [Error] clock port name={pin_pos} is illegal name.")
        my_exit()

      #-- get pin value
      ival = self.mec.ival;          #initial value dict
      val0 = ival[pin][pos] if (pin in ival and pos < len(ival[pin])) else ""

      if val0:
        self.target_clkport      = pin_pos
        self.target_clkport_val  = val0
      else :
        print(f"Error clock port value error(ival={val0}).")
        my_exit();

    #---- role
    self.clk_role= "related" if self.mec.pin_oirc[2]=="c0" else "input" if self.mec.pin_oirc[1] =="c0" else "nouse"
    #---- init mode (SPEC_seq_lat.md §5): LAT は t_init* の初期状態で 3 段判定
    #----   1) RN/SETN active        → stable（Q は reset/set で初期化）
    #----   2) inactive & E transparent → stable（latch transparent、 D で Q 初期化）
    #----   3) inactive & E not-transparent → pulse（latch closed、 init phase の E↑ で Q 初期化）
    #---- 極性はハードコードせず logic 名サフィックスから決定（charao は任意プロセス対応）：
    #----   _PE/_NE: enable 極性、 _PR/_NR: reset 極性、 _PS/_NS: set 極性
    if self.mlc.islatch:
      name = self.mlc.logic
      ival = self.mec.ival
      #-- 極性: transparent / active になる端子レベルを logic 名から決定（None = その端子なし）
      e_on = "1" if "_PE" in name else "0" if "_NE" in name else "1"
      r_on = "0" if "_NR" in name else "1" if "_PR" in name else None
      s_on = "0" if "_NS" in name else "1" if "_PS" in name else None
      #-- t_init* の端子初期値（ival）
      c_init = ival["c"][0] if ("c" in ival and ival["c"]) else None
      r_init = ival["r"][0] if ("r" in ival and ival["r"]) else None
      s_init = ival["s"][0] if ("s" in ival and ival["s"]) else None
      reset_active  = (r_on is not None and r_init == r_on)
      set_active    = (s_on is not None and s_init == s_on)
      e_transparent = (c_init == e_on)
      if reset_active or set_active:
        self.clk_init = "stable"     # 段1: RN/SETN active
      elif e_transparent:
        self.clk_init = "stable"     # 段2: inactive & E transparent
      else:
        self.clk_init = "pulse"      # 段3: inactive & E not-transparent
    else:
      self.clk_init = "pulse"

    
  def set_stable_inport(self):
    # ISS-00135 reorg(I6): pin_oirc 非空ピン（VOUT/VIN/VREL/VCLK 駆動）を除外、 残りを stable に。
    #   計測対象(pin_oirc[2]) も自動除外。 clock も特別扱いせず統一（駆動 clock は pin_oirc[3] に入る）。
    driven = {p for p in self.mec.pin_oirc if p}
    for typ in ["i", "b", "r", "s", "c"]:
      values=self.mec.ival.get(typ,[])
      for i in range (len(values)):
        pin=typ+"{:}".format(i)
        if pin not in driven:
          self.stable_inport_val[pin]=self.mec.ival[typ][i]

  def set_nontarget_outport(self):
    typ="o"
    values=self.mec.ival.get(typ,[])
    out_pin=self.target_outport
    for i in range (len(values)):

      pin=typ+"{:}".format(i)
      
      if out_pin != pin:
        self.nontarget_outport.append(pin)
        #self.nontarget_outport.append(self.mec.ival[typ][i])

    #print(f"not={self.nontarget_outport}")

        
  #def set_lut(self, template_kind:str, value_name:str):
  def set_lut(self, value_name:str):
    
    ## select mag
    #mag = self.mls.energy_mag if value_name in ["eintl","ein"] else self.mls.time_mag
    if value_name in ["ein"]:
      print("not support value_name=ein")
      my_exit()
      
    mag = self.mls.energy_mag if value_name in ["eintl"] else self.mls.time_mag

    ## ISS-00075: 出力 transition は Liberty 規約 stored = 実測(30-70%) / slew_derate_from_library で格納
    ##   （gf180 derate=0.5 → 格納値=実測×2）。trans のみ対象（delay/setup_hold 等の「時刻」は非対象）。
    ##   derate=1.0 なら従来どおり無変換。jsonc(config_lib) の slew_derate_from_library を参照。
    derate = self.mls.slew_derate_from_library if value_name == "trans" else 1.0

    ## significant digits
    sigdigs=self.mls.significant_digits
    
    ## get index
    #if value_name in ["eintl", "ein"]:
    if value_name in ["eintl"]:
      if not self.template_kind in ["power_tout","power_tin","passive", "power_c2c", "power_i2c", "power_c2i", "power_i2i"]:
        print(f"[Error] value_name={value_name}/template_kind={self.template_kind} are missmatch.")
        my_exit()
    else:
      if not self.template_kind in ["delay","delay_disable","const", "delay_c2c", "delay_i2c", "delay_c2i", "delay_i2i", "mpw"]:
        print(f"[Error] value_name={value_name}/template_kind={self.template_kind} are missmatch.")
        my_exit()

    ## skip if not dict_list2
    if not value_name in self.dict_list2.keys():
      print(f"[ERROR] dict_list2[{value_name}] is not exist.")
      my_exit()

    ##
    outline=""
    self.lut[value_name]         = []
    self.lut_min2max[value_name] = []

    index_1_list=self.template.index_1
    index_2_list=self.template.index_2
    
    index_2_list_is_none=1 if len(index_2_list)<1  else 0
    
    ## index_1
    outline = 'index_1("' + ','.join(map(str, index_1_list)) + '");'
    self.lut[value_name].append(outline)
    
    ## index_2
    if len(index_2_list)>0:
      outline = 'index_2("' + ','.join(map(str, index_2_list)) + '");'
      self.lut[value_name].append(outline)
    
    ## values
    self.lut[value_name].append("values ( \\")
    
    if len(index_2_list)<1:
      index_2_list=[0];  #-- dummy

    str_colon=""
    outline=""
    
    ##---- sort dict_list2
    if index_2_list_is_none:
      #tmp      =", ".join(f2s_ceil(f=self.dict_list2[value_name][x][0]/mag, sigdigs=sigdigs) for x in self.dict_list2[value_name].keys())
      s = [self.dict_list2[value_name][k][0] for k in sorted(index_1_list, key=lambda x: float(x))]
      tmp      =", ".join(f2s_ceil(f=x/mag/derate, sigdigs=sigdigs) for x in s)
      outline  ='"' + tmp + '"'
    else:
      for index1 in index_1_list:
        #tmp      =", ".join(f2s_ceil(f=x/mag, sigdigs=sigdigs) for x in self.dict_list2[value_name][index1].values())
        s = [self.dict_list2[value_name][index1][k] for k in sorted(index_2_list, key=lambda x: float(x))]
        tmp      =", ".join(f2s_ceil(f=x/mag/derate, sigdigs=sigdigs) for x in s)
        outline +=str_colon+'"' + tmp + '"'
        str_colon = ",\\\n          "

    self.lut[value_name].append(outline+");")

    # store min/center/max for doc
    index_2_center=index_2_list[int(len(index_2_list)/2)]
    
    #values=list(self.dict_list2[value_name][index_2_center].values())
    values=[self.dict_list2[value_name][index1][index_2_center] for index1 in self.dict_list2[value_name].keys()]

    
    val_min=np.amin  (values)
    val_mid=np.median(values)
    val_max=np.amax  (values)
    
    self.lut_min2max[value_name].append(str("{:5f}".format(val_min/mag)))
    self.lut_min2max[value_name].append(str("{:5f}".format(val_mid/mag)))
    self.lut_min2max[value_name].append(str("{:5f}".format(val_max/mag)))
    

  #def gen_instance_for_tb(self, targetLib:Mls, targetCell:Mlc) -> str :
  def gen_instance_for_tb(self) -> str :

    # parse subckt definition
    tmp_array = self.mlc.instance.split()

    #tmp_line = tmp_array[0] # remove XDUT
    tmp_line = tmp_array.pop(0)
    cell_name = tmp_array.pop(-1); # remove cell name
    
    #targetLib.print_msg(tmp_line)
    
    for w1 in tmp_array:

      # match tmp_array and harness 
      # search target inport
      is_matched = 0

      # ISS-00135 reorg(U1): pin_oirc 直参照。 pin_oirc=[o0(VOUT),i0(VIN),r0(VREL),c0(VCLK)]。
      #   clock は必ず pin_oirc[3]。 DO NOT CHANGE ORDER(CLK->REL->IN)
      if(self.mec.pin_oirc[3] and w1 == self.mec.pin_oirc[3]):
        tmp_line += ' CLK'
        is_matched += 1
        continue

      if(self.mec.pin_oirc[2] and w1 == self.mec.pin_oirc[2]):
        tmp_line += ' REL'
        is_matched += 1
        continue

      if(self.mec.pin_oirc[1] and w1 == self.mec.pin_oirc[1]):
        tmp_line += ' IN'
        is_matched += 1
        continue
      
      # search stable inport
      is_matched2=0
      for w2 in self.stable_inport_val.keys():
        if(w1 == w2):
          val = self.stable_inport_val[w2]
          if(val == '1'):
            tmp_line += ' HIGH'
            is_matched += 1
            is_matched2  =1
          elif(val == '0'):
            tmp_line += ' LOW'
            is_matched += 1
            is_matched2  =1
          else:
            print(f'Illigal input value for stable input({w1})={val}')
            my_exit()

      if is_matched2:
        continue
            
      # one target outport for one simulation (ISS-00135 reorg(U1): pin_oirc[0]=VOUT)
      if(self.mec.pin_oirc[0] and w1 == self.mec.pin_oirc[0]):
        tmp_line += ' OUT'
        is_matched += 1
        continue
        
      # search non-terget outport
      if w1 in self.nontarget_outport:
        # this is non-terget outport
        # search outdex for this port
        tmp_line += ' WFLOAT'
        is_matched += 1
        continue

      # VDD/VSS
      if(w1.upper() == self.mls.vdd_name.upper()):
          # tmp_line += ' '+w1.upper() 
          tmp_line += ' VDD' 
          is_matched += 1
          continue
        
      if(w1.upper() == self.mls.vss_name.upper()):
          # tmp_line += ' '+w1.upper() 
          tmp_line += ' VSS' 
          is_matched += 1
          continue
        
      if(w1.upper() == self.mls.pwell_name.upper()):
          # tmp_line += ' '+w1.upper() 
          tmp_line += ' VPW' 
          is_matched += 1
          continue
        
      if(w1.upper() == self.mls.nwell_name.upper()):
          # tmp_line += ' '+w1.upper() 
          tmp_line += ' VNW' 
          is_matched += 1
          continue

      #
      print(f"[Error] not used port name={w1} in XDUT")
      print(f"[Error]  instance={self.mlc.instance}")
      print(f"Error]   pin_oirc={self.mec.pin_oirc}")
      print(f"Error]   pin_tr  ={self.mec.pin_tr}")
      print(f"Error]   nontarget_outport={self.nontarget_outport}")
      print(f"Error]   stable_inport_val={self.stable_inport_val}")
      my_exit()
        
    ## show error if this port has not matched
    if(is_matched == 0):
      ## if w1 is wire name, abort
      ## check this is instance tmp_array[0] or circuit name tmp_array[-1]
      if((w1 != tmp_array[0]) and (w1 != tmp_array[-1])): 
        print("port: "+str(w1)+" has not matched in netlist parse!! " + tmp_array[0] + " or " + tmp_array[-1])
        my_exit()
          
    #tmp_line += " "+str(tmp_array[len(tmp_array)-1])+"\n" # CIRCUIT NAME
    tmp_line += " "+cell_name+"\n"

    return(tmp_line)
    
