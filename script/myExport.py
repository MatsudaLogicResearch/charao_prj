
import argparse, re, os, shutil, subprocess, sys, inspect, datetime 
from itertools import groupby

from myFunc import my_exit
#import myExpectLogic as mel
from myLibrarySetting       import MyLibrarySetting        as Mls 
from myLogicCell            import MyLogicCell             as Mlc
from myConditionsAndResults import MyConditionsAndResults  as Mcar
from myExpectLogic          import MyExpectLogic           as Mel
from myExpectLogic          import logic_dict              

def exportFiles(harnessList:list[Mcar]):

  ## refer to  harness
  targetLib = harnessList[0].mls
  targetCell= harnessList[0].mlc
  
  ## initialize tmp file
  if(targetLib.isexport == 0):
    initLib(targetLib, targetCell)

  ## generate / update library general settings 
  exportLib(targetLib, targetCell)

  ## export comb. logic
  if((targetLib.isexport == 1) and (targetCell.isexport == 0) and (targetCell.isflop == 0)):
    exportHarness(harnessList)
    exportVerilog(targetLib, targetCell)
    compressFiles(targetLib, targetCell)
  ## export seq. logic
  elif((targetLib.isexport == 1) and (targetCell.isexport == 0) and (targetCell.isflop == 1)):
    exportHarnessFlop(targetLib, targetCell, harnessList2)
    exportVerilogFlop(targetLib, targetCell)
    compressFiles(targetLib, targetCell)

## initialize export lib and verilog 
def initLib(targetLib:Mls, targetCell:Mlc):
  
  ## initilize dotlib file
  outlines = []
  with open(targetLib.tmp_file, 'w') as f:
    f.writelines(outlines)
  f.close()
  ## initilize verilog file 
  outlines = []
  with open(targetLib.verilog_name, 'w') as f:
    outlines.append("// Verilog model for "+targetLib.lib_name+"; \n")
    outlines.append("`timescale 1ns/1ns\n")
    f.writelines(outlines)
  f.close()

## export library definition to .lib
def exportLib(targetLib:Mls, targetCell:Mlc):
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
    outlines.append("  operating_conditions ("+targetLib.operating_conditions+") {\n")
    outlines.append("    process : 1;\n")
    outlines.append("    temperature : "+str(targetLib.temperature)+";\n")
    outlines.append("    voltage : "+str(targetLib.vdd_voltage)+";\n")
    outlines.append("  }\n")
    outlines.append("  default_operating_conditions : "+targetLib.operating_conditions+";\n")
    
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
  with open(targetLib.tmp_file, 'a') as f:
    outlines = []
    outlines.append("\n") 
    outlines.append("  cell ("+targetCell.cell+") {\n") ## cell start
    outlines.append("    area : "+str(targetCell.area)+";\n")
    ##outlines.append("    cell_leakage_power : "+targetCell.pleak+";\n")
    #outlines.append("    cell_leakage_power : "+harnessList2[0][0].pleak+";\n") ## use leak of 1st harness
    #outlines.append("    cell_leakage_power : "+str(harnessList[0].avg["pleak"])+";\n") ## use leak of 1st harness
    outlines.append("    cell_leakage_power : "+str(targetCell.pleak_cell)+";\n")
    outlines.append("    pg_pin ("+targetLib.vdd_name+"){\n")
    outlines.append("      pg_type : primary_power;\n")
    outlines.append("      voltage_name : \""+targetLib.vdd_name+"\";\n")
    outlines.append("    }\n")
    outlines.append("    pg_pin ("+targetLib.vss_name+"){\n")
    outlines.append("      pg_type : primary_ground;\n")
    outlines.append("      voltage_name : \""+targetLib.vss_name+"\";\n")
    outlines.append("    }\n")

    ## for output port
    for outport in targetCell.outports:
      h_list = [h for h in harnessList if h.template_kind in ["delay","power"]]
      
      h_list_out = sorted(h_list, key=lambda x: (x.target_relport, x.timing_type, x.timing_when, x.direction_prop));
      
      if len(h_list_out) < 1:
        #print(f"Error: no harness result exist for target={outport}.")
        #my_exit()
        print(f"[Warn]: no harness result exist for target={outport}.")
        continue

      ## output pin infomation
      #outlines.append("    pin ("+ target_outport+"){\n") ## out pin start
      outlines.append("    pin ("+ targetCell.replace_by_portmap(outport)+"){\n") ## out pin start
      outlines.append("      direction : output;\n")
      #outlines.append("      function : \"("+targetCell.functions[target_outport]+")\";\n")
      outlines.append("      function : \"("+targetCell.replace_by_portmap(targetCell.functions[outport])+")\";\n")
      outlines.append("      related_power_pin : \""+targetLib.vdd_name+"\";\n")
      outlines.append("      related_ground_pin : \""+targetLib.vss_name+"\";\n")
      outlines.append("      max_capacitance : \""+str(targetCell.max_load4out[outport])+"\";\n") ## use max val. of load table
      outlines.append("      output_voltage : default_"+targetLib.vdd_name+"_"+targetLib.vss_name+"_output;\n")

      h_list_out_t = [h for h in h_list_out if (h.template_kind== "delay")]
      h_list_out_e = [h for h in h_list_out if (h.template_kind== "power")]

      ## timing(delay)
      sorted_harnessList=sorted(h_list_out_t, key=lambda x: (x.target_relport, x.timing_type, x.timing_when))
      for (target_relport,timing_type,timing_when),group in groupby(sorted_harnessList, key=lambda x:(x.target_relport, x.timing_type, x.timing_when)):
        group_list=list(group);
        size=len(group_list)
        print(f" group: target={outport}, relport={target_relport}, timing_type={timing_type}, timing_when={timing_when} -> {size}")

        size_exp=1 if timing_type in ["clear","preset"] else 2
        if size != size_exp: ## pair of fall/rise
          print(f"Error: len(group) is not {size_exp}(={size})")
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
        outlines.append("      timing () {\n")
        outlines.append("        related_pin : \""+targetCell.replace_by_portmap(target_relport)+"\";\n")

        #-- when/sense/type
        if h1.timing_when:
          outlines.append("        when  : \""+targetCell.replace_by_portmap(h1.timing_when).replace('&',' ')+"\";\n")
          outlines.append("        sdf_cond  : \""+targetCell.replace_by_portmap(h1.timing_when).replace('&',' ')+"\";\n")
        
        outlines.append("        timing_sense : \""+h1.timing_sense+"\";\n")
        outlines.append("        timing_type : \""+h1.timing_type+"\";\n")

        
        ## propagation & transition
        for h in group_list:
          t=h.template
          outlines.append("        " + h.direction_prop + " (" + t.kind + "_template_" + t.grid + ") {\n")
          
          for lut_line in h.lut["prop"]:
            outlines.append("          "+lut_line+"\n")
          outlines.append("        }\n") 

          #
          outlines.append("        " + h.direction_tran + " (" + t.kind + "_template_" + t.grid + ") {\n")
          for lut_line in h.lut["trans"]:
            outlines.append("          "+lut_line+"\n")
          outlines.append("        }\n") 

        outlines.append("      }\n") ## timing end

      ## energy(power)
      sorted_harnessList=sorted(h_list_out_e, key=lambda x: (x.target_relport, x.timing_type, x.timing_when))
      for (target_relport,timing_type,timing_when),group in groupby(sorted_harnessList, key=lambda x:(x.target_relport, x.timing_type, x.timing_when)):
        group_list=list(group);
        size=len(group_list)
        print(f" group: target_outport={outport}, target_relport={target_relport}, timing_type={timing_type}, timing_when={timing_when} -> {size}")
        
        size_exp=1 if timing_type in ["clear","preset"] else 2
        if size != 2:
          print(f"Error: len(group) is not {size_exp}(={size})")

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
        outlines.append("      internal_power () {\n")
        outlines.append("        related_pin : \""+targetCell.replace_by_portmap(target_relport)+"\";\n")

        #-- when
        if h1.timing_when != "":
          outlines.append("        when  : \""+targetCell.replace_by_portmap(h1.timing_when).replace('&',' ')+"\";\n")

        ## rise(fall)
        for h in group_list:
          t = h.template
          outlines.append("        "+h.direction_power+" (" + t.kind + "_energy_template_" + t.grid + ") {\n")
          
          for lut_line in h.lut["eintl"]:
            outlines.append("          "+lut_line+"\n")
          outlines.append("        }\n")
        
        outlines.append("      }\n") ## poert end
        
      outlines.append("    }\n") ## out pin end

    ## select one input pin from pinlist 
    for inport in targetCell.inports + [targetCell.clock]:
      #index1 = targetCell.inports.index(inport) 
      outlines.append("    pin ("+targetCell.replace_by_portmap(inport)+"){\n") ## out pin start
      outlines.append("      direction : input; \n")
      outlines.append("      related_power_pin : "+targetLib.vdd_name+";\n")
      outlines.append("      related_ground_pin : "+targetLib.vss_name+";\n")
      #outlines.append("      max_transition : "+str(targetCell.slope[-1])+";\n")
      #outlines.append("      capacitance : \""+str(targetCell.cins[index1])+"\";\n")

      max_transition = targetCell.max_trans4in[inport] if (inport in targetCell.max_trans4in.keys()) else 3.0
      outlines.append("      max_transition : "+str(max_transition)+";\n")
      
      max_capacitance = targetCell.cins[inport] if ( inport in targetCell.cins.keys()) else 3.0
      outlines.append("      capacitance : \""+str(max_capacitance)+"\";\n")
      
      outlines.append("      input_voltage : default_"+targetLib.vdd_name+"_"+targetLib.vss_name+"_input;\n")
      outlines.append("    }\n") ## in pin end

    outlines.append("  }\n") ## cell end
    f.writelines(outlines)
  f.close()
  targetCell.set_exported()

