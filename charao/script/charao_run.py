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


#==============================================================================
# DEBUG: sp-generation limit (ISS-00118)
#   charao.py が `--debug_stop N` で _DBG_SP_LIMIT を設定。
#   N 個の testbench (sim.sp) 生成時点で os._exit(0)。
#   lrPymRPC は正常終了として結果転送するため、 生成済 sp / work/ をローカル取得可能。
#==============================================================================
_DBG_SP_LIMIT = 0
_DBG_SP_COUNT = [0]
_DBG_SP_LOCK  = threading.Lock()


#==============================================================================
# ISS-00121: max 集約対象 measure_type と集約関数
#   出力 2 個セル（DFFB 等）で Q/QB の constraint 計測値の max を採用するため、
#   全 sim 完了後に runExpectation 末尾で同 group の harness を集約 → max 採用。
#   group key = (measure_type, target_relport, target_inport, timing_when, constraint)
#   group size=1 (dffrsnq 等) では skip → 既存動作と完全同じ。
#   既存 MultiThread の set_lut() 呼び出しはコメントアウト（動作確認完了まで）、
#   runExpectation 末尾で set_lut() を一括実行。
#==============================================================================
MAX_AGGREGATE_MEAS_TYPES = [
    "setup_rising", "setup_falling",
    "hold_rising",  "hold_falling",
    "recovery_rising", "recovery_falling",
    "removal_rising",  "removal_falling",
]


def _meas_type_to_value_names(measure_type):
  """measure_type → set_lut 対象の value_name list (空 list なら set_lut 不要)。"""
  if measure_type in ["delay", "rising_edge", "falling_edge", "clear", "preset"] or \
     measure_type.startswith("three_state_") or \
     measure_type.startswith("delay_"):
    return ["prop", "trans"]
  if measure_type in ["power_tout", "power_tin", "passive"]:
    return ["eintl"]
  if measure_type in MAX_AGGREGATE_MEAS_TYPES:
    return ["setup_hold"]
  # min_pulse_width_* / leakage は set_lut 不要（dict_list2 直接 export）
  return []


def _aggregate_max_in_harness_list(harness_list):
  """ISS-00121: 同 group の harness を集約、 各 (index1, index2) で max 採用。
  spice 結果 raw は dict_list2["setup_hold_raw"] に保持（変更しない）、 集約 max は
  rep (group[0]) の dict_list2["setup_hold"] に deep copy + max 上書きで新規格納し、
  rep.set_lut("setup_hold") で lut/lut_min2max[setup_hold] 生成。
  aux (group[1:]) の dict_list2["setup_hold"] / lut["setup_hold"] は未設定（export で skip）。
  group key = (measure_type, target_relport, target_inport, timing_when, constraint)
  """
  groups = {}
  for h in harness_list:
    if h.measure_type not in MAX_AGGREGATE_MEAS_TYPES:
      continue
    key = (h.measure_type, h.target_relport, h.target_inport, h.timing_when, h.direction_in_lib["constraint"])
    groups.setdefault(key, []).append(h)

  src_name = "setup_hold_raw"
  dst_name = "setup_hold"

  for group in groups.values():
    rep = group[0]
    # rep の dict_list2[setup_hold_raw] を deep copy → dict_list2[setup_hold] に新規格納
    rep.dict_list2[dst_name] = copy.deepcopy(rep.dict_list2[src_name])
    # group 内全 harness の raw 値で max 上書き
    for h in group:
      for i1, sub in h.dict_list2[src_name].items():
        for i2, val in sub.items():
          if val > rep.dict_list2[dst_name][i1][i2]:
            rep.dict_list2[dst_name][i1][i2] = val
    # rep の set_lut で lut/lut_min2max[setup_hold] 生成（aux は未生成のまま）
    rep.set_lut(dst_name)


def _check_dbg_sp(spicef:str, mls:Mls) -> None:
  #-- ISS-00226: 停止通知は print_msg_dbg 経由（supress_debug_msg="true" で抑制できる）。
  #   従来 print() 直書きで、 設定 supress_debug_msg が書いても効かない状態だった。
  if _DBG_SP_LIMIT <= 0:
    return
  with _DBG_SP_LOCK:
    _DBG_SP_COUNT[0] += 1
    if _DBG_SP_COUNT[0] >= _DBG_SP_LIMIT:
      mls.print_msg_dbg(f"[DEBUG] sp count {_DBG_SP_COUNT[0]} reached --debug_stop={_DBG_SP_LIMIT} (last={spicef}), forcing os._exit(0)")
      os._exit(0)


