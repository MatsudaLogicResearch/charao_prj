import argparse, re, os, shutil, subprocess, threading
from myFunc import my_exit
from pydantic import BaseModel, model_validator, Field
from typing import Any

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
  cell_name_prefix : str = "_V1"         ; #
  vdd_name         : str = "VDD"
  vss_name         : str = "VSS"
  pwell_name       : str = "VPW"
  nwell_name       : str = "VNW"    
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
  operating_conditions        : str = "TCCOM";#usually set by argv.
  process                     : float = 1.0  ;#usually set by argv.
  temperature                 : float = 25.0 ;#usually set by argv.
  vdd_voltage                 : float = 5.0  ;#usually set by argv.
  vss_voltage                 : float = 0.0  ;#usually set by argv.
  nwell_voltage               : float = 5.0  ;#usually set by argv.
  pwell_voltage               : float = 0.0  ;#usually set by argv.
  logic_threshold_high        : float = 0.8  ;#
  logic_threshold_low         : float = 0.2  ;#
  logic_high_to_low_threshold : float = 0.5  ;#
  logic_low_to_high_threshold : float = 0.5  ;#
  energy_meas_low_threshold   : float = 0.01 ;#
  energy_meas_high_threshold  : float = 0.99 ;#
  energy_meas_time_extent     : int   = 1    ;#
  slope  : list[list[Any]]= Field(default_factory=list); # [[1, 2, 3, "slope1"],[2, 3, 4, "slope2"]]
  load   : list[list[Any]]= Field(default_factory=list);
  ## characterizer setting 
  work_dir :str = "work"
  tmp_dir  :str = "work"
  tmp_file :str = "__tmp__"
  simulator : str = "ngspice"
  runsim   :str = "true"
  num_thread : int = 1 
  sim_nice :int = 19 
  compress_result :str = "true" 
  supress_msg      :str = "false"
  supress_sim_msg  :str = "false"
  supress_debug_msg:str = "false"
  #--- calculated after instanciation
  logic_threshold_high_voltage        : float = 4.0
  logic_threshold_low_voltage         : float = 1.0
  logic_high_to_low_threshold_voltage : float = 2.5
  logic_low_to_high_threshold_voltage : float = 2.5
  energy_meas_low_threshold_voltage   : float = 0.05
  energy_meas_high_threshold_voltage  : float = 4.95
  
  
  #--- local variable
  load_name       :list[str] = Field(default_factory=list);
  slope_name      :list[str] = Field(default_factory=list);
  load_slope_name :list[str] = Field(default_factory=list); 
  compress        : str = "true"
  log_file        :str = "false"
  logf            :str = None 

  ## template_lines
  constraint_template_lines : list[float]=[]
  recovery_template_lines   : list[float]= []
  removal_template_lines    : list[float]= []
  mpw_constraint_template_lines : list[float]= []
  passive_power_template_lines  : list[float]= []
  delay_template_lines : list[float]=[]
  power_template_lines : list[float]=[]
  
  #
  #model_config ={"frozen":True};  #-- not writable
  
  #--------------------------------------------------
  #def __init__(self): 

  def print_variable(self):
    for k,v in self.__dict__.items():
      print(f"   {k}={v}")
  
    
  def update_name(self):
    #--- convert float to string.(5.0 ----> 5P0)
    vdd_str="{:.2f}".format(self.vdd_voltage);
    vdd_str=vdd_str.replace('.','P');

    #--- convert float to string.(5.0 ----> 5P0)
    vdd_str="{:.2f}V".format(self.vdd_voltage);
    vdd_str=vdd_str.replace('.','P');
    
    #--- convert float to string.( -25.0 ----> M25)
    temp_str="M{:}C".format(int(-1.0 * self.temperature)) if self.temperature < 0 else "{:}C".format(int(self.temperature))

    #---
    self.lib_name         = self.process_name + "_"+self.lib_vendor_id+"_"+vdd_str+"_"+temp_str
    self.dotlib_name      = self.lib_name + ".lib"
    self.doc_name         = self.lib_name + ".md"
    self.verilog_name     = self.lib_name + ".v"
    self.cell_name_suffix = self.process_name + "_"+self.lib_vendor_id
    
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

  def gen_lut_templates(self,  targetCell):
    tmp_load_name = targetCell.load_name
    tmp_slope_name = targetCell.slope_name
    tmp_load_slope_name = str(targetCell.load_name)+"_"+str(targetCell.slope_name)
    
    ## if targetCell.load_name is not exists, register it to targetLib.load_name
    if(targetCell.load_name not in self.load_name):
      self.load_name.append(targetCell.load_name)
      #targetLib.load_name.append([targetCell.load_name,targetCell.load])
      
    ## if targetCell.slope_name is not exists, register it to targetLib.slope_name
    if(targetCell.slope_name not in self.slope_name):
      self.slope_name.append(targetCell.slope_name)
      
      #targetLib.slope_name.append([targetCell.slope_name,targetCell.slope])
      self.constraint_template_lines.append("  lu_table_template (constraint_template_"+targetCell.slope_name+") {\n")
      self.constraint_template_lines.append("    variable_1 : constrained_pin_transition;\n")
      self.constraint_template_lines.append("    variable_2 : related_pin_transition;\n")
      self.constraint_template_lines.append("    index_1 "+targetCell.return_slope()+"\n")
      self.constraint_template_lines.append("    index_2 "+targetCell.return_slope()+"\n")
      self.constraint_template_lines.append("  }\n")
      self.recovery_template_lines.append("  lu_table_template (recovery_template_"+targetCell.slope_name+") {\n")
      self.recovery_template_lines.append("    variable_1 : related_pin_transition;    \n")
      self.recovery_template_lines.append("    variable_2 : constrained_pin_transition;\n")
      self.recovery_template_lines.append("    index_1 "+targetCell.return_slope()+"\n")
      self.recovery_template_lines.append("    index_2 "+targetCell.return_slope()+"\n")
      self.recovery_template_lines.append("  }\n")
      self.removal_template_lines.append("  lu_table_template (removal_template_"+targetCell.slope_name+") {\n")
      self.removal_template_lines.append("    variable_1 : related_pin_transition;    \n")
      self.removal_template_lines.append("    variable_2 : constrained_pin_transition;\n")
      self.removal_template_lines.append("    index_1 "+targetCell.return_slope()+"\n")
      self.removal_template_lines.append("    index_2 "+targetCell.return_slope()+"\n")
      self.removal_template_lines.append("  }\n")
      self.mpw_constraint_template_lines.append("  lu_table_template (mpw_constraint_template_"+targetCell.slope_name+") {\n")
      self.mpw_constraint_template_lines.append("    variable_1 : constrained_pin_transition;\n")
      self.mpw_constraint_template_lines.append("    index_1 "+targetCell.return_slope()+"\n")
      self.mpw_constraint_template_lines.append("  }\n")
      self.passive_power_template_lines.append("  power_lut_template (passive_power_template_"+targetCell.slope_name+") {\n")
      self.passive_power_template_lines.append("    variable_1 : input_transition_time;\n")
      self.passive_power_template_lines.append("    index_1 "+targetCell.return_slope()+"\n")
      self.passive_power_template_lines.append("  }\n")

    ## if load_slope_name is not exists, register it to targetLib.load_slope_name
    tmp_load_slope_name = str(targetCell.load_name)+"_"+str(targetCell.slope_name)
    
    if(tmp_load_slope_name not in self.load_slope_name):
      self.load_slope_name.append(tmp_load_slope_name)

      #targetLib.load_slop_name.append([targetCell.load_name,targetCell.load,targetCell.slope])
      self.delay_template_lines.append("  lu_table_template (delay_template_"+tmp_load_slope_name+") {\n")
      self.delay_template_lines.append("    variable_1 : input_net_transition;\n")
      self.delay_template_lines.append("    variable_2 : total_output_net_capacitance;\n")
      self.delay_template_lines.append("    index_1 "+targetCell.return_slope()+"\n")
      self.delay_template_lines.append("    index_2 "+targetCell.return_load()+"\n")
      self.delay_template_lines.append("  }\n")
      self.power_template_lines.append("  power_lut_template (power_template_"+tmp_load_slope_name+") {\n")
      self.power_template_lines.append("    variable_1 : input_transition_time;\n")
      self.power_template_lines.append("    variable_2 : total_output_net_capacitance;\n")
      self.power_template_lines.append("    index_1 "+targetCell.return_slope()+"\n")
      self.power_template_lines.append("    index_2 "+targetCell.return_load()+"\n")
      self.power_template_lines.append("  }\n")