## export harness data to .lib
def exportHarnessFlop(targetLib, targetCell, harnessList2):
  with open(targetLib.tmp_file, 'a') as f:
    outlines = []
    outlines.append("  cell ("+targetCell.cell+") {\n") #### cell start
    outlines.append("    area : "+str(targetCell.area)+";\n")
##    outlines.append("    cell_leakage_power : "+targetCell.leak+";\n")
    outlines.append("    pg_pin ("+targetLib.vdd_name+"){\n")
    outlines.append("      pg_type : primary_power;\n")
    outlines.append("      voltage_name : \""+targetLib.vdd_name+"\";\n")
    outlines.append("    }\n")
    outlines.append("    pg_pin ("+targetLib.vss_name+"){\n")
    outlines.append("      pg_type : primary_ground;\n")
    outlines.append("      voltage_name : \""+targetLib.vss_name+"\";\n")
    outlines.append("    }\n")

    ## define flop
    outlines.append("    ff ("+str(targetCell.flops[0])+","+str(targetCell.flops[1])+"){\n") 
    outlines.append("    clocked_on : \""+targetCell.clock+"\";\n") 
    for target_inport in targetCell.inports:
      outlines.append("    next_state : \""+target_inport+"\";\n") 
    if targetCell.reset is not None:
      if(re.search('PR', targetCell.reset)):  ## posedge async. reset
        outlines.append("    clear : \""+targetCell.reset+"\";\n")   
      else:
        outlines.append("    clear : \"!"+targetCell.reset+"\";\n") 
    if targetCell.set is not None:
      if(re.search('PS', targetCell.set)):  ## posedge async. set
        outlines.append("    preset : \""+targetCell.set+"\";\n") 
      else:
        outlines.append("    preset : \"!"+targetCell.set+"\";\n") 
      if targetCell.reset is not None:
        ## value when set and reset both activate
        ## tool does not support this simulation, so hard coded to low
        outlines.append("    clear_preset_var1 : L ;\n") 
        outlines.append("    clear_preset_var2 : L ;\n") 
    outlines.append("    }\n") 
    ##
    ## (1) clock
    ##
    if targetCell.clock is not None:
      # index1 = targetCell.clock.index(target_clock) 
      index1 = 0 
      target_inport = targetCell.clock
      outlines.append("    pin ("+target_inport+"){\n") ## clock pin start 
      outlines.append("      direction : input;\n")
      outlines.append("      related_power_pin : \""+targetLib.vdd_name+"\";\n")
      outlines.append("      related_ground_pin : \""+targetLib.vss_name+"\";\n")
      outlines.append("      max_transition : "+str(targetCell.slope[-1])+";\n")
      #targetLib.print_msg(targetCell.cclks)
      outlines.append("      capacitance : \""+str(targetCell.cclks[index1])+"\";\n")
      outlines.append("      input_voltage : default_"+targetLib.vdd_name+"_"+targetLib.vss_name+"_input;\n")
      outlines.append("      clock : true;\n") 
  #   internal_power() {
  #     rise_power(passive_energy_template_7x1) {
  #       index_1 ("0.01669, 0.030212, 0.094214, 0.230514, 0.461228, 0.919101, 2.29957");
  #       values ("0.040923, 0.0374, 0.044187, 0.046943, 0.045139, 0.051569, 0.080466");
  #     }
  #     fall_power(passive_energy_template_7x1) {
  #       index_1 ("0.016236, 0.030811, 0.094437, 0.232485, 0.461801, 0.919137, 2.29958");
  #       values ("0.038868, 0.03793, 0.033501, 0.043008, 0.042432, 0.048973, 0.08357");
  #     }
  #   }
  #   min_pulse_width_high : 0.145244;
  #   min_pulse_width_low : 0.226781;
      outlines.append("    }\n") ## clock pin end



    ##
    ## (2) prop/tran/setup/hold for input pins 
    ##
    for target_inport in targetCell.inports:
      for target_outport in targetCell.outports:
        ## select inport with setup/hold informatioin
        index2 = targetCell.inports.index(target_inport) 
        index1 = targetCell.outports.index(target_outport) 
        #print(harnessList2[index1][index2*2].timing_type_setup)
        if((harnessList2[index1][index2*2].timing_type_setup == "setup_rising") or (harnessList2[index1][index2*2].timing_type_setup == "setup_falling")):
          outlines.append("    pin ("+target_inport+"){\n") #### inport pin start 
          outlines.append("      direction : input;\n")
          outlines.append("      related_power_pin : \""+targetLib.vdd_name+"\";\n")
          outlines.append("      related_ground_pin : \""+targetLib.vss_name+"\";\n")
          outlines.append("      max_transition : "+str(targetCell.slope[-1])+";\n")