def _tslew_from_template(slew:float, mls:Mls) -> float:
  """Convert template slew (physical threshold-window time) to SPICE PWL
  full-rail (0-100%) ramp duration. Template index_1 represents the
  slew_lower_threshold_pct -> slew_upper_threshold_pct transit time, so the
  full-rail linear ramp duration is slew / (high - low). time_mag is then
  applied to convert to SPICE seconds."""
  # ISS-00155 cal: index_1(stored slew) と実波形の関係は slew_derate_from_library で決まる。
  #   Liberty: 30-70% 遷移時間 = index_1 * slew_derate、full-rail(線形) = その / span。
  #   旧実装は derate を無視して slew/span としており、derate=0.5 のとき ramp が 2x 過大だった。
  span = mls.logic_threshold_high - mls.logic_threshold_low
  return float("{:.5g}".format(slew * mls.slew_derate_from_library / span * mls.time_mag))


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

      elif mt in ["setup_rising","setup_falling","hold_rising","hold_falling","recovery_rising","recovery_falling"]:
        # ISS-00138: setup/hold/recovery を degradation 判定で統一（runSpiceConst）。 FF/LAT は jp2 で吸収。
        # ISS-00143: LAT も統一パスを使用（jp2 の is_lat 分岐が judge_dly の TRIG/TARG を吸収済み。
        #   旧 islatch 分岐が呼んでいた runSpiceLatSetupMultiThread_orig は ISS-00133/00138
        #   リファクタで未定義となっていたため分岐を廃止。 Single_orig 実装は参照用に残置）
        rslt_Harness = runSpiceConstMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)

      elif mt in ["removal_rising","removal_falling"]:
        # ISS-00138: removal のみ電圧判定（CLK の後で Q が遷移しないため degradation 不可）
        if targetCell.islatch:
          rslt_Harness = runSpiceLatHoldMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)
        else:
          rslt_Harness = runSpiceRemovalMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)

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


  ## ISS-00121: max 集約 phase (set_lut の前に dict_list2 を max 更新)
  _aggregate_max_in_harness_list(harnessList)

  ## ISS-00121: set_lut 一括 (全 harness、 measure_type → value_name(s))
  ##   MAX_AGGREGATE_MEAS_TYPES は _aggregate_max_in_harness_list 内で
  ##   rep のみ set_lut("setup_hold") 済み → ここでは skip。
  for h in harnessList:
    if h.measure_type in MAX_AGGREGATE_MEAS_TYPES:
      continue
    for vname in _meas_type_to_value_names(h.measure_type):
      try:
        h.set_lut(value_name=vname)
      except Exception as e:
        print(f"[WARN] ISS-00121 set_lut('{vname}') failed for {h.measure_type}: {e}")

  ## average cin of each harness
  #targetCell.set_cin_avg(harnessList=harnessList)
  targetCell.set_cin_max(harnessList=harnessList)
  ## ISS-00135 reorg(U6): max_trans/max_load も post-hoc 集約（per-harness update_max_* は撤去）
  targetCell.set_max_trans(harnessList=harnessList)
  targetCell.set_max_load(harnessList=harnessList)

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

  temp=mlc.get_template(kind, mec.pin_oirc[0])   # ISS-00150: 出力 port 別 template 対応（adder S/CO）
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


  #h_delay.set_lut(value_name="prop")   # ISS-00121: runExpectation 末尾で一括実行
  #h_delay.set_lut(value_name="trans")  # ISS-00121: runExpectation 末尾で一括実行

  #------ update max_load/max_trans
  # ISS-00135 reorg(U6): max_trans/max_load は set_max_trans/load で post-hoc 集約（撤去）
  #mlc.update_max_load4out(port_name=h_delay.target_outport, new_value=max(index2_loads))
  #mlc.update_max_trans4in(port_name=h_delay.target_relport, new_value=max(index1_slopes))

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

    temp=mlc.get_template(kind, mec.pin_oirc[0])   # ISS-00150: 出力 port 別 template 対応（adder S/CO）
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


    #h_power.set_lut(value_name="eintl")  # ISS-00121: runExpectation 末尾で一括実行

    #------ update max_load/max_trans
    # ISS-00135 reorg(U6): max_trans/max_load は set_max_trans/load で post-hoc 集約（撤去）
    #mlc.update_max_load4out(port_name=h_power.target_outport, new_value=max(index2_loads))
    #mlc.update_max_trans4in(port_name=h_power.target_relport, new_value=max(index1_slopes))

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


  #h_power.set_lut(value_name="eintl")  # ISS-00121: runExpectation 末尾で一括実行

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
  maxstep  = max(h.mls.tmax_low, min(slope * 0.198, h.mls.tmax_high))

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

  ## ISS-00155: index1(slew) を related(切替)入力のスロットに割当てる。
  ##   related pin = pin_tr[1] を pin_oirc 逆引き（優先 c>r>i）。comb は slot2(rel/VREL)、
  ##   seq(clk->Q) は slot3(clk/VCLK)。旧実装は slew を tslew_clk 固定割当していたため、
  ##   comb(slot2)は VREL エッジが tslew_rel 既定=1ns 固定となり入力 slew が反映されていなかった。
  _rel_pin  = h.mec.pin_tr[1] if (len(h.mec.pin_tr) > 1 and h.mec.pin_tr[1]) else ""
  _rel_slot = 3   # 既定 clk（pin_tr[1] 空時は従来動作を維持）
  if _rel_pin:
    for _s in (3, 2, 1):
      if _s < len(h.mec.pin_oirc) and h.mec.pin_oirc[_s] == _rel_pin:
        _rel_slot = _s
        break
  _slope_s = _tslew_from_template(index1_slope, h.mls)

  param = Mtp(
     cap          = float("{:.5g}".format(cap  * h.mls.capacitance_mag))
    ,clk_role     = h.clk_role
    ,clk_init     = h.clk_init
    ,pullres_role = pullres_role
    ,pullres_gate = pullres_gate
    ,meas_energy  = 0
    ,time_energy  = [0,0]
    ,meas_o_max_min=0
    ,tslew_min    = float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,maxstep      = float("{:.5g}".format(maxstep  * h.mls.time_mag))
    ,tsim_end     = tsim_end
    ,tdelay_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tpulse_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    = 1e-9   # ISS-00076 WOUT pre-charge SW で Q を init 段で強制設定するため、 D→Q 待ち padding (sim_c2d_max) は不要
    ,tslew_in     = _slope_s if _rel_slot == 1 else float("{:.5g}".format(tslew_min_s    * h.mls.time_mag))
    ,tslew_rel    = _slope_s if _rel_slot == 2 else 1e-9
    ,tdelay_clk   = float("{:.5g}".format(h.mls.sim_d2c_max  * h.mls.time_mag))
    ,tslew_clk    = _slope_s if _rel_slot == 3 else float("{:.5g}".format(10*tslew_min_s * h.mls.time_mag))
    ,tpulse_clk   = tsim_end
    ,tsweep_clk   = 0.0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  param.compute_timing()

  with poolg_sema:
    spicefo  = _make_sim_path(f"{spicef}_{index2_load}_{index1_slope}")

    #-- ISS-00219: maxstep 確定（同一条件で反復）。 trans_out は maxstep に依存する測定値で、
    #   刻みが粗いと過大に出る。 delay は 1 点 1 sim なので、 分解能が足りない点だけが
    #   追加 sim を払う（大半は 1 回で収束＝コスト増なし）。 絞る方向にしか動かさない。
    #   trans が取れない／sentinel（1.0）の場合はクランプせず従来動作。
    _pts = getattr(h.mls, "simulation_points_per_transition", 0.0)
    for _it in range(4):
      rslt=genFileLogic_DelayTrial1x(targetHarness=h, spicef=spicefo, param=param)
      if _pts <= 0.0: break
      _tr = rslt.get("trans", 0.0)
      if not (0.0 < _tr < 1.0e-6): break        # 未取得 or sentinel
      _lim = _tr / _pts
      if _lim >= param.maxstep * 0.8: break     # 改善 20% 未満で収束
      param.maxstep = float("{:.5g}".format(min(_lim, param.maxstep)))

    with h._lock:
      h.dict_list2["prop" ][index1_slope][index2_load] = rslt["prop"]
      h.dict_list2["trans"][index1_slope][index2_load] = rslt["trans"]
      # ISS-00135 reorg(U6): max_trans/max_load 用に slew/load を per-position 保存
      h.dict_list2["slew_rel"][index1_slope][index2_load] = index1_slope   # delay: VREL=input slew
      h.dict_list2["load_out"][index1_slope][index2_load] = index2_load    # delay: VOUT=load


#--------------------------------------------------------------------------------------------------
def genFileLogic_DelayTrial1x(targetHarness:Mcar, spicef:str, param:Mtp) ->dict:
  """ISS-00080 Step 3：param は呼び出し側で early instantiate + compute_timing() 済を期待。"""
  h=targetHarness

  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
  param.write_pinmap_if_enabled(os.path.dirname(spicef))   # ISS-00078: sidecar .pinmap.json
  #-- ISS-00226: sim 1 本ごとの高頻度ログ。 supress_sim_msg="true" で抑制できる。
  h.mls.print_msg_sim(f"  [INFO] generate tb={spicef}")
  _check_dbg_sp(spicef, h.mls)   # ISS-00118 debug: stop after N sp

  #-- execute spice
  spicelis=h.mls.exec_spice(spicef=spicef)
                              
  #-- read result
  # read .mt0 for Xyce
  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  # read results
  # ISS-00133: prop は related pin(pin_tr[1]) で選択。 clock(c*) 基準 = prop_clk_out(CLK->OUT)、
  #   それ以外(input/async on VREL) = prop_rel_out(REL->OUT)。 comb は入力を VREL に置く(ISS-00135)ため
  #   prop_rel_out、 seq_ff rising/falling_edge は pin_tr=[o0,c0] -> prop_clk_out、 seq_lat は
  #   pin_tr[1]=input -> prop_rel_out。 pin_tr 未設定/短い場合は prop_rel_out（clock 基準でない）。
  _rel_pin  = h.mec.pin_tr[1] if len(h.mec.pin_tr) > 1 else ""
  _prop_key = "prop_clk_out" if _rel_pin.startswith("c") else "prop_rel_out"
  res_list=[_prop_key,"trans_out"]
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
  rslt["prop"] =float(res[_prop_key])
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
  maxstep  = max(h.mls.tmax_low, min(slope * 0.198, h.mls.tmax_high))
  #-- is_dtp: 短い init で OK な系。 power_tout は元 arc (rising_edge 等) と同じ sim で計測するため measure_type は元 arc 名 → "power" は判定不要
  is_dtp = h.measure_type.startswith(("delay","three"))

  #-- pullres_role (three_state_enable)
  pullres_role="nouse"
  if h.timing_type == "three_state_enable":
    pullres_role = "down" if arc_oirc[0]=="r" else "up" if arc_oirc[0]=="f" else "nouse"

  ## ISS-00155: index1(slew) を related(切替)入力のスロットに割当てる（delay と同じ。
  ##   power_tout は related pin(pin_tr[1]) 基準。旧実装は tslew_clk 固定割当で、comb(slot2=VREL)の
  ##   入力エッジが tslew_rel 既定=1ns 固定となり slew 依存(貫通/crowbar エネルギー)が反映されていなかった。
  _rel_pin  = h.mec.pin_tr[1] if (len(h.mec.pin_tr) > 1 and h.mec.pin_tr[1]) else ""
  _rel_slot = 3   # 既定 clk（pin_tr[1] 空時は従来動作を維持）
  if _rel_pin:
    for _s in (3, 2, 1):
      if _s < len(h.mec.pin_oirc) and h.mec.pin_oirc[_s] == _rel_pin:
        _rel_slot = _s
        break
  _slope_s = _tslew_from_template(index1_slope, h.mls)

  #-- param 早期 instantiate（共通部分、 sim 毎の変動 fields は loop で更新）
  param = Mtp(
     cap          = float("{:.5g}".format(index2_load * h.mls.capacitance_mag))
    ,clk_role     = h.clk_role
    ,clk_init     = h.clk_init
    ,pullres_role = pullres_role
    ,meas_energy  = 0          # 各 sim で更新
    ,time_energy  = [0,0]      # 各 sim で更新
    ,meas_o_max_min=0
    ,tslew_min    = float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,maxstep      = float("{:.5g}".format(maxstep * h.mls.time_mag))  # 各 sim で更新
    ,tsim_end     = 1e-6        # 各 sim で更新
    ,tdelay_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tpulse_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    = 1e-9   # ISS-00076 pre-force のため D→Q 待ち padding 不要
    ,tslew_in     = _slope_s if _rel_slot == 1 else float("{:.5g}".format(10*tslew_min_s    * h.mls.time_mag))
    ,tslew_rel    = _slope_s if _rel_slot == 2 else 1e-9
    ,tdelay_clk   = float("{:.5g}".format(h.mls.sim_d2c_max  * h.mls.time_mag))
    ,tslew_clk    = _slope_s if _rel_slot == 3 else float("{:.5g}".format(10*tslew_min_s * h.mls.time_mag))
    ,tpulse_clk   = 1e-6        # 各 sim で更新
    ,tsweep_clk   = 0.0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)

  with poolg_sema:
    spicefoe1 = _make_sim_path(f"{spicef}_{index2_load}_{index1_slope}_energy1")
    spicefoe2 = _make_sim_path(f"{spicef}_{index2_load}_{index1_slope}_energy2")

    ## 1st trial: extract energy_start/end (meas_energy=1, maxstep ratio=20)
    tsim_end1 = max(1e-6, 2*sim_c2d_max * h.mls.time_mag)
    param.meas_energy   = 1
    param.update_ener_thresholds_for_e1(arc_oirc=arc_oirc, mls=h.mls)  # ISS-00117: energy1 用ワイド閾値で eend 取得
    param.time_energy   = [0, 0]
    param.tsim_end      = tsim_end1
    param.tpulse_rel    = tsim_end1
    param.maxstep = float("{:.5g}".format(maxstep * h.mls.time_mag))
    param.compute_timing()
    rslt1 = genFileLogic_PowerToutTrial1x(targetHarness=h, spicef=spicefoe1, param=param)

    ## 2nd trial: energy measure (meas_energy=2)
    estart = rslt1["estart"]
    eend   = rslt1["eend"]
    param.meas_energy   = 2
    ## ISS-00094/00095: i_*_leak の AVG 区間（_t_in0 直前の 100*tslew_min 幅）に複数ステップが
    ##   入るよう _tmax を tslew_min*20（区間/5、 約 5 点）以下に抑える。 ただし基本ステップ
    ##   maxstep/20（旧 timestep_tstep 相当）を下限とする（ISS-00094/00095 の名残）。
    ##   「Timestep too small」 で収束破綻するため）。
    param.maxstep = float("{:.5g}".format(max(maxstep/20 * h.mls.time_mag, min(maxstep/5 * h.mls.time_mag, param.tslew_min * 20))))
    param.compute_timing()                       # t_in0/t_in1/t_rel0/t_rel1 確定（tsim_end 非依存）
    ## tsim_end は compute_timing 結果（t_rel1）を参照して算出（出力遷移 eend も考慮）
    ## ISS-00117: energy2 の sim_end は energy1 の autostop 時刻（=実証済の安全停止点）を使う。
    ##   固定 margin（eend+Nns）は、 深いと vrel/vss_dyn#branch の timestep collapse（テール深部の
    ##   marginal 理想源枝に最終ステップ着地）、 浅い(=0)と energy_end の WHEN が bracket できず
    ##   "out of interval"。 energy1 は autostop で eend 直後（+数 timestep）の安全点に止まり正常
    ##   終了するので、 同じ点を energy2 でも sim_end にする（corner 適応・電流注入なし・leakage 無汚染）。
    ##   fallback: autostop 時刻 未取得時のみ従来式（eend + 1e-9）。
    ## ISS-00117: テール de-singularization SW（jp2: SW_TAIL on VIN/VREL, eend+1ps で ON）で最終 DC 点の
    ##   collapse を解消する。 そのため sim_end は eend より十分後ろ（+2ns）にし、 SW が ON で居られる
    ##   tail 区間を確保する（sim_end≈eend だと SW の ON 区間が無く効かない）。 INTEG 窓 [estart,eend]
    ##   は SW OFF なので cin/energy/leakage は無影響。
    tsim_end2 = max(eend, param.t_rel1) + 2e-9
    param.ener_estart   = estart   # ISS-00151: energy2 の WHEN 不成立時フォールバック用（energy1 の確定値）
    param.ener_eend     = eend
    param.tsim_end      = tsim_end2
    param.tpulse_rel    = tsim_end2
    param.compute_timing()                       # tsim_end 反映（t_clk6/t_clk7 再計算）
    ## ISS-00094: energy 区間を .meas WHEN 依存（[estart,eend]）でなく既知時刻ベースに。
    ##   min(t_in0,t_rel0) 〜 max(t_in1,t_rel1,eend)（Liberty internal power の「1 スイッチング
    ##   イベントの全消費エネルギー」 を捕捉する区間）。 t_in/t_rel は compute_timing 済の既知時刻。
    ## ISS-00151: TO に尻尾 margin を追加。 eend（VOUT の energy 閾値交差）以降にも出力・内部電流の
    ##   指数尻尾が残り、 切り捨てられていた（icgtp_1 fall で 7.2% を実測、 2026-07-07）。
    ##   SW_TAIL の ON 時刻は jp2 が time_energy[1] を参照するため margin に自動追従（窓は常に SW OFF）。
    _EEND_MARGIN = 0.3e-9
    param.time_energy   = [min(param.t_in0, param.t_rel0), max(param.t_in1, param.t_rel1, eend) + _EEND_MARGIN]
    rslt2 = genFileLogic_PowerToutTrial1x(targetHarness=h, spicef=spicefoe2, param=param)

    print(f'  [INFO] pleak={rslt2["pleak"]}, load={index2_load}, slope={index1_slope}')

    with h._lock:
      h.dict_list2["eintl"][index1_slope][index2_load] = rslt2["eintl"]
      h.dict_list2["cin"  ][index1_slope][index2_load] = rslt2["cin"  ]
      # ISS-00135 reorg(U4/U5/U6): c_*/slew/load を per-position 保存
      h.dict_list2["c_in"   ][index1_slope][index2_load] = rslt2["c_in" ]
      h.dict_list2["c_rel"  ][index1_slope][index2_load] = rslt2["c_rel"]
      h.dict_list2["c_clk"  ][index1_slope][index2_load] = rslt2["c_clk"]
      h.dict_list2["slew_rel"][index1_slope][index2_load] = index1_slope   # power_tout: VREL=input slew
      h.dict_list2["load_out"][index1_slope][index2_load] = index2_load    # power_tout: VOUT=load


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
  #-- ISS-00188: power_tin だけ TSTEP の下限を分ける（未指定なら共通値）。
  #   共通値を下げると power_tout の大負荷点は救えるが、 power_tin の最速 slew が
  #   逆に `Timestep too small ... vclk#branch` で落ちるため（SKY130 実測 2026-08-05）。
  _ts_min = h.mls.tmax_low_power_tin
  if _ts_min is None:
    _ts_min = h.mls.tmax_low
  maxstep  = max(_ts_min, min(slope * 0.198, h.mls.tmax_high))

  #-- 計測対象（target pin pin_tr[0]）のスロット逆引き（優先順 c > r > i、 未検出は slot2=VREL）
  #   slope→tslew 割当と積分窓・cin 選択を「X を駆動するスロット」基準にする。
  #   set_common_value でも同じ走査で param.energy_tgt_slot に設定されるが、
  #   tslew_* は Mtp 生成時に必要なためここでも先行判定する。
  _tgt_pin  = h.mec.pin_tr[0] if h.mec.pin_tr else ""
  _tgt_slot = 2
  if _tgt_pin:
    for _s in (3, 2, 1):
      if _s < len(h.mec.pin_oirc) and h.mec.pin_oirc[_s] == _tgt_pin:
        _tgt_slot = _s
        break
  _slope_s = _tslew_from_template(index1_slope, h.mls)

  #-- param 早期 instantiate（meas_energy=5、 estart/eend は compute_timing 後に確定）
  is_dtp = h.measure_type.startswith(("delay","three","power"))
  param = Mtp(
     cap          = float("{:.5g}".format(0.0 * h.mls.capacitance_mag))
    ,clk_role     = h.clk_role
    ,clk_init     = h.clk_init
    ,pullres_role = "nouse"
    ,meas_energy  = 5
    ,time_energy  = [0,0]    # compute_timing 後に target スロットの遷移窓 [t_X0, t_X1 + 1e-9] で更新
    ,meas_o_max_min=0
    ,tslew_min    = float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ## ISS-00094/00095: i_*_leak の AVG 区間（100*tslew_min）に複数ステップが入るよう
    ##   maxstep を tslew_min*20 以下に抑える（下限は maxstep/20）。
    ,maxstep      = float("{:.5g}".format(max(maxstep/20 * h.mls.time_mag, min(maxstep/5 * h.mls.time_mag, tslew_min_s * h.mls.time_mag * 20))))
    ,tsim_end     = 1e-6      # compute_timing 後に確定
    ,tdelay_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tpulse_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    = 1e-9   # ISS-00076 pre-force のため D→Q 待ち padding 不要
    ## slope（index1 軸）は target スロットの tslew に割当てる（他スロットは従来の固定値）。
    ##   旧実装は tslew_clk 固定割当のため、 slot2(comb)=1ns 固定 / slot1(seq D)=10ps 固定で
    ##   index 軸が物理反映されていなかった。
    ,tslew_in     = _slope_s if _tgt_slot == 1 else float("{:.5g}".format(10*tslew_min_s * h.mls.time_mag))
    ,tslew_rel    = _slope_s if _tgt_slot == 2 else 1e-9
    ,tdelay_clk   = float("{:.5g}".format(h.mls.sim_d2c_max  * h.mls.time_mag))
    ,tslew_clk    = _slope_s if _tgt_slot == 3 else float("{:.5g}".format(10*tslew_min_s * h.mls.time_mag))
    ,tpulse_clk   = 1e-6      # 後で更新
    ,tsweep_clk   = 0.0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  param.compute_timing()

  #-- estart/eend: target スロットの遷移窓 [t_X0, t_X1 + 1ns] に anchoring
  #   slot1(VIN)=[t_in0,t_in1] / slot2(VREL)=[t_rel0,t_rel1]（旧式 estart=t_rel0,
  #   eend=t_rel0+tslew_rel+1ns と同値） / slot3(VCLK)=[t_clk4,t_clk5]（2nd edge）。
  #   旧式は t_rel0 固定 anchoring のため、 slot3(CLK-target) で窓が edge を外し
  #   かつ tsim_end < t_clk4 で edge 自体が sim 範囲外 → eintl 全 0 になっていた。
  if   param.energy_tgt_slot == 1:
    _t_x0, _t_x1 = param.t_in0, param.t_in1
  elif param.energy_tgt_slot == 3:
    _t_x0, _t_x1 = param.t_clk4, param.t_clk5
  else:
    _t_x0, _t_x1 = param.t_rel0, param.t_rel1
  estart   = _t_x0
  eend     = _t_x1 + 1e-9
  tsim_end = eend + 1e-9
  param.time_energy = [estart, eend]
  param.tsim_end    = tsim_end
  param.tpulse_clk  = tsim_end
  param.compute_timing()

  with poolg_sema:
    spicefoe2 = _make_sim_path(f"{spicef}_{index1_slope}_energy2")

    rslt2 = genFileLogic_PowerTinTrial1x(targetHarness=h, spicef=spicefoe2, param=param)

    print(f'  [INFO] pleak={rslt2["pleak"]}, slope={index1_slope}')

    with h._lock:
      h.dict_list2["eintl"][index1_slope][0.0] = rslt2["eintl"]
      h.dict_list2["cin"  ][index1_slope][0.0] = rslt2["cin"  ]
      # ISS-00135 reorg(U4/U5/U6)
      h.dict_list2["c_in"   ][index1_slope][0.0] = rslt2["c_in" ]
      h.dict_list2["c_rel"  ][index1_slope][0.0] = rslt2["c_rel"]
      h.dict_list2["c_clk"  ][index1_slope][0.0] = rslt2["c_clk"]
      h.dict_list2["slew_rel"][index1_slope][0.0] = index1_slope   # power_tin: VREL=input slew (1D)

    
    
  
#--------------------------------------------------------------------------------------------------
def genFileLogic_PowerToutTrial1x(targetHarness:Mcar, spicef:str, param:Mtp):
  """ISS-00080 Step 3：param は呼び出し側 (runSpicePowerToutSingle) で early instantiate +
  meas_energy/time_energy/tsim_end/tpulse_rel/maxstep 更新 + compute_timing() 済。
  """
  h=targetHarness

  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
  param.write_pinmap_if_enabled(os.path.dirname(spicef))   # ISS-00078: sidecar .pinmap.json
  #-- ISS-00226: sim 1 本ごとの高頻度ログ。 supress_sim_msg="true" で抑制できる。
  h.mls.print_msg_sim(f"  [INFO] generate tb={spicef}")
  _check_dbg_sp(spicef, h.mls)   # ISS-00118 debug: stop after N sp

  #-- execute spice
  spicelis=h.mls.exec_spice(spicef=spicef)
                              
  #-- read result
  # read .mt0 for Xyce
  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  #-- parse results
  ## ISS-00151: energy2 の energy_start/end WHEN は大 slew で out of interval になり得る（VOUT の
  ##   閾値到達が tsim_end 後）。 meas2 では必須にせず、 不成立時は energy1 の確定値（param.ener_*）を使う。
  res_list=["energy_start","energy_end"] if param.meas_energy == 1 else []
  res_list_opt=["energy_start","energy_end"] if param.meas_energy == 2 else []
  res=dict()
  if(param.meas_energy == 2):
    res_list += ["q_in_dyn","q_rel_dyn","q_out_dyn","q_vdd_dyn","q_vss_dyn",
                 "i_vdd_leak","i_vss_leak","i_vnw_leak","i_vpw_leak","i_rel_leak"]
    if h.mec.pin_oirc[3] != "":
      res_list += ["q_clk_dyn","i_clk_leak"]
    
  with open(spicelis,'r') as f:
    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub(r'\=',' ',inline)

      # search measure
      for key in res_list + res_list_opt:
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
  ## ISS-00151: WHEN 成立時は実測値、 不成立時（meas2 の大 slew）は energy1 の確定値
  rslt["estart"]=float(res["energy_start"]) if "energy_start" in res else param.ener_estart
  rslt["eend"]  =float(res["energy_end"])   if "energy_end"   in res else param.ener_eend
  energy_time=rslt["eend"] - rslt["estart"]
  
  if(param.meas_energy == 2):

    #q_in_dyn =res["q_clk_dyn"] if h.target_relport=="c0" else res["q_rel_dyn"]
    q_in_dyn  = res["q_in_dyn"]
    q_rel_dyn = res["q_rel_dyn"]
    q_clk_dyn = res["q_clk_dyn"] if h.mec.pin_oirc[3] != "" else 0.0

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
    rslt["c_in"]=c_in; rslt["c_rel"]=c_rel; rslt["c_clk"]=c_clk  # ISS-00135 reorg(U4/U5): c_* 個別保存

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
  #-- ISS-00226: sim 1 本ごとの高頻度ログ。 supress_sim_msg="true" で抑制できる。
  h.mls.print_msg_sim(f"  [INFO] generate tb={spicef}")
  _check_dbg_sp(spicef, h.mls)   # ISS-00118 debug: stop after N sp

  ## execute spice
  spicelis = h.mls.exec_spice(spicef=spicef)

  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0"

  ## parse results (no energy_start/end for meas_energy=5)
  res_list = ["q_in_dyn","q_rel_dyn","q_out_dyn","q_vdd_dyn","q_vss_dyn",
              "i_vdd_leak","i_vss_leak","i_vnw_leak","i_vpw_leak","i_rel_leak"]
  if h.mec.pin_oirc[3] != "":
    res_list += ["q_clk_dyn","i_clk_leak"]
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
  q_clk_dyn = res["q_clk_dyn"] if h.mec.pin_oirc[3] != "" else 0.0

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
  ## cin は計測対象スロットの電荷から決定（旧: target_relport=="c0" 分岐は pin_oirc[2] 依存で、
  ##   slot2 空の新方式 entry では常に c_rel（遊休 VREL≈0）となり CLK/D target の cin が壊れるため）
  cin = {1: c_in, 2: c_rel, 3: c_clk}.get(param.energy_tgt_slot, c_rel)

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
  rslt["c_in"]=c_in; rslt["c_rel"]=c_rel; rslt["c_clk"]=c_clk  # ISS-00135 reorg(U4/U5): c_* 個別保存

  return rslt


#--------------------------------------------------------------------------------------------------
def runSpiceConstMultiThread(num:int, mls:Mls, mlc:Mlc, mec:Mec)  -> list[Mcar]:
  """ISS-00138: setup/hold/recovery を degradation(遅延)判定で統一計測する harness。
  secant は runSpiceConstSingle。 removal は電圧判定で別関数。
  ISS-00219(2026-08-12): 前身の runSpiceSetupMultiThread は dispatch から呼ばれない dead code
    となっていたため削除した（本関数へ統合済み）。
  """
  spicef = _build_spicef_base(mls, mlc, mec, num)

  poolg_sema = threading.BoundedSemaphore(mls.num_thread)
  print("Num threads for simulation:"+str(mls.num_thread))

  thread_id = 0
  threadlist = list()

  h_const = Mcar(mls=mls, mlc=mlc, mec=mec)
  h_const.set_update()

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

  for index2_slope_rel in index2_slopes_rel:
    for index1_slope_const in index1_slopes_const:
      thread = threading.Thread(target=runSpiceConstSingle,
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

  return [h_const]

#--------------------------------------------------------------------------------------------------
def runSpiceConstSingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope_const:float, index2_slope_rel:float):
  """ISS-00138: setup/hold/recovery を degradation(遅延)判定で統一計測する単一 secant。
  FF/LAT 差は jp2 が judge で吸収（本関数に FF/LAT 分岐なし）。
  ISS-00219(2026-08-12): 前身の runSpiceSetupSingle は dead code だったため削除した。
   - is_async (recovery)  : 制約信号を VREL(async) 駆動（setup/hold は VIN=D 駆動）
   - is_hold  (hold)      : 制約信号が CLK の後 → CLK を正方向に掃引（setup/recovery は負方向）
  値 = dly（setup→dly_in_clk / hold→dly_clk_in / recovery→dly_rel_clk）、 判定 = prop_clk_out の degradation。
  ISS-00153: hold × seq_lat（LAT/ICG、 保持成功＝Q 無遷移）のみ degradation 不可のため
  removal と同方式の電圧化け判定（judge_vlt_max/min、 vout_infos 観測ノード置換対応）に分岐。
  removal は電圧判定のため本関数では扱わない。
  """
  h=targetHarness
  arc_oirc = h.mec.arc_oirc

  is_async = h.measure_type in ["recovery_rising","recovery_falling"]  # 制約信号 = VREL(async)
  is_hold  = h.measure_type in ["hold_rising","hold_falling"]          # 制約信号が CLK の後

  #-- sim_c2d_max 実効値
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * 0.1, h.mls.sim_c2d_min)
  sim_c2d_max = min(sim_c2d_max, h.mls.sim_c2d_max)

  #-- timestep （CLK slew 由来）
  slope          = index2_slope_rel
  maxstep  = max(h.mls.tmax_low, min(slope * 0.198, h.mls.tmax_high))

  tdelay_in_rel = float("{:.5g}".format(_tslew_from_template(index2_slope_rel, h.mls) + sim_c2d_max * h.mls.time_mag))
  tslew_in_rel  = _tslew_from_template(index1_slope_const, h.mls)

  param = Mtp(
    cap           = 0.0
    ,clk_role     =h.clk_role
    ,clk_init     =h.clk_init
    ,meas_energy  =0
    ,time_energy  =[0,0]
    ,meas_o_max_min=0
    ,tslew_min    =float("{:.5g}".format(h.mls.simulation_slew_min * h.mls.time_mag))
    ,maxstep      = float("{:.5g}".format(maxstep  * h.mls.time_mag))
    ,tsim_end     =1.0E-6
    ,tdelay_init  =float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tpulse_init  =float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))

    ,tdelay_in    = 1.0E-9 if is_async else tdelay_in_rel
    ,tslew_in     = 1.0E-9 if is_async else tslew_in_rel

    ,tdelay_rel   = tdelay_in_rel  if is_async else 1.0E-9
    ,tslew_rel    = tslew_in_rel   if is_async else 1.0E-9
    ,tpulse_rel   = 1.0E-9

    ,tdelay_clk   =float("{:.5g}".format(h.mls.sim_d2c_max  * h.mls.time_mag))
    ,tslew_clk    =_tslew_from_template(index2_slope_rel, h.mls)
    ,tpulse_clk   =1.0E-6
    ,tsweep_clk   =0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  param.compute_timing()

  segstep_min  = h.mls.sim_segment_timestep_min * h.mls.time_mag

  with poolg_sema:
    #-- ISS-00138: setup/hold/recovery は同一の degradation 計測。 違いは seg_start/seg_end のみ。
    #   tsweep_clk = tsweep（符号付き）、 掃引向き direction は sign(seg_end - seg_start) で自動決定。
    if is_hold:
      #-- 制約信号(D-fall)が CLK の後：_t_clk4 を「D 手前(pass)」→「t_in0(fail 境界)」へ
      ## ISS-00152: 旧 seg_end = t_in0（D 遷移開始とちょうど同時刻）では fail 側（D 戻りが透過に
      ##   食い込む領域）に一歩も入らず、 大 slew で境界未検出（latrsnq (9,9) で secant 終端＝同時刻を実測）。
      ##   D 遷移完了 t_in1 ＋ CLK slew 2 本分まで延長し、 full-swing の乱れが必ず現れる領域まで掃引する。
      seg_start  = param.tsweep_for_clk4_at(param.t_in0) - 0.5*(param.t_in0 - param.t_init3) - param.tslew_clk
      seg_end    = param.tsweep_for_clk4_at(param.t_in1 + 2*param.tslew_clk)
      ## ISS-00153: 保持型（is_lat）の電圧判定は judge 窓が _t_clk4 から始まる。 VIN の capture
      ##   遷移は _t_init3 固定アンカーのため、 clk_init pulse を持つセル（ICG）では seg_start が
      ##   _t_init3 と衝突し、 観測ノードの正当な capture 遷移が窓に入って初手 FAIL（探索不能）に
      ##   なる（icgtp CLK 大 slew corner で実測）。 capture 完了＋settle 以後へ clamp する。
      if param.is_lat:
        seg_start = max(seg_start, param.tsweep_for_clk4_at(param.t_init3 + 2e-9))
    else:
      #-- 制約信号が CLK の前(setup/recovery)：_t_clk4 を「nominal(pass)」→「(t_init3+t_in0)/2(fail)」へ
      seg_start  = 0.0
      seg_end    = param.tsweep_for_clk4_at((param.t_init3 + param.t_in0) / 2)

    direction  = 1.0 if seg_end >= seg_start else -1.0   # 掃引向き（pass→fail）

    ratio      = h.mls.sim_segment_timestep_ratio
    #-- ISS-00218(B): 劣化量の閾値は「絶対値の上限」と「基準遅延 d0 への比例項」の小さい方。
    #   threshold_abs は上限（従来の固定値）、 実効値は掃引ループ内で prop_min から算出する。
    #   ratio=0.0（既定・未指定）なら比例項を無効化し、 従来どおり上限のみで判定する。
    threshold_abs   = h.mls.sim_time_const_threshold * h.mls.time_mag
    threshold_ratio = h.mls.sim_time_const_threshold_ratio
    threshold  = threshold_abs   # 保持型 hold など、 比例項を使わない経路のための既定

    #-- ISS-00153: 保持型 hold（LAT/ICG=seq_lat）は電圧判定（removal と同方式）に使う閾値
    #   is_lat は set_common_value 済の param から取る（logic_type は mls.logic_dict 辞書引きのため）
    is_lat          = param.is_lat
    threshold_high  = h.mls.hold_meas_high_threshold * h.mls.vdd_voltage
    threshold_low   = h.mls.hold_meas_low_threshold  * h.mls.vdd_voltage

    tsweep_pass=seg_start
    const_pass =0

    tsim_end=1.0E-6
    #-- ISS-00219: maxstep 確定フェーズ（掃引位置を固定したまま反復）。
    #   trans_out は maxstep に依存する測定値（刻みが粗いと過大に出る）。 一方 setup/hold の
    #   掃引位置を動かすと trans_out も変わるため、 両者を同時に動かすと変化がどちらに由来
    #   するか分離できない（実測：s100→s101 で trans_out 99→29 ps）。 そこで掃引位置を
    #   固定して maxstep だけを収束させ、 確定後に探索を開始する。
    #   絞る方向にしか動かないので発散しない。 収束＝改善 20% 未満、 上限 4 回。
    _pts_per_trans = getattr(h.mls, "simulation_points_per_transition", 0.0)
    if _pts_per_trans > 0.0 and not (is_hold and is_lat):
      for _it in range(4):
        _sfp = _make_sim_path(f"{spicef}_c{index1_slope_const}_r{index2_slope_rel}_p{_it}")
        param.tsweep_clk = seg_start
        param.tsim_end   = tsim_end
        param.tpulse_clk = tsim_end
        param.compute_timing()
        param.tsim_end   = max(param.t_clk5, param.t_in1, param.t_rel1) + 3e-9
        param.tpulse_clk = param.tsim_end
        param.compute_timing()
        _rp = genFileLogic_Const1x(targetHarness=h, spicef=_sfp, param=param)
        _tr = _rp.get("trans_out", 0.0)
        if _tr <= 0.0:
          #-- trans_out が取れないと maxstep を確定できない。 元の刻みのまま続けても
          #   「分解能不明の値」が出るだけなので、 この measure はここで打ち切る。
          raise RuntimeError(
            f"[ERROR] ISS-00219: trans_out 未取得のため maxstep を確定できません: {_sfp}")
        _lim = _tr / _pts_per_trans
        if _lim >= param.maxstep * 0.8:
          break
        param.maxstep = float("{:.5g}".format(min(_lim, param.maxstep)))
    prop_min=1.0

    segstep = h.mls.sim_segment_timestep_start * h.mls.time_mag

    cnt=0
    while segstep>= segstep_min:
      cnt=cnt+1
      tsweep_list=np.arange(seg_start, seg_end, direction*segstep)

      #-- search const(degradation): prop_clk_out が公称から閾値超え劣化したら境界
      for id,tsweep in enumerate(tsweep_list):
        spicefo  = _make_sim_path(f"{spicef}_c{index1_slope_const}_r{index2_slope_rel}_s{cnt*100+id}")

        param.tsweep_clk = tsweep
        param.tsim_end   = tsim_end
        param.tpulse_clk = tsim_end
        param.compute_timing()
        ## ISS-00152: pass 側（Q 無遷移が成功＝ICG の E/TE fall setup、 LAT hold 等）は prop_clk_out が
        ##   不成立で autostop が効かず、 tsim_end=1µs を極小 timestep で走る擬似ハングになる。
        ##   判定情報（prop/dly/グリッチ）は CLK edge 直後に集中するため、 tsim_end を毎反復
        ##   既知時刻に短縮する（autostop 成立ケースは元々それ以前に停止、 結果不変）。
        ##   hold は D 戻り（t_in1/t_rel1）が closure の後に来るため max で含める（切り落とすと
        ##   dly_clk_in 不成立＝値が出ない。 latrsnq (9,9) で実測）。
        param.tsim_end   = max(param.t_clk5, param.t_in1, param.t_rel1) + 3e-9
        param.tpulse_clk = param.tsim_end
        param.compute_timing()

        rslt=genFileLogic_Const1x(targetHarness=h, spicef=spicefo, param=param)


        const_last=rslt["setup"]   # = dly（_dly_key 経由で setup/hold/recovery を切替済）

        if is_hold and is_lat:
          #- ISS-00153: 保持型 hold（LAT/ICG）は電圧化け判定（removal と同方式）。
          #   閉じた後の観測ノード（vout_infos 適用可）が保持値から動いたら fail。
          #   arc[0] の意味: "0"/"r"=保持 L（違反で上昇）、 "1"/"f"=保持 H（違反で下降）。
          _held_o = arc_oirc[0]
          if   (_held_o in ("0","r")) and (threshold_low  < rslt["vlt_max"]):
            break
          elif (_held_o in ("1","f")) and (threshold_high > rslt["vlt_min"]):
            break
        else:
          #- degradation 判定。 ISS-00218(A): FF/LAT とも judge_dly に一本化した。
          #   旧実装は FF で prop_clk_out（CLK→Q）を流用していたが、 これは .lib の
          #   rising_edge/falling_edge の値そのものなので TRIG 閾値を動かせない。
          #   judge_dly は判定専用（.lib 非出力）なので TRIG を遷移開始側に置ける。
          #   ISS-00221: 透過ラッチでは enable→Q が掃引量そのもの（幾何量）になり、 abs()＋
          #   running-min の組合せで「戻ると必ず break／進むと絶対に break しない」となって
          #   絞り込みが壊れる。 judge_dly は制約信号起点なのでこの問題を持たない。
          #   judge_dly が取得できない点は「掃引が進んで Q が一度も遷移しない＝真の崖」で、
          #   既定値 1（秒）が必ず prop_min+threshold を超えるため下の判定が fail として break する。
          prop_last =abs(rslt["judge_dly"])
          prop_min=min(prop_min, prop_last)
          #-- ISS-00218(B): 実効閾値 = min(絶対値の上限, d0 × 比例係数)。 d0 は judge_dly の
          #   running-min（＝判定式の基準そのもの）。 prop_min が既定 1.0 秒のまま（judge_dly を
          #   一度も取得できていない）ときは比例項が桁違いに大きくなるので上限側が効く。
          threshold = (min(threshold_abs, prop_min * threshold_ratio)
                       if threshold_ratio > 0.0 else threshold_abs)
          if prop_last > prop_min + threshold:
            break;

        tsim_end=rslt["chg_out"] + 10e-9
        tsweep_pass=tsweep
        const_pass =const_last

      if segstep <= segstep_min:
        break;

      segstep_old=segstep
      segstep    =segstep*ratio
      seg_start = tsweep_pass - 2.0*direction*segstep      # pass 側へ戻す
      seg_end   = tsweep_pass + 1.0*direction*segstep_old  # fail 側へ進める

    #-- result
    with h._lock:
      if h.measure_type in ["setup_rising","setup_falling","hold_rising","hold_falling","recovery_rising","recovery_falling"]:
        h.dict_list2["setup_hold_raw" ][index1_slope_const][index2_slope_rel] = const_pass
      else:
        print(f"[Error] not support measure_type={h.measure_type}")
        my_exit()

