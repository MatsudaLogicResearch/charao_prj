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
import argparse, re, os, shutil, subprocess, sys, inspect 
from itertools import groupby
from pathlib import Path

from .myFunc import my_exit, f2s_ceil
from .myLibrarySetting       import MyLibrarySetting        as Mls 
from .myLogicCell            import MyLogicCell             as Mlc
from .myConditionsAndResults import MyConditionsAndResults  as Mcar
from .myExpectCell           import MyExpectCell            as Mec
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

    ## general settings
    outlines.append(f'---')
    outlines.append(f'title: "Cell Library Specification"')
    outlines.append(f'subtitle: "{targetLib.lib_name}(build_rev:{targetLib.build_stamp})"')
    outlines.append(f'author: ""')
    outlines.append(f'date: "{targetLib.build_date}"')
    outlines.append(f'toc: false')
    outlines.append(f'toc-depth: 2')
    outlines.append(f'---')
    outlines.append(f"\\clearpage")
    outlines.append(f"\\tableofcontents")
    outlines.append(f"\\clearpage")

    
    outlines.append(f"# Library settings")
    outlines.append(f"| lib. name | delay model |")
    outlines.append(f"|----|----|")
    outlines.append(f"| {targetLib.lib_name} | {targetLib.delay_model}|")
    outlines.append(f"")
    outlines.append(f"## Units")
    outlines.append(f"| cap | volt | cur | energy | leak | time | res |")
    outlines.append(f"|----|----|----|----|----|----|----|")
    outlines.append(f"| {targetLib.capacitance_unit} | {targetLib.voltage_unit} | {targetLib.current_unit} | {targetLib.energy_unit} | {targetLib.leakage_power_unit} | {targetLib.time_unit} | {targetLib.resistance_unit} |")
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
    
    out_file = Path(targetLib.doc_name)
    out_file.parent.mkdir(parents=True, exist_ok=True)
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
    #-- ISS-00250(2026-08-16): 行末の `|` が欠けており Markdown の表が崩れていた（全セル）
    outlines.append(f"|area | {str(targetCell.area)} |")
    outlines.append(f"")
    
    ##-------------------------------------------------
    if targetCell.isflop:
      outlines.append(f'### FLOP GROUP')
      outlines.append(f'| Attribute| Expression |')
      outlines.append(f'|----|----|')
      outlines.append(f'|Registers  | {targetCell.replace_by_portmap(targetCell.ff["out"])} |')
      outlines.append(f'|Clocked On | {targetCell.replace_by_portmap(targetCell.ff["clocked_on"])} |')
      outlines.append(f'|Next State | {targetCell.replace_by_portmap(targetCell.ff["next_state"])} |')
      if "clear" in targetCell.ff.keys():
        outlines.append(f'|Clear | {targetCell.replace_by_portmap(targetCell.ff["clear"])} |')
      if "preset" in targetCell.ff.keys():
        outlines.append(f'|Preset | {targetCell.replace_by_portmap(targetCell.ff["preset"])} |')
      outlines.append(f'')

    elif targetCell.islatch:
      outlines.append(f'### LATCH GROUP')
      outlines.append(f'| Attribute| Expression |')
      outlines.append(f'|----|----|')
      outlines.append(f'|Latch     | {targetCell.replace_by_portmap(targetCell.latch["out"])} |')
      outlines.append(f'|Enable    | {targetCell.replace_by_portmap(targetCell.latch["enable"])} |')
      outlines.append(f'|Data In   | {targetCell.replace_by_portmap(targetCell.latch["data_in"])} |')
      if "clear" in targetCell.latch.keys():
        outlines.append(f'|Clear | {targetCell.replace_by_portmap(targetCell.latch["clear"])} |')
      if "preset" in targetCell.latch.keys():
        outlines.append(f'|Preset | {targetCell.replace_by_portmap(targetCell.latch["preset"])} |')
      outlines.append(f'')

    ##-------------------------------------------------
    if targetCell.functions:
      outlines.append(f'### FUNCTIONS')
      outlines.append(f'| Output Pin| Function |')
      outlines.append(f'|----|----|')
      #-- ISS-00250(2026-08-16): 関数式の `|`(OR) が Markdown の列区切りと衝突し表が崩れる
      #   （`!((A1&A2)|B1|C1)` が 3 列に割れる）。 セル内の `|` を `\|` にエスケープする。
      #   ⚠ .lib 側の function は Liberty 構文なのでエスケープしない（ここは .md のみ）。
      for p,f in targetCell.functions.items():
          _fn = targetCell.replace_by_portmap(f).replace("|", "\\|")
          outlines.append(f'|{targetCell.replace_by_portmap(p)}  | {_fn} |')
      outlines.append(f'')

      for p,f in targetCell.functions.items():
        outlines.append(f'### TRUTH TABLE FOR ({targetCell.replace_by_portmap(p)})')
        outlines.append(f'')

    ##-------------------------------------------------
    outlines.append(f'### INPUT PIN CAPACITANCE({targetLib.capacitance_unit})')
    outlines.append(f'| Pin| Direction | Capacitance ({targetLib.capacitance_unit}) |')
    outlines.append(f'|----|----|----|')

    for p in targetCell.cins.keys():
      cap="-" if abs(targetCell.cins[p]) < 1e-20 else f2s_ceil(f=targetCell.cins[p], sigdigs=sigdigs)
      name=targetCell.replace_by_portmap(p)
      direction="input" if (p in targetCell.inports + [targetCell.clock]) else "inout" if (p in targetCell.biports + targetCell.vports) else "output"
      outlines.append(f'| {name} | {direction} | {cap} |')
      
    outlines.append(f'')

    ##-------------------------------------------------
    inports=[p for p in (targetCell.inports + [targetCell.clock] + targetCell.biports) if p is not None]
    
    if targetCell.min_pulse_width_high.keys() or targetCell.min_pulse_width_low.keys():

      outlines.append(f'### MIN PULSE WIDTH')
      outlines.append(f'（ISS-00160: slew-index テーブル。値は index_1 順のカンマ区切り）')
      outlines.append(f'| Input Pin| When | Width for L({targetLib.time_unit}) | Width for H({targetLib.time_unit})|')
      outlines.append(f'|----|----|----|----|')

      # ISS-00082/00160: min_pulse_width_high/low の値は (lut 行リスト, grid) tuple。values 行(最終行)から index_1 順の値列を抽出
      mpw_keys = sorted(set(targetCell.min_pulse_width_high.keys()) | set(targetCell.min_pulse_width_low.keys()))
      for (port, when) in mpw_keys:
        port_name = targetCell.replace_by_portmap(port)
        when_disp = targetCell.replace_by_portmap(when) if when else "-"
        _vl = targetCell.min_pulse_width_low.get((port,when))
        _vh = targetCell.min_pulse_width_high.get((port,when))
        val_low = _vl[0][-1].strip().strip('"') if (isinstance(_vl,tuple) and _vl[0]) else "-"
        val_high= _vh[0][-1].strip().strip('"') if (isinstance(_vh,tuple) and _vh[0]) else "-"

        if (val_low !="-")  or (val_high !="-") :
          outlines.append(f'| {port_name} | {when_disp} | {val_low} | {val_high} |')

      #---
      outlines.append(f'')

    ##-------------------------------------------------
    #h_list = [h for h in harnessList if (h.template_kind.startswith("delay") and  h.timing_type.startswith("three_state"))]

    for setup_hold in ["setup","hold","recovery","removal"]:
      h_list = [h for h in harnessList if (h.template_kind in ["const"] and h.timing_type.startswith(setup_hold))]
      # ISS-00135/127: .lib const と整合。 Constraint Pin=lib_target_pin(pin_tr[0]), Related pin=lib_related_pin(pin_tr[1])
      sorted_h=sorted(h_list, key=lambda x: (x.timing_type, x.lib_target_pin, x.lib_related_pin, x.direction_in_lib["constraint"], x.timing_when))

      if sorted_h:
        outlines.append(f'### CONSTRAINTS ({setup_hold})')
        outlines.append(f'')

        for (timing_type, inport, relport, constraint,timing_when),group in groupby(sorted_h, key=lambda x:(x.timing_type, x.lib_target_pin,x.lib_related_pin, x.direction_in_lib["constraint"], x.timing_when)):
          group_list=list(group);
          size=len(group_list)
        
          ## ISS-00121: aux (dummy) は dict_list2["setup_hold"] 未設定 → rep のみ使用。
          g=next((h for h in group_list if "setup_hold" in h.dict_list2), None)
          if g is None:
            continue
          const_arc=constraint.replace('_constraint',"")
          rel_arc  =timing_type.replace(setup_hold+"_","")
          const_pin=f'{targetCell.replace_by_portmap(inport)}({const_arc})'
          rel_pin  =f'{targetCell.replace_by_portmap(relport)}({rel_arc})'
          when    ="default" if timing_when =="" else targetCell.replace_by_portmap(timing_when)

          # md-format 2026-07-12: full grid。index1=constrained-pin slew(行) / index2=related-pin slew(列)
          #   （myLibrarySetting var_1=constrained / var_2=related、set_lut と整合。旧 rep は const/rel 逆で表示バグ）。
          outlines.append(f'#### constrained {const_pin} vs related {rel_pin} (when {when})')
          outlines.append(f'')
          i1=list(g.template.index_1)   # constrained-pin slew
          i2=list(g.template.index_2)   # related-pin slew
          outlines.append(f'**{setup_hold} ({targetLib.time_unit})**')
          outlines.append(f'')
          outlines.append(f'| constrained-slew / related-slew | ' + ' | '.join(str(x) for x in i2) + ' |')
          outlines.append(f'|----|' + '----|'*len(i2))
          for s in i1:
            vals=[f2s_ceil(f=g.dict_list2["setup_hold"][s][ld]/targetLib.time_mag, sigdigs=sigdigs) for ld in i2]
            outlines.append(f'| {s} | ' + ' | '.join(vals) + ' |')
            
        #
        outlines.append(f'')

    
    ##-------------------------------------------------    
    h_list = [h for h in harnessList if (h.template_kind.startswith("delay") and (not h.timing_type.startswith("three_state")))]
    sorted_h=sorted(h_list, key=lambda x: (x.target_outport, x.target_relport, x.timing_when, x.direction_in_lib["tran"]))

    if sorted_h:
      outlines.append(f'### DELAY AND OUTPUT TRANSITION TIME')
      outlines.append(f'')

      # md-format 2026-07-12: アークごとに index1(slew)×index2(load) の full grid テーブルを出力する。
      #   1 アーク (relport->outport, when) につき Cell delay(fall/rise)・Output transition(fall/rise) の 4 表。
      #   fall/rise は同アーク内の別 harness（sorted_h が direction_in_lib["tran"] 昇順なので fall→rise の順）。
      for (outport, relport, timing_when),group in groupby(sorted_h, key=lambda x:(x.target_outport, x.target_relport, x.timing_when)):
        glist=list(group)
        rel_pin=targetCell.replace_by_portmap(relport)
        out_pin=targetCell.replace_by_portmap(outport)
        when   ="default" if timing_when =="" else targetCell.replace_by_portmap(timing_when)
        outlines.append(f'#### {rel_pin} -> {out_pin} (when {when})')
        outlines.append(f'')

        for datakey,dlabel in [("prop","Cell delay"),("trans","Output transition")]:
          # ISS-00157: transition のみ Liberty 規約 stored=実測/slew_derate（.lib set_lut と一致）。delay(prop) は非対象。
          derate = targetLib.slew_derate_from_library if datakey=="trans" else 1.0
          for g in glist:
            edge=g.direction_in_lib["tran"].replace("_transition","")
            i1=list(g.template.index_1)
            i2=list(g.template.index_2) if len(g.template.index_2)>0 else [0.0]   # 1D template は load 非依存
            outlines.append(f'**{dlabel} ({edge})** ({targetLib.time_unit})')
            outlines.append(f'')
            outlines.append(f'| slew / load | ' + ' | '.join(str(x) for x in i2) + ' |')
            outlines.append(f'|----|' + '----|'*len(i2))
            for s in i1:
              vals=[f2s_ceil(f=g.dict_list2[datakey][s][ld]/targetLib.time_mag/derate, sigdigs=sigdigs) for ld in i2]
              outlines.append(f'| {s} | ' + ' | '.join(vals) + ' |')
            outlines.append(f'')

    
    ##-------------------------------------------------    
    #h_list = [h for h in harnessList if (h.template_kind in ["delay"])]
    h_list = [h for h in harnessList if (h.template_kind.startswith("delay") and  h.timing_type.startswith("three_state"))]
    sorted_h=sorted(h_list, key=lambda x: (x.target_outport, x.target_relport, x.timing_when, x.timing_type, x.direction_in_lib["tran"]))

    if sorted_h:
      outlines.append(f'### THREE_STATE AND OUTPUT TRANSITION TIME')
      outlines.append(f'')

      # md-format 2026-07-12: DELAY と同様に arc ごとの full grid テーブル。
      #   OE=enable(2D: slew x load) / disable(1D: slew のみ、load 非依存) を分けて出力。
      for (outport, relport, timing_when, oe),group in groupby(sorted_h, key=lambda x:(x.target_outport, x.target_relport, x.timing_when, "enable" if x.timing_type.startswith("three_state_enable") else "disable")):
        glist=list(group)
        rel_pin=targetCell.replace_by_portmap(relport)
        out_pin=targetCell.replace_by_portmap(outport)
        when   ="default" if timing_when =="" else targetCell.replace_by_portmap(timing_when)
        outlines.append(f'#### OE={oe}: {rel_pin} -> {out_pin} (when {when})')
        outlines.append(f'')

        for datakey,dlabel in [("prop","Cell delay"),("trans","Output transition")]:
          # ISS-00157: transition のみ Liberty 規約 stored=実測/slew_derate（.lib set_lut と一致）。delay(prop) は非対象。
          derate = targetLib.slew_derate_from_library if datakey=="trans" else 1.0
          for g in glist:
            edge=g.direction_in_lib["tran"].replace("_transition","")
            i1=list(g.template.index_1)
            has2=len(g.template.index_2)>0
            outlines.append(f'**{dlabel} ({edge})** ({targetLib.time_unit})')
            outlines.append(f'')
            if has2:
              i2=list(g.template.index_2)
              outlines.append(f'| slew / load | ' + ' | '.join(str(x) for x in i2) + ' |')
              outlines.append(f'|----|' + '----|'*len(i2))
              for s in i1:
                vals=[f2s_ceil(f=g.dict_list2[datakey][s][ld]/targetLib.time_mag/derate, sigdigs=sigdigs) for ld in i2]
                outlines.append(f'| {s} | ' + ' | '.join(vals) + ' |')
            else:
              outlines.append(f'| slew | value (load-independent) |')
              outlines.append(f'|----|----|')
              for s in i1:
                v=f2s_ceil(f=g.dict_list2[datakey][s][0.0]/targetLib.time_mag/derate, sigdigs=sigdigs)
                outlines.append(f'| {s} | {v} |')
            outlines.append(f'')

    
    ##-------------------------------------------------
    #h_list = [h for h in harnessList if (h.template_kind in ["power"])]
    #h_list = [h for h in harnessList if (h.template_kind.startswith("power") and (h.timing_type.startswith("three_state"))]
    h_list = [h for h in harnessList if (h.template_kind.startswith(("power_tout","power_c","power_i")))]
    sorted_h=sorted(h_list, key=lambda x: (x.target_outport, x.timing_when, x.target_relport, x.timing_type, x.direction_in_lib["tran"]))


    if sorted_h:
      outlines.append(f'### DYNAMIC ENERGY')
      outlines.append(f'| Input Pin | When | Output pin | Input Pin Slew({targetLib.time_unit}) | Out Load({targetLib.capacitance_unit}) | Energy({targetLib.energy_unit})|')
      outlines.append(f'|----|----|----|----|----|----|')

      for (timing_type, relport, outport, direction_power, timing_when),group in groupby(sorted_h, key=lambda x:(x.timing_type, x.target_relport,x.target_outport, x.direction_in_lib["power"], x.timing_when)):
        group_list=list(group);
        size=len(group_list)
      
        for g in group_list:
          index1_pos=len(g.template.index_1)//2
          index1_val=g.template.index_1[index1_pos]
          if len(g.template.index_2) > 0:
            index2_pos=len(g.template.index_2)//2
            index2_val=g.template.index_2[index2_pos]
          else:
            index2_val=0.0   # 1D template (delay_disable): load-independent
          
          rel_dir="LH" if g.mec.arc_oirc[2]=='r' else "HL"
          pwr_dir =direction_power.replace("_power","")
      
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

      for (inport, arc_in, timing_when),group in groupby(sorted_h, key=lambda x:(x.target_inport, x.mec.arc_oirc[1], x.timing_when)):
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