#          targetLib.print_msg(targetCell.cins)
#          targetLib.print_msg(targetCell)
#          targetLib.print_msg(targetCell.inports)
#          targetLib.print_msg(targetCell.outports)
#          targetLib.print_msg(target_outport)
          outlines.append("      capacitance : \""+str(targetCell.cins[index1])+"\";\n")
          outlines.append("      input_voltage : default_"+targetLib.vdd_name+"_"+targetLib.vss_name+"_input;\n")
          ## (2-1) setup
          outlines.append("      timing () {\n")
          outlines.append("        related_pin : \""+targetCell.clock+"\";\n")
          outlines.append("        timing_type : \""+harnessList2[index1][index2*2].timing_type_setup+"\";\n")
          ## setup rise
          #outlines.append("        "+harnessList2[index1][index2*2].timing_sense_setup+" (constraint_template) {\n")
          outlines.append("        "+harnessList2[index1][index2*2].timing_sense_setup+" ("+targetCell.constraint_template_name+") {\n")
          for lut_line in harnessList2[index1][index2*2].lut_setup:
            outlines.append("          "+lut_line+"\n")
          outlines.append("        }\n") 
          ## setup fall
          #outlines.append("        "+harnessList2[index1][index2*2+1].timing_sense_setup+" (constraint_template) {\n")
          outlines.append("        "+harnessList2[index1][index2*2+1].timing_sense_setup+" ("+targetCell.constraint_template_name+") {\n")
          for lut_line in harnessList2[index1][index2*2+1].lut_setup:
            outlines.append("          "+lut_line+"\n")
          outlines.append("        }\n")
                                        
          outlines.append("      }\n") 
          ## (2-2) hold
          outlines.append("      timing () {\n")
          index1 = targetCell.outports.index(target_outport) 
          outlines.append("        related_pin : \""+targetCell.clock+"\";\n")
          outlines.append("        timing_type : \""+harnessList2[index1][index2*2].timing_type_hold+"\";\n")
          ## hold rise
          #outlines.append("        "+harnessList2[index1][index2*2].timing_sense_hold+" (constraint_template) {\n")
          outlines.append("        "+harnessList2[index1][index2*2].timing_sense_hold+" ("+targetCell.constraint_template_name+") {\n")
          for lut_line in harnessList2[index1][index2*2].lut_hold:
            outlines.append("          "+lut_line+"\n")
          outlines.append("        }\n") 
          ## hold fall
          #outlines.append("        "+harnessList2[index1][index2*2+1].timing_sense_hold+" (constraint_template) {\n")
          outlines.append("        "+harnessList2[index1][index2*2+1].timing_sense_hold+" ("+targetCell.constraint_template_name+") {\n")
          for lut_line in harnessList2[index1][index2*2+1].lut_hold:
            outlines.append("          "+lut_line+"\n")
          outlines.append("        }\n") 
          outlines.append("      }\n") 
    outlines.append("    }\n") ## inport pin end

    ##
    ## (3) outport 
    ##
    for target_outport in targetCell.outports:
      index1 = targetCell.outports.index(target_outport) 
      outlines.append("    pin ("+target_outport+"){\n") #### out pin start
      outlines.append("      direction : output;\n")
      #outlines.append("      function : \"("+targetCell.functions[index1]+")\";\n")
      outlines.append("      function : \"("+targetCell.functions[target_outport]+")\";\n")
      outlines.append("      related_power_pin : \""+targetLib.vdd_name+"\";\n")
      outlines.append("      related_ground_pin : \""+targetLib.vss_name+"\";\n")
      outlines.append("      max_capacitance : \""+str(targetCell.load[-1])+"\";\n") ## use max val. of load table
      outlines.append("      output_voltage : default_"+targetLib.vdd_name+"_"+targetLib.vss_name+"_output;\n")
      ## (3-1) clock
      if targetCell.clock is not None:
        ## index2 is a base pointer for harness search
        ## index2_offset and index2_offset_max are used to 
        ## search harness from harnessList2 which contain "timing_type_set"
        index2 = targetCell.outports.index(target_outport) 
        index2_offset = 0
        index2_offset_max = 10
        while(index2_offset < index2_offset_max):
          if hasattr(harnessList2[index1][index2*2+index2_offset], "timing_type_setup"):
            break
          index2_offset += 1
        if(index2_offset == 10):
          print("Error: index2_offset exceed max. search number\n")
          my_exit()

        ##target_inport = targetCell.clock
        outlines.append("      timing () {\n")
        outlines.append("        related_pin : \""+targetCell.clock+"\";\n")
        outlines.append("        timing_type : \""+harnessList2[index1][index2*2+index2_offset].timing_type_clock+"\";\n")
        outlines.append("        timing_sense : \""+harnessList2[index1][index2*2+index2_offset].timing_sense_clock+"\";\n")
        #### (3-1-1) rise
        ## propagation delay
        #outlines.append("        "+harnessList2[index1][index2*2+index2_offset].direction_prop+" (delay_template) {\n")
        outlines.append("        "+harnessList2[index1][index2*2+index2_offset].direction_prop+" ("+targetCell.delay_template_name+") {\n")
        for lut_line in harnessList2[index1][index2*2+index2_offset].lut_prop:
          outlines.append("          "+lut_line+"\n")
        outlines.append("        }\n") 
        ## transition delay
        #outlines.append("        "+harnessList2[index1][index2*2+index2_offset].direction_tran+" (delay_template) {\n")
        outlines.append("        "+harnessList2[index1][index2*2+index2_offset].direction_tran+" ("+targetCell.delay_template_name+") {\n")
        for lut_line in harnessList2[index1][index2*2+index2_offset].lut_tran:
          outlines.append("          "+lut_line+"\n")
        outlines.append("        }\n") 
        #### (3-1-2) fall
        ## propagation delay
        #outlines.append("        "+harnessList2[index1][index2*2+index2_offset+1].direction_prop+" (delay_template) {\n")
        outlines.append("        "+harnessList2[index1][index2*2+index2_offset+1].direction_prop+" ("+targetCell.delay_template_name+") {\n")
        for lut_line in harnessList2[index1][index2*2+index2_offset+1].lut_prop:
          outlines.append("          "+lut_line+"\n")
        outlines.append("        }\n") 
        ## transition delay
        #outlines.append("        "+harnessList2[index1][index2*2+index2_offset+1].direction_tran+" (delay_template) {\n")
        outlines.append("        "+harnessList2[index1][index2*2+index2_offset+1].direction_tran+" ("+targetCell.delay_template_name+") {\n")
        for lut_line in harnessList2[index1][index2*2+index2_offset+1].lut_tran:
          outlines.append("          "+lut_line+"\n")
        outlines.append("        }\n") 
        outlines.append("      }\n") ## timing end 
      ##outlines.append("    }\n") ## out pin end -> continue for reset

      ## (3-2) reset (one directrion)
      if targetCell.reset is not None:
        ##target_inport = targetCell.reset
        outlines.append("      timing () {\n")

        ## Harness search for reset
        ## index2 is an base pointer for harness search
        ## index2_offset and index2_offset_max are used to 
        ## search harness from harnessList2 which contain "timing_type_set"
        index2 = targetCell.outports.index(target_outport) 
        index2_offset = 0
        index2_offset_max = 10
        while(index2_offset < index2_offset_max):
          #print(harnessList2[index1][index2*2+index2_offset])
          if hasattr(harnessList2[index1][index2*2+index2_offset], "timing_type_reset"):
            break
          index2_offset += 1
        if(index2_offset == 10):
          print("Error: index2_offset exceed max. search number\n")
          my_exit()

        outlines.append("        related_pin : \""+targetCell.reset+"\";\n")
        outlines.append("        timing_sense : \""+harnessList2[index1][index2*2+index2_offset].timing_sense_reset+"\";\n")
        outlines.append("        timing_type : \""+harnessList2[index1][index2*2+index2_offset].timing_type_reset+"\";\n")
        ## (3-2-1) propagation delay
        #outlines.append("        "+harnessList2[index1][index2*2+index2_offset].direction_reset_prop+" (delay_template) {\n")
        outlines.append("        "+harnessList2[index1][index2*2+index2_offset].direction_reset_prop+" ("+targetCell.delay_template_name+") {\n")
        #for lut_line in harnessList2[index1][index2*2+index2_offset].lut_prop:
        for lut_line in harnessList2[index1][index2*2+index2_offset].lut_prop_reset:
          outlines.append("          "+lut_line+"\n")
        outlines.append("        }\n") 
        ## (3-2-2) transition delay
        #outlines.append("        "+harnessList2[index1][index2*2+index2_offset].direction_reset_tran+" (delay_template) {\n")
        outlines.append("        "+harnessList2[index1][index2*2+index2_offset].direction_reset_tran+" ("+targetCell.delay_template_name+") {\n")
        #for lut_line in harnessList2[index1][index2*2+index2_offset].lut_tran:
        for lut_line in harnessList2[index1][index2*2+index2_offset].lut_tran_reset:
          outlines.append("          "+lut_line+"\n")
        outlines.append("        }\n") 
        outlines.append("      }\n") 
      ##outlines.append("    }\n") #### out pin end -> continue for set

      ## (3-3) set (one directrion)
      if targetCell.set is not None:
        ##target_inport = targetCell.set
        outlines.append("      timing () {\n")
        ## Harness search for set
        ## index2 is an base pointer for harness search
        ## index2_offset and index2_offset_max are used to 
        ## search harness from harnessList2 which contain "timing_type_set"
        index2 = targetCell.outports.index(target_outport) 
        index2_offset = 0
        index2_offset_max = 10
        while(index2_offset < index2_offset_max):
          if hasattr(harnessList2[index1][index2*2+index2_offset], "timing_type_set"):
            break
          index2_offset += 1
        if(index2_offset == 10):
          print("Error: index2_offset exceed max. search number\n")
          my_exit()

        outlines.append("        related_pin : \""+targetCell.set+"\";\n")
        outlines.append("        timing_sense : \""+harnessList2[index1][index2*2+index2_offset].timing_sense_set+"\";\n")
        outlines.append("        timing_type : \""+harnessList2[index1][index2*2+index2_offset].timing_type_set+"\";\n")
        ## (3-3-1) propagation delay
        #outlines.append("        "+harnessList2[index1][index2*2+index2_offset].direction_set_prop+" (delay_template) {\n")
        outlines.append("        "+harnessList2[index1][index2*2+index2_offset].direction_set_prop+" ("+targetCell.delay_template_name+") {\n")
        #for lut_line in harnessList2[index1][index2*2+index2_offset].lut_prop:
        for lut_line in harnessList2[index1][index2*2+index2_offset].lut_prop_set:
          outlines.append("          "+lut_line+"\n")
        outlines.append("        }\n") 
        ## (3-3-2) transition delay
        #outlines.append("        "+harnessList2[index1][index2*2+index2_offset].direction_set_tran+" (delay_template) {\n")
        outlines.append("        "+harnessList2[index1][index2*2+index2_offset].direction_set_tran+" ("+targetCell.delay_template_name+") {\n")
        #for lut_line in harnessList2[index1][index2*2+index2_offset].lut_tran:
        for lut_line in harnessList2[index1][index2*2+index2_offset].lut_tran_set:
          outlines.append("          "+lut_line+"\n")
        outlines.append("        }\n") 
        outlines.append("      }\n") 
      ##outlines.append("    }\n") #### out pin end
      
      ## (3-4) clock power
      if targetCell.clock is not None:
        ## index2 is a base pointer for harness search
        ## index2_offset and index2_offset_max are used to 
        ## search harness from harnessList2 which contain "timing_type_set"
        index2 = targetCell.outports.index(target_outport) 
        index2_offset = 0
        index2_offset_max = 10
        while(index2_offset < index2_offset_max):
          if hasattr(harnessList2[index1][index2*2+index2_offset], "timing_type_setup"):
            break
          index2_offset += 1
        if(index2_offset == 10):
          print("Error: index2_offset exceed max. search number\n")
          my_exit()

        outlines.append("      internal_power () {\n")
        index2 = targetCell.inports.index(target_inport) 
        outlines.append("        related_pin : \""+targetCell.clock+"\";\n")
        ## rise(fall)
        #outlines.append("        "+harnessList2[index1][index2*2].direction_power+" (power_template) {\n")
        outlines.append("        "+harnessList2[index1][index2*2].direction_power+" ("+targetCell.power_template_name+") {\n")
        for lut_line in harnessList2[index1][index2*2].lut_eintl:
          outlines.append("          "+lut_line+"\n")
        outlines.append("        }\n") 
        ## fall(rise)
        #outlines.append("        "+harnessList2[index1][index2*2+1].direction_power+" (power_template) {\n")
        outlines.append("        "+harnessList2[index1][index2*2+1].direction_power+" ("+targetCell.power_template_name+") {\n")
        for lut_line in harnessList2[index1][index2*2+1].lut_eintl:
          outlines.append("          "+lut_line+"\n")
        outlines.append("        }\n") 
        outlines.append("      }\n") ## power end 

      ## (3-5) reset power 
      if targetCell.reset is not None:

        ## Harness search for reset
        ## index2 is an base pointer for harness search
        ## index2_offset and index2_offset_max are used to 
        ## search harness from harnessList2 which contain "timing_type_set"
        index2 = targetCell.outports.index(target_outport) 
        index2_offset = 0
        index2_offset_max = 10
        while(index2_offset < index2_offset_max):
          #print(harnessList2[index1][index2*2+index2_offset])
          if hasattr(harnessList2[index1][index2*2+index2_offset], "timing_type_reset"):
            break
          index2_offset += 1
        if(index2_offset == 10):
          print("Error: index2_offset exceed max. search number\n")
          my_exit()

        outlines.append("      internal_power () {\n")
        index2 = targetCell.inports.index(target_inport) 
        outlines.append("        related_pin : \""+targetCell.reset+"\";\n")
        ## rise(fall)
        #outlines.append("        "+harnessList2[index1][index2*2].direction_power+" (power_template) {\n")
        outlines.append("        "+harnessList2[index1][index2*2].direction_power+" ("+targetCell.power_template_name+") {\n")
        for lut_line in harnessList2[index1][index2*2].lut_eintl:
          outlines.append("          "+lut_line+"\n")
        outlines.append("        }\n") 
        ## fall(rise)
        #outlines.append("        "+harnessList2[index1][index2*2+1].direction_power+" (power_template) {\n")
        outlines.append("        "+harnessList2[index1][index2*2+1].direction_power+" ("+targetCell.power_template_name+") {\n")
        for lut_line in harnessList2[index1][index2*2+1].lut_eintl:
          outlines.append("          "+lut_line+"\n")
        outlines.append("        }\n") 
        outlines.append("      }\n") ## power end 

      ## (3-6) set power 
      if targetCell.set is not None:

        ## Harness search for set
        ## index2 is an base pointer for harness search
        ## index2_offset and index2_offset_max are used to 
        ## search harness from harnessList2 which contain "timing_type_set"
        index2 = targetCell.outports.index(target_outport) 
        index2_offset = 0
        index2_offset_max = 10
        while(index2_offset < index2_offset_max):
          #print(harnessList2[index1][index2*2+index2_offset])
          if hasattr(harnessList2[index1][index2*2+index2_offset], "timing_type_set"):
            break
          index2_offset += 1
        if(index2_offset == 10):
          print("Error: index2_offset exceed max. search number\n")
          my_exit()

        outlines.append("      internal_power () {\n")
        index2 = targetCell.inports.index(target_inport) 
        outlines.append("        related_pin : \""+targetCell.set+"\";\n")
        ## rise(fall)
        #outlines.append("        "+harnessList2[index1][index2*2].direction_power+" (power_template) {\n")
        outlines.append("        "+harnessList2[index1][index2*2].direction_power+" ("+targetCell.power_template_name+") {\n")
        for lut_line in harnessList2[index1][index2*2].lut_eintl:
          outlines.append("          "+lut_line+"\n")
        outlines.append("        }\n") 
        ## fall(rise)
        #outlines.append("        "+harnessList2[index1][index2*2+1].direction_power+" (power_template) {\n")
        outlines.append("        "+harnessList2[index1][index2*2+1].direction_power+" ("+targetCell.power_template_name+") {\n")
        for lut_line in harnessList2[index1][index2*2+1].lut_eintl:
          outlines.append("          "+lut_line+"\n")
        outlines.append("        }\n") 
        outlines.append("      }\n") ## power end 
      ##outlines.append("    }\n") #### out pin end
    outlines.append("    }\n") ## out pin end

    ## (4) Reset
    if targetCell.reset is not None:
      # for target_reset in targetCell.reset:
      target_reset = targetCell.reset
      index1 = targetCell.reset.index(target_reset) 
      outlines.append("    pin ("+target_reset+"){\n") #### out pin start
      outlines.append("      direction : input;\n")
      #outlines.append("      function : \"("+targetCell.functions[index1]+")\"\n")
      outlines.append("      related_power_pin : \""+targetLib.vdd_name+"\";\n")
      outlines.append("      related_ground_pin : \""+targetLib.vss_name+"\";\n")
      outlines.append("      max_transition : "+str(targetCell.slope[-1])+";\n")
      #targetLib.print_msg(targetCell.crsts)
      ##outlines.append("      capacitance : \""+str(targetCell.crsts[index1])+"\";\n")
      outlines.append("      capacitance : \""+str(targetCell.crsts[0])+"\";\n") # use 0 as representative
      outlines.append("      input_voltage : default_"+targetLib.vdd_name+"_"+targetLib.vss_name+"_input;\n")
      ##target_inport = targetCell.reset
  
      ## Harness search for reset
      ## index2 is an base pointer for harness search
      ## index2_offset and index2_offset_max are used to 
      ## search harness from harnessList2 which contain "timing_type_set"
      index2 = targetCell.outports.index(target_outport) 
      index2_offset = 0
      index2_offset_max = 10
      while(index2_offset < index2_offset_max):
        #print(harnessList2[index1][index2*2+index2_offset])
        if hasattr(harnessList2[index1][index2*2+index2_offset], "timing_type_reset"):
          break
        index2_offset += 1
      if(index2_offset == 10):
        print("Error: index2_offset exceed max. search number\n")
        my_exit()
      #for a in inspect.getmembers(harnessList2[index1][index2*2+index2_offset]):
      #  print (a) 
      ## (4-1) recovery
      outlines.append("      timing () {\n")
      outlines.append("        related_pin : \""+targetCell.clock+"\";\n")
      outlines.append("        timing_type : \""+harnessList2[index1][index2*2+index2_offset].timing_type_reset_recov+"\";\n")
      if (1 != len(targetCell.inports)):
        print ("Error: number of targetCell.inports is "+str(len(targetCell.inports))+", not one! die" )
        my_exit()
      #for target_inport in targetCell.inports: ## only one target_inport should be available
      #  outlines.append("        when : \""+harnessList2[index1][index2*2+index2_offset].timing_type_reset+"\";\n")
      #outlines.append("        "+harnessList2[index1][index2*2+index2_offset].timing_sense_reset_recov+" (recovery_template) {\n")
      outlines.append("        "+harnessList2[index1][index2*2+index2_offset].timing_sense_reset_recov+" ("+targetCell.recovery_template_name+") {\n")
      for lut_line in harnessList2[index1][index2*2+index2_offset].lut_setup:
        outlines.append("          "+lut_line+"\n")
      outlines.append("        }\n") 
      outlines.append("      }\n") 
      ## (4-2)removal 
      outlines.append("      timing () {\n")
      outlines.append("        related_pin : \""+targetCell.clock+"\";\n")
      outlines.append("        timing_type : \""+harnessList2[index1][index2*2+index2_offset].timing_type_reset_remov+"\";\n")
      if (1 != len(targetCell.inports)):
        print ("Error: number of targetCell.inports is "+str(len(targetCell.inports))+", not one! die" )
        my_exit()
      #for target_inport in targetCell.inports: ## only one target_inport should be available
      #  outlines.append("        when : \""+harnessList2[index1][index2*2+index2_offset].timing_type_reset+"\";\n")
      #outlines.append("        "+harnessList2[index1][index2*2+index2_offset].timing_sense_reset_remov+" (removal_template) {\n")
      outlines.append("        "+harnessList2[index1][index2*2+index2_offset].timing_sense_reset_remov+" ("+targetCell.removal_template_name+") {\n")
      for lut_line in harnessList2[index1][index2*2+index2_offset].lut_hold:
        outlines.append("          "+lut_line+"\n")
      outlines.append("        }\n") 
      outlines.append("      }\n")
                        
    if targetCell.reset is not None:
            outlines.append("    }\n") #### out pin end -> continue for set

    ## (5) set
    if targetCell.set is not None:
      #for target_set in targetCell.set:
      target_set = targetCell.set
      index1 = targetCell.set.index(target_set) 
      outlines.append("    pin ("+target_set+"){\n") #### out pin start
      outlines.append("      direction : input;\n")
      #outlines.append("      function : \"("+targetCell.functions[index1]+")\"\n")
      outlines.append("      related_power_pin : \""+targetLib.vdd_name+"\";\n")
      outlines.append("      related_ground_pin : \""+targetLib.vss_name+"\";\n")
      outlines.append("      max_transition : "+str(targetCell.slope[-1])+";\n")
      #targetLib.print_msg(targetCell.csets)
      #outlines.append("      capacitance : \""+str(targetCell.csets[index1])+"\";\n")
      outlines.append("      capacitance : \""+str(targetCell.csets[0])+"\";\n") # use 0 as representative val
      outlines.append("      input_voltage : default_"+targetLib.vdd_name+"_"+targetLib.vss_name+"_input;\n")
      ##target_inport = targetCell.set
  
      ## Harness search for set
      ## index2 is an base pointer for harness search
      ## index2_offset and index2_offset_max are used to 
      ## search harness from harnessList2 which contain "timing_type_set"
      index2 = targetCell.outports.index(target_outport) 
      index2_offset = 0
      index2_offset_max = 10
      while(index2_offset < index2_offset_max):
        #print(harnessList2[index1][index2*2+index2_offset])
        if hasattr(harnessList2[index1][index2*2+index2_offset], "timing_type_set"):
          break
        index2_offset += 1
      if(index2_offset == 10):
        print("Error: index2_offset exceed max. search number\n")
        my_exit()
  
      ## (5-1) recovery
      outlines.append("      timing () {\n")
      outlines.append("        related_pin : \""+targetCell.clock+"\";\n")
      outlines.append("        timing_type : \""+harnessList2[index1][index2*2+index2_offset].timing_type_set_recov+"\";\n")
      if (1 != len(targetCell.inports)):
        print ("Error: number of targetCell.inports is "+str(len(targetCell.inports))+", not one! die" )
        my_exit()
      #for target_inport in targetCell.inports: ## only one target_inport should be available
      #  outlines.append("        when : \""+harnessList2[index1][index2*2+index2_offset].timing_type_set+"\";\n")
      #outlines.append("        "+harnessList2[index1][index2*2+index2_offset].timing_sense_set_recov+" (recovery_template) {\n")
      outlines.append("        "+harnessList2[index1][index2*2+index2_offset].timing_sense_set_recov+" ("+targetCell.recovery_template_name+") {\n")
      for lut_line in harnessList2[index1][index2*2+index2_offset].lut_setup:
        outlines.append("          "+lut_line+"\n")
      outlines.append("        }\n") 
      outlines.append("      }\n") 
  
      ## (5-2)removal 
      outlines.append("      timing () {\n")
      outlines.append("        related_pin : \""+targetCell.clock+"\";\n")
      outlines.append("        timing_type : \""+harnessList2[index1][index2*2+index2_offset].timing_type_set_remov+"\";\n")
      if (1 != len(targetCell.inports)):
        print ("Error: number of targetCell.inports is "+str(len(targetCell.inports))+", not one! die" )
        my_exit()
      #for target_inport in targetCell.inports: ## only one target_inport should be available
      #  outlines.append("        when : \""+harnessList2[index1][index2*2+index2_offset].timing_type_set+"\";\n")
      #outlines.append("        "+harnessList2[index1][index2*2+index2_offset].timing_sense_set_remov+" (removal_template) {\n")
      outlines.append("        "+harnessList2[index1][index2*2+index2_offset].timing_sense_set_remov+" ("+targetCell.removal_template_name+") {\n")
      for lut_line in harnessList2[index1][index2*2+index2_offset].lut_hold:
        outlines.append("          "+lut_line+"\n")
      outlines.append("        }\n") 
      outlines.append("      }\n")
                        
    if targetCell.set is not None:
            outlines.append("    }\n") #### out pin end -> continue for set

    outlines.append("  }\n") #### cell end
    f.writelines(outlines)
  f.close()
  targetCell.set_exported()

