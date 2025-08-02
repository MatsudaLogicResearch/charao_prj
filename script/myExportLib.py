import argparse, re, os, shutil, subprocess, sys, inspect, datetime 
from itertools import groupby

from myFunc import my_exit, f2s_ceil
from myLibrarySetting       import MyLibrarySetting        as Mls 
from myLogicCell            import MyLogicCell             as Mlc
from myConditionsAndResults import MyConditionsAndResults  as Mcar
#from myExpectCell          import MyExpectCell
from myExpectCell          import logic_dict              
from myExpectCell          import code_primitive

def exportFiles(harnessList:list[Mcar]):

  ## remove unuse harness
  harnessList_new=[h for h in harnessList if h.measure_type != "no_type"]
  
  ## refer to  harness
  targetLib = harnessList_new[0].mls
  targetCell= harnessList_new[0].mlc
  
  ## initialize tmp file
  if(targetLib.isexport == 0):
    initLib(targetLib)

  ## generate / update library general settings 
  exportLib(targetLib)
  
  ## export comb. logic
  if((targetLib.isexport == 1) and (targetCell.isexport == 0)):
    exportHarness(harnessList_new)
    exportVerilog(targetLib, targetCell)
    compressFiles(targetLib, targetCell)
    
## initialize export lib and verilog 
def initLib(targetLib:Mls):
  
  ## initilize dotlib file
  outlines = []
  with open(targetLib.tmp_file, 'w') as f:
    f.writelines(outlines)
  
  ## initilize verilog file 
  outlines = []
  with open(targetLib.verilog_name, 'w') as f:
    outlines.append(f'// Verilog model for {targetLib.lib_name} \n')
    outlines.append(f'`timescale 1ns/1ns\n')
    outlines.append(f'\n')
    outlines.append(f'{code_primitive}')
    outlines.append(f'\n')
    
    f.writelines(outlines)


