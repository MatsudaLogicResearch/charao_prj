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
import argparse, re, os, shutil, subprocess, threading
from pydantic import BaseModel, model_validator, Field
from typing import Any
from itertools import groupby

from myItem import MyItemTemplate
from myFunc import my_exit

import time

class MyLibrarySetting(BaseModel):
  #=====================================
  # class variable
  
  #=====================================
  # instance variable by BaseModel
  
  isexport    : int = 0;
  isexport2doc: int = 0;
  delay_model : str = "table_lookup"

  #--- update by config_lib_common.jsonc
  process_name     : str = "FAB0P80"
  lib_vendor_id    : str = "VENDOR"      
  model_path       : str = "./target"    
  cell_spice_path  : str = "./spice"     
  io_spice_path    : str = "./spice"     
  revision         : str = "V1"
  vdd_name         : str = "VDD"
  vss_name         : str = "VSS"
  vdd2_name        : str = ""
  vss2_name        : str = ""
  pwell_name       : str = "VPW"
  nwell_name       : str = "VNW"    
  vddio_name       : str = ""
  vssio_name       : str = ""
  voltage_unit     : str = "V"
  capacitance_unit : str = "pf"
  resistance_unit  : str = "Ohm"
  current_unit     : str = "mA"
  leakage_power_unit: str = "pW"
  energy_unit       : str = "fJ"
  time_unit         : str = "ns"
  #--- self calculated after instaciation
  file_model        : str = "model_tt.spi"; #
  lib_name          : str = "libname"     ; #
  dotlib_name       : str = "libname.lib" ; #
  doc_name          : str = "libname.md"  ; #
  verilog_name      : str = "libname.v"   ; #
  cell_name_suffix  : str = "libname_"    ; #
  voltage_mag       : float = 1.0         ; #
  capacitance_mag   : float = 1e-12       ; #
  resistance_mag    : float = 1.0         ; #
  current_mag       : float = 1e-3        ; #
  leakage_power_mag : float = 1e-12       ; #
  energy_mag        : float = 1e-15       ; #
  time_mag          : float = 1e-9        ; #
  
  #--- update by config_char_cond.jsonc
  cell_group                  : str = "std"  ;#usually set by argv.
  usage_voltage               : float=5.0    ;#usually set by argv.
  process_corner              : str = "TC"   ;#usually set by argv.
  #operating_condition        : str = "TCCOM";#usually set by argv.
  #process                    : float = 1.0  ;#usually set by argv.
  temperature                 : float = 25.0 ;#usually set by argv.
  vdd_voltage                 : float = 5.0  ;#usually set by argv.
  vss_voltage                 : float = 0.0  ;#usually set by argv.
  vdd2_voltage                : float|None = None  ;#usually set by argv.
  vss2_voltage                : float|None = None  ;#usually set by argv.
  nwell_voltage               : float = 5.0  ;#usually set by argv.
  pwell_voltage               : float = 0.0  ;#usually set by argv.
  vddio_voltage               : float|None = None  ;#usually set by argv.
  vssio_voltage               : float|None = None  ;#usually set by argv.
  logic_threshold_high        : float = 0.8  ;#
  logic_threshold_low         : float = 0.2  ;#
  logic_high_to_low_threshold : float = 0.5  ;#
  logic_low_to_high_threshold : float = 0.5  ;#
  energy_meas_low_threshold   : float = 0.01 ;#
  energy_meas_high_threshold  : float = 0.99 ;#
  hold_meas_low_threshold     : float = 0.01 ;#
  hold_meas_high_threshold    : float = 0.99 ;#
  
  #slope  : list[list[Any]]= Field(default_factory=list); # [[1, 2, 3, "slope1"],[2, 3, 4, "slope2"]]
  #load   : list[list[Any]]= Field(default_factory=list);
  #slope  : dict[str,list[float]]= Field(default_factory=dict); # {"slope1":[1, 2, 3]},{"slope2":[2, 3, 4]}
  #load   : dict[str,list[float]]= Field(default_factory=dict); # {"load1":[1, 2, 3]},{"load2":[2, 3, 4]}
  #slope_loads : dict[str,MyItemSlopeLoad] =Field(default_factory=dict);
  templates : list[MyItemTemplate] =Field(default_factory=list);
  input_voltages : dict[str,Any] =Field(default_factory=dict);
  output_voltages : dict[str,Any] =Field(default_factory=dict);
  
  
  ## characterizer setting 
  work_dir :str = "work"
  tmp_dir  :str = "work"
  tmp_file :str = "__tmp__"
  simulator : str = "ngspice"
  runsim   :str = "true"
  num_thread : int = 1 
  sim_nice :int = 19

  simulation_timestep : float = 0.001
  sim_pulse_max       : float = 2.0
  sim_prop_max        : float =10.0
  sim_prop_tri_max    : float =20.0
  sim_prop_io_max     : float =20.0
  sim_prop_io_tri_max : float =20.0
  sim_d2c_max         : float = 5.0
  sim_c2d_min         : float =10.0
  sim_c2d_max         : float =200.0
  sim_c2d_max_per_unit: float = 10.0; # additional delay per 1ps.
  #sim_c2d_max         : float = 5.0;
  sim_segment_timestep_start : float = 1.0
  sim_segment_timestep_ratio : float = 0.1
  sim_segment_timestep_min   : float = 0.001
  sim_time_const_threshold   : float = 0.001
  sim_time_end_extent        : int   = 10    ;#
  sim_tsim_end4hold          : float = 50.0
  sim_pullres_enable         : float = 100
  sim_pullres_disable        : float = 0.1
  
  compress_result :str = "true" 
  supress_msg      :str = "false"
  supress_sim_msg  :str = "false"
  supress_debug_msg:str = "false"
  
  #--- calculated after instanciation
  operating_condition                 : str = "";
  
  logic_threshold_high_voltage        : float = 4.0
  logic_threshold_low_voltage         : float = 1.0
  logic_high_to_low_threshold_voltage : float = 2.5
  logic_low_to_high_threshold_voltage : float = 2.5
  energy_meas_low_threshold_voltage   : float = 0.05
  energy_meas_high_threshold_voltage  : float = 4.95
  
  #--- argv option
  significant_digits : int  = 3
  
  #--- other variable
  #load_name       :list[str] = Field(default_factory=list);
  #slope_name      :list[str] = Field(default_factory=list);
  #load_slope_name :list[str] = Field(default_factory=list); 
  compress        :str = "true"
  log_file        :str = "false"
  logf            :str = None 
  date            :str =""
  
  ## template_lines
  template_lines  : dict[str,list[str]] = Field(default_factory=lambda:{
    "const"  :[],
    "delay"  :[],
    "delay_c2c"  :[],
    "delay_c2i"  :[],
    "delay_i2c"  :[],
    "delay_i2i"  :[],
    "mpw"    :[],
    "passive":[],
    "power"  :[],
    "power_c2c"  :[],
    "power_c2i"  :[],
    "power_i2c"  :[],
    "power_i2i"  :[],
  })
  #constraint_template_lines : list[float]=[]
  #recovery_template_lines   : list[float]= []
  #removal_template_lines    : list[float]= []
  #mpw_constraint_template_lines : list[float]= []
  #passive_power_template_lines  : list[float]= []
  #delay_template_lines : list[float]=[]
  #power_template_lines : list[float]=[]
  
  #
  #model_config ={"frozen":True};  #-- not writable
  
  #--------------------------------------------------
  #def __init__(self): 

  def print_variable(self):
    for k,v in self.__dict__.items():
      print(f"   {k}={v}")
  
    
  def update_name(self):
    #--- convert float to string.(5.0 ----> 5P00V)
    uv_str="{:.2f}V".format(self.usage_voltage);
    uv_str=uv_str.replace('.','P');
    
    #--- convert float to string.(5.0 ----> 5P00V)
    vdd_str="{:.2f}V".format(self.vdd_voltage);
    vdd_str=vdd_str.replace('.','P');
    
    vdd2_str=""
    if self.vdd2_name:
      vdd2_str="{:.2f}V".format(self.vdd2_voltage);
      vdd2_str=vdd_str.replace('.','P');

    vddio_str=""
    if self.vddio_name:
      vddio_str="{:.2f}V".format(self.vddio_voltage);
      vddio_str=vdd_str.replace('.','P');
      
    #--- convert float to string.( -25.0 ----> M25C)
    temp_str="M{:}C".format(int(-1.0 * self.temperature)) if self.temperature < 0 else "{:}C".format(int(self.temperature))

    #---
    #self.operating_condition=f"{self.process_corner}_{vdd_str}_{temp_str}"
    self.operating_condition=f"{self.process_corner}{vdd_str}{vdd2_str}{vddio_str}{temp_str}"
    
    #---
    #self.lib_name         = self.process_name + "_"+self.lib_vendor_id+"_"+vdd_str+"_"+temp_str
    #basename=f"{self.process_name}_{self.lib_vendor_id}_{self.cell_group}_{uv_str}"
    basename=f"{self.process_name}_{self.lib_vendor_id}_{self.cell_group}"
    
    self.lib_name         = f"{basename}_{self.operating_condition}"
    self.dotlib_name      = f"{self.lib_name}.lib"
    self.doc_name         = f"{self.lib_name}.md"
    #self.verilog_name     = f"{self.lib_name}.v"
    self.verilog_name     = f"{basename}.v"
    
    self.cell_name_suffix = f"{basename}".upper()
    
  def update_mag(self):
    match self.voltage_unit.upper() :
      case 'V' : self.voltage_mag = 1.0;
      case 'MV': self.voltage_mag = 1e-3;
      case   _ : my_exit("illegal unit for set_voltage_unit");my_exit();
                            
    match self.capacitance_unit.upper() :
      case 'NF': self.capacitance_mag = 1e-9;
      case 'PF': self.capacitance_mag = 1e-12;
      case 'FF': self.capacitance_mag = 1e-15;
      case   _ : my_exit("illegal unit for set_capacitance_unit");my_exit();

    match self.resistance_unit.upper() :
      case 'OHM' : self.resistance_mag = 1.0;
      case 'KOHM': self.resistance_mag = 1e+3;
      case 'MOHM': self.resistance_mag = 1e+6;
      case   _ : my_exit("illegal unit for set_resistance_unit");my_exit();

    match self.time_unit.upper() :
      case 'PS': self.time_mag = 1e-12;
      case 'NS': self.time_mag = 1e-9;
      case 'US': self.time_mag = 1e-6;
      case   _ : my_exit("illegal unit for set_time_unit");my_exit();
    
    match self.current_unit.upper() :
      case 'A' : self.current_mag = 1.0;
      case 'MA': self.current_mag = 1e-3;
      case 'UA': self.current_mag = 1e-6;
      case 'NA': self.current_mag = 1e-9;
      case   _ : my_exit("illegal unit for set_current_unit");my_exit();
    
    match self.leakage_power_unit.upper() :
      case 'FW': self.leakage_power_mag = 1e-15;
      case 'PW': self.leakage_power_mag = 1e-12;
      case 'NW': self.leakage_power_mag = 1e-9;
      case 'UW': self.leakage_power_mag = 1e-6;
      case   _ : my_exit("illegal unit for set_leakage_power_unit");my_exit();
    
    match self.energy_unit.upper() :
      case 'FJ': self.energy_mag = 1e-15;
      case 'PJ': self.energy_mag = 1e-12;
      case 'NJ': self.energy_mag = 1e-9;
      case   _ : my_exit("illegal unit for set_enegy_unit");my_exit();

  def update_threshold_voltage(self):
    self.logic_threshold_high_voltage = self.logic_threshold_high * self.vdd_voltage * self.voltage_mag;
    
    self.logic_threshold_low_voltage  = self.logic_threshold_low  * self.vdd_voltage * self.voltage_mag;

    self.logic_low_to_high_threshold_voltage = self.logic_low_to_high_threshold * self.vdd_voltage * self.voltage_mag;
    
    self.logic_high_to_low_threshold_voltage = self.logic_high_to_low_threshold * self.vdd_voltage * self.voltage_mag;
    
    self.energy_meas_low_threshold_voltage = self.energy_meas_low_threshold * self.vdd_voltage * self.voltage_mag
    
    self.energy_meas_high_threshold_voltage = self.energy_meas_high_threshold * self.vdd_voltage * self.voltage_mag
                            
      

  def set_exported(self):
    self.isexport = 1 
  
  def set_exported2doc(self):
    self.isexport2doc = 1 

  def print_error(self, message=""):
    print(message)
    my_exit()

  def print_msg(self, message=""):
    if((self.supress_msg.lower() == "false")or(self.supress_msg.lower() == "f")):
      print(message)
  
  def print_msg_sim(self, message=""):
    if((self.supress_sim_msg.lower() == "false")or(self.supress_sim_msg.lower() == "f")):
      print(message)
  
  def print_msg_dbg(self,  message=""):
    if((self.supress_debug_msg.lower() == "false")or(self.supress_debug_msglower() == "f")):
      print(message)

  def gen_lut_templates(self):

    #-- lu_table_template for kind/grid
    var_1_dict={"const"  :"related_pin_transition",
                "delay"  :"input_net_transition",
                "delay_c2c"  :"input_net_transition",
                "delay_i2c"  :"input_net_transition",
                "delay_c2i"  :"input_net_transition",
                "delay_i2i"  :"input_net_transition",
                "mpw"    :"related_pin_transition",
                "passive":"input_transition_time",
                "power"  :"input_transition_time",
                "power_c2c"  :"input_transition_time",
                "power_c2i"  :"input_transition_time",
                "power_i2c"  :"input_transition_time",
                "power_i2i"  :"input_transition_time",
                }

    var_2_dict={"const"  :"constrained_pin_transition",
                "delay"  :"total_output_net_capacitance",
                "delay_c2c"  :"total_output_net_capacitance",
                "delay_c2i"  :"total_output_net_capacitance",
                "delay_i2c"  :"total_output_net_capacitance",
                "delay_i2i"  :"total_output_net_capacitance",
                "mpw"    :"not_supported",
                "passive":"not_supported",
                "power"  :"total_output_net_capacitance",
                "power_c2c"  :"total_output_net_capacitance",
                "power_c2i"  :"total_output_net_capacitance",
                "power_i2c"  :"total_output_net_capacitance",
                "power_i2i"  :"total_output_net_capacitance",
                }
      
    
    #-- remove grid="" and sort for groupby
    filtered_templates=filter(lambda x: x.grid !="", self.templates)
    sorted_templates  =sorted(filtered_templates, key=lambda x: (x.kind, x.grid))
    for (kind,grid),group in groupby(sorted_templates, key=lambda x:(x.kind, x.grid)):

      group_list=list(group)
      ptn=r"(\d+)[xX](\d+)"

      #-- decode grid size
      flag=re.match(ptn, grid)

      if flag:
        index1_num=int(flag.group(1))
        index2_num=int(flag.group(2))
        
      else:
        print(f"[Error]: grid name={grid} is illegal on {kind}/{grid}. expect=[0-9]+[xX][0-9]+")
        my_exit()

      #-- check index length
      len1=[len(d.index_1) for d in group_list]
      len2=[len(d.index_2) for d in group_list]

      #print(f"[DEBUG]len1={len1}, len2={len2} @kind={kind}, grid={grid}")
      len1_min,len1_max = min(len1),max(len1)
      len2_min,len2_max = min(len2),max(len2)

      if (len1_min != len1_max) or (len2_min != len2_max):
        print(f"[ERROR] index_1/index_2 length is missmatch in template. kind={kind}, grid={grid}.")
        my_exit()

      if (len1_min != index1_num) or (len2_min != index2_num):
          print(f'[Warnning] (index_1 x index_2)={len1}x{len2} size is missmatch with grid in template(kind={kind}/grid={grid}).')
          index1_num = len1_min
          index2_num = len2_min
          
      #-- ignore grid=0x0 
      if index1_num==0 and index2_num==0:
        continue
      
      #-- create table header
      #if kind in ["const","delay","mpw"]:
      if kind in ["const","delay","mpw","delay_c2c","delay_i2c","delay_c2i","delay_i2i"]:
        self.template_lines[kind].append(f'  lu_table_template ({kind}_template_{grid}) {{')
      else:
        self.template_lines[kind].append(f'  power_lut_template ({kind}_energy_template_{grid}) {{')
          
      #-- create variable_1
      #if index1_num>0:
      if index1_num>1:
        self.template_lines[kind].append(f'    variable_1 : {var_1_dict[kind]};')
        
      #-- create variable_2
      #if index2_num>0:
      if index2_num>1:
        self.template_lines[kind].append(f'    variable_2 : {var_2_dict[kind]};')
          
      #-- create variable_1
      #if index1_num>0:
      if index1_num>1:
        num=index1_num
        dmy_values_list=[0.001 * (i+1) for i in range(num)]
        dmy_values_str=",".join([str(x) for x in dmy_values_list])
        self.template_lines[kind].append(f'    index_1 ("{dmy_values_str}");')

      #if index2_num>0:
      if index2_num>1:
        num=index2_num
        dmy_values_list=[0.001 * (i+1) for i in range(num)]
        dmy_values_str=",".join([str(x) for x in dmy_values_list])
        self.template_lines[kind].append(f'    index_2 ("{dmy_values_str}");')

      #
      self.template_lines[kind].append(f'  }}')

      #
      print(f"   add lut_template={kind}/{grid}.")

      
  def exec_spice(self,spicef:str) ->str:
    #---
    spicelis = spicef + ".lis"
    spicerun = spicef + ".run"

    #-- command
    if(re.search("ngspice", self.simulator)):
      cmd = "nice -n "+str(self.sim_nice)+" "+str(self.simulator)+" -b "+str(spicef)+" > "+str(spicelis)+" 2>&1 \n"
    elif(re.search("hspice", self.simulator)):
      cmd = "nice -n "+str(self.sim_nice)+" "+str(self.simulator)+" "+str(spicef)+" -o "+str(spicelis)+" 2> /dev/null \n"
    elif(re.search("Xyce", self.simulator)):
      cmd = "nice -n "+str(self.sim_nice)+" "+str(self.simulator)+" "+str(spicef)+" -hspice-ext all 1> "+str(spicelis)

    #-- create execute file
    with open(spicerun,'w') as f:
      outlines = []
      outlines.append(cmd) 
      f.writelines(outlines)

    #- do spice simulation
    cmd = ['sh', spicerun]
    
    if(self.runsim == "true"):
      try:
        res = subprocess.check_call(cmd)
      except:
        print (f"Failed to lunch spice. lis={spicelis}")

    #--
    return(spicelis)
