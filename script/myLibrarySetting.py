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
                            
      
  #def set_lib_name(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.lib_name = tmp_array[1] 
  #  #print(tmp_array[1])
  #  
  #def set_dotlib_name(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.dotlib_name = tmp_array[1] 
  #  #print(tmp_array[1])
  #  
  #def set_doc_name(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.doc_name = tmp_array[1] 
  #  #print(tmp_array[1])
  #      
  #def set_verilog_name(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.verilog_name = tmp_array[1] 
  #  #print(tmp_array[1])
  #  
  #def set_cell_name_suffix(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.cell_name_suffix = tmp_array[1] 
  #  #print(tmp_array[1])
  #
  #def set_cell_name_prefix(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.cell_name_prefix = tmp_array[1] 
  #  #print(tmp_array[1])
  #
  #def set_voltage_unit(self, line="tmp"):
  #  tmp_array = line.split()
  #  #print(tmp_array[1])
  #  if(tmp_array[1].upper() == 'V'):
  #    self.voltage_unit = "V" 
  #    self.voltage_mag = 1  
  #  elif(tmp_array[1].upper() == 'MV'):
  #    self.voltage_unit = "mV"  
  #    self.voltage_mag = 1e-3 
  #  else:
  #    my_exit("illegal unit for set_voltage_unit")
  #
  #def set_capacitance_unit(self, line="tmp"):
  #  tmp_array = line.split()
  #  #print(tmp_array[1])
  #  if(tmp_array[1].upper() == 'PF'):
  #    self.capacitance_unit = "pF"  
  #    self.capacitance_mag = 1e-12  
  #  elif(tmp_array[1].upper() == 'NF'):
  #    self.capacitance_unit = "nF"  
  #    self.capacitance_mag = 1e-9 
  #  else:
  #    print("illegal unit for set_capacitance_unit")
  #    my_exit()
  #
  #def set_resistance_unit(self, line="tmp"):
  #  tmp_array = line.split()
  #  #print(tmp_array[1])
  #  if(tmp_array[1].upper() == 'OHM'):
  #    self.resistance_unit = "Ohm"  
  #    self.resistance_mag = 1 
  #  elif(tmp_array[1].upper() == 'KOHM'):
  #    self.resistance_unit = "kOhm" 
  #    self.resistance_mag = 1e3 
  #  else:
  #    print("illegal unit for set_resistance_unit")
  #    my_exit()
  #
  #def set_time_unit(self, line="tmp"):
  #  tmp_array = line.split()
  #  #print(tmp_array[1])
  #  if(tmp_array[1].upper() == 'PS'):
  #    self.time_unit = "ps" 
  #    self.time_mag = 1e-12 
  #  elif(tmp_array[1].upper() == 'NS'):
  #    self.time_unit = "ns" 
  #    self.time_mag = 1e-9  
  #  elif(tmp_array[1].upper() == 'US'):
  #    self.time_unit = "us" 
  #    self.time_mag = 1e-6  
  #  else:
  #    print("illegal unit for set_time_unit")
  #    my_exit()
  #
  #def set_current_unit(self, line="tmp"):
  #  tmp_array = line.split()
  #  #print(tmp_array[1])
  #  if(tmp_array[1].upper() == 'A'):
  #    self.current_unit = "A" 
  #    self.current_mag = 1  
  #  elif(tmp_array[1].upper() == 'MA'):
  #    self.current_unit = "mA"  
  #    self.current_mag = 1e-3 
  #  elif(tmp_array[1].upper() == 'UA'):
  #    self.current_unit = "uA"  
  #    self.current_mag = 1e-6 
  #  else:
  #    print("illegal unit for set_current_unit")
  #    my_exit()
  #
  #def set_leakage_power_unit(self, line="tmp"):
  #  tmp_array = line.split()
  #  #print(tmp_array[1])
  #  if(tmp_array[1].upper() == 'PW'):
  #    self.leakage_power_unit = "pW"  
  #    self.leakage_power_mag = 1e-12  
  #  elif(tmp_array[1].upper() == 'NW'):
  #    self.leakage_power_unit = "nW"  
  #    self.leakage_power_mag = 1e-9 
  #  else:
  #    print("illegal unit for set_leakage_power_unit")
  #    my_exit()
  #
  #def set_energy_unit(self, line="tmp"):
  #  tmp_array = line.split()
  #  #print(tmp_array[1])
  #  if(tmp_array[1].upper() == 'FJ'):
  #    self.energy_unit = "fJ" 
  #    self.energy_mag = 1e-12 
  #  elif(tmp_array[1].upper() == 'PJ'):
  #    self.energy_unit = "pJ" 
  #    self.energy_mag = 1e-9  
  #    print("Energy unit is not in fJ!")
  #  elif(tmp_array[1].upper() == 'NJ'):
  #    self.energy_unit = "nJ" 
  #    self.energy_mag = 1e-6  
  #    print("Energy unit is not in fJ!")
  #  else:
  #    print("illegal unit for set_energy_unit")
  #    my_exit()
  #
  #def set_vdd_name(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.vdd_name = tmp_array[1] 
  #  #print(tmp_array[1])
  #
  #def set_vss_name(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.vss_name = tmp_array[1] 
  #  #print(tmp_array[1])
  #
  #def set_pwell_name(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.pwell_name = tmp_array[1] 
  #  #print(tmp_array[1])
  #
  #def set_nwell_name(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.nwell_name = tmp_array[1] 
  #  #print(tmp_array[1])
  #
  #def set_process(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.process = tmp_array[1] 
  #  #print(tmp_array[1])
  #
  #def set_temperature(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.temperature = float(tmp_array[1]) 
  #  #print(tmp_array[1])
  #
  #def set_vdd_voltage(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.vdd_voltage = float(tmp_array[1]) 
  #  #print(self.vdd_voltage)
  #
  #def set_vss_voltage(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.vss_voltage = float(tmp_array[1]) 
  #  #print(tmp_array[1])
  #
  #def set_nwell_voltage(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.nwell_voltage = float(tmp_array[1]) 
  #  #print(tmp_array[1])
  #
  #def set_pwell_voltage(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.pwell_voltage = float(tmp_array[1]) 
  #  #print(tmp_array[1])
  #
  #def set_logic_threshold_high(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.logic_threshold_high = float(tmp_array[1])
  #  self.logic_threshold_high_voltage = float(tmp_array[1])*self.vdd_voltage*self.voltage_mag
  #  #print(tmp_array[1])
  #
  #def set_logic_threshold_low(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.logic_threshold_low = float(tmp_array[1])
  #  self.logic_threshold_low_voltage = float(tmp_array[1])*self.vdd_voltage*self.voltage_mag
  #  #print(tmp_array[1])
  #
  #def set_logic_high_to_low_threshold(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.logic_high_to_low_threshold = float(tmp_array[1])
  #  self.logic_high_to_low_threshold_voltage = float(tmp_array[1])*self.vdd_voltage*self.voltage_mag
  #  #print(tmp_array[1])
  #
  #def set_logic_low_to_high_threshold(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.logic_low_to_high_threshold = float(tmp_array[1])
  #  self.logic_low_to_high_threshold_voltage = float(tmp_array[1])*self.vdd_voltage*self.voltage_mag
  #  #print(tmp_array[1])
  #
  #def set_work_dir(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.work_dir = tmp_array[1] 
  #  #print(tmp_array[1])
  #
  #def set_tmp_dir(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.tmp_dir = tmp_array[1] 
  #  #print(tmp_array[1])
  #
  #def set_tmp_file(self, line="__tmp__"):
  #  tmp_array = line.split()
  #  self.tmp_file = self.tmp_dir+"/"+tmp_array[1] 
  #  #print(tmp_array[1])
  #
  #def set_sim_nice(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.sim_nice = tmp_array[1] 
  #  #print(tmp_array[1])
  #
  #def set_simulator(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.simulator = tmp_array[1] 
  #  if(re.search("ngspice", self.simulator)):
  #    print("Set simulator ngspice")
  #  elif(re.search("hspice", self.simulator)):
  #    print("Set simulator hspice")
  #  elif(re.search("Xyce", self.simulator)):
  #    print("Set simulator Xyce")
  #  else:
  #    print("Simulator "+self.simulator+" is not supported!")
  #    my_exit()
  #
  #def set_compress_result(self, line="True"):
  #  tmp_array = line.split()
  #  self.compress_result = tmp_array[1] 
  #  #print(tmp_array[1])
  #
  #def set_energy_meas_low_threshold(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.energy_meas_low_threshold = float(tmp_array[1]) 
  #  self.energy_meas_low_threshold_voltage = float(tmp_array[1]) *self.vdd_voltage*self.voltage_mag
  #  #print(tmp_array[1])
  #
  #def set_energy_meas_high_threshold(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.energy_meas_high_threshold = float(tmp_array[1]) 
  #  self.energy_meas_high_threshold_voltage = float(tmp_array[1]) *self.vdd_voltage*self.voltage_mag
  #  #print(tmp_array[1])
  #
  #def set_energy_meas_time_extent(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.energy_meas_time_extent = float(tmp_array[1])
  #  #print(tmp_array[1])
  #
  #def set_operating_conditions(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.operating_conditions = tmp_array[1] 
  #  #print(tmp_array[1])
  #
  ## self.slope is 2D array
  ## [[1, 2, 3, "slope1"],[2, 3, 4, "slope2"]]
  #def set_slope(self, line="tmp"):
  #  line = re.sub('\{','',line)
  #  line = re.sub('\}','',line)
  #  line = re.sub('^set_slope ','',line)
  #  tmp_array = line.split()
  #  tmp_name = tmp_array.pop(0) # pop out slope name
  #  tmp_slope = [] 
  #  for w in tmp_array:
  #    #self.slope.append(float(w))
  #    tmp_slope.append(float(w))
  #  tmp_slope.append(tmp_name)
  #  self.slope.append(tmp_slope)
  #  # print (self.slope)
  #
  ## self.load is 2D array
  ## [[1, 2, 3, "load1"],[2, 3, 4, "load2"]]
  #def set_load(self, line="tmp"):
  #  line = re.sub('\{','',line)
  #  line = re.sub('\}','',line)
  #  line = re.sub('^set_load ','',line)
  #  tmp_array = line.split()
  #  tmp_name = tmp_array.pop(0) # pop out load name
  #  tmp_load = [] 
  #  for w in tmp_array:
  #    #self.load.append(float(w))
  #    tmp_load.append(float(w))
  #  tmp_load.append(tmp_name)
  #  self.load.append(tmp_load)
  #  # print (self.load)
  #
  def set_exported(self):
    self.isexport = 1 
  
  def set_exported2doc(self):
    self.isexport2doc = 1 
  
  #def set_compress_result(self, line="true"):
  #  tmp_array = line.split()
  #  self.compress = tmp_array[1] 
  #
  #def set_run_sim(self, line="true"):
  #  tmp_array = line.split()
  #  self.runsim = tmp_array[1] 
  #  print(tmp_array[1])
  #
  #def set_num_thread(self, line="true"):
  #  tmp_array = line.split()
  #  self.num_thread = int(tmp_array[1]) 
  #  print(line)
  #
  #def set_supress_message(self, line="false"):
  #  tmp_array = line.split()
  #  self.supress_msg = tmp_array[1] 
  #  self.print_msg(line)
  #
  #def set_supress_sim_message(self, line="false"):
  #  tmp_array = line.split()
  #  self.supress_sim_msg = tmp_array[1] 
  #  self.print_msg(line)
  #
  #def set_supress_debug_message(self, line="false"):
  #  tmp_array = line.split()
  #  self.supress_debug_msg = tmp_array[1] 
  #  self.print_msg(line)

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