## export library definition to .lib
def exportLib(targetLib:Mls):

  with open(targetLib.dotlib_name, 'w') as f:
    outlines = []
    ## general settings
    outlines.append("/* dotlib file generated libretto; */\n")
    outlines.append("library ("+targetLib.lib_name+"){\n")
    outlines.append("  delay_model : \""+targetLib.delay_model+"\";\n")
    outlines.append("  capacitive_load_unit (1,"+targetLib.capacitance_unit+");\n")
    outlines.append("  current_unit : \"1"+targetLib.current_unit+"\";\n")
    outlines.append("  leakage_power_unit : \"1"+targetLib.leakage_power_unit+"\";\n")
    outlines.append("  pulling_resistance_unit : \"1"+targetLib.resistance_unit+"\";\n")
    outlines.append("  time_unit : \"1"+targetLib.time_unit+"\";\n")
    outlines.append("  voltage_unit : \"1"+targetLib.voltage_unit+"\";\n")
    outlines.append("  voltage_map ("+targetLib.vdd_name+", "+str(targetLib.vdd_voltage)+");\n")
    outlines.append("  voltage_map ("+targetLib.vss_name+", "+str(targetLib.vss_voltage)+");\n")
    outlines.append("  voltage_map (GND , "+str(targetLib.vss_voltage)+");\n")
    outlines.append("  default_cell_leakage_power : 0;\n")
    outlines.append("  default_fanout_load : 1;\n")
    outlines.append("  default_max_transition : 1000;\n")
    outlines.append("  default_input_pin_cap : 0;\n")
    outlines.append("  default_inout_pin_cap : 0;\n")
    outlines.append("  default_leakage_power_density : 0;\n")
    outlines.append("  default_max_fanout : 100;\n")
    outlines.append("  default_output_pin_cap : 0;\n")
    outlines.append("  in_place_swap_mode : match_footprint;\n")
    outlines.append("  input_threshold_pct_fall : "+str(targetLib.logic_high_to_low_threshold*100)+";\n")
    outlines.append("  input_threshold_pct_rise : "+str(targetLib.logic_low_to_high_threshold*100)+";\n")
    outlines.append("  nom_process : 1;\n")
    outlines.append("  nom_temperature : \""+str(targetLib.temperature)+"\";\n")
    outlines.append("  nom_voltage : \""+str(targetLib.vdd_voltage)+"\";\n")
    outlines.append("  output_threshold_pct_fall : "+str(targetLib.logic_high_to_low_threshold*100)+";\n")
    outlines.append("  output_threshold_pct_rise : "+str(targetLib.logic_low_to_high_threshold*100)+";\n")
    outlines.append("  slew_derate_from_library : 1;\n")
    outlines.append("  slew_lower_threshold_pct_fall : "+str(targetLib.logic_threshold_low*100)+";\n")
    outlines.append("  slew_lower_threshold_pct_rise : "+str(targetLib.logic_threshold_low*100)+";\n")
    outlines.append("  slew_upper_threshold_pct_fall : "+str(targetLib.logic_threshold_high*100)+";\n")
    outlines.append("  slew_upper_threshold_pct_rise : "+str(targetLib.logic_threshold_high*100)+";\n")
    ## operating conditions
    outlines.append("  operating_conditions ("+targetLib.operating_condition+") {\n")
    outlines.append("    process : 1;\n")
    outlines.append("    temperature : "+str(targetLib.temperature)+";\n")
    outlines.append("    voltage : "+str(targetLib.vdd_voltage)+";\n")
    outlines.append("  }\n")
    outlines.append("  default_operating_conditions : "+targetLib.operating_condition+";\n")
    
    ## definition of LUT template
    outlines.extend(targetLib.template_lines["const"])
    outlines.extend(targetLib.template_lines["delay"])
    outlines.extend(targetLib.template_lines["mpw"])
    outlines.extend(targetLib.template_lines["passive"])
    outlines.extend(targetLib.template_lines["power"])

    ## voltage
    outlines.append("  input_voltage (default_"+targetLib.vdd_name+"_"+targetLib.vss_name+"_input) {\n")
    outlines.append("    vil : "+str(targetLib.vss_voltage)+";\n")
    outlines.append("    vih : "+str(targetLib.vdd_voltage)+";\n")
    outlines.append("    vimin : "+str(targetLib.vss_voltage)+";\n")
    outlines.append("    vimax : "+str(targetLib.vdd_voltage)+";\n")
    outlines.append("  }\n")
    outlines.append("  output_voltage (default_"+targetLib.vdd_name+"_"+targetLib.vss_name+"_output) {\n")
    outlines.append("    vol : "+str(targetLib.vss_voltage)+";\n")
    outlines.append("    voh : "+str(targetLib.vdd_voltage)+";\n")
    outlines.append("    vomin : "+str(targetLib.vss_voltage)+";\n")
    outlines.append("    vomax : "+str(targetLib.vdd_voltage)+";\n")
    outlines.append("  }\n")
  
    f.writelines(outlines)
  f.close()
  targetLib.set_exported()


