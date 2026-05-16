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
# Originally named: chara_comb.py in OriginalProject
###############################################################################
import argparse, re, os, shutil, subprocess, sys, inspect, threading 
import copy

from .myConditionsAndResults import MyConditionsAndResults  as Mcar
from .myLibrarySetting       import MyLibrarySetting        as Mls 
from .myLogicCell            import MyLogicCell             as Mlc
from .myExpectCell           import MyExpectCell            as Mec
from .myTbParam              import MyTbParam               as Mtp
from .myFunc import my_exit


def _tslew_from_template(slew:float, mls:Mls) -> float:
  """Convert template slew (physical threshold-window time) to SPICE PWL
  full-rail (0-100%) ramp duration. Template index_1 represents the
  slew_lower_threshold_pct -> slew_upper_threshold_pct transit time, so the
  full-rail linear ramp duration is slew / (high - low). time_mag is then
  applied to convert to SPICE seconds."""
  span = mls.logic_threshold_high - mls.logic_threshold_low
  return float("{:.5g}".format(slew / span * mls.time_mag))


def _build_spicef_base(mls:Mls, mlc:Mlc, mec:Mec, num:int) -> str:
  """sim file base path を生成し、 第 1, 2 層 dir を作成する。
  ISS-00079 対策で sim ごとに専用 subdir に書く構造（btrfs B-tree contention 回避）。
  return: '<cell>/vt_<v>_<t>_<n>_<meas>/oir=<o>_arc=<a>' 形式の base path"""
  cell_dir = str(mlc.cell)
  meas_dir = f"vt_{mls.vdd_voltage}_{mls.temperature}_{num}_{mec.meas_type}"
  arc_part = "oir=" + ''.join(mec.pin_oirc) + "_arc=" + ''.join(mec.arc_oirc)
  os.makedirs(f"{cell_dir}/{meas_dir}", exist_ok=True)
  return f"{cell_dir}/{meas_dir}/{arc_part}"


def _make_sim_path(spicef_base:str) -> str:
  """spicef_base (sim 個別 path、 拡張子なし) を dir として作成し、 spicef_base/sim.sp を返す。
  ISS-00079 対策で 1 sim = 1 dir の構造（並列 inode 作成の contention 回避）。"""
  os.makedirs(spicef_base, exist_ok=True)
  return f"{spicef_base}/sim.sp"

import numpy as np
from typing import List
from jinja2 import Environment, FileSystemLoader
from dataclasses import dataclass
from pathlib import Path

#env = Environment(
#    loader=FileSystemLoader('.'),
#    line_comment_prefix='##',
#)
#tb_template = env.get_template('./template/temp_testbench.sp.jp2')


base_dir=Path(__file__).resolve().parent
env = Environment(
    loader=FileSystemLoader(str(base_dir)),
    line_comment_prefix='##',
)
tb_template = env.get_template("temp_testbench.sp.jp2")
  
#--------------------------------------------------------------------------------------------------
def runExpectation(targetLib:Mls, targetCell:Mlc, expectationdictList:List[Mec]):
  harnessList = []

  size=len(expectationdictList)
  for ii in range(size):
    exp_tmp = expectationdictList[ii]

    ## meas_types is mandatory (legacy meas_type external input is removed)
    meas_types_list = list(exp_tmp.meas_types)
    if not meas_types_list:
      print(f"[Error] meas_types is empty for entry {ii}.")
      my_exit()

    for mt in meas_types_list:
      #--- skip for debug
      if (targetLib.measures_only) and (mt not in targetLib.measures_only):
        continue

      ## deep copy and set meas_type per loop iteration via setter
      expectationdict = copy.deepcopy(exp_tmp)
      expectationdict.set_meas_type(mt)

      #--- do simulation
      if   mt in ["delay","preset","clear","rising_edge","falling_edge"]:
        rslt_Harness = runSpiceDelayMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)

      elif mt in ["power_tout","power_c2c","power_i2c","power_c2i","power_i2i"]:
        rslt_Harness = runSpicePowerToutMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)

      elif mt in ["power_tin"]:
        rslt_Harness = runSpicePowerTinMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)

      elif mt in ["setup_rising","setup_falling","recovery_rising", "recovery_falling"]:
        rslt_Harness = runSpiceSetupMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)

      elif mt in ["hold_rising","hold_falling","removal_rising","removal_falling"]:
        rslt_Harness = runSpiceHoldMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)

      elif mt in ["passive"]:
        rslt_Harness = runSpicePassiveMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)

      elif mt in ["min_pulse_width_low","min_pulse_width_high"]:
        rslt_Harness = runSpiceMinPulseMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)

      elif mt in ["delay_i2i","delay_i2c","delay_c2i","delay_c2c"]: #-- for IO cell
        rslt_Harness = runSpiceDelayMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)

      elif mt.startswith("three_state_"): #-- IO cell (_c2i suffix) or std cell (no suffix)
        rslt_Harness = runSpiceDelayMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)

      elif mt in ["leakage"]:
        rslt_Harness = runSpiceLeakageMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)

      else:
        print(f"[Error] not support measure_type={mt}.")
        my_exit()

      ## add result
      harnessList.extend(rslt_Harness)


  ## average cin of each harness
  #targetCell.set_cin_avg(harnessList=harnessList)
  targetCell.set_cin_max(harnessList=harnessList)

  ## max pleak in each input condition
  #targetCell.set_pleak_icrs(harnessList=harnessList)
  ## average pleak of each harness & cell
  targetCell.set_max_pleak(harnessList=harnessList)

  ##
  return harnessList

#--------------------------------------------------------------------------------------------------
def runSpiceDelayMultiThread(num:int, mls:Mls, mlc:Mlc, mec:Mec)  -> list[Mcar]:

  ## spice file name (ISS-00079: sim ごとに dir 分離、 第 1,2 層は _build_spicef_base で作成)
  spicef = _build_spicef_base(mls, mlc, mec, num)

  # Limit number of threads
  poolg_sema = threading.BoundedSemaphore(mls.num_thread)
  print("Num threads for simulation:"+str(mls.num_thread))

  ###################################################################
  #-- for delay
  thread_id = 0
  threadlist = list()

  h_delay = Mcar(mls=mls, mlc=mlc, mec=mec)
  h_delay.set_update()

  #------ get slopes/loads
  if h_delay.measure_type in ["rising_edge","falling_edge","clear","preset"]:
    kind="delay"
  else:
    kind=h_delay.measure_type.replace("three_state_enable","delay").replace("three_state_disable","delay_disable")

  temp=mlc.template[kind]
  if not temp:
    print(f"[Error] not defined template={kind} in cell_xx.jsonc .")
    my_exit()

  index1_slopes=temp.index_1
  index2_loads =temp.index_2
  if mls.template_index1_only:
    index1_slopes = [index1_slopes[i] for i in mls.template_index1_only if i < len(index1_slopes)]
  if mls.template_index2_only:
    index2_loads  = [index2_loads[i]  for i in mls.template_index2_only if i < len(index2_loads)]

  h_delay.template_kind  = kind
  h_delay.template       = temp

  if len(index2_loads)<1:
    if kind == "delay_disable":
      index2_loads = [0.0]   # 1D template (10x0) uses a single load=0; output disable arc is load-independent
    else:
      print(f"[Error] load size is 0 for template.")
      my_exit()

  if len(index1_slopes)<1:
    print(f"[Error] slope size is 0 for template.")
    my_exit()

  #------ search delay(trans)
  for index2_load in index2_loads:
    for index1_slope in index1_slopes:
      thread = threading.Thread(target=runSpiceDelaySingle,
                                kwargs={"poolg_sema"   :poolg_sema,
                                        "targetHarness":h_delay,
                                        "spicef"       :spicef,
                                        "index1_slope" :index1_slope,
                                        "index2_load"  :index2_load},
                                name="%d" % thread_id)

      threadlist.append(thread)
      thread_id += 1

  for thread in threadlist:
    thread.start()

  for thread in threadlist:
    thread.join()


  h_delay.set_lut(value_name="prop")
  h_delay.set_lut(value_name="trans")

  #------ update max_load/max_trans
  mlc.update_max_load4out(port_name=h_delay.target_outport, new_value=max(index2_loads))
  mlc.update_max_trans4in(port_name=h_delay.target_relport, new_value=max(index1_slopes))

  return [h_delay]


#--------------------------------------------------------------------------------------------------
def runSpicePowerToutMultiThread(num:int, mls:Mls, mlc:Mlc, mec:Mec)  -> list[Mcar]:

  ## spice file name (ISS-00079: sim ごとに dir 分離、 第 1,2 層は _build_spicef_base で作成)
  spicef = _build_spicef_base(mls, mlc, mec, num)

  # Limit number of threads
  poolg_sema = threading.BoundedSemaphore(mls.num_thread)
  print("Num threads for simulation:"+str(mls.num_thread))

  ###################################################################
  #-- for power
  thread_id = 0
  threadlist = list()

  h_power = Mcar(mls=mls, mlc=mlc, mec=mec)
  h_power.set_update()

  if not h_power.measure_type.startswith("three_state_disable"):

    #------ get slopes/loads
    if h_power.measure_type in ["rising_edge","falling_edge","clear","preset"]:
      kind="power_tout"
    elif h_power.measure_type == "power_tout":
      kind="power_tout"
    else:
      kind=h_power.measure_type.replace("delay","power").replace("three_state_enable","power")

    temp=mlc.template[kind]
    if not temp:
      print(f"[Error] not defined template={kind} in cell_xx.jsonc .")
      my_exit()

    index1_slopes=temp.index_1
    index2_loads =temp.index_2
    if mls.template_index1_only:
      index1_slopes = [index1_slopes[i] for i in mls.template_index1_only if i < len(index1_slopes)]
    if mls.template_index2_only:
      index2_loads  = [index2_loads[i]  for i in mls.template_index2_only if i < len(index2_loads)]

    h_power.template_kind  = kind
    h_power.template       = temp

    if len(index2_loads)<1:
      print(f"[Error] load size is 0 for template.")
      my_exit()

    if len(index1_slopes)<1:
      print(f"[Error] slope size is 0 for template.")
      my_exit()

    #------ energy
    for index2_load in index2_loads:
      for index1_slope in index1_slopes:
        thread = threading.Thread(target=runSpicePowerToutSingle,
                                  kwargs={"poolg_sema"   :poolg_sema,
                                          "targetHarness":h_power,
                                          "spicef"       :spicef,
                                          "index1_slope" :index1_slope,
                                          "index2_load"  :index2_load},
                                  name="%d" % thread_id)

        threadlist.append(thread)
        thread_id += 1

    for thread in threadlist:
      thread.start()

    for thread in threadlist:
      thread.join()


    h_power.set_lut(value_name="eintl")

    #------ update max_load/max_trans
    mlc.update_max_load4out(port_name=h_power.target_outport, new_value=max(index2_loads))
    mlc.update_max_trans4in(port_name=h_power.target_relport, new_value=max(index1_slopes))

  return [h_power]