## export library definition to .lib
def exportVerilog(targetLib:Mls, targetCell:Mlc):
  with open(targetLib.verilog_name, 'a') as f:
    outlines = []

    ## list ports in one line (order is same as SPICE netlist)
    
    #--portlist = "("
    #--numport = 0
    #--for target_outport in targetCell.outports:
    #--  if(numport != 0):
    #--    portlist = portlist+", "
    #--  portlist = portlist+target_outport
    #--  numport += 1
    #--for target_inport in targetCell.inports:
    #--  portlist = portlist+","+target_inport
    #--  numport += 1
    #--portlist = portlist+");"

    #--
    ports_s=targetCell.definition.split(); # .subckt NAND2_1X A B YB VDD VSS VNW VPW
    ports_s.pop(0);                   # NAND2_1X A B YB VDD VSS VNW VPW
    ports_s.pop(0);                   # A B YB VDD VSS VNW VPW
    portlist = "(" + ",".join(ports_s) + ");"
    
    outlines.append("`celldefine\n")
    outlines.append("module "+targetCell.cell+portlist+"\n")

    ## input/output statement
    #for target_outport in targetCell.outports:
    for target_outport in targetCell.rvs_portmap(targetCell.outports):
      outlines.append("output "+target_outport+";\n")
    #for target_inport in targetCell.inports:
    for target_inport in targetCell.rvs_portmap(targetCell.inports):
      outlines.append("input "+target_inport+";\n")

    ## inout statement
    #for target_biport in targetCell.biports:
    for target_biport in targetCell.rvs_portmap(targetCell.biports):
      outlines.append("inout "+target_biport+";\n")

    ## power statement
    #for target_vport in targetCell.vports:
    for target_vport in targetCell.rvs_portmap(targetCell.vports):
      outlines.append("inout "+target_vport+";\n")
      
    ## branch for sequencial cell
    if(targetCell.logic == "DFFARAS"):
      print ("This cell "+targetCell.logic+" is not supported for verilog out\n")
      my_exit()  

    ## branch for combinational cell
    else:
    ## assign statement
      for target_outport in targetCell.outports:
        #index1 = targetCell.outports.index(target_outport) 
        #outlines.append("assign "+target_outport+" = "+targetCell.functions[index1]+";\n")
        outlines.append("assign "+targetCell.replace_by_portmap(target_outport)+" = "+targetCell.replace_by_portmap(targetCell.functions[target_outport])+";\n")

    ## specify
    outlines.append("\nspecify\n");
    
    for expectationdict in logic_dict[targetCell.logic]["expect"]:
      if expectationdict.specify != "":
        when   =targetCell.replace_by_portmap(expectationdict.tmg_when)

        flag_ifnone=False
        if expectationdict.specify.endswith(";;"):
          flag_ifnone=True;
          
        specify=targetCell.replace_by_portmap(expectationdict.specify.replace(";;",";"))
        
        if when != "":
          outlines.append("  if (" + when + ") "+specify +"\n");
        else:
          outlines.append("  "+specify+"\n");

        if flag_ifnone:
          outlines.append("  ifnone "+specify + "\n\n");
        
    outlines.append("endspecify\n");
    outlines.append("endmodule\n")
    outlines.append("`endcelldefine\n\n")
    f.writelines(outlines)
  f.close()