## export harness data to .lib
def exportHarness(harnessList:list[Mcar]):

  ## refer to  harness
  targetLib = harnessList[0].mls
  targetCell= harnessList[0].mlc
  
  ##
  sigdigs = targetLib.significant_digits
  
  ##
  with open(targetLib.tmp_file, 'a') as f:
    outlines = []
    
    outlines.append(f'  cell ({targetCell.cell}) {{\n') ## cell start
    #outlines.append(f'    cell_leakage_power : {targetCell.pleak_cell};\n')
    outlines.append(f'    cell_leakage_power : {f2s_ceil(f=targetCell.pleak_cell, sigdigs=sigdigs)};\n')
    
    outlines.append(f'    area : {targetCell.area};\n')
    outlines.append(f'    cell_footprint : "{targetCell.logic}";\n')

    if targetCell.isflop:
      outlines.append(f'    ff ({targetCell.replace_by_portmap(targetCell.ff["out"])}){{\n')
      outlines.append(f'      next_state :"{targetCell.replace_by_portmap(targetCell.ff["next_state"])}";\n')
      outlines.append(f'      clocked_on :"{targetCell.replace_by_portmap(targetCell.ff["clocked_on"])}";\n')
      for k in ["clear","preset","clear_preset_var1", "clear_preset_var2"]:
        if k in targetCell.ff.keys():
          outlines.append(f'      {k}      :"{targetCell.replace_by_portmap(targetCell.ff[k])}";\n')
      outlines.append(f'    }}\n')
    
    outlines.append(f'    pg_pin ({targetLib.vdd_name}){{\n')
    outlines.append(f'      pg_type : primary_power;\n')
    outlines.append(f'      voltage_name : "{targetLib.vdd_name}";\n')
    outlines.append(f'    }}\n')
    outlines.append(f'    pg_pin ({targetLib.vss_name}){{\n')
    outlines.append(f'      pg_type : primary_ground;\n')
    outlines.append(f'      voltage_name : "{targetLib.vss_name}";\n')
    outlines.append(f'    }}\n')


    
    ##=========================================================================
    ## for output port
    for outport in targetCell.outports:

      h_list = [h for h in harnessList if (h.template_kind in ["delay","power"]) and (h.target_outport==outport)]
      h_list_out = sorted(h_list, key=lambda x: (x.target_relport, x.timing_type, x.timing_when, x.direction_prop));
      
      if len(h_list_out) < 1:
        #print(f"Error: no harness result exist for target={outport}.")
        #my_exit()
        print(f"[Warn]: no harness result exist for target={outport}.")
        continue

      ##-------------------------------------------------------------------------
      ## pin infomation
      outlines.append(f'    pin ({targetCell.replace_by_portmap(outport)}){{\n') ## out pin start
      outlines.append(f'      direction : output;\n')
      outlines.append(f'      function : "{targetCell.replace_by_portmap(targetCell.functions[outport])}";\n')
      
      outlines.append(f'      related_power_pin : "{targetLib.vdd_name}";\n')
      outlines.append(f'      related_ground_pin : "{targetLib.vss_name}";\n')
      outlines.append(f'      max_capacitance : "{f2s_ceil(f=targetCell.max_load4out[outport],sigdigs=sigdigs)}";\n') ## use max val. of load table
      
      outlines.append(f'      output_voltage : default_{targetLib.vdd_name}_{targetLib.vss_name}_output;\n')

      h_list_out_t = [h for h in h_list_out if (h.template_kind== "delay")]
      h_list_out_e = [h for h in h_list_out if (h.template_kind== "power")]
      
      ##-------------------------------------------------------------------------
      ## timing(delay)
      sorted_harnessList=sorted(h_list_out_t, key=lambda x: (x.target_relport, x.timing_type, x.timing_when))
      for (target_relport,timing_type,timing_when),group in groupby(sorted_harnessList, key=lambda x:(x.target_relport, x.timing_type, x.timing_when)):
        group_list=list(group);
        size=len(group_list)
        print(f"  [INFO] group(delay): target={outport}, relport={target_relport}, timing_type={timing_type}, timing_when={timing_when} -> {size}")

        size_exp=1 if timing_type in ["clear","preset"] else 2
        if size != size_exp: ## pair of fall/rise
          print(f"Error: len(group) is not {size_exp}(={size}) @{timing_type}")
          my_exit()

        ## check
        h1 = group_list[0]
        if size > 1:
          h2 = group_list[1]
        
          if (h1.stable_inport_val.keys() != h2.stable_inport_val.keys()) :
            print("Error: stable_inport missmatch in %s . harness[N]=%s, harness[N+1]=%s." %(targetCell.logic, h1.stable_inport_val.keys(), h2.stable_inport_val.keys()));
            my_exit();
          
          if (h1.timing_sense != h2.timing_sense) :
            print("Error: timing_sense missmatch in %s. harness[N]=%s, harness[N+1]=%s." %(targetCell.logic, h1.timing_sense, h2.timing_sense));
            my_exit();

        ## infomation
        outlines.append(f'      timing () {{\n')
        outlines.append(f'        related_pin : "{targetCell.replace_by_portmap(target_relport)}";\n')

        #-- when/sense/type
        if h1.timing_when:
          outlines.append(f'        when  : "{targetCell.replace_by_portmap(h1.timing_when).replace("&"," ")}";\n')
          outlines.append(f'        sdf_cond  : "{targetCell.replace_by_portmap(h1.timing_when).replace("&"," ")}";\n')
        
        outlines.append(f'        timing_sense : "{h1.timing_sense}";\n')
        outlines.append(f'        timing_type : "{h1.timing_type}";\n')

        
        ## propagation & transition
        for h in group_list:
          t=h.template
          outlines.append(f'        {h.direction_prop} ({t.kind}_template_{t.grid}) {{\n')
          
          for lut_line in h.lut["prop"]:
            outlines.append(f'          {lut_line}\n')
          outlines.append(f'        }}\n') 

          #
          outlines.append(f'        {h.direction_tran} ({t.kind}_template_{t.grid}) {{\n')
          for lut_line in h.lut["trans"]:
            outlines.append(f'          {lut_line}\n')
          outlines.append(f'        }}\n') 

        outlines.append(f'      }}\n') ## timing end

      ##-------------------------------------------------------------------------
      ## energy(power)
      sorted_harnessList=sorted(h_list_out_e, key=lambda x: (x.target_relport, x.timing_type, x.timing_when))
      for (target_relport,timing_type,timing_when),group in groupby(sorted_harnessList, key=lambda x:(x.target_relport, x.timing_type, x.timing_when)):
        group_list=list(group);
        size=len(group_list)
        print(f"  [INFO] group(power): target={outport}, relport={target_relport}, timing_type={timing_type}, timing_when={timing_when} -> {size}")
        
        size_exp=1 if timing_type in ["clear","preset"] else 2
        if size != size_exp:
          print(f"Error: len(group) is not {size_exp}(={size}) @{timing_type}")

        ## check
        h1 = group_list[0]
        if size > 1:
          h2 = group_list[1]
        
          if (h1.stable_inport_val.keys() != h2.stable_inport_val.keys()) :
            print("Error: stable_inport missmatch in %s . harness[N]=%s, harness[N+1]=%s." %(targetCell.logic, h1.stable_inport_val.keys(), h2.stable_inport_val.keys()));
            my_exit();
          
          if (h1.timing_sense != h2.timing_sense) :
            print("Error: timing_sense missmatch in %s. harness[N]=%s, harness[N+1]=%s." %(targetCell.logic, h1.timing_sense, h2.timing_sense));
            my_exit();
          
        #-- infomation
        outlines.append(f'      internal_power () {{\n')
        outlines.append(f'        related_pin : "{targetCell.replace_by_portmap(target_relport)}";\n')

        #-- when
        if h1.timing_when != "":
          outlines.append(f'        when  : "{targetCell.replace_by_portmap(h1.timing_when).replace("&"," ")}";\n')

        ## rise(fall)
        for h in group_list:
          t = h.template
          outlines.append(f'        {h.direction_power} ({t.kind}_energy_template_{t.grid}) {{\n')
          
          for lut_line in h.lut["eintl"]:
            outlines.append(f'          {lut_line}\n')
          outlines.append(f'        }}\n')
        
        outlines.append(f'      }}\n') ## port end        
      outlines.append(f'    }}\n') ## out pin end

    ##=========================================================================
    ## select one input pin from pinlist 
    for inport in [p for p in (targetCell.inports + [targetCell.clock]) if p is not None]:

      ##-------------------------------------------------------------------------
      ## pin infomation
      outlines.append(f'    pin ({targetCell.replace_by_portmap(inport)}){{\n') ## out pin start
      outlines.append(f'      direction : input; \n')
      outlines.append(f'      related_power_pin : {targetLib.vdd_name};\n')
      outlines.append(f'      related_ground_pin : {targetLib.vss_name};\n')
      
      max_transition = targetCell.max_trans4in[inport] if (inport in targetCell.max_trans4in.keys()) else 3.0
      outlines.append(f'      max_transition : {f2s_ceil(f=max_transition, sigdigs=sigdigs)};\n')
      
      max_capacitance = targetCell.cins[inport] if ( inport in targetCell.cins.keys()) else 3.0
      outlines.append(f'      capacitance : "{f2s_ceil(f=max_capacitance, sigdigs=sigdigs)}";\n')
      
      outlines.append(f'      input_voltage : default_{targetLib.vdd_name}_{targetLib.vss_name}_input;\n')

      if inport == "c0":
        outlines.append(f'      clock : true;\n')

      if inport in targetCell.min_pulse_width_high.keys():
        outlines.append(f'      min_pulse_width_high : {f2s_ceil(f=targetCell.min_pulse_width_high[inport], sigdigs=sigdigs)};\n')
        
      if inport in targetCell.min_pulse_width_low.keys():
        outlines.append(f'      min_pulse_width_low : {f2s_ceil(f=targetCell.min_pulse_width_low[inport], sigdigs=sigdigs)};\n')
      
      ##-------------------------------------------------------------------------
      ## check timing/power infomation
      h_list = [h for h in harnessList if (h.template_kind in ["const","passive"]) and (h.target_inport == inport)]
      h_list_in = sorted(h_list, key=lambda x: (x.target_relport, x.timing_type, x.timing_when, x.constraint));
      
      if len(h_list_in) < 1:
        print(f"[INFO]: no harness result exist for target={inport}.")
        outlines.append(f'    }}\n') ## input pin end
        continue
      
      h_list_in_c = [h for h in h_list_in if (h.template_kind== "const")]
      h_list_in_p = [h for h in h_list_in if (h.template_kind== "passive")]
      
      ##-------------------------------------------------------------------------
      ## timing(const)
      sorted_harnessList=sorted(h_list_in_c, key=lambda x: (x.target_relport, x.timing_type, x.timing_when))
      for (target_relport,timing_type,timing_when),group in groupby(sorted_harnessList, key=lambda x:(x.target_relport, x.timing_type, x.timing_when)):
        group_list=list(group);
        size=len(group_list)
        print(f"  [INFO] group(const): target={inport}, relport={target_relport}, timing_type={timing_type}, timing_when={timing_when} -> {size}")

        size_exp=1 if timing_type in ["removal_rising","removal_falling","recovery_rising","recovery_falling"] else 2
        if size != size_exp: ## pair of fall/rise
          print(f"Error: len(group) is not {size_exp}(={size}) @{timing_type}")
          my_exit()

        ## check
        h1 = group_list[0]
        if size > 1:
          h2 = group_list[1]
        
          if (h1.stable_inport_val.keys() != h2.stable_inport_val.keys()) :
            print("Error: stable_inport missmatch in %s . harness[N]=%s, harness[N+1]=%s." %(targetCell.logic, h1.stable_inport_val.keys(), h2.stable_inport_val.keys()));
            my_exit();
          
          if (h1.timing_sense != h2.timing_sense) :
            print("Error: timing_sense missmatch in %s. harness[N]=%s, harness[N+1]=%s." %(targetCell.logic, h1.timing_sense, h2.timing_sense));
            my_exit();

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        outlines.append(f'      timing () {{\n')
        outlines.append(f'        related_pin : "{targetCell.replace_by_portmap(target_relport)}";\n')

        #-- when/sense/type
        if h1.timing_when:
          outlines.append(f'        when  : "{targetCell.replace_by_portmap(h1.timing_when).replace("&"," ")}";\n')
          outlines.append(f'        sdf_cond  : "{targetCell.replace_by_portmap(h1.timing_when).replace("&"," ")}";\n')
        
        outlines.append(f'        timing_type : "{h1.timing_type}";\n')

        ## constraint
        for h in group_list:
          t=h.template
          outlines.append(f'        {h.constraint } ({t.kind + "_template_" + t.grid }) {{\n')
          
          for lut_line in h.lut["setup_hold"]:
            outlines.append(f'          {lut_line}\n')
          outlines.append(f'        }}\n') 

        outlines.append(f'      }}\n') ## timing end

      ##-------------------------------------------------------------------------
      ## energy(passive)
      sorted_harnessList=sorted(h_list_in_p, key=lambda x: (x.target_relport, x.timing_type, x.timing_when))
      for (target_relport,timing_type,timing_when),group in groupby(sorted_harnessList, key=lambda x:(x.target_relport, x.timing_type, x.timing_when)):
        group_list=list(group);
        size=len(group_list)
        print(f"  [INFO] group(passive): inport={inport}, relport={target_relport}, timing_type={timing_type}, timing_when={timing_when} -> {size}")
        
        size_exp=1 if timing_type in ["removal_rising","removal_fallin","removal_rising","removal_falling"] else 2
        if size != size_exp:
          print(f"Error: len(group) is not {size_exp}(={size}) @ {timing_type}")

        ## check
        h1 = group_list[0]
        if size > 1:
          h2 = group_list[1]
        
          if (h1.stable_inport_val.keys() != h2.stable_inport_val.keys()) :
            print("Error: stable_inport missmatch in %s . harness[N]=%s, harness[N+1]=%s." %(targetCell.logic, h1.stable_inport_val.keys(), h2.stable_inport_val.keys()));
            my_exit();
          
          if (h1.timing_sense != h2.timing_sense) :
            print("Error: timing_sense missmatch in %s. harness[N]=%s, harness[N+1]=%s." %(targetCell.logic, h1.timing_sense, h2.timing_sense));
            my_exit();
          
        #-- infomation
        outlines.append(f'      internal_power () {{\n')

        #-- when
        if h1.timing_when != "":
          outlines.append(f'        when  : "{targetCell.replace_by_portmap(h1.timing_when).replace("&"," ")}";\n')

        ## rise(fall)
        for h in group_list:
          t = h.template
          outlines.append(f'        {h.passive_power} ({t.kind}_energy_template_{t.grid}) {{\n')
          
          for lut_line in h.lut["eintl"]:
            outlines.append(f'          {lut_line}\n')
          outlines.append(f'        }}\n')

      
        outlines.append(f'      }}\n') ## port end        
      outlines.append(f'    }}\n') ## in pin end

    outlines.append(f'  }}\n') ## cell end
    f.writelines(outlines)
    
  targetCell.set_exported()


