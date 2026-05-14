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
  val0_oirc    :list[str]=Field(default_factory=list);

  clk_role     :str        ="nouse"; # nouse/related/input
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

    # PWL slew 用の最小時間（秒換算）。 .tran の print 間隔（simulation_timestep）と独立に細かい値を扱える
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
  
    self.arc_oirc     =["rise" if arc_oirc[0]=="r" else "fall" if arc_oirc[0]=="f" else "none",
                        "rise" if arc_oirc[1]=="r" else "fall" if arc_oirc[1]=="f" else "none",
                        "rise" if arc_oirc[2]=="r" else "fall" if arc_oirc[2]=="f" else "none",
                        "rise" if arc_oirc[3]=="r" else "fall" if arc_oirc[3]=="f" else "none"]
    
    self.val0_oirc    =[h.target_outport_val,h.target_inport_val,h.target_relport_val,h.target_clkport_val]


    #--
    if   h.timing_type == "three_state_enable":
      v = h.mls.sim_pullres_io_enable if h.mlc.isio else h.mls.sim_pullres_std_enable
      self.pullres = float("{:.5g}".format(v * h.mls.resistance_mag))
    elif h.timing_type == "three_state_disable":
      v = h.mls.sim_pullres_io_disable if h.mlc.isio else h.mls.sim_pullres_std_disable
      self.pullres = float("{:.5g}".format(v * h.mls.resistance_mag))


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
    
