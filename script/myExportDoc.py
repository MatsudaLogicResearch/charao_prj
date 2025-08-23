import argparse, re, os, shutil, subprocess, sys, inspect 
from itertools import groupby
from myFunc import my_exit, f2s_ceil

from myLibrarySetting       import MyLibrarySetting        as Mls 
from myLogicCell            import MyLogicCell             as Mlc
from myConditionsAndResults import MyConditionsAndResults  as Mcar
from myExpectCell           import MyExpectCell            as Mec
#from myExpectCell           import logic_dict              

def exportDoc(targetCell:Mls, harnessList:[Mcar]):
    #targetLib = harnessList[0].mls
    #targetCell= harnessList[0].mlc
    targetLib = targetCell.mls

    
    if(targetLib.isexport2doc == 0):
        exportLib2doc(targetLib=targetLib, targetCell=targetCell)

    ## export comb. logic
    #if((targetLib.isexport2doc == 1) and (targetCell.isexport2doc == 0) and (targetCell.isflop == 0)):
    if((targetLib.isexport2doc == 1) and (targetCell.isexport2doc == 0)) :
        exportHarness2doc(targetCell=targetCell, harnessList=harnessList)
        
    ## export seq. logic
    #elif((targetLib.isexport2doc == 1) and (targetCell.isexport2doc == 0) and (targetCell.isflop == 1)):
    #    #exportHarnessFlop2doc(targetLib, targetCell, harnessList2)
    #    exportHarnessFlop2doc(harnessList)

## export library definition to .lib
def exportLib2doc(targetLib:Mls, targetCell:Mlc):
    
    outlines = []

    outlines.append(f"\\newpage")    #-- command for luatext
    
    ## general settings
    outlines.append(f"# Library settings")
    outlines.append(f"| lib. name | delay model |")
    outlines.append(f"|----|----|")
    outlines.append(f"| {targetLib.lib_name} | {targetLib.delay_model}|")
    outlines.append(f"")
    outlines.append(f"## Units")
    outlines.append(f"| cap | volt | cur | energy | leak | time | res |")
    outlines.append(f"|----|----|----|----|----|----|----|")
    outlines.append(f"| {targetLib.capacitance_unit} | {targetLib.voltage_unit} | | {targetLib.current_unit} | {targetLib.energy_unit} | {targetLib.leakage_power_unit} | {targetLib.time_unit} | {targetLib.resistance_unit} |")
    outlines.append(f"")
    
    outlines.append(f"## Voltage terminals")
    vv=dict();
    if targetLib.vdd_name:
        vv["vdd"]=targetLib.vdd_name
    if targetLib.vss_name:
        vv["vss"]=targetLib.vss_name
    if targetLib.vdd2_name:
        vv["vdd2"]=targetLib.vdd2_name
    if targetLib.vss2_name:
        vv["vss2"]=targetLib.vss2_name
    if targetLib.vdd2_name:
        vv["vddio"]=targetLib.vddio_name
    if targetLib.vssio_name:
        vv["vssio"]=targetLib.vssio_name

    hd ="|" + "|".join(vv.keys()) + "|"
    bar="|---" * len(vv.keys()) + "|"
    val="|" + "|".join(vv.values()) + "|"
    outlines.append(f"{hd}")
    outlines.append(f"{bar}")
    outlines.append(f"{val}")
    outlines.append(f"")

    outlines.append(f"## Operating conditions \n")
    vv=dict();
    vv["OperatingCondition"]=targetLib.operating_condition
    vv["ProcessCorner"]     =targetLib.process_corner
    vv["Temperature"]       =f"{targetLib.temperature}"
    if targetLib.vdd_name:
      n=f"CoreVoltage({targetLib.voltage_unit})"
      vv[n]     =f"{targetLib.vdd_voltage:.2f}"
    if targetLib.vdd2_name:
      n=f"Core2Voltage({targetLib.voltage_unit})"
      vv[n]    =f"{targetLib.vdd2_voltage:.2f}"
    if targetLib.vddio_name:
      n=f"IoVoltage({targetLib.voltage_unit})"
      vv[n]       =f"{targetLib.vddio_voltage:.2f}"

    hd ="|" + "|".join(vv.keys()) + "|"
    bar="|---" * len(vv.keys()) + "|"
    val="|" + "|".join(vv.values()) + "|"
    outlines.append(f"{hd}")
    outlines.append(f"{bar}")
    outlines.append(f"{val}")
    outlines.append(f"")

    outlines.append(f"## Logic threshold")
    outlines.append(f"| input rise(%)| input fall(%)| output rise(%)| output fall(%)|")
    outlines.append(f"|----|----|----|----|")
    outlines.append(f"| {str(targetLib.logic_low_to_high_threshold*100)} | {str(targetLib.logic_high_to_low_threshold*100)} | {str(targetLib.logic_low_to_high_threshold*100)} | {str(targetLib.logic_high_to_low_threshold*100)} |")
    outlines.append(f"")

    
    outlines.append(f"\\newpage")    #-- command for luatext
    outlines.append(f"# Cell Infomation")

    #-----
    print(targetLib.doc_name)
    with open(targetLib.doc_name, 'w') as f:
        s = "\n".join(outlines) + "\n"
        f.write(s)

    targetLib.set_exported2doc()