## export library definition to .lib
def exportVerilog(targetLib:Mls, targetCell:Mlc):

  cell_suffix=targetLib.cell_name_suffix
  
  with open(targetLib.verilog_name, 'a') as f:
    outlines = []

    #--
    ports_s=targetCell.definition.split(); # .subckt NAND2_1X A B YB VDD VSS VNW VPW
    ports_s.pop(0);                   # NAND2_1X A B YB VDD VSS VNW VPW
    ports_s.pop(0);                   # A B YB VDD VSS VNW VPW
    portlist = "(" + ",".join(ports_s) + ");"
    
    outlines.append(f'`celldefine\n')
    outlines.append(f'module {targetCell.cell} {portlist}\n')
    #outlines.append(f'module {targetCell.cell}_{cell_suffix} {portlist}\n')

    ## input/output statement
    for outport in targetCell.rvs_portmap(targetCell.outports):
      outlines.append(f'output {outport};\n')
      
    for clkport in targetCell.rvs_portmap([targetCell.clock]):
      outlines.append(f'input {clkport};\n')
      
    for inport in targetCell.rvs_portmap(targetCell.inports):
      outlines.append(f'input {inport};\n')

    ## inout statement
    for target_biport in targetCell.rvs_portmap(targetCell.biports):
      outlines.append(f'inout {target_biport};\n')

    ## power statement
    for target_vport in targetCell.rvs_portmap(targetCell.vports):
      outlines.append(f'inout {target_vport};\n')

    #===================================================================
    ## branch for sequencial cell
    if(targetCell.isflop):
      ## lr_dff (q, d, cp, cdn, sdn, notifier)  ---- q=o0, d=i0, cp=c0, cdn=r0, sdn=s0
      
      ##---- clock
      if "c0" != targetCell.clock:
        print(f"[ERROR] clock port is not defined.")
        my_exit()
      cp     = targetCell.rvs_portmap(["c0"])[0]
      cp_buf = cp
        
      ##---- d
      if "i0" not in  targetCell.inports:
        print(f"[ERROR] clock port is not defined.")
        my_exit()

      d=targetCell.rvs_portmap(["i0"])[0]
      d_buf = d
        
      ##---- reset
      rst_buf ="rst_buf"
      if "r0" in targetCell.inports:
        rst =targetCell.rvs_portmap(["r0"])[0]
        outlines.append(f'buf   ({rst_buf}, {rst});\n')
      else:
        outlines.append(f'pullup({rst_buf});\n')

      ##---- set
      set_buf ="set_buf"
      if "s0" in targetCell.inports:
        set =targetCell.rvs_portmap(["s0"])[0]
        outlines.append(f'buf   ({set_buf}, {set});\n')
      else:
        outlines.append(f'pullup({set_buf});\n')

      ##---- q
      q_buf ="q_buf"
      if "o0" in targetCell.outports:
        q =targetCell.rvs_portmap(["o0"])[0]
        outlines.append(f'buf   ({q}, {q_buf});\n')
      else:
        print(f"[ERROR] output port(o0) is not defined.")
        my_exit()

      ##---- qn
      qn_buf ="qn_buf"
      if "o1" in targetCell.inports:
        qn =targetCell.rvs_portmap(["o1"])[0]
        outlines.append(f'not   ({qn}, {qn_buf});\n')

      ##---- notifier
      outlines.append(f'reg   notifier;\n')
      
      ##---- instance
      outlines.append(f'lr_dff({q_buf},{d_buf},{cp_buf},{rst_buf},{set_buf},notifier);\n')
        
    #===================================================================
    ## branch for combinational cell
    else:
      ## assign statement
      for outport in targetCell.outports:
        outlines.append(f'assign {targetCell.replace_by_portmap(outport)} = {targetCell.replace_by_portmap(targetCell.functions[outport])};\n')

    #===================================================================
    ## specify
    outlines.append(f'\n');
    outlines.append(f'specify\n');
    
    for expectationdict in logic_dict[targetCell.logic]["expect"]:
      if expectationdict.specify != "":
        when   =targetCell.replace_by_portmap(expectationdict.tmg_when)

        flag_ifnone=False
        if expectationdict.specify.endswith(";;"):
          flag_ifnone=True;
          
        specify=targetCell.replace_by_portmap(expectationdict.specify.replace(";;",";"))
        
        if when != "":
          outlines.append(f'  if ({when}) {specify}\n');
        else:
          outlines.append(f'  {specify}\n');

        if flag_ifnone:
          outlines.append(f'  ifnone {specify}\n');
        
    outlines.append(f'endspecify\n');
    outlines.append(f'endmodule\n')
    outlines.append(f'`endcelldefine\n\n')
    f.writelines(outlines)
  f.close()