#--------------------------------------------------------------------------------------------------
def runSpicePowerTinMultiThread(num:int, mls:Mls, mlc:Mlc, mec:Mec)  -> list[Mcar]:
  ## input pin internal_power: 1D template (input slope only, output load = 0pF)

  ## spice file name (ISS-00079: sim ごとに dir 分離、 第 1,2 層は _build_spicef_base で作成)
  spicef = _build_spicef_base(mls, mlc, mec, num)

  # Limit number of threads
  poolg_sema = threading.BoundedSemaphore(mls.num_thread)
  print("Num threads for simulation:"+str(mls.num_thread))

  ###################################################################
  #-- for input pin internal_power
  thread_id = 0
  threadlist = list()

  h_power = Mcar(mls=mls, mlc=mlc, mec=mec)
  h_power.set_update()

  kind = "power_tin"
  temp = mlc.template[kind]
  if not temp:
    print(f"[Error] not defined template={kind} in cell_xx.jsonc .")
    my_exit()

  index1_slopes = temp.index_1
  if mls.template_index1_only:
    index1_slopes = [index1_slopes[i] for i in mls.template_index1_only if i < len(index1_slopes)]

  h_power.template_kind = kind
  h_power.template      = temp

  if len(index1_slopes) < 1:
    print(f"[Error] slope size is 0 for template.")
    my_exit()

  # 1D loop: index_1 only (no index_2)
  for index1_slope in index1_slopes:
    thread = threading.Thread(target=runSpicePowerTinSingle,
                              kwargs={"poolg_sema"   :poolg_sema,
                                      "targetHarness":h_power,
                                      "spicef"       :spicef,
                                      "index1_slope" :index1_slope},
                              name="%d" % thread_id)

    threadlist.append(thread)
    thread_id += 1

  for thread in threadlist:
    thread.start()

  for thread in threadlist:
    thread.join()


  h_power.set_lut(value_name="eintl")

  return [h_power]


