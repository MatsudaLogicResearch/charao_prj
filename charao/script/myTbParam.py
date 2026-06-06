#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
# This file is part of charao.
#
# Copyright (C) 2025 MATSUDA Masahiro
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
from dataclasses import dataclass
from pydantic import BaseModel, Field
import os, json

from .myLibrarySetting       import MyLibrarySetting        as Mls
from .myLogicCell            import MyLogicCell             as Mlc
from .myConditionsAndResults import MyConditionsAndResults  as Mcar


@dataclass
class MyTbParam:
  model        :str  ="";
  netlist      :str  ="";
  temp         :float=0.0;
  voltage_vsnp :list[float]=Field(default_factory=list);#for vdd/vss/vnw/vpw
  prop_vth_oirc:list[str]  =Field(default_factory=list); #for outport/inport/related/clock
  tran_v0_oirc :list[str]  =Field(default_factory=list); #for outport/inport/related/clock
  tran_v1_oirc :list[str]  =Field(default_factory=list); #for outport/inport/related/clock
  ener_v0_oirc :list[str]  =Field(default_factory=list); #for outport/inport/related/clock
  ener_v1_oirc :list[str]  =Field(default_factory=list); #for outport/inport/related/clock
  
  tb_instance  :str        =""
  cap          :float      =0.0;
  pullres      :float      =1000;
  pullres_gate :str        ="driver.ngate";
  arc_oirc     :list[str]=Field(default_factory=list);
  arc_oirc4measure :list[str]=Field(default_factory=list);  # ISS-00101: r→rise, f→fall。.MEASURE TRAN edge spec 用
  pin_oirc     :list[str]=Field(default_factory=list);  # ISS-00101: pin name (o0/i0/r0/s0/c0 等) を testbench に渡す
  val_oirc    :list[str]=Field(default_factory=list);

  clk_role     :str        ="nouse"; # nouse/related/input
  clk_init     :str        ="pulse"; # pulse (default) or stable (for LAT combinational arc)
  pullres_role :str        ="nouse"; # nosue/up/down/up_ngate/up_pgate/down_ngate/down_pgate
  meas_energy  :int        =0;  # 0:No Meas for Energy/ 1:Meas Only Time/ 2:Meas all
  time_energy  :list[float]=Field(default_factory=list); #[start,end]

  meas_o_max_min:int       =0;
  
  timestep     :float      =1e-9;
  tslew_min    :float      =1e-12;  # PWL slew 用の最小時間（秒、 .tran の timestep より細かい用途）
  timestep_tmax:float      =1e-9;
  tsim_end     :float      =1e-9;
  tdelay_init  :float      =1e-9;  #-- for VCLK
  tpulse_init  :float      =1e-9;  #-- for VCLK
  tdelay_in    :float      =1e-9;  #-- for VIN(inport)
  tslew_in     :float      =1e-9;  #-- for VIN(inport)
  tdelay_rel   :float      =1e-9;  #-- for VREL(relport)
  tslew_rel    :float      =1e-9;  #-- for VREL(relport)
  tpulse_rel   :float      =1e-9;  #-- for VREL(relport)
  tsweep_rel   :float      =0;  #-- for VREL(relport), setup/hold timing

  #-- ISS-00080: testbench jp2 の `.param _t_*` を Python 側でも保持。
  #   secant 制御で `_t_rel0` を `_t_init3` まで戻す等の物理単位指定を可能にする。
  #   `compute_timing()` で算出。 jp2 側 `.param` と同じ式で値も一致する想定（二重管理だが
  #   spice 側で `.param` 評価 / Python 側で secant 制御、 用途を分離）。
  t_init0      :float      =0.0
  t_init1      :float      =0.0
  t_init2      :float      =0.0
  t_init3      :float      =0.0
  t_in0        :float      =0.0
  t_in1        :float      =0.0
  t_rel0       :float      =0.0
  t_rel1       :float      =0.0
  t_rel2       :float      =0.0
  t_rel3       :float      =0.0
  t_clk0       :float      =0.0
  t_clk1       :float      =0.0
  t_clk2       :float      =0.0
  t_clk3       :float      =0.0
  t_clk4       :float      =0.0
  t_clk5       :float      =0.0
  t_clk6       :float      =0.0
  t_clk7       :float      =0.0

  wave_raw         :bool=False  #-- ISS-00078: True で .save / -r 出力
  wave_save_list   :str ="";    #-- testbench top node の固定 14 リスト
  pinmap_dict      :dict        = None #-- raw signal → cell port mapping (sidecar .pinmap.json 用)

  def set_common_value(self, harness:Mcar, arc_oirc:list[str]):
    h=harness

    #-- ISS-00078: wave_raw 設定 + testbench top node を .save
    #   raw 内の signal name は ngspice 内部 node 名（generic）のまま。 viewer 側で
    #   sidecar .pinmap.json (DUT pin name -> plot signal name) を参照して表示変換する。
    self.wave_raw = bool(getattr(h.mls, "wave_raw", False))
    if self.wave_raw:
      # XCELL（DUT instance）に渡す 14 信号のみ。 WOUT/WFLOAT は XCELL の port ではないため除外。
      # ngspice の control block write は vector name を小文字で要求する（'no writable vector' 回避）。
      self.wave_save_list = (
        "v(vclk) v(vrel) v(vin) v(vout) "
        "v(vhigh) v(vlow) v(vhigh_io) v(vlow_io) "
        "v(vdd_dyn) v(vss_dyn) v(vnw_dyn) v(vpw_dyn) v(vddio_dyn) v(vssio_dyn)"
      )
      # DUT cell port name -> plot signal name の mapping
      # ports_dict は {cell_port_name: logic_port_name}（例 dffsnq_1: {"D":"i0","CLK":"c0",...}）
      # target_*port / stable_inport_val / nontarget_outport は logic port name (i0/c0/s0/...) ベース。
      # 電源ピンは大文字名で mls.vdd_name 等と直接照合。
      pinmap = {}
      ports_dict = h.mlc.ports_dict if (hasattr(h.mlc, "ports_dict") and h.mlc.ports_dict) else {}
      vdd_u = (h.mls.vdd_name or "").upper()
      vss_u = (h.mls.vss_name or "").upper()
      vnw_u = (h.mls.nwell_name or "").upper()
      vpw_u = (h.mls.pwell_name or "").upper()
      for port, logic_port in ports_dict.items():
        pu = port.upper()
        if   logic_port == h.target_inport:  pinmap[port] = "v(vin)"
        elif logic_port == h.target_outport: pinmap[port] = "v(vout)"
        elif logic_port == h.target_clkport: pinmap[port] = "v(vclk)"
        elif logic_port == h.target_relport: pinmap[port] = "v(vrel)"
        elif logic_port in (h.stable_inport_val or {}):
          val = h.stable_inport_val[logic_port]
          pinmap[port] = "v(vhigh)" if val == "1" else ("v(vlow)" if val == "0" else "")
        elif logic_port in (h.nontarget_outport or []): pinmap[port] = "v(wfloat)"
        elif pu == vdd_u: pinmap[port] = "v(vdd_dyn)"
        elif pu == vss_u: pinmap[port] = "v(vss_dyn)"
        elif pu == vnw_u: pinmap[port] = "v(vnw_dyn)"
        elif pu == vpw_u: pinmap[port] = "v(vpw_dyn)"
        # else: unmapped (viewer 側で除外 or generic 名表示)
      self.pinmap_dict = pinmap
    else:
      self.wave_save_list = ""
      self.pinmap_dict = None

    #--
    self.tb_instance  = h.gen_instance_for_tb()

    # PWL slew 用の最小時間（秒換算）。 .tran の print 間隔（simulation_timestep_max / _min）と独立に細かい値を扱える
    self.tslew_min = float("{:.5g}".format(h.mls.simulation_slew_min * h.mls.time_mag))
    
    #self.model        = h.mlc.model   if h.mlc.model.startswith("/")   else "../" + h.mlc.model
    #self.netlist      = h.mlc.netlist if h.mlc.netlist.startswith("/") else "../" + h.mlc.netlist
    self.model        = h.mlc.model   
    self.netlist      = h.mlc.netlist

    #--
    self.temp         = h.mls.temperature

    self.voltage_vsnp =[h.mls.vdd_voltage, h.mls.vss_voltage, h.mls.nwell_voltage, h.mls.pwell_voltage]

    self.prop_vth_oirc=[h.mls.logic_low_to_high_threshold_voltage if arc_oirc[0]=="r" else h.mls.logic_high_to_low_threshold_voltage,
                        h.mls.logic_low_to_high_threshold_voltage if arc_oirc[1]=="r" else h.mls.logic_high_to_low_threshold_voltage,
                        h.mls.logic_low_to_high_threshold_voltage if arc_oirc[2]=="r" else h.mls.logic_high_to_low_threshold_voltage,
                        h.mls.logic_low_to_high_threshold_voltage if arc_oirc[3]=="r" else h.mls.logic_high_to_low_threshold_voltage]

    self.tran_v0_oirc =[h.mls.logic_threshold_low_voltage  if arc_oirc[0]=="r" else h.mls.logic_threshold_high_voltage,
                        h.mls.logic_threshold_low_voltage  if arc_oirc[1]=="r" else h.mls.logic_threshold_high_voltage,
                        h.mls.logic_threshold_low_voltage  if arc_oirc[2]=="r" else h.mls.logic_threshold_high_voltage,
                        h.mls.logic_threshold_low_voltage  if arc_oirc[3]=="r" else h.mls.logic_threshold_high_voltage]

    self.tran_v1_oirc =[h.mls.logic_threshold_high_voltage  if arc_oirc[0]=="r" else h.mls.logic_threshold_low_voltage,
                        h.mls.logic_threshold_high_voltage  if arc_oirc[1]=="r" else h.mls.logic_threshold_low_voltage,
                        h.mls.logic_threshold_high_voltage  if arc_oirc[2]=="r" else h.mls.logic_threshold_low_voltage,
                        h.mls.logic_threshold_high_voltage  if arc_oirc[3]=="r" else h.mls.logic_threshold_low_voltage]

    self.ener_v0_oirc =[h.mls.energy_meas_low_threshold_voltage  if arc_oirc[0]=="r" else h.mls.energy_meas_high_threshold_voltage,
                        h.mls.energy_meas_low_threshold_voltage  if arc_oirc[1]=="r" else h.mls.energy_meas_high_threshold_voltage,
                        h.mls.energy_meas_low_threshold_voltage  if arc_oirc[2]=="r" else h.mls.energy_meas_high_threshold_voltage,
                        h.mls.energy_meas_low_threshold_voltage  if arc_oirc[3]=="r" else h.mls.energy_meas_high_threshold_voltage]

    self.ener_v1_oirc =[h.mls.energy_meas_high_threshold_voltage  if arc_oirc[0]=="r" else h.mls.energy_meas_low_threshold_voltage,
                        h.mls.energy_meas_high_threshold_voltage  if arc_oirc[1]=="r" else h.mls.energy_meas_low_threshold_voltage,
                        h.mls.energy_meas_high_threshold_voltage  if arc_oirc[2]=="r" else h.mls.energy_meas_low_threshold_voltage,
                        h.mls.energy_meas_high_threshold_voltage  if arc_oirc[3]=="r" else h.mls.energy_meas_low_threshold_voltage]
  
    #-- ISS-00101: arc_oirc は生の値（r/f/0/1/z、 移行期 s、 pin なし ""）のまま渡す。
    #   rise/fall への変換は廃止（temp_testbench 側で r/f/0/1/z を直接判定）。
    self.arc_oirc     =list(arc_oirc)
    # .MEASURE TRAN edge spec 用（r/p→rise / f/n→fall、 他は素通し）
    # ISS-00101: p (pos pulse) は最初の rise edge、 n (neg pulse) は最初の fall edge を TRIG として扱う
    _edge_map = {"r": "rise", "f": "fall", "p": "rise", "n": "fall"}
    self.arc_oirc4measure = [_edge_map.get(v, v) for v in arc_oirc]
    # ISS-00101: pin name を testbench に渡す（pin_oirc[1] vs [2] の異同で prop_in_out 生成判定）
    self.pin_oirc     =list(h.mec.pin_oirc)

    self.val_oirc    =[h.target_outport_val,h.target_inport_val,h.target_relport_val,h.target_clkport_val]


    #--
    if   h.timing_type == "three_state_enable":
      v = h.mls.sim_pullres_io_enable if h.mlc.isio else h.mls.sim_pullres_std_enable
      self.pullres = float("{:.5g}".format(v * h.mls.resistance_mag))
    elif h.timing_type == "three_state_disable":
      v = h.mls.sim_pullres_io_disable if h.mlc.isio else h.mls.sim_pullres_std_disable
      self.pullres = float("{:.5g}".format(v * h.mls.resistance_mag))


  def update_ener_thresholds_for_e1(self, arc_oirc:list[str], mls):
    """ISS-00117: meas_energy=1 (energy1: estart/eend 抽出のみ) 用の閾値補正。
    energy1 で eend を「VOUT が VDD 完全 settle した時刻」 として取得することで、
    energy2 の tsim_end が VOUT settle 後まで延長 → 余計な ramping 区間での ngspice 収束失敗を回避。

    呼出順序：param.meas_energy=1 設定後、 set_common_value 完了後に呼び、 ener_v0_oirc/ener_v1_oirc を上書きする。

    閾値仕様（係数 1%、 1.01 × high = VDD ちょうど到達まで広げる）：
      arc_oirc[i]=="r" (rise): v0=low (現状) / v1=1.01×high (VDD 完全到達まで)
      arc_oirc[i]!="r" (fall): v0=0.99×high (緩めに高値検出) / v1=0.99×low (緩めに低値検出)

    制約（myLibrarySetting.py で守る）：
      energy_meas_low_threshold  >= 0.01  → 0.99×low が負電圧化しない
      energy_meas_high_threshold <= 0.99  → 1.01×high が VDD 超過しない
    """
    self.ener_v0_oirc =[mls.energy_meas_low_threshold_voltage      if arc_oirc[i]=="r" else 0.99*mls.energy_meas_high_threshold_voltage for i in range(4)]
    self.ener_v1_oirc =[1.01*mls.energy_meas_high_threshold_voltage if arc_oirc[i]=="r" else 0.99*mls.energy_meas_low_threshold_voltage  for i in range(4)]


  def write_pinmap_if_enabled(self, sim_dir:str):
    """ISS-00078: wave_raw 有効時に sim_dir に .pinmap.json を書き出す。
    内容: DUT cell port name -> plot signal name (raw 内 generic 名) の dict。"""
    if not self.wave_raw or not self.pinmap_dict or not sim_dir:
      return
    try:
      with open(os.path.join(sim_dir, ".pinmap.json"), "w", encoding="utf-8") as f:
        json.dump(self.pinmap_dict, f, indent=2, ensure_ascii=False)
    except OSError:
      pass

  def compute_timing(self):
    """ISS-00080: testbench jp2 の `.param _t_*` と同じロジックで Python 側 timing を算出。
    secant 制御 (tsweep_rel 更新) の後に呼ぶことで `_t_rel0..t_clk7` を再計算する。
    `_t_clk4..7` は `clk_role` に応じて分岐（jp2 line 105-120 と同じ）。
    呼び出し順序：set_common_value(harness, arc_oirc) → 個別 field 設定 → compute_timing()。
    """
    self.t_init0 = self.tslew_min + self.tdelay_init
    self.t_init1 = self.t_init0  + 2*self.tslew_min
    self.t_init2 = self.t_init1  + self.tpulse_init
    self.t_init3 = self.t_init2  + 2*self.tslew_min
    self.t_in0   = self.t_init3  + self.tdelay_in
    self.t_in1   = self.t_in0    + self.tslew_in
    self.t_rel0  = self.t_in1    + self.tdelay_rel + self.tsweep_rel
    self.t_rel1  = self.t_rel0   + self.tslew_rel
    self.t_rel2  = self.t_rel1   + self.tpulse_rel
    self.t_rel3  = self.t_rel2   + 2*self.tslew_min
    # _t_clk0..3 は init phase 共通（jp2 line 101-104）
    self.t_clk0 = self.t_init0
    self.t_clk1 = self.t_init1
    self.t_clk2 = self.t_init2
    self.t_clk3 = self.t_init3
    # _t_clk4..7 は clk_role に応じて分岐（jp2 line 105-120）
    if   self.clk_role == "related":
      self.t_clk4 = self.t_rel0
      self.t_clk5 = self.t_rel1
      self.t_clk6 = self.t_rel2
      self.t_clk7 = self.t_rel3
    elif self.clk_role == "input":
      self.t_clk4 = self.t_in0
      self.t_clk5 = self.t_in1
      self.t_clk6 = self.tsim_end + 2*self.tslew_min
      self.t_clk7 = self.t_clk6   + 2*self.tslew_min
    else:
      self.t_clk4 = self.tsim_end + 2*self.tslew_min
      self.t_clk5 = self.t_clk4   + 2*self.tslew_min
      self.t_clk6 = self.t_clk5   + 2*self.tslew_min
      self.t_clk7 = self.t_clk6   + 2*self.tslew_min

  def tsweep_for_rel0_at(self, target_time:float) -> float:
    """ISS-00080: `_t_rel0` を `target_time` にするための `tsweep_rel` を返す。
    secant の seg_start/seg_end を物理単位（例 `param.t_init3`）で指定可能にする。
    呼び出し前に `compute_timing()` で `t_in1, tdelay_rel` を確定しておくこと。
    """
    return target_time - self.t_in1 - self.tdelay_rel