## compress (Cristiano, 20240514)
def compressFiles(targetLib, targetCell):
  if(targetLib.compress == "true"):
    now = datetime.datetime.now()
    dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
    targetLib.print_msg(dt_string+" creating "+targetCell.cell+" directory")
    cmd_str = "mkdir "+targetLib.work_dir+"/"+targetCell.cell 
    subprocess.run(cmd_str, shell=True)  
    targetLib.print_msg(dt_string+" compress "+targetCell.cell+" characterization result")
    
    cmd_str = "mv "+targetLib.work_dir+"/vt*"+targetCell.cell+"* "+targetLib.work_dir+"/"+targetCell.cell 
    subprocess.run(cmd_str, shell=True)
    
    #cmd_str = "tar -zcvf "+targetLib.work_dir+"/"+targetCell.cell+".tgz "+targetLib.work_dir+"/"+targetCell.cell 
    cmd_str = "tar -zcf "+targetLib.work_dir+"/"+targetCell.cell+".tgz "+targetLib.work_dir+"/"+targetCell.cell 
    cmd_str += " && rm -rf " + targetLib.work_dir+"/"+targetCell.cell
    subprocess.run(cmd_str, shell=True)

## export harness data to .lib
def exitFiles(targetLib, num_gen_file):
  try:
    with open(targetLib.dotlib_name, 'a') as out:
      with open(targetLib.tmp_file, 'r') as infile:
        out.write(infile.read())
        out.write(f"\n}}\n")

    #
    print(f"\n--  generation completed!!  ")
    print(f"--  {num_gen_file} cells generated in {targetLib.dotlib_name}.\n")

  except FileNotFoundError as e:
    print(f"[ERROR] no file exist.: {e.filename}")
  except Exception as e:
    print(f"[ERROR] unknown error: {e}")