#--------------------------------------------------------------------------------------------------
def genFileLogic_Const1x(targetHarness:Mcar, spicef:str, param:Mtp) -> dict:
  # rename
  h=targetHarness

  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
  param.write_pinmap_if_enabled(os.path.dirname(spicef))   # ISS-00078: sidecar .pinmap.json
  #-- ISS-00226: sim 1 本ごとの高頻度ログ。 supress_sim_msg="true" で抑制できる。
  h.mls.print_msg_sim(f"  [INFO] generate tb={spicef}")
  _check_dbg_sp(spicef, h.mls)   # ISS-00118 debug: stop after N sp

  #-- execute spice
  spicelis=h.mls.exec_spice(spicef=spicef)

  #-- read result
  # read .mt0 for Xyce
  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  # read results(set default value)
  # ISS-00133/138: 新 MEASURE 名。 setup→dly_in_clk / hold→dly_clk_in / recovery→dly_rel_clk（計測対象遅延）、
  #            prop_clk_out（CLK→Q、 FF/LAT 共通の degradation 判定用）。 removal は電圧判定（別関数）。
  if   h.measure_type.startswith("setup"):    _dly_key = "dly_in_clk"
  elif h.measure_type.startswith("hold"):     _dly_key = "dly_clk_in"
  elif h.measure_type.startswith("recovery"): _dly_key = "dly_rel_clk"
  else:                                        _dly_key = "dly_rel_clk"
  # ISS-00219: trans_out（出力遷移時間）は maxstep の上限決定に使う。 measure が無い場合に
  #   備えて既定 0（0 なら上限クランプは働かず従来動作）。
  # ISS-00221: LAT は prop_clk_out（enable→Q）が掃引に 1:1 追従する幾何量になり判定に使えない。
  #   透過ラッチの setup は judge_dly（VIN→VOUT ＝ D→Q）の劣化で判定する。 jp2 が is_lat 分岐で
  #   TRIG を VIN に切り替えているので、 ここで読み出して判定側でも使う。
  res_list=["chg_out", _dly_key, "prop_clk_out", "trans_out", "judge_dly"]
  res={"chg_out":1, _dly_key:1, "prop_clk_out":1, "trans_out":0, "judge_dly":1}

  # ISS-00153: LAT/ICG(seq_lat) の hold は電圧判定（removal と同方式）→ judge_vlt_max/min も読む
  if h.measure_type.startswith("hold") and param.is_lat:
    res_list += ["judge_vlt_max", "judge_vlt_min"]
    res.update({"judge_vlt_max":1, "judge_vlt_min":1})

  with open(spicelis,'r') as f:
    
    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub(r'\=',' ',inline)
      
      # search measure
      #for key in ["chg_out","setup_in_rel","hold_rel_in","prop_rel_out"]:
      for key in res_list:
        if((re.search(key, inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res[key]= "{:e}".format(float(sparray[2].strip()))
          
  # check spice finish successfully

  
  # result
  rslt={
    "chg_out"     :float(res["chg_out"]),
    "setup"       :float(res[_dly_key]),
    "prop_clk_out":float(res["prop_clk_out"]),
    "vlt_max"     :float(res.get("judge_vlt_max", 1)),   # ISS-00153: seq_lat hold のみ実値
    "vlt_min"     :float(res.get("judge_vlt_min", 1)),
    "trans_out"   :float(res.get("trans_out", 0)),   # ISS-00219: maxstep 上限決定用
    "judge_dly"   :float(res.get("judge_dly", 1))}   # ISS-00221: LAT の劣化判定用（VIN→VOUT）

  return (rslt)



#--------------------------------------------------------------------------------------------------
def runSpiceRemovalMultiThread(num:int, mls:Mls, mlc:Mlc, mec:Mec)  -> list[Mcar]:

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
      thread = threading.Thread(target=runSpiceRemovalSingle,
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
  #h_const.set_lut(value_name="setup_hold")  # ISS-00121: runExpectation 末尾で一括実行
  
  ###################################################################
  return [h_const]

#--------------------------------------------------------------------------------------------------
def runSpiceRemovalSingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope_const:float, index2_slope_rel:float):
                      
  """ISS-00080 Step 2：Mtp 早期 instantiate + compute_timing() で物理単位の secant 制御。
  hold は tdelay_in = 2*sim_c2d_max（setup の 2 倍）、 tsweep_clk は負方向。
  """
  h=targetHarness
  arc_oirc = h.mec.arc_oirc

  #-- ISS-00138: 本関数は removal 専用（hold は runSpiceConst へ移行）。 is_removal 分岐は撤去。
  #-- sim_c2d_max 実効値
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * 0.1, h.mls.sim_c2d_min)
  sim_c2d_max = min(sim_c2d_max, h.mls.sim_c2d_max)

  #-- timestep
  slope          = index2_slope_rel
  tslew_min_s    = h.mls.simulation_slew_min   # ns 単位（後で time_mag 倍）
  maxstep  = max(h.mls.tmax_low, min(slope * 0.198, h.mls.tmax_high))

  tdelay_in_rel = float("{:.5g}".format(_tslew_from_template(index2_slope_rel, h.mls) + sim_c2d_max * h.mls.time_mag))
  tslew_in_rel  = _tslew_from_template(index1_slope_const, h.mls)
  
  #-- param 早期 instantiate（hold: meas_o_max_min=1、 tsim_end は compute_timing 後に確定）
  param = Mtp(
    cap           = 0.0
    ,clk_role     =h.clk_role
    ,clk_init     =h.clk_init
    ,meas_energy  =0
    ,time_energy  =[0,0]
    ,meas_o_max_min=1
    ,tslew_min    =float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,maxstep      = float("{:.5g}".format(maxstep  * h.mls.time_mag))
    ,tsim_end     =1e-6   # 暫定値。 compute_timing 後に param.t_rel1 + 1ns で再設定
    ,tdelay_init  =float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tpulse_init  =float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    
    ,tdelay_in    = 1.0E-9          # removal: VIN(D) は副次（保持のみ）
    ,tslew_in     = 1.0E-9

    ,tdelay_rel   = tdelay_in_rel   # removal: 制約信号 = VREL(async) を駆動
    ,tslew_rel    = tslew_in_rel
    ,tpulse_rel   = 1.0E-9
    
    ,tdelay_clk   =float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tslew_clk    =_tslew_from_template(index2_slope_rel, h.mls)
    ,tpulse_clk   =1e-6   # 暫定値、 tsim_end と同期して再設定
    ,tsweep_clk   =0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  param.compute_timing()
  
  tsim_end = param.t_clk5+10E-9
  param.tsim_end   = tsim_end
  param.tpulse_clk = tsim_end
  param.compute_timing()

  segstep_min  = h.mls.sim_segment_timestep_min * h.mls.time_mag

  with poolg_sema:
    #-- removal: 制約信号 = VREL(async 解放 t_rel0) 基準で CLK を掃引
    seg_start  = param.tsweep_for_clk4_at(param.t_rel0) - 0.5*(param.t_rel0 - param.t_init3) - param.tslew_clk
    seg_end    = 0

    ratio      = h.mls.sim_segment_timestep_ratio
    threshold_high  = h.mls.hold_meas_high_threshold * h.mls.vdd_voltage
    threshold_low   = h.mls.hold_meas_low_threshold  * h.mls.vdd_voltage
    arc_o           = h.mec.arc_oirc[0]   # ISS-133: 捕捉後 Q 期待は arc[0]（r=H/f=L）

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
        param.tsweep_clk = tsweep * 1.0
        param.compute_timing()

        rslt=genFileLogic_Removal1x(targetHarness=h, spicef=spicefo, param=param)

        #-- get result
        hold_last =rslt["hold"]

        #- removal 違反検出（ISS-00138）：Q は reset/set 値を保持するのが正常。
        #   arc_o="r"（Q=L 保持期待）→ vlt_min>threshold_low で fail / arc_o="f"（Q=H 保持期待）→ vlt_max<threshold_high で fail。
        if   (arc_o=="r" ) and (threshold_low  < rslt["vlt_max"]):
            break
        elif (arc_o=="f" ) and (threshold_high > rslt["vlt_min"]):
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
        h.dict_list2["setup_hold_raw" ][index1_slope_const][index2_slope_rel] = hold_pass
      else:
        print(f"[Error] not support measure_type={h.measure_type}")
        my_exit()
      
    #--
    print(f"  [INFO] hold={hold_pass}")
        
#--------------------------------------------------------------------------------------------------
def genFileLogic_Removal1x(targetHarness:Mcar, spicef:str, param:Mtp) -> dict:
  """ISS-00080 Step 2：param は呼び出し側 (runSpiceRemovalSingle) で early instantiate +
  compute_timing() 済を期待。 本関数は testbench 生成 + spice 実行 + 結果 read のみ。
  param.tsweep_clk / param.tsim_end / param.tpulse_rel は secant ループで毎回更新される。
  """
  h=targetHarness

  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
  param.write_pinmap_if_enabled(os.path.dirname(spicef))   # ISS-00078: sidecar .pinmap.json
  #-- ISS-00226: sim 1 本ごとの高頻度ログ。 supress_sim_msg="true" で抑制できる。
  h.mls.print_msg_sim(f"  [INFO] generate tb={spicef}")
  _check_dbg_sp(spicef, h.mls)   # ISS-00118 debug: stop after N sp

  #-- execute spice
  spicelis=h.mls.exec_spice(spicef=spicef)

  #-- read result
  # read .mt0 for Xyce
  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  # read results(set default value)
  # ISS-00133: hold→dly_clk_in / removal→dly_clk_rel、 judge_vlt_max/min（CLK後窓で Q 保持判定）。 旧 hold_rel_in/o_max_v/o_min_v 置換
  _dly_key = "dly_clk_in" if h.measure_type.startswith("hold") else "dly_clk_rel"
  res_list=["judge_vlt_max","judge_vlt_min", _dly_key]
  res={"judge_vlt_max":1, "judge_vlt_min":1, _dly_key:1}
  
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
    "vlt_min":float(res["judge_vlt_min"]),
    "vlt_max":float(res["judge_vlt_max"]),
    "hold"   :float(res[_dly_key])}

  return (rslt)

#--------------------------------------------------------------------------------------------------
def runSpiceLatHoldMultiThread(num:int, mls:Mls, mlc:Mlc, mec:Mec)  -> list[Mcar]:
  """ISS-00090 Phase 1：LAT 用 hold/removal harness。 runSpiceRemovalMultiThread のコピーベース。
  違いは runSpiceLatHoldSingle を呼ぶ点のみ（LAT 固有の clk_init は Single 側で処理）。
  """

  ## spice file name (ISS-00079: sim ごとに dir 分離、 第 1,2 層は _build_spicef_base で作成)
  spicef = _build_spicef_base(mls, mlc, mec, num)

  # Limit number of threads
  poolg_sema = threading.BoundedSemaphore(mls.num_thread)
  print("Num threads for simulation:"+str(mls.num_thread))

  ###################################################################
  #-- for hold (LAT)
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
      thread = threading.Thread(target=runSpiceLatHoldSingle,
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
  #h_const.set_lut(value_name="setup_hold")  # ISS-00121: runExpectation 末尾で一括実行

  ###################################################################
  return [h_const]

#--------------------------------------------------------------------------------------------------
def runSpiceLatHoldSingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope_const:float, index2_slope_rel:float):
  """ISS-00090 Phase 1：LAT 用 hold/removal secant。 runSpiceRemovalSingle のコピーベース。
  clk_init は myConditionsAndResults の t_init* 基準判定（h.clk_init、 SPEC_seq_lat §5）に従う。
  hold/removal は t_init* で E=H（または RN/SETN active）のため "stable" に決まり、 VCLK は
  init phase の pulse を抑制し closure edge は保持（jp2 の stable 分岐は t_clk0,1,2 を初期値
  固定、 t_clk3..7 の closure edge は出力）。
  metastable 判定（o_max_v/o_min_v）と genFileLogic_Removal1x は DFF 版と共用。
  """
  h=targetHarness
  arc_oirc = h.mec.arc_oirc

  #-- sim_c2d_max 実効値
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * 0.1, h.mls.sim_c2d_min)
  sim_c2d_max = min(sim_c2d_max, h.mls.sim_c2d_max)

  #-- timestep
  slope          = index2_slope_rel
  tslew_min_s    = h.mls.simulation_slew_min
  maxstep  = max(h.mls.tmax_low, min(slope * 0.198, h.mls.tmax_high))

  #-- param 早期 instantiate（hold: meas_o_max_min=1）
  param = Mtp(
    cap           = 0.0
    ,clk_role     =h.clk_role
    ,clk_init     =h.clk_init   # SPEC_seq_lat §5: clk_init は myConditionsAndResults で t_init* 基準判定
    ,meas_energy  =0
    ,time_energy  =[0,0]
    ,meas_o_max_min=1
    ,tslew_min    =float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,maxstep      = float("{:.5g}".format(maxstep  * h.mls.time_mag))
    ,tsim_end     =1e-6
    ,tdelay_init  =float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tpulse_init  =float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    =float("{:.5g}".format(_tslew_from_template(index2_slope_rel, h.mls) + sim_c2d_max * h.mls.time_mag))
    ,tslew_in     =_tslew_from_template(index1_slope_const, h.mls)
    ,tdelay_rel   =float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tslew_rel    =_tslew_from_template(index2_slope_rel, h.mls)
    ,tpulse_rel   =1e-6
    ,tsweep_clk   =0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  param.compute_timing()
  tsim_end = param.t_rel1 + 1e-9
  param.tsim_end   = tsim_end
  param.tpulse_rel = tsim_end
  param.compute_timing()

  segstep_min  = h.mls.sim_segment_timestep_min * h.mls.time_mag

  with poolg_sema:
    seg_start  = param.tsweep_for_clk4_at((param.t_init3 + param.t_in0) / 2)
    seg_end    = 0

    ratio      = h.mls.sim_segment_timestep_ratio
    threshold_high  = h.mls.hold_meas_high_threshold * h.mls.vdd_voltage
    threshold_low   = h.mls.hold_meas_low_threshold  * h.mls.vdd_voltage
    arc_o           = h.mec.arc_oirc[0]   # ISS-133: 捕捉後 Q 期待は arc[0]（r=H/f=L）

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
        param.tsweep_clk = tsweep * 1.0
        param.compute_timing()

        rslt=genFileLogic_Removal1x(targetHarness=h, spicef=spicefo, param=param)

        #-- get result
        hold_last =rslt["hold"]

        #- removal 違反検出（ISS-00138、 LAT も FF と同判定）：Q は reset/set 値を保持するのが正常。
        #   arc_o="r"（Q=L 保持期待）→ vlt_min>threshold_low で fail / arc_o="f"（Q=H 保持期待）→ vlt_max<threshold_high で fail。
        if   (arc_o=="r" ) and (threshold_low  < rslt["vlt_max"]):
            break
        elif (arc_o=="f" ) and (threshold_high > rslt["vlt_min"]):
            break

        #- keep successfull result
        tsweep_pass=tsweep
        hold_pass  =hold_last

      #--
      if segstep <= segstep_min:
        break

      #-- update step/list range
      segstep_old=segstep
      segstep    =segstep*ratio

      seg_start = tsweep_pass - 2*segstep
      seg_end   = tsweep_pass + 1.0*segstep_old

    #-- result in targetHarness
    with h._lock:
      if  h.measure_type in ["hold_rising","hold_falling","removal_rising","removal_falling"]:
        h.dict_list2["setup_hold_raw" ][index1_slope_const][index2_slope_rel] = hold_pass
      else:
        print(f"[Error] not support measure_type={h.measure_type}")
        my_exit()

    #--
    print(f"  [INFO] hold={hold_pass}")

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
  # ISS-00135 reorg(U6): max_trans は set_max_trans で post-hoc 集約（撤去）
  #mlc.update_max_trans4in(port_name=h_passive.target_inport, new_value=max(index1_slopes_in))

  #--- generate lut table
  #h_passive.set_lut(value_name="eintl")  # ISS-00121: runExpectation 末尾で一括実行
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
  maxstep  = max(h.mls.tmax_low, min(slope * 0.198, h.mls.tmax_high))
  ## ISS-00094/00095: i_*_leak の AVG 区間（100*tslew_min）に複数ステップが入るよう
  ##   maxstep を tslew_min*20 以下に抑える（下限は maxstep/20）。
  maxstep  = max(maxstep/20, min(maxstep, tslew_min_s * 20))

  #-- param 早期 instantiate（passive: meas_energy=4、 tsim_end/time_energy は compute_timing 後に確定）
  param = Mtp(
     cap          =0.0
    ,clk_role     =h.clk_role
    ,clk_init     =h.clk_init
    ,meas_energy  =4
    ,time_energy  =[0, 0]     # compute_timing 後に [t_rel0, t_rel1 + 2ns] で確定
    ,meas_o_max_min=0
    ,tslew_min    =float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,maxstep      = float("{:.5g}".format(maxstep  * h.mls.time_mag))
    ,tsim_end     =1e-6       # 暫定値、 compute_timing 後に eend+1ns で再設定
    ,tdelay_init  =float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tpulse_init  =float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    =float("{:.5g}".format(_tslew_from_template(index1_slope_in, h.mls) + sim_c2d_max * h.mls.time_mag))   # ISS-00087: setup/hold と同流儀 (tdelay_in = tslew_rel + sim_c2d_max)。 passive は rel = input pin で tslew_rel = tslew_in
    ,tslew_in     =_tslew_from_template(index1_slope_in, h.mls)
    ,tdelay_rel   =float("{:.5g}".format(h.mls.sim_d2c_max  * h.mls.time_mag))
    ,tslew_rel    =_tslew_from_template(index1_slope_in, h.mls)
    ,tpulse_rel   =1e-6       # 暫定値、 tsim_end と同期して再設定
    ,tsweep_clk   =0.0
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
      # ISS-00135 reorg(U4/U5/U6)
      h.dict_list2["c_in"   ][index1_slope_in][0]=rslt["c_in" ]
      h.dict_list2["c_rel"  ][index1_slope_in][0]=rslt["c_rel"]
      h.dict_list2["c_clk"  ][index1_slope_in][0]=rslt["c_clk"]
      h.dict_list2["slew_rel"][index1_slope_in][0]=index1_slope_in   # passive: VREL=input slew


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
  #-- ISS-00226: sim 1 本ごとの高頻度ログ。 supress_sim_msg="true" で抑制できる。
  h.mls.print_msg_sim(f"  [INFO] generate tb={spicef}")
  _check_dbg_sp(spicef, h.mls)   # ISS-00118 debug: stop after N sp

  #-- execute spice
  spicelis=h.mls.exec_spice(spicef=spicef)
                              
  #-- read result
  # read .mt0 for Xyce
  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  #-- parse results
  res=dict()
  res_list=["q_rel_dyn","q_in_dyn","q_out_dyn","q_vdd_dyn","q_vss_dyn",
            "i_vdd_leak","i_vss_leak","i_vnw_leak","i_vpw_leak"]
  if h.mec.pin_oirc[3] != "":
    res_list += ["q_clk_dyn"]
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
  q_clk_dyn = res["q_clk_dyn"] if h.mec.pin_oirc[3] != "" else 0.0

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
    "c_in" : c_in, "c_rel": c_rel, "c_clk": c_clk,  # ISS-00135 reorg(U4/U5): c_* 個別保存
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
  # ISS-00135 U7: min_pulse のパルス対象ピンは pin_tr[t](=pin_tr[0])。 旧 target_relport は reorg で廃止(空)。
  # ISS-00160: scalar 廃止。value=(lut 行リスト, template grid) を格納し、出力は timing() constraint テーブルで行う。
  mlc.set_min_pulse_width(port_name=h_min_pulse.mec.pin_tr[0], value=(h_min_pulse.lut["min_pulse"], h_min_pulse.template.grid), measure_type=h_min_pulse.measure_type, when=h_min_pulse.timing_when)
    
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
  maxstep  = 5 * h.mls.tmax_high        # 旧 max(100*_max, max(_min,_max)) と等価（5*high が常に支配）

  #-- ISS-00160: パルス slew は mpw template の index_1 を汎用ループ（要素数は PDK 依存、gf180=3）。
  #   simulation_slew_for_pulse（スカラー固定）は廃止。cell の template_kgn に ["mpw","3x0","d000"] が必要。
  _mpw_temp = h.mlc.template.get("mpw") if (h.mlc is not None and hasattr(h.mlc, "template")) else None
  if _mpw_temp is None or len(_mpw_temp.index_1) < 1:
    print(f"[Error] min_pulse: mpw template not found. cell の template_kgn に ['mpw','3x0','d000'] を追加してください。")
    my_exit()
  h.template      = _mpw_temp
  h.template_kind = "mpw"
  _slews = list(_mpw_temp.index_1)

  #-- param 早期 instantiate（tslew は slew(index_1) ごとに更新、tpulse_rel/tpulse_clk/tsim_end は secant で更新）
  #   ISS-00133: パルス対象ピン pin_tr[0] で能動側(delay)を切替（c*→clk 能動 / async→rel 能動）。
  _is_clk = (h.mec.pin_tr[0] if h.mec.pin_tr else "").startswith("c")
  _d2c    = float("{:.5g}".format(h.mls.sim_d2c_max * h.mls.time_mag))
  _tslew0 = _tslew_from_template(_slews[0], h.mls)
  param = Mtp(
    cap           = 0.0
    ,clk_role     =h.clk_role
    ,clk_init     =h.clk_init
    ,meas_energy  =0
    ,time_energy  =[0,0]
    ,meas_o_max_min=0
    ,tslew_min    = float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,maxstep      = float("{:.5g}".format(maxstep  * h.mls.time_mag))
    ,tsim_end     =1.0E-6
    ,tdelay_init  =float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))   # min_pulse には delay 系 measure_type は来ないため固定
    ,tpulse_init  =float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    =float("{:.5g}".format(sim_c2d_max         * h.mls.time_mag))
    ,tslew_in     =_tslew0
    ,tdelay_rel   = 1.0E-9 if _is_clk else _d2c
    ,tslew_rel    =_tslew0
    ,tpulse_rel   =0.0
    ,tdelay_clk   = _d2c if _is_clk else 1.0E-9
    ,tslew_clk    =_tslew0
    ,tpulse_clk   =0.0
    ,tsweep_clk   =0.0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)

  with poolg_sema:
    #-- ISS-00160: index_1(slew) ごとに探索し dict_list2["min_pulse"][slew][0] に格納（1D）
    for si, _slew_idx in enumerate(_slews):
      tslew = _tslew_from_template(_slew_idx, h.mls)
      param.tslew_in  = tslew
      param.tslew_rel = tslew
      param.tslew_clk = tslew
      param.compute_timing()

      seg_start  = h.mls.sim_pulse_max * h.mls.time_mag
      seg_end    = 0.0
      tstep_min  = h.mls.sim_segment_timestep_min * h.mls.time_mag
      ratio      = h.mls.sim_segment_timestep_ratio
      #-- ISS-00218(B): min_pulse 専用の閾値。 従来は sim_time_const_threshold を const と
      #   共用していたが、 const 側に比例項を入れたため分離した（既定値は従来と同じ 0.1）。
      threshold  = h.mls.sim_time_pulse_threshold * h.mls.time_mag

      tsweep_pass=seg_start
      pulse_pass =seg_start
      prop_min   =1.0
      trans_min  =1.0
      tsim_end_dyn=1.0E-6

      #-- ISS-00219: maxstep 確定フェーズ（掃引位置を seg_start に固定したまま反復）。
      #   const と同型。 掃引位置と maxstep を同時に動かすと trans_out の変化がどちらに
      #   由来するか分離できないため、 位置を固定して maxstep だけを収束させてから探索する。
      _pts_per_trans = getattr(h.mls, "simulation_points_per_transition", 0.0)
      if _pts_per_trans > 0.0:
        _pt0 = h.mec.pin_tr[0] if h.mec.pin_tr else ""
        for _it in range(4):
          _sfp = _make_sim_path(f"{spicef}_sl{si}_p{_it}")
          param.tpulse_clk = seg_start if _pt0.startswith("c") else 1.0e-6
          param.tpulse_rel = 1.0e-9    if _pt0.startswith("c") else seg_start
          param.tsim_end   = tsim_end_dyn
          param.compute_timing()
          _rp = genFileLogic_MinPulse1x(targetHarness=h, spicef=_sfp, param=param)
          _tr = _rp.get("trans", 0.0)
          if not (0.0 < _tr < 1.0e-6): break     # 未取得 or sentinel
          _lim = _tr / _pts_per_trans
          if _lim >= param.maxstep * 0.8: break  # 改善 20% 未満で収束
          param.maxstep = float("{:.5g}".format(min(_lim, param.maxstep)))

      tstep = h.mls.sim_segment_timestep_start * h.mls.time_mag
      cnt=0
      while tstep> tstep_min:
        cnt=cnt+1

        tsweep_list=np.arange(seg_start, seg_end, -1.0*tstep)
        tsweep_list=np.append(tsweep_list, 0.0)

        for id,tsweep in enumerate(tsweep_list):

          spicefo  = _make_sim_path(f"{spicef}_sl{si}_s{cnt*100+id}")

          #-- ISS-00080 / ISS-00133: param 更新。 min_pulse の sweep は pin_tr[0] で振り分け
          _pt = h.mec.pin_tr[0] if h.mec.pin_tr else ""
          param.tpulse_clk = tsweep if _pt.startswith("c") else 1.0e-6
          param.tpulse_rel = 1.0e-9 if _pt.startswith("c") else tsweep
          param.tsim_end   = tsim_end_dyn
          param.compute_timing()

          rslt=genFileLogic_MinPulse1x(targetHarness=h, spicef=spicefo, param=param)

          prop_last =abs(rslt["prop"])
          prop_min  =min(prop_min, prop_last)
          trans_last=abs(rslt["trans"])
          trans_min =min(trans_min, trans_last)

          # ISS-00133: prop(CLK→Q delay) と trans(出力 slew) のどちらか劣化で境界とする
          if (prop_last > prop_min + threshold) or (trans_last > trans_min + threshold):
            break;

          tsweep_pass=tsweep
          #-- ISS-00101: tsim_end_dyn は 1 sim 目（s100）でのみ確定、 以降は固定（measure 失敗時 chg_out=1 汚染で 1s hang 対策）。
          if cnt == 1 and id == 0:
            tsim_end_dyn=rslt["chg_out"] + 10e-9
          pulse_pass =rslt["pulse"]

        tstep    =tstep*ratio
        seg_start = tsweep_pass + 2*tstep

      with h._lock:
        h.dict_list2["min_pulse"][_slew_idx][0] = pulse_pass

  #-- ISS-00160: 汎用 set_lut で 1D テーブル(index_1+values)化 → h.lut["min_pulse"]
  h.set_lut("min_pulse")


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
  #-- ISS-00226: sim 1 本ごとの高頻度ログ。 supress_sim_msg="true" で抑制できる。
  h.mls.print_msg_sim(f"  [INFO] generate tb={spicef}")
  _check_dbg_sp(spicef, h.mls)   # ISS-00118 debug: stop after N sp

  #-- execute spice
  spicelis=h.mls.exec_spice(spicef=spicef)

  #-- read result
  # read .mt0 for Xyce
  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  # ISS-00133: min_pulse の対象 delay は pin_tr[0] で切替（setup/Const1x と同じ考え方）。
  #   CLK パルス(c*)→prop_clk_out(CLK→OUT)、 async/data(r*/s*/i*)→prop_rel_out(REL→OUT)。
  #   jp2 が出す MEASURE 名（CLK パルスでは prop_clk_out）と一致させる。
  _is_clk   = (h.mec.pin_tr[0] if h.mec.pin_tr else "").startswith("c")
  _prop_key = "prop_clk_out" if _is_clk else "prop_rel_out"
  _pw_key   = "pulse_width_clk" if _is_clk else "pulse_width_rel"

  # read results(set default value)
  res={"chg_out":1, _prop_key:1, "trans_out":1, _pw_key:1}

  with open(spicelis,'r') as f:

    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub(r'\=',' ',inline)

      # search measure
      for key in ["chg_out", _prop_key, "trans_out", _pw_key]:
        if((re.search(key, inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res[key]= "{:e}".format(float(sparray[2].strip()))
          
  # check spice finish successfully

  
  # min_pulse result（pulse 幅 = slew + 計測対象パルス幅。 CLK パルスは tpulse_clk を採用）
  rslt={
    "chg_out" :float(res["chg_out"]),
    "prop"    :float(res[_prop_key]),
    "trans"   :float(res["trans_out"]),
    "pulse"   :float(res[_pw_key])}   # ISS-00133: 実測 pulse_width(0.5VDD) を保存

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
  maxstep  = h.mls.tmax_low             # 旧 20 * _min と等価

  #-- is_dtp: FF でない (= not isflop) → 短い init で OK
  is_dtp = (not h.mlc.isflop)

  param = Mtp(
     cap          = 0.0
    ,clk_role     = h.clk_role
    ,clk_init     = h.clk_init
    ,pullres_role = "nouse"
    ,meas_energy  = 3
    ,time_energy  = [0, 0]    # compute_timing 後に [t_in0, t_in1] で確定
    ,meas_o_max_min=0
    ,tslew_min    = float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,maxstep      = float("{:.5g}".format(maxstep  * h.mls.time_mag))
    ,tsim_end     = 1e-6      # 暫定値、 compute_timing 後に t_rel3 で再設定
    ,tdelay_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_d2c_max   * h.mls.time_mag))
    ,tpulse_init  = 1e-9 if is_dtp else float("{:.5g}".format(h.mls.sim_pulse_max * h.mls.time_mag))
    ,tdelay_in    = 1e-9 if is_dtp else 10e-9  # ISS-00087: 非 FF は 1ns、 FF は settling 確保 10ns（orig との 10〜30 倍乖離は別途調査）
    ,tslew_in     = float("{:.5g}".format(h.mls.leakage_stable_time * h.mls.time_mag))  # ISS-00166/00167: 状態確立 tran を leakage_stable_time(ns)まで延長し内部ノードを静定させる（旧 ISS-00087: 1ns 固定）
    ,tdelay_rel   = 1e-9      # leakage: rel transition なし、 短い 1 ns
    ,tslew_rel    = float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,tpulse_rel   = float("{:.5g}".format(tslew_min_s * h.mls.time_mag))
    ,tsweep_clk   = 0.0
  )
  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  param.compute_timing()
  #-- ISS-00087: 計測 window = [t_in0, t_in1] / tsim_end = t_rel3。 compute_timing で算出された
  #   絶対時刻に合わせて Mtp を再設定し、 compute_timing() を **2 回目**呼び直して t_clk6/7 を再計算
  param.time_energy = [param.t_in0, param.t_in1]
  param.tsim_end    = param.t_rel3
  param.compute_timing()

  #-- ISS-00166: leakage は DC op で計測（tran は状態確立のみ）。 op が双安定の保持ノードを
  #   メタステーブル（貫通）に落とすのを防ぐため、 tran 終端の全内部ノード電圧を meas find で
  #   取得→alterparam で nodeset に書き戻し→reset→op する（B 案）。 内部ノード名は netlist から
  #   自動列挙、 論理値は tran が測るので、 セル依存の nodeset 表は不要。
  #   meas find の時刻は tsim_end 丁度だと最終点の浮動小数ずれで out-of-interval になるため僅か手前。
  #-- ISS-00166/00167: leakage op は全状態で B案（tran で状態確立→内部ノード電圧を nodeset に
  #   書き戻し→op）。 set/reset active の競合状態（例 latch の nMOS パス劣化 H≈VDD-Vth）も、
  #   tslew_in=leakage_stable_time まで tran を延ばして内部ノードを静定させれば nodeset が安定し、
  #   op が正しい安定解に収束する（過渡途中を拾うと metastable=貫通）。 内部ノード名は netlist 自動列挙。
  param.internal_nodes = h.mlc.get_internal_nodes()
  param.leak_meas_at   = param.tsim_end - param.maxstep

  with poolg_sema:
    spicefoe1 = _make_sim_path(f"{spicef}_leakage")

    rslt = genFileLogic_LeakageTrial1x(targetHarness=h, spicef=spicefoe1, param=param)

    print(f'  [INFO] pleak2={rslt["pleak"]}')

    with h._lock:
      #-- ISS-00165: 計測値に leakage_offset（嵩上げ値）を**加算**する（**全セル対象**）。
      #   offset は表示単位（leakage_power_unit）なので leakage_power_mag で raw へ換算して足す。
      #
      #   【なぜ clamp でなく加算か（2026-07-24 実測で確定）】
      #     orig - charao(計測値) は inv_1〜inv_20（駆動 1x〜20x）の全域で 4.90〜5.00e-05 の
      #     ほぼ一定値（比は 2.96→1.10 と大きく変動）＝orig は全セルに一律定数を加算している。
      #     この成分は sim では再現不可：(1) i_vnw は 1e-20 レベルの数値ノイズで well 接合が
      #     実質モデル化されていない、(2) fill セルは空 subckt（Tr ゼロ）で全端子電流 0 なのに
      #     orig は 5e-05 を持つ、(3) fill_1(area 2.2) と fill_64(area 140) で orig 値がほぼ不変
      #     ＝面積依存でなく規約定数。よって測定端子を増やしても取得できず、加算するしかない。
      #
      #   ここで加算することで、 leakage_power() の個別 value（myExportLib）と
      #   cell_leakage_power（set_max_pleak の max）が同一基準になり、 両者の逆転が起きない。
      #   なお measure なしのセル（物理セル＝expect[]）は本関数を通らないため、
      #   その分は myLogicCell.set_max_pleak の初期値側が担当する。
      h.pleak = rslt["pleak"] + h.mls.leakage_offset * h.mls.leakage_power_mag


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
  #-- ISS-00226: sim 1 本ごとの高頻度ログ。 supress_sim_msg="true" で抑制できる。
  h.mls.print_msg_sim(f"  [INFO] generate tb={spicef}")
  _check_dbg_sp(spicef, h.mls)   # ISS-00118 debug: stop after N sp

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
  #-- ISS-00167: pleak は min(p_supply, p_absorb) を採用。 入力ピン経由の駆動電流（例 latch の
  #   pass gate 経由で D が内部ノードを VDD/VSS へ引く貫通）は VDD 側か VSS 側の片方にしか出ない
  #   ため、 その状態では p_supply≠p_absorb と不均衡になる。 真の電源間リークは両側に均等に出る
  #   （clean 状態は p_supply==p_absorb）ので min を取れば片側の入力駆動貫通を除去でき、リークは保存。
  #   latrsnq 実測：VDD 側貫通(num86 系)も VSS 側貫通(num95/99)も min で正常値へ。 旧 max は逆に貫通側を拾う。
  #-- ISS-00170: min の前に p_supply/p_absorb を 0.0 でクランプする（ダーマツ判断 2026-07-27）。
  #   負値＝その電源枝が「供給／吸収」ではなく **入力ピン駆動電流の帰り道** になっている状態で、
  #   リーク成分ではない（電源間経路を持たない antenna＝ダイオード 2 個のみのセルで顕在化。
  #   min が負側を採り leakage_power が負＝Liberty 不正になっていた）。 供給／吸収の電力は
  #   物理的に負にならないため 0 とみなす。 両側とも正の通常セルには影響しない。
  p_supply = max(0.0, p_supply)
  p_absorb = max(0.0, p_absorb)
  pleak = min(p_supply, p_absorb)

  #if h.target_relport_val == "0":
  #if (i_rel_leak > 0.0) and (pleak > i_rel_leak):
  #  pleak = pleak - i_rel_leak

  #
  #print(f"i_vdd_leak={i_vdd_leak}, i_rel_leak={i_rel_leak}, pleak={pleak}")
  rslt["pleak"]=pleak

  #
  return (rslt)