## export library definition to .lib
def exportVerilogFlop(targetLib, targetCell):
  with open(targetLib.verilog_name, 'a') as f:
    outlines = []

    ## list ports in one line 
    portlist = "("
    numport = 0
    for target_outport in targetCell.outports:
      if(numport != 0):
        portlist = portlist+", "
      portlist = portlist+target_outport
      numport += 1
    for target_inport in targetCell.inports:
      portlist = portlist+","+target_inport
      numport += 1
    if targetCell.clock is not None:
      portlist = portlist+","+targetCell.clock
      numport += 1
    if targetCell.reset is not None:
      portlist = portlist+","+targetCell.reset
      numport += 1
    if targetCell.set is not None:
      portlist = portlist+","+targetCell.set
      numport += 1
    portlist = portlist+");"

    outlines.append("module "+targetCell.cell+portlist+"\n")

    ## input/output statement
    for target_outport in targetCell.outports:
      #outlines.append("output "+target_outport+";\n")
      outlines.append("output reg "+target_outport+";\n")
    for target_inport in targetCell.inports:
      outlines.append("input "+target_inport+";\n")
    if targetCell.clock is not None:
      outlines.append("input "+targetCell.clock+";\n")
    if targetCell.reset is not None:
      outlines.append("input "+targetCell.reset+";\n")
    if targetCell.set is not None:
      outlines.append("input "+targetCell.set+";\n")

    ## assign statement
    for target_outport in targetCell.outports:
      for target_inport in targetCell.inports:
        line = 'always@('
        resetlines = []
        setlines = []
        #print(str(targetCell.logic))
        ## clock
        if(re.search('PC', targetCell.logic)):  ## posedge clock
          line=line+"posedge "+targetCell.clock
        elif(re.search('NC', targetCell.logic)):  ## negedge clock
          line=line+"negedge "+targetCell.clock
        else:
          print("Error! failed to generate DFF verilog!")
          my_exit()

        ## reset (option)
        if(targetCell.reset != None):  ## reset
          if(re.search('PR', targetCell.logic)):  ## posedge async. reset
            line=line+" or posedge "+targetCell.reset
            resetlines.append('if('+targetCell.reset+') begin\n')
            resetlines.append('  '+target_outport+'<=0;\n')
            resetlines.append('end else begin\n')
          elif(re.search('NR', targetCell.logic)):  ## negedge async. reset
            line=str(line)+" or negedge "+targetCell.reset
            resetlines.append('if(!'+targetCell.reset+') begin\n')
            resetlines.append('  '+target_outport+'<=0;\n')
            resetlines.append('end else begin\n')
        ## set (option)
        if(targetCell.set != None):  ## reset
          if(re.search('PS', targetCell.logic)):  ## posedge async. set 
            line=line+" or posedge "+targetCell.set
            setlines.append('if('+targetCell.set+') begin\n')
            setlines.append('  '+target_outport+'<=1;\n')
            setlines.append('end else begin\n')
          elif(re.search('NS', targetCell.logic)):  ## negedge async. set 
            line=line+" or negedge "+targetCell.set
            setlines.append('if(!'+targetCell.set+') begin\n')
            setlines.append('  '+target_outport+'<=1;\n')
            setlines.append('end else begin\n')
        line=line+")begin\n"
        outlines.append(line)
        if targetCell.set is not None:  
          outlines.append(setlines[0])
          outlines.append(setlines[1])
          outlines.append(setlines[2])
        if targetCell.reset is not None:  
          outlines.append(resetlines[0])
          outlines.append(resetlines[1])
          outlines.append(resetlines[2])
        outlines.append(target_outport+'<='+target_inport+';')
        outlines.append('\nend\n')
        outlines.append('end\n')
      ## for target_inport
    ## for target_outport
    outlines.append("endmodule\n\n")
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
    cmd_str = "tar -zcvf "+targetLib.work_dir+"/"+targetCell.cell+".tgz "+targetLib.work_dir+"/"+targetCell.cell 
    subprocess.run(cmd_str, shell=True)  

## export harness data to .lib
def exitFiles(targetLib, num_gen_file):
  cat_cmd = "cat "+str(targetLib.tmp_file)+" >> "+str(targetLib.dotlib_name)+" \n"
  with open("cat_run.sh",'w') as f:
    outlines = []
    outlines.append(cat_cmd) 
    f.writelines(outlines)
  f.close()
  cmd = ['sh', 'cat_run.sh']
  try:
    res = subprocess.check_call(cmd)
  except:
    print ("Failed to cat dotlib file")
  with open(targetLib.dotlib_name, 'a') as f:
    outlines = []
    outlines.append("}\n")
    f.writelines(outlines)
  f.close()
  print("\n-- dotlib file generation completed!!  ")
  print("--  "+str(num_gen_file)+" cells generated!!  \n")