#--------------------------------------------------------------------------------------------------
def runSpiceDelaySingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope:float, index2_load:float):
  """ISS-00080 Step 3：Mtp 早期 instantiate + param 渡し型に変更。"""
  h=targetHarness
  arc_oirc = h.mec.arc_oirc

  #-- sim_c2d_max（load 依存、 io セルは 0.1 倍）
  sim_c2d_max_per_unit = h.mls.sim_c2d_max_per_unit
  if h.mlc.isio:
    sim_c2d_max_per_unit = sim_c2d_max_per_unit * 0.1
  sim_c2d_max = max(sim_c2d_max_per_unit * index2_load, h.mls.sim_c2d_min)
  sim_c2d_max = min(sim_c2d_max, h.mls.sim_c2d_max)

  #-- tsim_end
  tsim_end=max(1e-6, 2*sim_c2d_max * h.mls.time_mag)

  #-- timestep
  slope          = index1_slope
  tslew_min_s    = h.mls.simulation_slew_min
  timestep_tstep = max(h.mls.simulation_timestep_min, min(slope * 0.0099, h.mls.simulation_timestep_max))
  timestep_tmax  = 20 * timestep_tstep

  #-- pullres_role / pullres_gate（three_state arc 依存）
  pullres_role="nouse"
  pullres_gate=""
  if h.timing_type == "three_state_enable":
    pullres_role = "down" if arc_oirc[0]=="r" else "up"   if arc_oirc[0]=="f" else "nouse"
  elif h.timing_type == "three_state_disable":
    outport=h.mec.pin_oirc[0]
    if outport not in h.mlc.oe_infos.keys():
      print(f"[ERROR] no oe_infos exist for {outport} in cell_xx.jsonc.")
      my_exit()
    if arc_oirc[0]=="r":
      cell_type = h.mlc.oe_infos[outport]["drv0"]["type"]
      pullres_role = "up_ngate" if cell_type=="nmos" else "up_pgate"
      pullres_gate="xcell.xdut." + h.mlc.oe_infos[outport]["drv0"]["gate"]
    elif arc_oirc[0]=="f":
      cell_type = h.mlc.oe_infos[outport]["drv1"]["type"]
      pullres_role = "down_ngate" if cell_type=="nmos" else "down_pgate"
      pullres_gate="xcell.xdut." + h.mlc.oe_infos[outport]["drv1"]["gate"]

  #-- cap (remove cap when three_state_disable)
  cap = 0.0 if h.timing_type == "three_state_disable" else index2_load

  #-- param 早期 instantiate
  #-- is_dtp: 短い init で OK な系 (delay/three_state)。 FF 系 (rising_edge/falling_edge/clear/preset) は False で長い init
  #-- runSpiceDelaySingle には power 系は来ないため "power" は判定不要
  is_dtp = h.measure_type.startswith(("delay","three"))
  param = Mtp(
     cap          = float("{:.5g}".format(cap  * h.mls.capacitance_mag))
    ,clk_role     = h.clk_role
    ,pullres_role = pullres_role
    ,pullres_gate = pullres_gate
    ,meas_energy  = 0
    ,time_energy  = [0,0]
    ,meas_o_max_min=0
    ,tslew_min    = float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,timestep     = float("{:.5g}".format(timestep_tstep * h.mls.time_mag))
    ,timestep_tmax= float("{:.5g}".format(timestep_tmax  * h.mls.time_mag))
    ,tsim_end     = tsim_end
    ,tdelay_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tpulse_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    = 1e-9   # ISS-00076 WOUT pre-charge SW で Q を init 段で強制設定するため、 D→Q 待ち padding (sim_c2d_max) は不要
    ,tslew_in     = float("{:.5g}".format(tslew_min_s    * h.mls.time_mag))
    ,tdelay_rel   = float("{:.5g}".format(h.mls.sim_d2c_max  * h.mls.time_mag))
    ,tslew_rel    = _tslew_from_template(index1_slope, h.mls)
    ,tpulse_rel   = tsim_end
    ,tsweep_rel   = 0.0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  param.compute_timing()

  with poolg_sema:
    spicefo  = _make_sim_path(f"{spicef}_{index2_load}_{index1_slope}")

    rslt=genFileLogic_DelayTrial1x(targetHarness=h, spicef=spicefo, param=param)

    with h._lock:
      h.dict_list2["prop" ][index1_slope][index2_load] = rslt["prop"]
      h.dict_list2["trans"][index1_slope][index2_load] = rslt["trans"]


#--------------------------------------------------------------------------------------------------
def genFileLogic_DelayTrial1x(targetHarness:Mcar, spicef:str, param:Mtp) ->dict:
  """ISS-00080 Step 3：param は呼び出し側で early instantiate + compute_timing() 済を期待。"""
  h=targetHarness

  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
  param.write_pinmap_if_enabled(os.path.dirname(spicef))   # ISS-00078: sidecar .pinmap.json
  print(f"  [INFO] generate tb={spicef}")
  
  #-- execute spice
  spicelis=h.mls.exec_spice(spicef=spicef)
                              
  #-- read result
  # read .mt0 for Xyce
  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  # read results
  res_list=["prop_in_out","trans_out"]
  res=dict()
  with open(spicelis,'r') as f:
    
    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub(r'\=',' ',inline)
      
      # search measure
      for key in res_list:
        if((re.search(key, inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res[key]= "{:e}".format(float(sparray[2].strip()))

  # chack if result is exist
  non_value_list=set(res_list)-set(res.keys())

  if non_value_list:
    for k in  non_value_list:
      h.mls.print_msg(f"Value res_{k} is not defined!!")
      h.mls.print_msg(f"Check simulation result in work directory. rslt={spicelis}")
    my_exit()

  #-- result
  rslt=dict()
  rslt["prop"] =float(res["prop_in_out"])
  rslt["trans"]=float(res["trans_out"])

  
  return (rslt)


#--------------------------------------------------------------------------------------------------
def runSpicePowerToutSingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope:float, index2_load:float):
  """ISS-00080 Step 3：Mtp 早期 instantiate + param 渡し型。 PowerTout は 2-trial：
  1st (meas_energy=1) で estart/eend 抽出 → 2nd (meas_energy=2) で energy 測定。
  共通 param を流用、 各 sim 前に変動 fields を更新 + compute_timing()。
  """
  h=targetHarness
  arc_oirc = h.mec.arc_oirc

  #-- sim_c2d_max（load 依存、 io 0.1 倍）
  sim_c2d_max_per_unit = h.mls.sim_c2d_max_per_unit
  if h.mlc.isio:
    sim_c2d_max_per_unit = sim_c2d_max_per_unit * 0.1
  sim_c2d_max = max(sim_c2d_max_per_unit * index2_load, h.mls.sim_c2d_min)
  sim_c2d_max = min(sim_c2d_max, h.mls.sim_c2d_max)

  #-- timestep
  slope          = index1_slope
  tslew_min_s    = h.mls.simulation_slew_min
  timestep_tstep = max(h.mls.simulation_timestep_min, min(slope * 0.0099, h.mls.simulation_timestep_max))
  #-- is_dtp: 短い init で OK な系。 power_tout は元 arc (rising_edge 等) と同じ sim で計測するため measure_type は元 arc 名 → "power" は判定不要
  is_dtp = h.measure_type.startswith(("delay","three"))

  #-- pullres_role (three_state_enable)
  pullres_role="nouse"
  if h.timing_type == "three_state_enable":
    pullres_role = "down" if arc_oirc[0]=="r" else "up" if arc_oirc[0]=="f" else "nouse"

  #-- param 早期 instantiate（共通部分、 sim 毎の変動 fields は loop で更新）
  param = Mtp(
     cap          = float("{:.5g}".format(index2_load * h.mls.capacitance_mag))
    ,clk_role     = h.clk_role
    ,pullres_role = pullres_role
    ,meas_energy  = 0          # 各 sim で更新
    ,time_energy  = [0,0]      # 各 sim で更新
    ,meas_o_max_min=0
    ,tslew_min    = float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,timestep     = float("{:.5g}".format(timestep_tstep * h.mls.time_mag))
    ,timestep_tmax= float("{:.5g}".format(20*timestep_tstep * h.mls.time_mag))  # 各 sim で更新
    ,tsim_end     = 1e-6        # 各 sim で更新
    ,tdelay_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tpulse_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    = 1e-9   # ISS-00076 pre-force のため D→Q 待ち padding 不要
    ,tslew_in     = float("{:.5g}".format(10*tslew_min_s    * h.mls.time_mag))
    ,tdelay_rel   = float("{:.5g}".format(h.mls.sim_d2c_max  * h.mls.time_mag))
    ,tslew_rel    = _tslew_from_template(index1_slope, h.mls)
    ,tpulse_rel   = 1e-6        # 各 sim で更新
    ,tsweep_rel   = 0.0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)

  with poolg_sema:
    spicefoe1 = _make_sim_path(f"{spicef}_{index2_load}_{index1_slope}_energy1")
    spicefoe2 = _make_sim_path(f"{spicef}_{index2_load}_{index1_slope}_energy2")

    ## 1st trial: extract energy_start/end (meas_energy=1, timestep_tmax ratio=20)
    tsim_end1 = max(1e-6, 2*sim_c2d_max * h.mls.time_mag)
    param.meas_energy   = 1
    param.time_energy   = [0, 0]
    param.tsim_end      = tsim_end1
    param.tpulse_rel    = tsim_end1
    param.timestep_tmax = float("{:.5g}".format(20*timestep_tstep * h.mls.time_mag))
    param.compute_timing()
    rslt1 = genFileLogic_PowerToutTrial1x(targetHarness=h, spicef=spicefoe1, param=param)

    ## 2nd trial: energy measure (meas_energy=2, time_energy=[estart,eend], timestep_tmax ratio=4)
    estart = rslt1["estart"]
    eend   = rslt1["eend"]
    tslew_rel_s = _tslew_from_template(index1_slope, h.mls)
    tsim_end2 = max(eend, estart + tslew_rel_s) + 1e-9
    param.meas_energy   = 2
    param.time_energy   = [estart, eend]
    param.tsim_end      = tsim_end2
    param.tpulse_rel    = tsim_end2
    param.timestep_tmax = float("{:.5g}".format(4*timestep_tstep * h.mls.time_mag))
    param.compute_timing()
    rslt2 = genFileLogic_PowerToutTrial1x(targetHarness=h, spicef=spicefoe2, param=param)

    print(f'  [INFO] pleak={rslt2["pleak"]}, load={index2_load}, slope={index1_slope}')

    with h._lock:
      h.dict_list2["eintl"][index1_slope][index2_load] = rslt2["eintl"]
      h.dict_list2["cin"  ][index1_slope][index2_load] = rslt2["cin"  ]


#--------------------------------------------------------------------------------------------------
def runSpicePowerTinSingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope:float):
  """ISS-00080 Step 3：Mtp 早期 instantiate + param 渡し型。
  input pin internal_power: 1D template (no output load).
  meas_energy=5: estart/eend は input transition window で固定（VREL biport stim）、
  param.compute_timing() の絶対時刻と一致させる。
  """
  h = targetHarness
  arc_oirc = h.mec.arc_oirc

  #-- sim_c2d_max（load=0）
  sim_c2d_max_per_unit = h.mls.sim_c2d_max_per_unit
  if h.mlc.isio:
    sim_c2d_max_per_unit = sim_c2d_max_per_unit * 0.1
  sim_c2d_max = max(sim_c2d_max_per_unit * 0.0, h.mls.sim_c2d_min)
  sim_c2d_max = min(sim_c2d_max, h.mls.sim_c2d_max)

  #-- timestep
  slope          = index1_slope
  tslew_min_s    = h.mls.simulation_slew_min
  timestep_tstep = max(h.mls.simulation_timestep_min, min(slope * 0.0099, h.mls.simulation_timestep_max))

  #-- param 早期 instantiate（meas_energy=5、 estart/eend は compute_timing 後に確定）
  is_dtp = h.measure_type.startswith(("delay","three","power"))
  param = Mtp(
     cap          = float("{:.5g}".format(0.0 * h.mls.capacitance_mag))
    ,clk_role     = h.clk_role
    ,pullres_role = "nouse"
    ,meas_energy  = 5
    ,time_energy  = [0,0]    # compute_timing 後に [t_rel0, t_rel0 + tslew_rel + 1e-9] で更新
    ,meas_o_max_min=0
    ,tslew_min    = float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,timestep     = float("{:.5g}".format(timestep_tstep * h.mls.time_mag))
    ,timestep_tmax= float("{:.5g}".format(4*timestep_tstep * h.mls.time_mag))
    ,tsim_end     = 1e-6      # compute_timing 後に確定
    ,tdelay_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tpulse_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    = 1e-9   # ISS-00076 pre-force のため D→Q 待ち padding 不要
    ,tslew_in     = float("{:.5g}".format(10*tslew_min_s    * h.mls.time_mag))
    ,tdelay_rel   = float("{:.5g}".format(h.mls.sim_d2c_max  * h.mls.time_mag))
    ,tslew_rel    = _tslew_from_template(index1_slope, h.mls)
    ,tpulse_rel   = 1e-6      # 後で更新
    ,tsweep_rel   = 0.0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  param.compute_timing()

  #-- estart/eend を param.t_rel0/t_rel1 から確定（VREL transition window）
  estart   = param.t_rel0
  eend     = param.t_rel0 + param.tslew_rel + 1e-9
  tsim_end = eend + 1e-9
  param.time_energy = [estart, eend]
  param.tsim_end    = tsim_end
  param.tpulse_rel  = tsim_end
  param.compute_timing()

  with poolg_sema:
    spicefoe2 = _make_sim_path(f"{spicef}_{index1_slope}_energy2")

    rslt2 = genFileLogic_PowerTinTrial1x(targetHarness=h, spicef=spicefoe2, param=param)

    print(f'  [INFO] pleak={rslt2["pleak"]}, slope={index1_slope}')

    with h._lock:
      h.dict_list2["eintl"][index1_slope][0.0] = rslt2["eintl"]
      h.dict_list2["cin"  ][index1_slope][0.0] = rslt2["cin"  ]

    
    
  
#--------------------------------------------------------------------------------------------------
def genFileLogic_PowerToutTrial1x(targetHarness:Mcar, spicef:str, param:Mtp):
  """ISS-00080 Step 3：param は呼び出し側 (runSpicePowerToutSingle) で early instantiate +
  meas_energy/time_energy/tsim_end/tpulse_rel/timestep_tmax 更新 + compute_timing() 済。
  """
  h=targetHarness

  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
  param.write_pinmap_if_enabled(os.path.dirname(spicef))   # ISS-00078: sidecar .pinmap.json
  print(f"  [INFO] generate tb={spicef}")
  
  #-- execute spice
  spicelis=h.mls.exec_spice(spicef=spicef)
                              
  #-- read result
  # read .mt0 for Xyce
  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  #-- parse results
  res_list=["energy_start","energy_end"]
  res=dict()
  if(param.meas_energy == 2):
    res_list += ["q_in_dyn","q_rel_dyn","q_clk_dyn","q_out_dyn","q_vdd_dyn","q_vss_dyn",
                 "i_vdd_leak","i_vss_leak","i_vnw_leak","i_vpw_leak","i_in_leak","i_rel_leak","i_clk_leak"]
    
  with open(spicelis,'r') as f:
    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub(r'\=',' ',inline)
      
      # search measure
      for key in res_list:
        if((re.search(key, inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res[key]= "{:e}".format(float(sparray[2].strip()))

  # check if measure is exist or not
  non_value_list=set(res_list)-set(res.keys())
  if non_value_list:
    for k in  non_value_list:
      h.mls.print_msg(f"Value res_{k} is not defined!!")
      h.mls.print_msg(f"Check simulation result in work directory. rslt={spicelis}")
    sys.exit()


  # calculate result
  rslt=dict()
  rslt["estart"]=float(res["energy_start"])
  rslt["eend"]  =float(res["energy_end"])
  energy_time=rslt["eend"] - rslt["estart"]
  
  if(param.meas_energy == 2):

    #q_in_dyn =res["q_clk_dyn"] if h.target_relport=="c0" else res["q_rel_dyn"]
    q_in_dyn  = res["q_in_dyn"]
    q_rel_dyn = res["q_rel_dyn"]
    q_clk_dyn = res["q_clk_dyn"]
    
    ## Pleak = max(supply, absorb) * Vdd
    ## supply = I_vdd + I_vnw (into DUT), absorb = I_vss + I_vpw (out of DUT)
    i_vdd = -float(res["i_vdd_leak"])
    i_vss =  float(res["i_vss_leak"])
    i_vnw = -float(res["i_vnw_leak"])
    i_vpw =  float(res["i_vpw_leak"])
    p_supply = i_vdd * (h.mls.vdd_voltage - h.mls.vss_voltage) + i_vnw * (h.mls.nwell_voltage - h.mls.pwell_voltage)
    p_absorb = i_vss * (h.mls.vdd_voltage - h.mls.vss_voltage) + i_vpw * (h.mls.nwell_voltage - h.mls.pwell_voltage)
    pleak = max(p_supply, p_absorb)
    
    ## input energy(=relport energy)
    #ein = abs(float(res["q_in_dyn"])) * h.mls.vdd_voltage
    #ein = abs(float(q_in_dyn)) * h.mls.vdd_voltage

    ## Cin = Qin / V
    c_in  = abs(float(q_in_dyn))/(h.mls.vdd_voltage)
    c_rel = abs(float(q_rel_dyn))/(h.mls.vdd_voltage)
    c_clk = abs(float(q_clk_dyn))/(h.mls.vdd_voltage)

    cin = c_clk if h.target_relport == "c0" else c_rel
    
    ## intl. energy: min-rail method
    ## min(|Q_vdd|, |Q_vss|) = short-circuit charge
    q_vdd = abs(float(res["q_vdd_dyn"]))
    q_vss = abs(float(res["q_vss_dyn"]))
    q_min = min(q_vdd, q_vss)

    e_leak = pleak * energy_time

    eintl = q_min * h.mls.vdd_voltage - e_leak
    if eintl < 0.0:
      eintl = 0.0

    #
    rslt["eintl"]=eintl
    rslt["pleak"]=pleak
    #rslt["ein"  ]=ein
    
    rslt["cin"]=cin

  #
  return (rslt)



#--------------------------------------------------------------------------------------------------
def genFileLogic_PowerTinTrial1x(targetHarness:Mcar, spicef:str, param:Mtp):
  """ISS-00080 Step 3：param は呼び出し側 (runSpicePowerTinSingle) で early instantiate +
  meas_energy=5 / time_energy / tsim_end / tpulse_rel 設定 + compute_timing() 済。
  estart/eend は param.time_energy から取得。
  """
  h = targetHarness
  estart = param.time_energy[0]
  eend   = param.time_energy[1]

  ## generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
  param.write_pinmap_if_enabled(os.path.dirname(spicef))   # ISS-00078: sidecar .pinmap.json
  print(f"  [INFO] generate tb={spicef}")

  ## execute spice
  spicelis = h.mls.exec_spice(spicef=spicef)

  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0"

  ## parse results (no energy_start/end for meas_energy=5)
  res_list = ["q_in_dyn","q_rel_dyn","q_clk_dyn","q_out_dyn","q_vdd_dyn","q_vss_dyn",
              "i_vdd_leak","i_vss_leak","i_vnw_leak","i_vpw_leak","i_in_leak","i_rel_leak","i_clk_leak"]
  res = dict()

  with open(spicelis, 'r') as f:
    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub(r'\=', ' ', inline)
      for key in res_list:
        if((re.search(key, inline, re.IGNORECASE)) and not (re.search("failed", inline)) and not (re.search("Error", inline))):
          sparray = re.split(" +", inline)
          res[key] = "{:e}".format(float(sparray[2].strip()))

  ## check measure existence
  non_value_list = set(res_list) - set(res.keys())
  if non_value_list:
    for k in non_value_list:
      h.mls.print_msg(f"Value res_{k} is not defined!!")
      h.mls.print_msg(f"Check simulation result in work directory. rslt={spicelis}")
    sys.exit()

  ## calculate result
  rslt = dict()
  rslt["estart"] = estart
  rslt["eend"]   = eend
  energy_time    = eend - estart

  q_in_dyn  = res["q_in_dyn"]
  q_rel_dyn = res["q_rel_dyn"]
  q_clk_dyn = res["q_clk_dyn"]

  i_vdd = -float(res["i_vdd_leak"])
  i_vss =  float(res["i_vss_leak"])
  i_vnw = -float(res["i_vnw_leak"])
  i_vpw =  float(res["i_vpw_leak"])
  p_supply = i_vdd * (h.mls.vdd_voltage - h.mls.vss_voltage) + i_vnw * (h.mls.nwell_voltage - h.mls.pwell_voltage)
  p_absorb = i_vss * (h.mls.vdd_voltage - h.mls.vss_voltage) + i_vpw * (h.mls.nwell_voltage - h.mls.pwell_voltage)
  pleak = max(p_supply, p_absorb)

  c_in  = abs(float(q_in_dyn))  / h.mls.vdd_voltage
  c_rel = abs(float(q_rel_dyn)) / h.mls.vdd_voltage
  c_clk = abs(float(q_clk_dyn)) / h.mls.vdd_voltage
  cin = c_clk if h.target_relport == "c0" else c_rel

  q_vdd = abs(float(res["q_vdd_dyn"]))
  q_vss = abs(float(res["q_vss_dyn"]))
  q_min = min(q_vdd, q_vss)

  e_leak = pleak * energy_time
  eintl = q_min * h.mls.vdd_voltage - e_leak
  if eintl < 0.0:
    eintl = 0.0

  rslt["eintl"] = eintl
  rslt["pleak"] = pleak
  rslt["cin"]   = cin

  return rslt


#--------------------------------------------------------------------------------------------------
def runSpiceSetupMultiThread(num:int, mls:Mls, mlc:Mlc, mec:Mec)  -> list[Mcar]:

  ## spice file name (ISS-00079: sim ごとに dir 分離、 第 1,2 層は _build_spicef_base で作成)
  spicef = _build_spicef_base(mls, mlc, mec, num)
  
  # Limit number of threads
  # define semaphore 
  poolg_sema = threading.BoundedSemaphore(mls.num_thread)
  print("Num threads for simulation:"+str(mls.num_thread))

  ###################################################################
  #-- for setup
  thread_id = 0
  threadlist = list()

  h_const = Mcar(mls=mls, mlc=mlc, mec=mec)
  h_const.set_update()
  
  #------ get slopes/slopes
  kind="const"
  temp=mlc.template[kind]
  if not temp:
    print(f"[Error] not defined template={kind} in cell_xx.jsonc .")
    my_exit()

  index1_slopes_const  =temp.index_1
  index2_slopes_rel=temp.index_2
  if mls.template_index1_only:
    index1_slopes_const   = [index1_slopes_const[i]   for i in mls.template_index1_only if i < len(index1_slopes_const)]
  if mls.template_index2_only:
    index2_slopes_rel = [index2_slopes_rel[i] for i in mls.template_index2_only if i < len(index2_slopes_rel)]

  h_const.template_kind  = kind
  h_const.template       = temp

  if len(index1_slopes_const)<1:
    print(f"[Error] slope for constraint(index_1) size is 0 for template.")
    my_exit()

  if len(index2_slopes_rel)<1:
    print(f"[Error] slope for related  (index_2) size is 0 for template.")
    my_exit()

  #------ search delay(trans)
  for index2_slope_rel in index2_slopes_rel:
    for index1_slope_const in index1_slopes_const:
      ##--- result is written in h_delay.dict_list2 with _lock
      thread = threading.Thread(target=runSpiceSetupSingle,
                                kwargs={"poolg_sema":poolg_sema,
                                        "targetHarness":h_const,
                                        "spicef":spicef,
                                        "index1_slope_const":index1_slope_const,
                                        "index2_slope_rel":index2_slope_rel},
                                name="%d" % thread_id)
      
      threadlist.append(thread)
      thread_id += 1

  for thread in threadlist:
    thread.start() 

  for thread in threadlist:
    thread.join() 

  #--- generate lut table
  h_const.set_lut(value_name="setup_hold")

  #------ update max_trans_in
  mlc.update_max_trans4in(port_name=h_const.target_relport, new_value=max(index2_slopes_rel))

    
  ###################################################################
  return [h_const]

#--------------------------------------------------------------------------------------------------
def runSpiceSetupSingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope_const:float, index2_slope_rel:float):
  """ISS-00080 Step 2：Mtp 早期 instantiate + compute_timing() で物理単位の secant 制御。
  param.tsweep_rel / param.tsim_end / param.tpulse_rel を secant ループで更新、
  genFileLogic_Setup1x には param を渡す。 secant range は `param.tsweep_for_rel0_at((t_init3+t_in0)/2)` で算出（ISS-00087）。
  """
  h=targetHarness
  arc_oirc = h.mec.arc_oirc

  #-- sim_c2d_max 実効値（charao_run 内で clamp 後の値）
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * 0.1, h.mls.sim_c2d_min)
  sim_c2d_max = min(sim_c2d_max, h.mls.sim_c2d_max)

  #-- timestep （CLK slew 由来）
  slope          = index2_slope_rel
  timestep_tstep = max(h.mls.simulation_timestep_min, min(slope * 0.0099, h.mls.simulation_timestep_max))
  timestep_tmax  = 20 * timestep_tstep

  #-- param 早期 instantiate（setup: tdelay_in = sim_c2d_max 1倍）
  param = Mtp(
    cap           = 0.0
    ,clk_role     =h.clk_role
    ,meas_energy  =0
    ,time_energy  =[0,0]
    ,meas_o_max_min=0
    ,tslew_min    =float("{:.5g}".format(h.mls.simulation_slew_min * h.mls.time_mag))
    ,timestep     =float("{:.5g}".format(timestep_tstep * h.mls.time_mag))
    ,timestep_tmax=float("{:.5g}".format(timestep_tmax  * h.mls.time_mag))
    ,tsim_end     =1.0E-6
    ,tdelay_init  =float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))   # setup には delay 系 measure_type は来ないため固定
    ,tpulse_init  =float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    =float("{:.5g}".format(_tslew_from_template(index2_slope_rel, h.mls) + sim_c2d_max * h.mls.time_mag))   # ISS-00087: tdelay_in = tslew_rel + sim_c2d_max。 small slew でも sim_c2d_max が下限となり、 seg_start で rel signal を動かす余裕を確保
    ,tslew_in     =_tslew_from_template(index1_slope_const, h.mls)
    ,tdelay_rel   =float("{:.5g}".format(h.mls.sim_d2c_max  * h.mls.time_mag))
    ,tslew_rel    =_tslew_from_template(index2_slope_rel, h.mls)
    ,tpulse_rel   =1.0E-6
    ,tsweep_rel   =0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  param.compute_timing()

  segstep_min  = h.mls.sim_segment_timestep_min * h.mls.time_mag

  with poolg_sema:

    seg_start  = 0.0
    #-- ISS-00080: secant range を物理単位で（_t_rel0 を seg 端まで戻す tsweep を符号反転）
    #-- ISS-00087: seg 端を `(t_init3 + t_in0)/2` に変更（旧 t_init3 端では VCLK 2nd rise が
    #   1st fall と同時刻になり L 期間 0 で ngspice 不安定。 中間配置で L 期間を確保）
    seg_end    = -param.tsweep_for_rel0_at((param.t_init3 + param.t_in0) / 2)

    ratio      = h.mls.sim_segment_timestep_ratio
    threshold  = h.mls.sim_time_const_threshold * h.mls.time_mag

    tsweep_pass=seg_start
    setup_pass =0

    tsim_end=1.0E-6
    prop_min=1.0

    segstep = h.mls.sim_segment_timestep_start * h.mls.time_mag

    cnt=0
    while segstep>= segstep_min:
      cnt=cnt+1

      tsweep_list=np.arange(seg_start, seg_end, segstep)

      #-- search setup and check trans while prop is valid
      for id,tsweep in enumerate(tsweep_list):

        spicefo  = _make_sim_path(f"{spicef}_c{index1_slope_const}_r{index2_slope_rel}_s{cnt*100+id}")

        #-- ISS-00080: param を更新して genFileLogic に渡す
        param.tsweep_rel = tsweep * -1.0
        param.tsim_end   = tsim_end
        param.tpulse_rel = tsim_end
        param.compute_timing()

        rslt=genFileLogic_Setup1x(targetHarness=h, spicef=spicefo, param=param)

        #- check prop_in_out
        prop_last=abs(rslt["prop_in_out"])
        setup_last=rslt["setup_in_rel"]

        prop_min=min(prop_min, prop_last)

        #- check metastable
        if prop_last > prop_min + threshold:
          break;

        #- keep successfull result
        tsim_end=rslt["chg_out"] + 10e-9
        tsweep_pass=tsweep
        setup_pass =setup_last

      #--
      if segstep <= segstep_min:
        break;

      #-- update step/list range
      segstep_old=segstep
      segstep    =segstep*ratio

      seg_start = tsweep_pass - 2*segstep
      seg_end   = tsweep_pass + 1.0*segstep_old

    #-- result in targetHarness
    with h._lock:
      if h.measure_type in ["setup_rising","setup_falling","recovery_rising","recovery_falling"]:
        h.dict_list2["setup_hold" ][index1_slope_const][index2_slope_rel] = setup_pass

      else:
        print(f"[Error] not support measure_type={h.measure_type}")
        my_exit()
      

        
#--------------------------------------------------------------------------------------------------
def genFileLogic_Setup1x(targetHarness:Mcar, spicef:str, param:Mtp) -> dict:
  """ISS-00080 Step 2：param は呼び出し側 (runSpiceSetupSingle) で early instantiate +
  compute_timing() 済を期待。 本関数は testbench 生成 + spice 実行 + 結果 read のみ。
  param.tsweep_rel / param.tsim_end / param.tpulse_rel は secant ループで毎回更新される。
  """
  # rename
  h=targetHarness

  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
  param.write_pinmap_if_enabled(os.path.dirname(spicef))   # ISS-00078: sidecar .pinmap.json
  print(f"  [INFO] generate tb={spicef}")
  
  #-- execute spice
  spicelis=h.mls.exec_spice(spicef=spicef)

  #-- read result
  # read .mt0 for Xyce
  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  # read results(set default value)
  res_list=["chg_out","setup_in_rel","prop_in_out"]
  res={"chg_out"     :1,
       "setup_in_rel":1,
       "prop_in_out" :1}
  
  with open(spicelis,'r') as f:
    
    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub(r'\=',' ',inline)
      
      # search measure
      #for key in ["chg_out","setup_in_rel","hold_rel_in","prop_in_out"]:
      for key in res_list:
        if((re.search(key, inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res[key]= "{:e}".format(float(sparray[2].strip()))
          
  # check spice finish successfully

  
  # result
  rslt={
    "chg_out"      :float(res["chg_out"]),
    "setup_in_rel" :float(res["setup_in_rel"]),
    "prop_in_out"  :float(res["prop_in_out"])}

  return (rslt)



#--------------------------------------------------------------------------------------------------
def runSpiceHoldMultiThread(num:int, mls:Mls, mlc:Mlc, mec:Mec)  -> list[Mcar]:

  ## spice file name (ISS-00079: sim ごとに dir 分離、 第 1,2 層は _build_spicef_base で作成)
  spicef = _build_spicef_base(mls, mlc, mec, num)
  
  # Limit number of threads
  # define semaphore 
  poolg_sema = threading.BoundedSemaphore(mls.num_thread)
  print("Num threads for simulation:"+str(mls.num_thread))

  ###################################################################
  #-- for hold
  thread_id = 0
  threadlist = list()

  h_const = Mcar(mls=mls, mlc=mlc, mec=mec)
  h_const.set_update()
  
  #------ get slopes/slopes
  kind="const"
  temp=mlc.template[kind]
  if not temp:
    print(f"[Error] not defined template={kind} in cell_xx.jsonc .")
    my_exit()

  index1_slopes_const  =temp.index_1
  index2_slopes_rel=temp.index_2
  if mls.template_index1_only:
    index1_slopes_const   = [index1_slopes_const[i]   for i in mls.template_index1_only if i < len(index1_slopes_const)]
  if mls.template_index2_only:
    index2_slopes_rel = [index2_slopes_rel[i] for i in mls.template_index2_only if i < len(index2_slopes_rel)]

  h_const.template_kind  = kind
  h_const.template       = temp

  if len(index1_slopes_const)<1:
    print(f"[Error] slope for constraint(index_1) size is 0 for template.")
    my_exit()

  if len(index2_slopes_rel)<1:
    print(f"[Error] slope for related  (index_2) size is 0 for template.")
    my_exit()

  #------ search hold
  for index2_slope_rel in index2_slopes_rel:
    for index1_slope_const in index1_slopes_const:
      ##--- result is written in h_delay.dict_list2 with _lock
      thread = threading.Thread(target=runSpiceHoldSingle,
                                kwargs={"poolg_sema":poolg_sema,
                                        "targetHarness":h_const,
                                        "spicef":spicef,
                                        "index1_slope_const":index1_slope_const,
                                        "index2_slope_rel":index2_slope_rel},
                                name="%d" % thread_id)
      
      threadlist.append(thread)
      thread_id += 1

  for thread in threadlist:
    thread.start() 

  for thread in threadlist:
    thread.join() 

  #--- generate lut table
  h_const.set_lut(value_name="setup_hold")
  
  ###################################################################
  return [h_const]

#--------------------------------------------------------------------------------------------------
def runSpiceHoldSingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope_const:float, index2_slope_rel:float):
                      
  """ISS-00080 Step 2：Mtp 早期 instantiate + compute_timing() で物理単位の secant 制御。
  hold は tdelay_in = 2*sim_c2d_max（setup の 2 倍）、 tsweep_rel は負方向。
  """
  h=targetHarness
  arc_oirc = h.mec.arc_oirc

  #-- sim_c2d_max 実効値
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * 0.1, h.mls.sim_c2d_min)
  sim_c2d_max = min(sim_c2d_max, h.mls.sim_c2d_max)

  #-- timestep
  slope          = index2_slope_rel
  tslew_min_s    = h.mls.simulation_slew_min   # ns 単位（後で time_mag 倍）
  timestep_tstep = max(h.mls.simulation_timestep_min, min(slope * 0.0099, h.mls.simulation_timestep_max))
  timestep_tmax  = 20 * timestep_tstep

  #-- param 早期 instantiate（hold: meas_o_max_min=1、 tsim_end は compute_timing 後に確定）
  param = Mtp(
    cap           = 0.0
    ,clk_role     =h.clk_role
    ,meas_energy  =0
    ,time_energy  =[0,0]
    ,meas_o_max_min=1
    ,tslew_min    =float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,timestep     =float("{:.5g}".format(timestep_tstep * h.mls.time_mag))
    ,timestep_tmax=float("{:.5g}".format(timestep_tmax  * h.mls.time_mag))
    ,tsim_end     =1e-6   # 暫定値。 compute_timing 後に param.t_rel1 + 1ns で再設定
    ,tdelay_init  =float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tpulse_init  =float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    =float("{:.5g}".format(_tslew_from_template(index2_slope_rel, h.mls) + sim_c2d_max * h.mls.time_mag))   # ISS-00087: tdelay_in = tslew_rel + sim_c2d_max。 small slew でも sim_c2d_max が下限となり、 seg_start で rel signal を動かす余裕を確保
    ,tslew_in     =_tslew_from_template(index1_slope_const, h.mls)
    ,tdelay_rel   =float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tslew_rel    =_tslew_from_template(index2_slope_rel, h.mls)
    ,tpulse_rel   =1e-6   # 暫定値、 tsim_end と同期して再設定
    ,tsweep_rel   =0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  param.compute_timing()
  #-- ISS-00087: tsim_end は旧 hold 固定式 (5*tslew_min + sim_d2c_max + sim_pulse_max + ...) ではなく、
  #   compute_timing() で算出された param.t_rel1 (= rel signal slew 完了時刻) + 1 ns buffer で確定。
  #   tdelay_in 式変更時にも自動で整合する。 t_clk6/7 は tsim_end 依存（clk_role="input"/"nouse" 分岐）
  #   なので、 tsim_end 確定後に compute_timing() を **2 回目**呼び直して t_clk6/7 を再計算する。
  tsim_end = param.t_rel1 + 1e-9
  param.tsim_end   = tsim_end
  param.tpulse_rel = tsim_end
  param.compute_timing()

  segstep_min  = h.mls.sim_segment_timestep_min * h.mls.time_mag

  with poolg_sema:
    #-- ISS-00080: secant range を物理単位で（_t_rel0 を seg 端まで戻す tsweep_rel）
    #-- ISS-00087: seg 端を `(t_init3 + t_in0)/2` に変更（旧 t_init3 端では VCLK 2nd rise が
    #   1st fall と同時刻になり L 期間 0 で ngspice 不安定。 中間配置で L 期間を確保）
    seg_start  = param.tsweep_for_rel0_at((param.t_init3 + param.t_in0) / 2)
    seg_end    = 0

    ratio      = h.mls.sim_segment_timestep_ratio
    threshold_high  = h.mls.hold_meas_high_threshold * h.mls.vdd_voltage
    threshold_low   = h.mls.hold_meas_low_threshold  * h.mls.vdd_voltage
    ival_o          = h.target_outport_val

    tsweep_pass=seg_start
    hold_pass  =0

    segstep = h.mls.sim_segment_timestep_start * h.mls.time_mag

    cnt=0
    while segstep>= segstep_min:
      cnt=cnt+1

      tsweep_list=np.arange(seg_start, seg_end, segstep)

      #-- search hold and check v_
      for id,tsweep in enumerate(tsweep_list):

        spicefo  = _make_sim_path(f"{spicef}_c{index1_slope_const}_r{index2_slope_rel}_s{cnt*100+id}")

        #-- ISS-00080: param を更新して genFileLogic に渡す（hold は tsweep 正方向）
        param.tsweep_rel = tsweep * 1.0
        param.compute_timing()

        rslt=genFileLogic_Hold1x(targetHarness=h, spicef=spicefo, param=param)

        #-- get result
        hold_last =rslt["hold_rel_in"]

        #- check metastable(outport=stable)
        if   (ival_o=="0" ) and (threshold_low < rslt["o_max_v"]):
            break
        elif (ival_o=="1" ) and (threshold_high > rslt["o_min_v"]):
            break

        #- keep successfull result
        tsweep_pass=tsweep
        hold_pass  =hold_last

      #--
      #if tstep <= tstep_min:
      if segstep <= segstep_min:
        break
      
      #-- update step/list range
      #tstep_old=tstep
      #tstep    =tstep*ratio
      segstep_old=segstep
      segstep    =segstep*ratio

      #seg_start = tsweep_pass - 1.0*tstep_old
      #seg_start = tsweep_pass - 2*tstep
      #seg_end   = tsweep_pass + 1.0*tstep_old
      seg_start = tsweep_pass - 2*segstep
      seg_end   = tsweep_pass + 1.0*segstep_old

    #
    #print(f"tstep={tstep}, tsweep={tsweep_pass}, setup/hold={setup_pass}/{hold_pass}")
      
    #-- result in targetHarness
    with h._lock:
      if  h.measure_type in ["hold_rising","hold_falling","removal_rising","removal_falling"]:
        h.dict_list2["setup_hold" ][index1_slope_const][index2_slope_rel] = hold_pass
      else:
        print(f"[Error] not support measure_type={h.measure_type}")
        my_exit()
      
    #--
    print(f"  [INFO] hold={hold_pass}")
        
#--------------------------------------------------------------------------------------------------
def genFileLogic_Hold1x(targetHarness:Mcar, spicef:str, param:Mtp) -> dict:
  """ISS-00080 Step 2：param は呼び出し側 (runSpiceHoldSingle) で early instantiate +
  compute_timing() 済を期待。 本関数は testbench 生成 + spice 実行 + 結果 read のみ。
  param.tsweep_rel / param.tsim_end / param.tpulse_rel は secant ループで毎回更新される。
  """
  h=targetHarness

  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
  param.write_pinmap_if_enabled(os.path.dirname(spicef))   # ISS-00078: sidecar .pinmap.json
  print(f"  [INFO] generate tb={spicef}")
  
  #-- execute spice
  spicelis=h.mls.exec_spice(spicef=spicef)

  #-- read result
  # read .mt0 for Xyce
  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  # read results(set default value)
  res_list=["o_max_v","o_min_v","hold_rel_in"]
  res={"o_max_v"     :1,       
       "o_min_v"     :1,
       "hold_rel_in" :1}
  
  with open(spicelis,'r') as f:
    
    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub(r'\=',' ',inline)
      
      # search measure
      for key in res_list:
        if((re.search(key, inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res[key]= "{:e}".format(float(sparray[2].strip()))
          
  # check spice finish successfully

  
  # result
  rslt={
    "o_min_v"    :float(res["o_min_v"]),
    "o_max_v"    :float(res["o_max_v"]),
    "hold_rel_in":float(res["hold_rel_in"])}

  return (rslt)

#--------------------------------------------------------------------------------------------------
def runSpicePassiveMultiThread(num:int, mls:Mls, mlc:Mlc, mec:Mec)  -> list[Mcar]:

  ## spice file name (ISS-00079: sim ごとに dir 分離、 第 1,2 層は _build_spicef_base で作成)
  spicef = _build_spicef_base(mls, mlc, mec, num)
  
  # Limit number of threads
  # define semaphore 
  poolg_sema = threading.BoundedSemaphore(mls.num_thread)
  print("Num threads for simulation:"+str(mls.num_thread))

  ###################################################################
  #-- for passive
  thread_id = 0
  threadlist = list() 

  h_passive = Mcar(mls=mls, mlc=mlc, mec=mec)
  h_passive.set_update()
 
  #------ get slopes/loads
  kind="passive"
  temp=mlc.template[kind]
  if not temp:
    print(f"[Error] not defined template={kind} in cell_xx.jsonc .")
    my_exit()

  index1_slopes_in=temp.index_1
  index2_unuse =temp.index_2
  if mls.template_index1_only:
    index1_slopes_in = [index1_slopes_in[i] for i in mls.template_index1_only if i < len(index1_slopes_in)]

  h_passive.template_kind  = kind
  h_passive.template       = temp
  
  if len(index1_slopes_in)<1:
    print(f"[Error] slope size(index_1) is 0 for template.")
    my_exit()
    
  if len(index2_unuse)>0:
    print(f"[Error] not support index_2 in  template.")
    my_exit()
    
  #------ energy
  for index1_slope in index1_slopes_in:
    thread = threading.Thread(target=runSpicePassiveSingle,
                              args=([poolg_sema, h_passive, spicef, index1_slope]),
                              name="%d" % thread_id)
      
    threadlist.append(thread)
    thread_id += 1

  for thread in threadlist:
    thread.start() 

  for thread in threadlist:
    thread.join() 

  #------ update max_trans_in
  mlc.update_max_trans4in(port_name=h_passive.target_inport, new_value=max(index1_slopes_in))

  #--- generate lut table
  h_passive.set_lut(value_name="eintl")
  #h_passive.set_lut(value_name="ein")
  
  ###################################################################
  return [h_passive]


#--------------------------------------------------------------------------------------------------
def runSpicePassiveSingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope_in:float):
  """ISS-00080 Step 4：Mtp 早期 instantiate + param 渡し型。"""
  h=targetHarness
  arc_oirc = h.mec.arc_oirc

  #-- sim_c2d_max
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * 0.1, h.mls.sim_c2d_min)
  sim_c2d_max = min(sim_c2d_max, h.mls.sim_c2d_max)

  #-- timestep
  slope          = index1_slope_in
  tslew_min_s    = h.mls.simulation_slew_min
  timestep_tstep = max(h.mls.simulation_timestep_min, min(slope * 0.0099, h.mls.simulation_timestep_max))
  timestep_tmax  = 20 * timestep_tstep

  #-- param 早期 instantiate（passive: meas_energy=4、 tsim_end/time_energy は compute_timing 後に確定）
  param = Mtp(
     cap          =0.0
    ,clk_role     =h.clk_role
    ,meas_energy  =4
    ,time_energy  =[0, 0]     # compute_timing 後に [t_rel0, t_rel1 + 2ns] で確定
    ,meas_o_max_min=0
    ,tslew_min    =float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,timestep     =float("{:.5g}".format(timestep_tstep * h.mls.time_mag))
    ,timestep_tmax=float("{:.5g}".format(timestep_tmax  * h.mls.time_mag))
    ,tsim_end     =1e-6       # 暫定値、 compute_timing 後に eend+1ns で再設定
    ,tdelay_init  =float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tpulse_init  =float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    =float("{:.5g}".format(_tslew_from_template(index1_slope_in, h.mls) + sim_c2d_max * h.mls.time_mag))   # ISS-00087: setup/hold と同流儀 (tdelay_in = tslew_rel + sim_c2d_max)。 passive は rel = input pin で tslew_rel = tslew_in
    ,tslew_in     =_tslew_from_template(index1_slope_in, h.mls)
    ,tdelay_rel   =float("{:.5g}".format(h.mls.sim_d2c_max  * h.mls.time_mag))
    ,tslew_rel    =_tslew_from_template(index1_slope_in, h.mls)
    ,tpulse_rel   =1e-6       # 暫定値、 tsim_end と同期して再設定
    ,tsweep_rel   =0.0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  param.compute_timing()
  #-- ISS-00087: 計測 window = [t_rel0, t_rel1 + 2ns] / tsim_end = eend + 1ns
  #   compute_timing() で算出された絶対時刻に合わせて再設定し、 compute_timing() を 2 回目呼び直す
  estart = param.t_rel0
  eend   = param.t_rel1 + 2e-9
  tsim_end = eend + 1e-9
  param.time_energy = [estart, eend]
  param.tsim_end    = tsim_end
  param.tpulse_rel  = tsim_end
  param.compute_timing()

  with poolg_sema:
    spicefoe = _make_sim_path(f"{spicef}_i{index1_slope_in}_energy")

    rslt = genFileLogic_PassiveTrial1x(targetHarness=h, spicef=spicefoe, param=param)

    with h._lock:
      h.dict_list2["eintl"][index1_slope_in][0]=rslt["eintl"]
      h.dict_list2["cin"  ][index1_slope_in][0]=rslt["cin"]
      h.dict_list2["pleak"][index1_slope_in][0]=rslt["pleak"]


#--------------------------------------------------------------------------------------------------
def genFileLogic_PassiveTrial1x(targetHarness:Mcar, spicef:str, param:Mtp):
  """ISS-00080 Step 4：param は呼び出し側 (runSpicePassiveSingle) で early instantiate +
  estart/eend/tsim_end/tpulse_rel 設定 + compute_timing() 済。
  estart/eend は param.time_energy から取得。
  """
  h=targetHarness
  estart = param.time_energy[0]
  eend   = param.time_energy[1]

  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
  param.write_pinmap_if_enabled(os.path.dirname(spicef))   # ISS-00078: sidecar .pinmap.json
  print(f"  [INFO] generate tb={spicef}")
  
  #-- execute spice
  spicelis=h.mls.exec_spice(spicef=spicef)
                              
  #-- read result
  # read .mt0 for Xyce
  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  #-- parse results
  res=dict()
  res_list=["q_rel_dyn","q_in_dyn","q_clk_dyn","q_out_dyn","q_vdd_dyn","q_vss_dyn",
            "i_vdd_leak","i_vss_leak","i_vnw_leak","i_vpw_leak"]
  with open(spicelis,'r') as f:
    
    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub(r'\=',' ',inline)
      
      # search measure
      for key in res_list:
        if((re.search(key, inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res[key]= "{:e}".format(float(sparray[2].strip()))

  # chack if result is exist
  non_value_list=set(res_list)-set(res.keys())
  if non_value_list:
    for k in  non_value_list:
      h.mls.print_msg(f"Value res_{k} is not defined!!")
      h.mls.print_msg(f"Check simulation result in work directory. rslt={spicelis}")
    sys.exit()

  # calculate result
  energy_time = eend - estart
  
  ## Cin = Qin / V
  q_in_dyn  = res["q_in_dyn"]
  q_rel_dyn = res["q_rel_dyn"]
  q_clk_dyn = res["q_clk_dyn"]
  
  c_in  = abs(float(q_in_dyn))/(h.mls.vdd_voltage)
  c_rel = abs(float(q_rel_dyn))/(h.mls.vdd_voltage)
  c_clk = abs(float(q_clk_dyn))/(h.mls.vdd_voltage)

  cin = c_clk if h.target_relport == "c0" else c_rel

  ## Pleak = max(supply, absorb) * Vdd
  i_vdd = -float(res["i_vdd_leak"])
  i_vss =  float(res["i_vss_leak"])
  i_vnw = -float(res["i_vnw_leak"])
  i_vpw =  float(res["i_vpw_leak"])
  p_supply = i_vdd * (h.mls.vdd_voltage - h.mls.vss_voltage) + i_vnw * (h.mls.nwell_voltage - h.mls.pwell_voltage)
  p_absorb = i_vss * (h.mls.vdd_voltage - h.mls.vss_voltage) + i_vpw * (h.mls.nwell_voltage - h.mls.pwell_voltage)
  pleak = max(p_supply, p_absorb)

  ## intl. energy: min-rail method
  q_vdd = abs(float(res["q_vdd_dyn"]))
  q_vss = abs(float(res["q_vss_dyn"]))
  q_min = min(q_vdd, q_vss)

  e_leak = pleak * energy_time

  eintl = q_min * h.mls.vdd_voltage - e_leak
  if eintl < 0.0:
    eintl = 0.0
  
  # result
  rslt={
    "pleak": pleak,
    "cin"  : cin,
    "eintl": eintl
  }
  
  return (rslt)


#--------------------------------------------------------------------------------------------------
def runSpiceMinPulseMultiThread(num:int, mls:Mls, mlc:Mlc, mec:Mec)  -> list[Mcar]:

  ## spice file name (ISS-00079: sim ごとに dir 分離、 第 1,2 層は _build_spicef_base で作成)
  spicef = _build_spicef_base(mls, mlc, mec, num)
  
  # Limit number of threads
  # define semaphore 
  poolg_sema = threading.BoundedSemaphore(mls.num_thread)
  print("Num threads for simulation:"+str(mls.num_thread))

  ###################################################################
  #-- min_pulse
  thread_id = 0
  threadlist = list()

  h_min_pulse = Mcar(mls=mls, mlc=mlc, mec=mec)
  h_min_pulse.set_update()
  
  #------ no slope
  kind="none"
  #temp=mlc.template[kind]
  
  #------ search delay(trans)
  thread = threading.Thread(target=runSpiceMinPulseSingle,
                            kwargs={"poolg_sema":poolg_sema,
                                    "targetHarness":h_min_pulse,
                                    "spicef":spicef},
                            name="%d" % thread_id)
      
  threadlist.append(thread)
  thread_id += 1

  for thread in threadlist:
    thread.start() 

  for thread in threadlist:
    thread.join() 

  #------ set min_pulse
  mlc.set_min_pulse_width(port_name=h_min_pulse.target_relport, value=h_min_pulse.min_pulse_width, measure_type=h_min_pulse.measure_type)
    
  ###################################################################
  return [h_min_pulse]

#--------------------------------------------------------------------------------------------------
def runSpiceMinPulseSingle(poolg_sema, targetHarness:Mcar, spicef:str):
  """ISS-00080 Step 4：Mtp 早期 instantiate + param 渡し型。
  MinPulse は secant ループで `param.tpulse_rel` を sweep（pulse 幅減少 → break 検出）。
  """
  h=targetHarness
  arc_oirc = h.mec.arc_oirc

  #-- sim_c2d_max
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * 0.1, h.mls.sim_c2d_min)
  sim_c2d_max = min(sim_c2d_max, h.mls.sim_c2d_max)

  #-- timestep
  tslew_min_s    = h.mls.simulation_slew_min
  timestep_tstep = max(h.mls.simulation_timestep_min, h.mls.simulation_timestep_max)
  timestep_tmax  = max(100 * h.mls.simulation_timestep_max, timestep_tstep)

  #-- tslew for tslew_in/rel（5 * tslew_min）
  tslew = 5 * tslew_min_s * h.mls.time_mag

  #-- param 早期 instantiate（tpulse_rel/tsim_end は secant で更新）
  param = Mtp(
    cap           = 0.0
    ,clk_role     =h.clk_role
    ,meas_energy  =0
    ,time_energy  =[0,0]
    ,meas_o_max_min=0
    ,tslew_min    = float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,timestep     =float("{:.5g}".format(timestep_tstep * h.mls.time_mag))
    ,timestep_tmax=float("{:.5g}".format(timestep_tmax  * h.mls.time_mag))
    ,tsim_end     =1.0E-6
    ,tdelay_init  =float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))   # min_pulse には delay 系 measure_type は来ないため固定
    ,tpulse_init  =float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    =float("{:.5g}".format(sim_c2d_max         * h.mls.time_mag))
    ,tslew_in     =tslew
    ,tdelay_rel   =float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tslew_rel    =tslew
    ,tpulse_rel   =0.0
    ,tsweep_rel   =0.0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  param.compute_timing()

  with poolg_sema:
    seg_start  = h.mls.sim_pulse_max * h.mls.time_mag
    seg_end    = 0.0
    tstep_min  = h.mls.sim_segment_timestep_min * h.mls.time_mag
    ratio      = h.mls.sim_segment_timestep_ratio
    threshold  = h.mls.sim_time_const_threshold * h.mls.time_mag

    tsweep_pass=seg_start
    pulse_pass =seg_start
    prop_min   =1.0
    tsim_end_dyn=1.0E-6

    tstep = h.mls.sim_segment_timestep_start * h.mls.time_mag
    cnt=0
    while tstep> tstep_min:
      cnt=cnt+1

      tsweep_list=np.arange(seg_start, seg_end, -1.0*tstep)
      tsweep_list=np.append(tsweep_list, 0.0)

      for id,tsweep in enumerate(tsweep_list):

        spicefo  = _make_sim_path(f"{spicef}_s{cnt*100+id}")

        #-- ISS-00080: param 更新
        param.tpulse_rel = tsweep
        param.tsim_end   = tsim_end_dyn
        param.compute_timing()

        rslt=genFileLogic_MinPulse1x(targetHarness=h, spicef=spicefo, param=param)

        prop_last=abs(rslt["prop_in_out"])
        prop_min=min(prop_min, prop_last)

        if prop_last > prop_min + threshold:
          break;

        tsweep_pass=tsweep
        tsim_end_dyn=rslt["chg_out"] + 10e-9
        pulse_pass =rslt["pulse"]

      tstep_old=tstep
      tstep    =tstep*ratio
      seg_start = tsweep_pass + 2*tstep

    with h._lock:
      h.min_pulse_width = pulse_pass


#--------------------------------------------------------------------------------------------------
def genFileLogic_MinPulse1x(targetHarness:Mcar, spicef:str, param:Mtp) -> dict:
  """ISS-00080 Step 4：param は呼び出し側 (runSpiceMinPulseSingle) で early instantiate +
  tpulse_rel/tsim_end 更新 + compute_timing() 済。
  pulse 結果 = param.tslew_in + param.tpulse_rel（tslew = 5*tslew_min、 tpulse_rel = sweep 値）。
  """
  h=targetHarness

  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
  param.write_pinmap_if_enabled(os.path.dirname(spicef))   # ISS-00078: sidecar .pinmap.json
  print(f"  [INFO] generate tb={spicef}")
  
  #-- execute spice
  spicelis=h.mls.exec_spice(spicef=spicef)

  #-- read result
  # read .mt0 for Xyce
  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  # read results(set default value)
  res={"chg_out"     :1,
       "setup_in_rel":1,
       "hold_rel_in" :1,
       "prop_in_out" :1}
  
  with open(spicelis,'r') as f:
    
    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub(r'\=',' ',inline)
      
      # search measure
      for key in ["chg_out","setup_in_rel","hold_rel_in","prop_in_out"]:
        if((re.search(key, inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res[key]= "{:e}".format(float(sparray[2].strip()))
          
  # check spice finish successfully

  
  # hold result
  rslt={
    "chg_out"      :float(res["chg_out"]),
    "prop_in_out"  :float(res["prop_in_out"]),
    "pulse"        :param.tslew_in + param.tpulse_rel}

  return (rslt)

#--------------------------------------------------------------------------------------------------
def runSpiceLeakageMultiThread(num:int, mls:Mls, mlc:Mlc, mec:Mec)  -> list[Mcar]:

  ## spice file name (ISS-00079: sim ごとに dir 分離、 第 1,2 層は _build_spicef_base で作成)
  spicef = _build_spicef_base(mls, mlc, mec, num)
  
  # Limit number of threads
  # define semaphore 
  poolg_sema = threading.BoundedSemaphore(mls.num_thread)
  print("Num threads for simulation:"+str(mls.num_thread))

  ###################################################################
  #-- for leakage
  thread_id = 0
  threadlist = list()

  h_leakage = Mcar(mls=mls, mlc=mlc, mec=mec)
  h_leakage.set_update()

  #------ get slopes/loads
  kind="leakage"

  temp=mlc.template[kind]
  if not temp:
    print(f"[Error] not defined template={kind} in cell_xx.jsonc .")
    my_exit()
  
  index1 =temp.index_1
  index2 =temp.index_2
  
  h_leakage.template_kind  = kind
  h_leakage.template       = temp
    
  if len(index2)>0:
    print(f"[Error] index1 size is over 0 for template.")
    my_exit()
      
  if len(index1)>0:
    print(f"[Error] index2 size is over 0 for template.")
    my_exit()
      
  #------ energy
  thread = threading.Thread(target=runSpiceLeakageSingle,
                            kwargs={"poolg_sema"   :poolg_sema,
                                    "targetHarness":h_leakage,
                                    "spicef"       :spicef},
                            name="%d" % thread_id)
  threadlist.append(thread)
  thread_id += 1
  
  for thread in threadlist:
    thread.start() 
  
  for thread in threadlist:
    thread.join() 
  
  #----
  return [h_leakage]

#--------------------------------------------------------------------------------------------------
def runSpiceLeakageSingle(poolg_sema, targetHarness:Mcar, spicef:str):
  """ISS-00080 Step 4 + ISS-00087: delaySingle ベースで refactor。
  leakage は全 signal stable（init pulse 後）で I(VDD) を AVG 計測（meas_energy=3）。
  計測 window = [t_in0, t_in1] / tsim_end = t_rel3。 D/rel は arc_oirc 全 "s" で transition なし。
  """
  h=targetHarness
  arc_oirc = h.mec.arc_oirc

  #-- timestep（leakage は slope/load 依存なし、 短 TSTEP で AVG window 内のサンプル数を確保）
  tslew_min_s    = h.mls.simulation_slew_min
  timestep_tstep = h.mls.simulation_timestep_min
  timestep_tmax  = 20 * timestep_tstep

  #-- is_dtp: FF でない (= isflop==0) → 短い init で OK
  is_dtp = (h.mlc.isflop == 0)

  param = Mtp(
     cap          = 0.0
    ,clk_role     = h.clk_role
    ,pullres_role = "nouse"
    ,meas_energy  = 3
    ,time_energy  = [0, 0]    # compute_timing 後に [t_in0, t_in1] で確定
    ,meas_o_max_min=0
    ,tslew_min    = float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,timestep     = float("{:.5g}".format(timestep_tstep * h.mls.time_mag))
    ,timestep_tmax= float("{:.5g}".format(timestep_tmax  * h.mls.time_mag))
    ,tsim_end     = 1e-6      # 暫定値、 compute_timing 後に t_rel3 で再設定
    ,tdelay_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tpulse_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    = 1e-9 if is_dtp else 10e-9  # ISS-00087: 非 FF は 1ns、 FF は settling 確保 10ns（orig との 10〜30 倍乖離は別途調査）
    ,tslew_in     = 1e-9      # ISS-00087: AVG window = [t_in0, t_in1] = tslew_in = 1ns
    ,tdelay_rel   = 1e-9      # leakage: rel transition なし、 短い 1 ns
    ,tslew_rel    = float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,tpulse_rel   = float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,tsweep_rel   = 0.0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  param.compute_timing()
  #-- ISS-00087: 計測 window = [t_in0, t_in1] / tsim_end = t_rel3。 compute_timing で算出された
  #   絶対時刻に合わせて Mtp を再設定し、 compute_timing() を **2 回目**呼び直して t_clk6/7 を再計算
  param.time_energy = [param.t_in0, param.t_in1]
  param.tsim_end    = param.t_rel3
  param.compute_timing()

  with poolg_sema:
    spicefoe1 = _make_sim_path(f"{spicef}_leakage")

    rslt = genFileLogic_LeakageTrial1x(targetHarness=h, spicef=spicefoe1, param=param)

    print(f'  [INFO] pleak2={rslt["pleak"]}')

    with h._lock:
      h.pleak = rslt["pleak"]


#--------------------------------------------------------------------------------------------------
def genFileLogic_LeakageTrial1x(targetHarness:Mcar, spicef:str, param:Mtp):
  """ISS-00080 Step 4：param は呼び出し側 (runSpiceLeakageSingle) で early instantiate +
  compute_timing() 済を期待。
  """
  h=targetHarness

  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
  param.write_pinmap_if_enabled(os.path.dirname(spicef))   # ISS-00078: sidecar .pinmap.json
  print(f"  [INFO] generate tb={spicef}")
  
  #-- execute spice
  spicelis=h.mls.exec_spice(spicef=spicef)
                              
  #-- read result
  # read .mt0 for Xyce
  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  #-- parse results
  res_list=["i_vdd_leak", "i_vss_leak", "i_vnw_leak", "i_vpw_leak", "i_vddio_leak", "i_rel_leak"]
  res=dict()
    
  with open(spicelis,'r') as f:
    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub(r'\=',' ',inline)
      
      # search measure
      for key in res_list:
        if((re.search(key, inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res[key]= "{:e}".format(float(sparray[2].strip()))

  # check if measure is exist or not
  non_value_list=set(res_list)-set(res.keys())
  if non_value_list:
    for k in  non_value_list:
      h.mls.print_msg(f"Value res_{k} is not defined!!")
      h.mls.print_msg(f"Check simulation result in work directory. rslt={spicelis}")
    sys.exit()


  # calculate result
  rslt=dict()
  
  ## Pleak = max(supply, absorb) * Vdd
  i_vdd = -float(res["i_vdd_leak"])
  i_vss =  float(res["i_vss_leak"])
  i_vnw = -float(res["i_vnw_leak"])
  i_vpw =  float(res["i_vpw_leak"])
  p_supply = i_vdd * (h.mls.vdd_voltage - h.mls.vss_voltage) + i_vnw * (h.mls.nwell_voltage - h.mls.pwell_voltage)
  p_absorb = i_vss * (h.mls.vdd_voltage - h.mls.vss_voltage) + i_vpw * (h.mls.nwell_voltage - h.mls.pwell_voltage)
  pleak = max(p_supply, p_absorb)

  #if h.target_relport_val == "0":
  #if (i_rel_leak > 0.0) and (pleak > i_rel_leak):
  #  pleak = pleak - i_rel_leak

  #
  #print(f"i_vdd_leak={i_vdd_leak}, i_rel_leak={i_rel_leak}, pleak={pleak}")
  rslt["pleak"]=pleak

  #
  return (rslt)

