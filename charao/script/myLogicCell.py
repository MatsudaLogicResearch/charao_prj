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
import argparse, re, os, shutil, subprocess, inspect
import copy
from pydantic import BaseModel, model_validator, Field
from typing import Any, Dict, TYPE_CHECKING, List, Optional
import statistics as st
from itertools import groupby
from pathlib import Path

from .myFunc import my_exit
from .myLibrarySetting       import MyLibrarySetting as Mls 
#from .myExpectCell           import logic_dict
from .myItem                 import MyItemTemplate

if TYPE_CHECKING:
  from .myConditionsAndResults import MyConditionsAndResults  as Mcar

class MyLogicCell(BaseModel):
  #=====================================
  # class variable
  
  #=====================================
  # instance variable by BaseModel

  #-- reference
  mls: Optional[Mls] = None
  
  spice_path: str = "./cdl"   ## path to spice
  cell      : str = None;     ## cell name
  logic     : str = None;     ## logic name
  area      : float= None;    ## set area
  spice     : str  = None;    ## spice file name
  functions : Dict[str,str] = Field(default_factory=dict); ## cell function
  vcode     : str = None;     ## verilog code
  ff        : Dict[str,str] = Field(default_factory=dict); ## ff infomation
  latch     : Dict[str,str] = Field(default_factory=dict); ## latch infomation (ISS-00070 LAT)
  #io        : Dict[str,str] = Field(default_factory=dict); ## io infomation
  #pin       : Dict[str,str] = Field(default_factory=dict); ## pin infomation for IO cell
  ports_dict: Dict[str,str] = Field(default_factory=dict); ## spice-port/name mapper

  cell_infos: Dict[str,Any]= Field(default_factory=dict); ## additional cell infomation
  rail_connections:Dict[str,str]= Field(default_factory=dict); ## additional cell infomation
  pad_infos : Dict[str,Dict[str,Any]]= Field(default_factory=dict); ## PAD infomation
  oe_infos  : Dict[str,Dict[str,Any]]= Field(default_factory=dict); ## OE infomation
  vout_infos: Dict[str,Dict[str,Any]]= Field(default_factory=dict); ## ISS-00152: const 計測の観測点差し替え（{"o0":{"node":"QD"}} 等、 xcell.xdut 配下の内部 net。 ICG の内部ラッチ出力等）
  vdd2_voltage:list[str] = Field(default_factory=list);       ## list of CORE2_VOLTAGE(vdd2)
  io_voltage:list[str] = Field(default_factory=list);       ## list of IO_VOLTAGE(vddio)
  
  inports   : list[str] = Field(default_factory=list); ## inport pins
  outports  : list[str] = Field(default_factory=list); ## outport pins
  biports   : list[str] = Field(default_factory=list); ## inout port pins
  clock     : str= None;      ## clock pin for flop
  #set       : str= None;      ## set pin for flop
  #reset     : str= None;      ## reset pin for flop 
  vports    : list[str] = Field(default_factory=list); ## vdd/vss port pins

  cins      : dict[str,float] = Field(default_factory=dict); ## inport caps. cins={"inport",cap}
  
  template_kgn: list[list[str]]= Field(default_factory=list);     ## kind/grid/name[/oport] of template
  ## ISS-00150: 出力 port 別 template（key="<kind>@<oport>"、例 "delay@o0"）。
  ##   orig は同一セルでも出力ピンごとに load 軸が異なる場合がある（adder の S/CO）。
  ##   template_kgn の第 4 要素（logic 出力 port 名）で指定。未指定の kind/port は従来のセル単位 template。
  template_pin: dict[str,MyItemTemplate] = Field(default_factory=dict);
  template: dict[str,MyItemTemplate] = Field(default_factory=lambda:{
    "leakage":None,
    "const"  :None,
    "delay"  :None,
    "delay_disable"  :None,
    "delay_c2c"  :None,
    "delay_i2c"  :None,
    "delay_c2i"  :None,
    "delay_i2i"  :None,
    "mpw"    :None,
    "passive":None,
    "power_tout":None,
    "power_tin" :None,
    "power_c2c"  :None,
    "power_i2c"  :None,
    "power_c2i"  :None,
    "power_i2i"  :None})
  
  max_load4out: dict[str,float] = Field(default_factory=dict);   ## outport load {"outport",max capacitance}
  max_trans4in: dict[str,float] = Field(default_factory=dict);   ## max transition {"inport",max transition}

  isexport            : int = 0;   ## exported or not
  isexport2doc        : int = 0; ## exported to doc or not
  isflop              : bool = False;  ## DFF or not
  islatch             : bool = False;  ## LATCH or not (ISS-00070 LAT)
  isio                : bool = False;  ## IO or not
  pleak_icrs   : dict[str,float] = Field(default_factory=dict);## leakage power with input condition. pleak_icrs={"condition",val}
  pleak_cell   : float=0.0;          ## cell leakage power

  min_pulse_width_low : dict = Field(default_factory=dict); #(port,when) -> float（ISS-00082）
  min_pulse_width_high: dict = Field(default_factory=dict); #(port,when) -> float（ISS-00082）
  
  supress_msg  : str = None;        ## supress message

  #-- local variable
  netlist      : str  = None;    ## spice file name & PATH
  definition   : str  = None;    ## dut subskt name in spice file. 
  instance     : str  = None;    ## DUT instance name in TB.
  model        : str  = "./model/TT.sp";
  
  #
  #model_config ={"frozen":True};  #-- not writable
  
  lut_names  : list[str]= Field(default_factory=list);     ## template name(const,delay,energy,passive)
  lut_template: Dict[str, MyItemTemplate] = Field(default_factory=lambda: {"const"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "delay"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "delay_c2c"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "delay_i2c"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "delay_c2i"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "delay_i2i"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           #"energy" : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "delay"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "power_c2c"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "power_i2c"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "power_c2i"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "power_i2i"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "passive": MyItemTemplate(name="", index_1=[], index_2=[])})
  #--def __init__ (self):  #-- not use

  def print_variable(self):
    for k,v in self.__dict__.items():
      print(f"   {k}={v}")

  def set_spice_path(self, spice_path:str="./cdl"):
    #self.spice_path = spice_path
    self.spice_path = Path(spice_path).resolve().as_posix(); #-- absolute PATH
    
  def set_supress_message(self):
    self.supress_msg = self.mls.supress_msg 

  def print_msg(self, message=""):
    if((self.supress_msg.lower() == "false")or(self.supress_msg.lower() == "f")):
      print(message)

  def add_template(self):

    for kgn in self.template_kgn:
      k=kgn[0]
      g=kgn[1]
      n=kgn[2]
      oport = kgn[3] if len(kgn) > 3 else ""   # ISS-00150: 第 4 要素＝出力 port 別割当（省略時は従来動作）

      # check kind/grid/name in library
      idx_src = next(
        (i for i, t in enumerate(self.mls.templates) if t.kind == k and t.grid == g and t.name == n),
        None  # no entry
      )

      if idx_src is None:
        print(f"[Error] unique template ={k}/{g}/{n} is not exist in targetLib.templates.")
        my_exit()

      # check kind in targetCell
      #print(self.template.keys())

      if k in self.template.keys():
        if oport:
          self.template_pin[f"{k}@{oport}"] = self.mls.templates[idx_src]
          print(f"   [Info] add template={k}{g}{n} for oport={oport}.")
        else:
          self.template[k] = self.mls.templates[idx_src]
          print(f"   [Info] add template={k}{g}{n}.")

      else:
        print(f"   [Error] unknown template kind={k}.")
        my_exit()

  def get_template(self, kind:str, oport:str=""):
    """ISS-00150: 出力 port 別 template があればそれを、無ければセル単位 template を返す。"""
    if oport:
      t = self.template_pin.get(f"{kind}@{oport}")
      if t is not None:
        return t
      # per-port miss → cell-level フォールバック（診断出力）
      print(f"   [TEMPLATE-FALLBACK] cell={self.cell} kind={kind} oport={oport} -> cell-level (no per-port key)")
    t = self.template.get(kind)
    if t is None:
      # 2026-07-12 ダーマツ判断(A)：template を取得できなかった場合は停止する
      print(f"[TEMPLATE-FAIL] cell={self.cell} kind={kind} oport={oport} "
            f"template_pin_keys={list(self.template_pin.keys())} template_keys={list(self.template.keys())}")
      my_exit()
    return t
        
  def update_max_trans4in(self, port_name:str, new_value:float):

    ## check port
    #if not port_name in self.inports + [self.clock]:    
    if not port_name in [p for p in (self.inports + [self.clock] + self.biports) if p is not None]:
      print(f"[Error] inport={port_name} is not exist in logic={self.logic}.")
      my_exit()
      
    ## initialize
    if not port_name in self.max_trans4in.keys():
      self.max_trans4in[port_name]=0.0

    ## update value
    #mag=self.mls.time_mag
    #self.max_trans4in[port_name] = max(new_value/mag, self.max_trans4in[port_name])
    self.max_trans4in[port_name] = max(new_value, self.max_trans4in[port_name])


    
  def update_max_load4out(self, port_name:str, new_value:float):

    ## check port
    if not port_name in (self.outports + self.biports):
      print(f"[Error] outport={port_name} is not exist in logic={self.logic}.")
      my_exit()
      
    ## initialize
    if not port_name in self.max_load4out.keys():
      self.max_load4out[port_name]=0.0

    ## update value
    #mag=self.mls.capacitance_mag
    #self.max_load4out[port_name] = max(new_value/mag, self.max_load4out[port_name])
    self.max_load4out[port_name] = max(new_value, self.max_load4out[port_name])



    
  def chk_netlist(self):
    targetLib=self.mls
    
    #if self.isio:
    #  self.netlist = targetLib.io_spice_path +"/"+self.spice
    #else:
    #  self.netlist = targetLib.cell_spice_path +"/"+self.spice
    self.netlist = f"{self.spice_path}/{self.spice}"
      
    self.definition = None

    ## search cell name in the netlist
    if not os.path.exists(self.netlist):
      print("  netlist is not exits. {0}".format(self.netlist))
      my_exit()
      
    with open(self.netlist, 'r') as f:
      for line in f:

        #print("self.cell.lower:"+str(self.cell.lower()))
        #print("line.lower:"+str(line.lower()))
        tokens = line.lower().split()
        if(len(tokens) >= 2 and tokens[0] == ".subckt" and tokens[1] == self.cell.lower()):
          print(f"   [INFO]: Cell definition found for {str(self.cell)} in netlist.")
          #print(line)
          self.definition = line
        
    ## if cell name is not found, show error
    if(self.definition == None):
      if((self.cell == None) and (self.logic == None)):
        print("Cell definition not found. Please use add_cell command to add your cell")
      elif(self.cell == None):
        print("Cell is not defined by add_cell. Please use add_cell command to add your cell")
      elif(self.logic == None):
        print("Logic is not defined by add_cell. Please use add_cell command to add your cell")
      else:
        print("Options for add_cell command might be wrong")
        print("Defined cell: "+self.cell)
        print("Defined logic: "+self.logic)
      my_exit()

  def chk_ports(self):
    self.instance = ""
    
    #-- get port name from spice file
    ports_s=self.definition.split(); # .subckt NAND2_1X A B YB VDD VSS VNW VPW
    ports_s.pop(0);                   # NAND2_1X A B YB VDD VSS VNW VPW
    cell_name=ports_s.pop(0);                   # A B YB VDD VSS VNW VPW

    #-- check port_map in cell_comb.json
    pos_s=0
    for name_j,name_tb in self.ports_dict.items():
      pos_s=pos_s + 1
      name_s = ports_s.pop(0);
      #print("pos={0}, spice={1}, json={2}.".format(pos_s, name_s, name_j))
      if name_s.upper() != name_j.upper():
        print("  Pin Name missmatch in PinPos={0}. spice={1}/json={2}.".format(pos_s,name_s,name_j))
        my_exit()

      #--- check name_tb
      if name_tb.upper().startswith("I"):
        self.inports.append(name_tb.lower())
      elif name_tb.upper().startswith("O"):
        self.outports.append(name_tb.lower())
      elif name_tb.upper().startswith("B"):
        self.biports.append(name_tb.lower())
      elif name_tb.upper().startswith("C"):
        self.clock = name_tb.lower()
      elif name_tb.upper().startswith("S"):
        #self.set = name_tb.lower()
        self.inports.append(name_tb.lower())
      elif name_tb.upper().startswith("R"):
        #self.reset = name_tb.lower()
        self.inports.append(name_tb.lower())
      elif name_tb.upper().startswith("V"):
        self.vports.append(name_tb.lower())
      else:
        print("  UnKnown port-name for TB in ports_dict(JSON file). {0}:{1}.".format(name_j,name_tb))
        my_exit()

      #--- 
      self.instance += ' ' + name_tb.lower()
      
    self.instance = 'XDUT' + self.instance + " " + cell_name
    
  def add_model(self):
    targetLib=self.mls

    #self.model = targetLib.model_path +"/.model_"+targetLib.process_name +"_"+targetLib.process_corner+".sp"
    model = targetLib.model_path +"/.model_"+targetLib.process_name +"_"+targetLib.process_corner+".sp"
    self.model = Path(model).resolve().as_posix(); #--absolute PATH

    if not os.path.exists(self.model):
      print("  model file is not exits. {0}".format(self.model))
      my_exit()
      
  #def add_simulation_timestep(self):
  #  self.simulation_timestep =self.slope[0] * self.timestep_res 

  def set_exported(self):
    self.isexport = 1 

  def set_exported2doc(self):
    self.isexport2doc = 1
        
  def add_function(self):
    if not self.logic in self.mls.logic_dict.keys():
      print(f"[Error] logic="+self.logic + " is not exist in MyExpectCell.py.");
      my_exit();

    self.functions = self.mls.logic_dict[self.logic]["functions"]
          
    print("add function: " + str(self.functions))

  def add_vcode(self):
    if "vcode" in self.mls.logic_dict[self.logic].keys():
      if self.mls.logic_dict[self.logic]["vcode"]:
        self.vcode = self.replace_by_portmap(self.mls.logic_dict[self.logic]["vcode"])
        print("add vcode")

  def add_ff(self):
    if not self.logic in self.mls.logic_dict.keys():
      print(f"[Error] logic="+self.logic + " is not exist in MyExpectCell.py.");
      my_exit();

    self.ff = self.mls.logic_dict[self.logic]["ff"]
    self.isflop=True

  def add_latch(self):
    if not self.logic in self.mls.logic_dict.keys():
      print(f"[Error] logic="+self.logic + " is not exist in MyExpectCell.py.");
      my_exit();

    self.latch = self.mls.logic_dict[self.logic]["latch"]
    self.islatch=True

  def add_io(self):
    if not self.logic in self.mls.logic_dict.keys():
      print(f"[Error] logic="+self.logic + " is not exist in MyExpectCell.py.");
      my_exit();

    self.isio=True

  ## ISS-00135 reorg(U4/U5/U6): per-pin 属性は「pin_oirc[k]==pin かつ arc_oirc[k]∈{r,f,p,n} の
  ##   位置 k の値」を全 harness 横断で集約。 cin/max_trans は入力ピン、 max_load は出力ピン。
  _TRANS = ("r", "f", "p", "n")

  @staticmethod
  def _flatten_d2(d2):
    ## dict_list2[key] (index1 -> index2 -> val) を flat list に
    return [v for i1 in d2.values() for v in i1.values()]

  def _gather_in(self, harnessList, keys):
    ## keys=("c_in","c_rel","c_clk") 等。 入力ピンごとに位置別 dict_list2 を集約
    out={}
    for inport in [p for p in (self.inports + [self.clock] + self.biports) if p is not None]:
      vals=[]
      for h in harnessList:
        po, arc = h.mec.pin_oirc, h.mec.arc_oirc
        if po[1]==inport and arc[1] in self._TRANS: vals += self._flatten_d2(h.dict_list2[keys[0]])
        if po[2]==inport and arc[2] in self._TRANS: vals += self._flatten_d2(h.dict_list2[keys[1]])
        if po[3]==inport and arc[3] in self._TRANS: vals += self._flatten_d2(h.dict_list2[keys[2]])
      out[inport]=vals
    return out

  def set_cin_avg(self, harnessList):
    mag=self.mls.capacitance_mag
    for inport, vals in self._gather_in(harnessList, ("c_in","c_rel","c_clk")).items():
      self.cins[inport] = (st.mean(vals)/mag) if vals else 0.0

  def set_cin_max(self, harnessList):
    mag=self.mls.capacitance_mag
    for inport, vals in self._gather_in(harnessList, ("c_in","c_rel","c_clk")).items():
      self.cins[inport] = (max(vals)/mag) if vals else 0.0

  def set_max_trans(self, harnessList):
    ## max_transition = 各入力ピンが駆動された最大 slew（pin_oirc[k]×arc）
    for inport, vals in self._gather_in(harnessList, ("slew_in","slew_rel","slew_clk")).items():
      if vals:
        self.max_trans4in[inport] = max(vals)

  def set_max_load(self, harnessList):
    ## max_capacitance = 各出力ピンが特性化された最大 load（pin_oirc[0]）
    for outport in self.outports:
      vals=[]
      for h in harnessList:
        if h.mec.pin_oirc[0]==outport:
          vals += self._flatten_d2(h.dict_list2["load_out"])
      if vals:
        self.max_load4out[outport] = max(vals)
      
  ## cell_cleak=max leakage
  def set_max_pleak(self, harnessList:list["Mcar"]):

    max_pleak = 0.0
    for h in [x for x in harnessList if x.measure_type == "leakage"]:
      if max_pleak < h.pleak:
        max_pleak = h.pleak
        
    #--
    self.pleak_cell=max_pleak

      
  #--- convert from local port name(i0) to spice port name(A).
  def rvs_portmap(self, local_ports:list):
    rvs_dict={v:k for k,v in self.ports_dict.items()}
    return [rvs_dict[v] for v in local_ports if v in rvs_dict]
  
  #--- replace local port name in local_str to spice port name.
  def replace_by_portmap(self, local_str):
    new_str=local_str
    
    for k,v in self.ports_dict.items():
      new_str = new_str.replace(v, k)
    return(new_str)

    
  def set_min_pulse_width(self, port_name:str, value:float, measure_type:str, when:str=""):

    ## check port
    if not port_name in [p for p in (self.inports + [self.clock]) if p is not None]:
      print(f"[Error] inport={port_name} is not exist in logic={self.logic}.")
      my_exit()

    ## check measure_type
    measure_type_list=["min_pulse_width_high","min_pulse_width_low"]
    if not measure_type in measure_type_list:
      print(f"[Error] measure_typ={measure_type} is not in {measure_type_list}")
      
    ## set value
    if measure_type=="min_pulse_width_high":
      self.min_pulse_width_high[(port_name,when)] = value/self.mls.time_mag
    else:
      self.min_pulse_width_low[(port_name,when)] = value/self.mls.time_mag
      
    ##
    #print(f"[Info] min_pulse_width={value} for {port_name}")