def exportHarness2doc(targetCell, harnessList: list[Mcar]):
    targetLib = targetCell.mls
    sigdigs = targetLib.significant_digits
    
    outlines = []
    outlines.append(f"## {targetCell.cell}")

    ##-------------------------------------------------
    outlines.append(f"### CELL ATTRIBUTES")
    outlines.append(f"| Attribute| Value |")
    outlines.append(f"|----|----|")
    outlines.append(f"|area | {str(targetCell.area)}")
    outlines.append(f"")
    
    ##-------------------------------------------------
    if targetCell.isflop:
      outlines.append(f'### FLOP GROUP')
      outlines.append(f'| Attribute| Expression |')
      outlines.append(f'|----|----|')
      outlines.append(f'|Registers  | {targetCell.replace_by_portmap(targetCell.ff["out"])} |')
      outlines.append(f'|Clocked On | {targetCell.replace_by_portmap(targetCell.ff["clocked_on"])} |')
      outlines.append(f'|Next State | {targetCell.replace_by_portmap(targetCell.ff["next_state"])} |')
      if targetCell.ff["clear"]:
        outlines.append(f'|Clear | {targetCell.replace_by_portmap(targetCell.ff["clear"])} |')
      if targetCell.ff["preset"]:
        outlines.append(f'|Preset | {targetCell.replace_by_portmap(targetCell.ff["preset"])} |')
      outlines.append(f'')

    ##-------------------------------------------------
    if targetCell.functions:
      outlines.append(f'### FUNCTIONS')
      outlines.append(f'| Output Pin| Function |')
      outlines.append(f'|----|----|')
      for p,f in targetCell.functions.items():
          outlines.append(f'|{targetCell.replace_by_portmap(p)}  | {targetCell.replace_by_portmap(f)} |')
      outlines.append(f'')

      for p,f in targetCell.functions.items():
        outlines.append(f'### TRUTH TABLE FOR ({targetCell.replace_by_portmap(p)})')
        outlines.append(f'')

    ##-------------------------------------------------
    #h_list = [h for h in harnessList if (h.template_kind.startswith("delay") and  h.timing_type.startswith("three_state"))]

    for setup_hold in ["setup","hold","recovery","removal"]:
      h_list = [h for h in harnessList if (h.template_kind in ["const"] and h.timing_type.startswith(setup_hold))]
      sorted_h=sorted(h_list, key=lambda x: (x.timing_type, x.target_inport, x.target_relport, x.constraint, x.timing_when))

      if sorted_h:
        outlines.append(f'### CONSTRAINTS ({setup_hold})')
        outlines.append(f'| Constraint Pin | Related pin | Constraint Pin Slew({targetLib.time_unit}) | Related pin Slew({targetLib.time_unit}) | When | {setup_hold}({targetLib.time_unit})|')
        outlines.append(f'|----|----|----|----|----|----|')

      for (timing_type, inport, relport, constraint,timing_when),group in groupby(sorted_h, key=lambda x:(x.timing_type, x.target_inport,x.target_relport, x.constraint, x.timing_when)):
        group_list=list(group);
        size=len(group_list)

        for g in group_list:
          index1_pos=len(g.template.index_1)//2
          index2_pos=len(g.template.index_2)//2
          index1_val=g.template.index_1[index1_pos]
          index2_val=g.template.index_2[index2_pos]
        
          const_arc=constraint.rstrip('_constraint')
          rel_arc  =timing_type.strip(setup_hold+"_")
        
          const_pin=f'{targetCell.replace_by_portmap(inport)}({const_arc})'
          rel_pin  =f'{targetCell.replace_by_portmap(relport)}({rel_arc})'
          const_slew=index2_val
          rel_slew=index1_val
          when    ="default" if timing_when =="" else targetCell.replace_by_portmap(timing_when)
          val     = g.dict_list2["setup_hold"][index1_val][index2_val] / targetLib.time_mag
          outlines.append(f'| {const_pin} | {rel_pin} | {const_slew} | {rel_slew} | {when} | {f2s_ceil(f=val, sigdigs=sigdigs)}|')
          
      #
      outlines.append(f'')

    
    ##-------------------------------------------------
    outlines.append(f'### PIN DIRECTION & CAPACITANCE({targetLib.capacitance_unit})')
    outlines.append(f'| Pin| Direction | Capacitance ({targetLib.capacitance_unit}) |')
    outlines.append(f'|----|----|----|')

    for p in targetCell.cins.keys():
      cap=f2s_ceil(f=targetCell.cins[p], sigdigs=sigdigs)
      name=targetCell.replace_by_portmap(p)
      direction="input" if (p in targetCell.inports + [targetCell.clock]) else "inout" if (p in targetCell.biports + targetCell.vports) else "output"
      outlines.append(f'| {name} | {direction} | {cap} |')
      
    outlines.append(f'')

    
    ##-------------------------------------------------    
    h_list = [h for h in harnessList if (h.template_kind.startswith("delay") and (not h.timing_type.startswith("three_state")))]
    sorted_h=sorted(h_list, key=lambda x: (x.target_outport, x.timing_when, x.target_relport, x.timing_type, x.direction_tran))

    if sorted_h:
      outlines.append(f'### DELAY AND OUTPUT TRANSITION TIME')
      outlines.append(f'| Input Pin | Output pin | When | Input Pin Slew({targetLib.time_unit}) | Out Load({targetLib.capacitance_unit}) | Delay({targetLib.time_unit})| Transition({targetLib.time_unit}) |')
      outlines.append(f'|----|----|----|----|----|----|----|')

    for (timing_type, relport, outport, direction_tran, timing_when),group in groupby(sorted_h, key=lambda x:(x.timing_type, x.target_relport,x.target_outport, x.direction_tran, x.timing_when)):
      group_list=list(group);
      size=len(group_list)

      for g in group_list:
        index1_pos=len(g.template.index_1)//2
        index2_pos=len(g.template.index_2)//2
        index1_val=g.template.index_1[index1_pos]
        index2_val=g.template.index_2[index2_pos]
        
        rel_dir="LH" if g.mec.arc_oir[2]=='r' else "HL"
        tran =direction_tran.rstrip("_transition")

        rel_pin=f'{targetCell.replace_by_portmap(relport)}({rel_dir})'
        out_pin=f'{targetCell.replace_by_portmap(outport)}({tran})'
        when    ="default" if timing_when =="" else targetCell.replace_by_portmap(timing_when)
        rel_slew =index1_val
        out_load=index2_val
        delay_val = g.dict_list2["prop"][index1_val][index2_val] / targetLib.time_mag
        trans_val = g.dict_list2["trans"][index1_val][index2_val] / targetLib.time_mag

        outlines.append(f'| {rel_pin} | {out_pin} | {when} | {rel_slew} | {out_load} | {f2s_ceil(f=delay_val, sigdigs=sigdigs)} | {f2s_ceil(f=trans_val, sigdigs=sigdigs)} |')
    #
    outlines.append(f'')

    ##-------------------------------------------------    
    #h_list = [h for h in harnessList if (h.template_kind in ["delay"])]
    h_list = [h for h in harnessList if (h.template_kind.startswith("delay") and  h.timing_type.startswith("three_state"))]
    sorted_h=sorted(h_list, key=lambda x: (x.target_outport, x.timing_when, x.target_relport, x.timing_type, x.direction_tran))
    
    if sorted_h:
      outlines.append(f'### THREE_STSTE AND OUTPUT TRANSITION TIME')
      outlines.append(f'| OE | Input Pin | Output pin | When | Input Pin Slew({targetLib.time_unit}) | Out Load({targetLib.capacitance_unit}) | Delay({targetLib.time_unit})| Transition({targetLib.time_unit}) |')
      outlines.append(f'|----|----|----|----|----|----|----|----|')

    for (timing_type, relport, outport, direction_tran, timing_when),group in groupby(sorted_h, key=lambda x:(x.timing_type, x.target_relport,x.target_outport, x.direction_tran, x.timing_when)):
      group_list=list(group);
      size=len(group_list)

      for g in group_list:
        index1_pos=len(g.template.index_1)//2
        index2_pos=len(g.template.index_2)//2
        index1_val=g.template.index_1[index1_pos]
        index2_val=g.template.index_2[index2_pos]
        
        rel_dir="LH" if g.mec.arc_oir[2]=='r' else "HL"
        tran =direction_tran.rstrip("_transition")

        #timing_type=g.timing_type
        timing_type=g.timing_type.strip("three_state_")
        rel_pin=f'{targetCell.replace_by_portmap(relport)}({rel_dir})'
        out_pin=f'{targetCell.replace_by_portmap(outport)}({tran})'
        when    ="default" if timing_when =="" else targetCell.replace_by_portmap(timing_when)
        rel_slew =index1_val
        out_load=index2_val
        delay_val = g.dict_list2["prop"][index1_val][index2_val] / targetLib.time_mag
        trans_val = g.dict_list2["trans"][index1_val][index2_val] / targetLib.time_mag

        outlines.append(f'| {timing_type} | {rel_pin} | {out_pin} | {when} | {rel_slew} | {out_load} | {f2s_ceil(f=delay_val, sigdigs=sigdigs)} | {f2s_ceil(f=trans_val, sigdigs=sigdigs)} |')
    #
    outlines.append(f'')

    
    ##-------------------------------------------------
    #h_list = [h for h in harnessList if (h.template_kind in ["power"])]
    #h_list = [h for h in harnessList if (h.template_kind.startswith("power") and (h.timing_type.startswith("three_state"))]
    h_list = [h for h in harnessList if (h.template_kind.startswith("power"))]
    sorted_h=sorted(h_list, key=lambda x: (x.target_outport, x.timing_when, x.target_relport, x.timing_type, x.direction_tran))

    
    if sorted_h:
      outlines.append(f'### DYNAMIC ENERGY')
      outlines.append(f'| Input Pin | When | Output pin | Input Pin Slew({targetLib.time_unit}) | Out Load({targetLib.capacitance_unit}) | Energy({targetLib.energy_unit})|')
      outlines.append(f'|----|----|----|----|----|----|')

    for (timing_type, relport, outport, direction_power, timing_when),group in groupby(sorted_h, key=lambda x:(x.timing_type, x.target_relport,x.target_outport, x.direction_power, x.timing_when)):
      group_list=list(group);
      size=len(group_list)

      for g in group_list:
        index1_pos=len(g.template.index_1)//2
        index2_pos=len(g.template.index_2)//2
        index1_val=g.template.index_1[index1_pos]
        index2_val=g.template.index_2[index2_pos]
        
        rel_dir="LH" if g.mec.arc_oir[2]=='r' else "HL"
        pwr_dir =direction_power.rstrip("_power")

        rel_pin=f'{targetCell.replace_by_portmap(relport)}({rel_dir})'
        when    ="default" if timing_when =="" else targetCell.replace_by_portmap(timing_when)
        out_pin=f'{targetCell.replace_by_portmap(outport)}({pwr_dir})'
        rel_slew =index1_val
        out_load=index2_val
        energy = g.dict_list2["eintl"][index1_val][index2_val] / targetLib.energy_mag

        outlines.append(f'| {rel_pin} | {when} | {out_pin} | {rel_slew} | {out_load} | {f2s_ceil(f=energy, sigdigs=sigdigs)} |')
        
    #
    outlines.append(f'')

    ##-------------------------------------------------
    h_list = [h for h in harnessList if (h.template_kind in ["passive"])]
    sorted_h=sorted(h_list, key=lambda x: (x.target_inport, x.timing_when))

    if sorted_h:
      outlines.append(f'### PASSIVE ENERGY')
      outlines.append(f'| Input Pin | When | Input Pin Slew({targetLib.time_unit}) | Energy({targetLib.energy_unit})|')
      outlines.append(f'|----|----|----|----|')

    for (inport, arc_in, timing_when),group in groupby(sorted_h, key=lambda x:(x.target_inport, x.mec.arc_oir[1], x.timing_when)):
      group_list=list(group);
      size=len(group_list)

      for g in group_list:
        index1_pos=len(g.template.index_1)//2
        index1_val=g.template.index_1[index1_pos]
        
        in_dir="LH" if arc_in=='r' else "HL"

        in_pin=f'{targetCell.replace_by_portmap(inport)}({in_dir})'
        when    ="default" if timing_when =="" else targetCell.replace_by_portmap(timing_when)

        in_slew =index1_val
        energy = g.dict_list2["eintl"][index1_val][0] / targetLib.energy_mag

        outlines.append(f'| {in_pin} | {when} | {in_slew} | {f2s_ceil(f=energy, sigdigs=sigdigs)} |')
        
    #
    outlines.append(f'')

    ##-------------------------------------------------
    outlines.append(f'### LEAKAGE POWER')
    outlines.append(f'| When | Power({targetLib.leakage_power_unit})|')
    outlines.append(f'|----|----|')

    h_list = [h for h in harnessList if (h.template_kind in ["leakage"])]
    sorted_h=sorted(h_list, key=lambda x: (x.timing_when))

    for (timing_when),group in groupby(sorted_h, key=lambda x:(x.timing_when)):
      group_list=list(group);
      size=len(group_list)

      for g in group_list:
        when    =targetCell.replace_by_portmap(timing_when)
        power = g.pleak/ targetLib.leakage_power_mag

        outlines.append(f'| {when} | {f2s_ceil(f=power, sigdigs=sigdigs)} |')
    #
    power_cell=targetCell.pleak_cell / targetLib.leakage_power_mag
    outlines.append(f'| default | {f2s_ceil(f=power_cell, sigdigs=sigdigs)} |')
    outlines.append(f'')

    #-----
    outlines.append(f"\\newpage")    #-- command for luatext
    with open(targetLib.doc_name, 'a') as f:
        s = "\n".join(outlines) + "\n"
        f.write(s)


## export harness data to .lib
def exitDocFiles(targetLib, num_gen_file):
    with open(targetLib.doc_name, 'a') as f:
        outlines = []
        outlines.append("}\n")
        f.writelines(outlines)
    f.close()
    targetLib.print_msg("\n-- doc file generation completed!!  ")
    targetLib.print_msg("--  "+str(num_gen_file)+" cells generated!!  \n")

