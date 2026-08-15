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
import math
from dataclasses import dataclass
from pydantic import BaseModel, Field
import os, json, re

from .myLibrarySetting       import MyLibrarySetting        as Mls
from .myLogicCell            import MyLogicCell             as Mlc
from .myConditionsAndResults import MyConditionsAndResults  as Mcar
from .myFunc                 import my_exit


@dataclass
class MyTbParam:
  model        :str  ="";
  model_sections:list[str]=Field(default_factory=list); #ISS-00184: .lib <model> <section> の section 群
  netlist      :str  ="";
  temp         :float=0.0;
  voltage_vsnp :list[float]=Field(default_factory=list);#for vdd/vss/vnw/vpw
  prop_vth_oirc:list[str]  =Field(default_factory=list); #for outport/inport/related/clock
  judge_vth_oirc:list[str] =Field(default_factory=list); #ISS-00218(A): const 判定 judge_dly の TRIG 側閾値
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
  pin_tr       :list[str]=Field(default_factory=list);  # ISS-00133: Liberty 出力用 pin 識別 [target, related]
  is_lat       :bool      =False;  # ISS-00133: LATCH cell かどうか (level-sensitive)。 jp2 の judge_dly の TRIG/TARG 切替に使用
  is_gated     :bool      =False;  # ISS-00218: EN 制御セル（ICG 等、mylogic の "is_gated"）かどうか。 保持型判定の観測点選択に使用
  energy_trig_node :str    ="VREL"; # ISS-00133: energy_start のトリガノード（related pin pin_tr[1] のスロットで決定：VIN/VREL/VCLK）
  energy_trig_slot :int    =2;      # ISS-00133: 同スロット index（ener_v0_oirc/arc_oirc4measure 参照用。 VIN=1/VREL=2/VCLK=3）
  ener_estart  :float     =0.0;    # ISS-00151: power_tout energy2 用。 energy1 で確定した estart/eend を保持し、
  ener_eend    :float     =0.0;    #   energy2 の WHEN 不成立（大 slew で out of interval）時のフォールバックに使う
  energy_tgt_node :str     ="VREL"; # power_tin: 計測対象ノード（target pin pin_tr[0] のスロットで決定：VIN/VREL/VCLK）
  energy_tgt_slot :int     =2;      # 同スロット index（VIN=1/VREL=2/VCLK=3、 未検出は 2=従来動作の保持）
  vout_path       :str    ="VOUT"; # ISS-00218: 判定に使わない measure（chg_out/prop_rel_out/energy/o_max_v）の観測点。 常に VOUT
  vout_judge_path :str    ="VOUT"; # ISS-00218: const 判定チェーン（judge_dly/judge_vlt/prop_clk_out/prop_in_out）の観測点。 is_gated は xcell.xdut.<net>
  setup_kind   :str       ="";     # ISS-00133: const 系の種別 "setup"/"hold"/"recovery"/"removal"、 jp2 の MEASURE 切替に使用
  measure_type :str       ="";     # ISS-00135: harness.measure_type を保持（compute_timing で leakage 判定用）
  val_oirc    :list[str]=Field(default_factory=list);

  clk_role     :str        ="nouse"; # nouse/related/input
  clk_init     :str        ="pulse"; # pulse (default) or stable (for LAT combinational arc)
  pullres_role :str        ="nouse"; # nosue/up/down/up_ngate/up_pgate/down_ngate/down_pgate
  meas_energy  :int        =0;  # 0:No Meas for Energy/ 1:Meas Only Time/ 2:Meas all
  time_energy  :list[float]=Field(default_factory=list); #[start,end]

  meas_o_max_min:int       =0;
  
  maxstep      :float      =1e-9;  # ISS-00219: .tran の内部積分ステップ上限（第4引数）。 第1引数にも同値を渡す
  tslew_min    :float      =1e-12;  # PWL slew 用の最小時間（秒、 .tran の timestep より細かい用途）
  tsim_end     :float      =1e-9;
  tdelay_init  :float      =1e-9;  #-- for VCLK
  tpulse_init  :float      =1e-9;  #-- for VCLK
  tdelay_in    :float      =1e-9;  #-- for VIN(inport)
  tslew_in     :float      =1e-9;  #-- for VIN(inport)
  tdelay_rel   :float      =1e-9;  #-- for VREL(relport)
  tslew_rel    :float      =1e-9;  #-- for VREL(relport)
  tpulse_rel   :float      =1e-9;  #-- for VREL(relport)
  #tsweep_rel   :float      =0;     #-- for VCLK(relport), setup/hold timing
  tdelay_clk   :float      =1e-9;  #-- for VCLK(clkport)
  tslew_clk    :float      =1e-9;  #-- for VCLK(clkport)
  tpulse_clk   :float      =1e-9;  #-- for VCLK(clkport)
  tsweep_clk   :float      =0;  #-- for VCLK(clkport), setup/hold timing

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
  t_clk4       :float      =0.0
  t_clk5       :float      =0.0
  t_clk6       :float      =0.0
  t_clk7       :float      =0.0

  wave_raw         :bool=False  #-- ISS-00078: True で .save / -r 出力
  wave_save_list   :str ="";    #-- testbench top node の固定 14 リスト
  pinmap_dict      :dict        = None #-- raw signal → cell port mapping (sidecar .pinmap.json 用)
  internal_nodes   :list[str]   = Field(default_factory=list); #-- ISS-00166: leakage op 用 DUT 内部ノード（nodeset/meas 対象）
  leak_meas_at     :float       = 0.0  #-- ISS-00166: leakage op で内部ノード電圧を meas find する時刻（tsim_end より僅か手前）
  #--- ISS-00220: const 掃引の高速化（初期化のやり直しを止める）。
  #   const は 1 格子点あたり約 30 sim 回るが、 掃引で変わるのは CLK の相対位置だけで
  #   「再開時刻」より前の内部状態は全掃引点で共通。 にもかかわらず毎回 0 から回し直しており、
  #   sky130 dfxtp_1 setup では初期化が 1 sim の 77.6% を占めていた。
  #   0 回目（準備 run）で再開時刻の内部ノード電圧を取得し、 1 回目以降は nodeset で復元して
  #   測定区間だけ回す。 時刻は jp2 側で `+ _t_ofs` するだけ（start_offset は負値で渡す）。
  #   .tran の tstart は 0 のまま（tstart を使っても 0〜tstart は計算されるので短縮にならない＝ISS-00219）。
  start_offset     :float       = 0.0  #-- 時間軸のシフト量[s]。 0=従来動作。 時短時は負値
  nodeset_file     :str         = ""   #-- 取り込む nodeset ファイル（sim dir からの相対パス）。 空なら出力しない
  nodeset_probe    :bool        = False #-- True で .control に内部ノード電圧の meas find を出す（0 回目のみ）
  nodeset_meas_at  :float       = 0.0  #-- 内部ノード電圧を meas find する時刻[s]（＝再開時刻）
  #-- ISS-00234: PWL 折れ点の時刻を丸める粒度[s]。 0=無効（従来動作）。
  #   端数を持つ折れ点で LTE が刻みを詰めて delmin を割る（Timestep too small）。
  #   jsonc の sim_segment_timestep_min[ns]（掃引の最小刻み）× time_mag を流用する。
  time_quantize    :float       = 0.0

  def set_common_value(self, harness:Mcar, arc_oirc:list[str]):
    h=harness

    #-- ISS-00078: wave_raw 設定 + testbench top node を .save
    #   raw 内の signal name は ngspice 内部 node 名（generic）のまま。 viewer 側で
    #   sidecar .pinmap.json (DUT pin name -> plot signal name) を参照して表示変換する。
    #-- ISS-00220: MyTbParam は @dataclass なので pydantic の Field(default_factory=...) は
    #   既定値として機能せず、 未設定だと FieldInfo が残る（jp2 で 'not iterable' になる）。
    #   leakage 経路は必ず代入するので露見していなかった。 ここで確実に空リストへ初期化する。
    if not isinstance(self.internal_nodes, list):
      self.internal_nodes = []
    self.wave_raw = bool(getattr(h.mls, "wave_raw", False))
    if self.wave_raw:
      # XCELL（DUT instance）に渡す 14 信号のみ。 WOUT/WFLOAT は XCELL の port ではないため除外。
      # ngspice の control block write は vector name を小文字で要求する（'no writable vector' 回避）。
      self.wave_save_list = (
        "v(vclk) v(vrel) v(vin) v(vout) "
        "v(vhigh) v(vlow) v(vhigh_io) v(vlow_io) "
        "v(vdd_dyn) v(vss_dyn) v(vnw_dyn) v(vpw_dyn) v(vddio_dyn) v(vssio_dyn) "
        "i(vdd_dyn) i(vss_dyn) i(vclk) i(vrel) i(vin)"  # ISS-00124 debug: 電流追加（pin(E) D=0/1 貫通電流確認）
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
        # ISS-00135 reorg(U3): pin_oirc 直参照＋判定順を gen_instance と同じ CLK->REL->IN->OUT に統一
        _po = h.mec.pin_oirc
        if   _po[3] and logic_port == _po[3]: pinmap[port] = "v(vclk)"
        elif _po[2] and logic_port == _po[2]: pinmap[port] = "v(vrel)"
        elif _po[1] and logic_port == _po[1]: pinmap[port] = "v(vin)"
        elif _po[0] and logic_port == _po[0]: pinmap[port] = "v(vout)"
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
    #-- ISS-00234: 時刻の量子化幅。 **掃引の最小刻み sim_segment_timestep_min[ns] を
    #   そのまま使う**（ダーマツ判断 2026-08-15）。 専用の設定は増やさない。
    #   掃引の分解能と同じ粒度なので掃引点は潰れず、 原点のずれ（実測 0.37ps）だけが消える。
    self.time_quantize = float(getattr(h.mls, "sim_segment_timestep_min", 0.0)) * h.mls.time_mag
    
    #self.model        = h.mlc.model   if h.mlc.model.startswith("/")   else "../" + h.mlc.model
    #self.netlist      = h.mlc.netlist if h.mlc.netlist.startswith("/") else "../" + h.mlc.netlist
    self.model        = h.mlc.model
    self.model_sections = h.mlc.model_sections
    self.netlist      = h.mlc.netlist

    #--
    self.temp         = h.mls.temperature

    self.voltage_vsnp =[h.mls.vdd_voltage, h.mls.vss_voltage, h.mls.nwell_voltage, h.mls.pwell_voltage]

    self.prop_vth_oirc=[h.mls.logic_low_to_high_threshold_voltage if arc_oirc[0]=="r" else h.mls.logic_high_to_low_threshold_voltage,
                        h.mls.logic_low_to_high_threshold_voltage if arc_oirc[1]=="r" else h.mls.logic_high_to_low_threshold_voltage,
                        h.mls.logic_low_to_high_threshold_voltage if arc_oirc[2]=="r" else h.mls.logic_high_to_low_threshold_voltage,
                        h.mls.logic_low_to_high_threshold_voltage if arc_oirc[3]=="r" else h.mls.logic_high_to_low_threshold_voltage]

    #-- ISS-00218(A): judge_dly の TRIG 側は「遷移の開始側」に置く（rise=0.1 / fall=0.9）。
    #   TARG（出力）は prop_vth_oirc[0]（50%）のまま。 .lib の値には影響しない。
    self.judge_vth_oirc=[h.mls.const_judge_threshold_rise_voltage if arc_oirc[0]=="r" else h.mls.const_judge_threshold_fall_voltage,
                         h.mls.const_judge_threshold_rise_voltage if arc_oirc[1]=="r" else h.mls.const_judge_threshold_fall_voltage,
                         h.mls.const_judge_threshold_rise_voltage if arc_oirc[2]=="r" else h.mls.const_judge_threshold_fall_voltage,
                         h.mls.const_judge_threshold_rise_voltage if arc_oirc[3]=="r" else h.mls.const_judge_threshold_fall_voltage]

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
    # ISS-00133: pin_tr (Liberty 出力用 [target, related]) と is_lat (LATCH 判定) を jp2 に渡す
    self.pin_tr       =list(getattr(h.mec, "pin_tr", []))
    # logic_type が "seq_lat" なら LATCH、 それ以外（"seq", "comb" 等）は FF or comb
    # ISS-00153: logic_type は Mlc の属性ではなく mls.logic_dict[mlc.logic] の辞書引き。
    #   旧 getattr(h.mlc,...) は常に "" → is_lat が全セル False（jp2 の LAT 分岐が不達）だった。
    self.is_lat       = (getattr(h.mls, "logic_dict", {}).get(h.mlc.logic, {}).get("logic_type", "") == "seq_lat")
    # ISS-00218: EN 制御セル（ICG）は mylogic 定義の "is_gated" で識別する。 logic_type は LATCH と同じ
    #   "seq_lat" のため is_lat では区別できない。 保持型判定の観測点選択（下記 vout_judge_path）に使う。
    self.is_gated     = bool(getattr(h.mls, "logic_dict", {}).get(h.mlc.logic, {}).get("is_gated", False))
    # ISS-00133: energy_start のトリガノードを related pin(pin_tr[1]) のスロットで選択。
    #   related が pin_oirc の VIN(1)/VREL(2)/VCLK(3) のどこに居るかでノード決定する。
    #   comb は入力を VREL に置くため slot2->VREL、 seq(CLK駆動)は pin_tr[1]=c0->slot3->VCLK。
    #   pin_tr[1] 未設定/未一致なら VREL(slot2) を既定（従来動作を保持）。
    _rel_pin = self.pin_tr[1] if len(self.pin_tr) > 1 else ""
    self.energy_trig_slot = 2
    self.energy_trig_node = "VREL"
    if _rel_pin:
      for _s, _nd in ((1, "VIN"), (2, "VREL"), (3, "VCLK")):
        if _s < len(self.pin_oirc) and self.pin_oirc[_s] == _rel_pin:
          self.energy_trig_slot = _s
          self.energy_trig_node = _nd
          break
    # power_tin: 計測対象（target pin pin_tr[0]）のスロット逆引き。
    #   estart/eend（積分窓）・slope→tslew 割当・cin 選択を「X を駆動するスロット」基準にするために使う。
    #   優先順 c > r > i（旧方式の重複記載 entry でも実駆動源と一致させる）。
    #   pin_tr[0] 未設定/未一致なら VREL(slot2) を既定（従来動作の保持、 biport 等の安全網）。
    _tgt_pin = self.pin_tr[0] if len(self.pin_tr) > 0 else ""
    self.energy_tgt_slot = 2
    self.energy_tgt_node = "VREL"
    if _tgt_pin:
      for _s, _nd in ((3, "VCLK"), (2, "VREL"), (1, "VIN")):
        if _s < len(self.pin_oirc) and self.pin_oirc[_s] == _tgt_pin:
          self.energy_tgt_slot = _s
          self.energy_tgt_node = _nd
          break
    # ISS-00133: measure_type から setup_kind を判定（setup/hold/recovery/removal の文字列）
    #   setup_kind の用途は jp2 の const MEASURE ブロック選択のみ（観測点の選択には使わない）。
    _mt = getattr(h, "measure_type", "")
    self.measure_type = _mt   # ISS-00135: compute_timing で leakage 判定用
    if   _mt.startswith("setup_"):    self.setup_kind = "setup"
    elif _mt.startswith("hold_"):     self.setup_kind = "hold"
    elif _mt.startswith("recovery_"): self.setup_kind = "recovery"
    elif _mt.startswith("removal_"):  self.setup_kind = "removal"
    else:                              self.setup_kind = ""
    # ISS-00152/00218: MEASURE の観測点パスを Python 側で解決し、 jp2 は変数を書き出すだけにする。
    #   vout_path       : 判定に使わない measure（chg_out / prop_rel_out / energy / o_max_v）＝常に VOUT。
    #   vout_judge_path : const 系の判定チェーン（judge_dly / judge_vlt_max/min / prop_clk_out / prop_in_out）
    #     の観測点。 is_gated セル（ICG）は捕捉の成否が確定する内部ラッチ出力と外部出力の間に enable
    #     ゲートが挟まる（GCLK = CLK AND QD）ため、 出力 Q で見ると setup は「E と CLK の幾何的な時間差」
    #     になり劣化を測れない。 vout_infos のセル内部 net（gf180 icgtp の QD）を観測する。 他は VOUT。
    #     判定値と基準値（prop_*）で観測点を揃えるため、 prop_clk_out / prop_in_out も対象に含める。
    #   ISS-00218: 一時 judge_dly を VOUT に戻したが、 gf180 icgtp_1 setup_rising が orig -0.183 に対し
    #     -5.07（内部 net 版は +0.92）と大幅悪化したため差し戻した。 全 sweep 点で judge_dly が一定なのは
    #     透過ラッチの正常挙動（フラット→崖で FAIL）であり、 故障ではない。
    self.vout_path       = "VOUT"
    self.vout_judge_path = "VOUT"
    _vi = getattr(h.mlc, "vout_infos", {}) or {}
    _o  = h.mec.pin_oirc[0]
    _internal = "xcell.xdut." + str(_vi[_o]["node"]) if (_o and _o in _vi and _vi[_o].get("node")) else ""
    if _internal:
      # ISS-00153: wave_raw 時は内部観測ノードも raw に保存（ngspice write は小文字要求）。
      #   判定に使わない measure でも波形確認できるよう、 保存は無条件に行う。
      if self.wave_raw and self.wave_save_list:
        self.wave_save_list += f" v({_internal.lower()})"
      if self.is_gated and self.setup_kind:
        self.vout_judge_path = _internal

    # ISS-00133: min_pulse の prop TRIG は「パルス先頭エッジ(arc_oirc4measure)」でなく
    #   「パルス対象ピン pin_tr[0] の能動エッジ」を使う（posedge DFF の low パルスは末尾立上りで捕捉）。
    #   能動エッジは logic 名サフィックスで決定：c→_PC/_NC, s→_PS/_NS, r→_PR/_NR（pos=rise/neg=fall）。
    if _mt in ("min_pulse_width_low", "min_pulse_width_high"):
      _pt   = self.pin_tr[0] if self.pin_tr else ""
      _name = getattr(h.mlc, "logic", "")
      _pfx  = _pt[:1]
      _cap_edge = None
      if   _pfx == "c": _cap_edge = "rise" if "_PC" in _name else "fall" if "_NC" in _name else None
      elif _pfx == "s": _cap_edge = "rise" if "_PS" in _name else "fall" if "_NS" in _name else None
      elif _pfx == "r": _cap_edge = "rise" if "_PR" in _name else "fall" if "_NR" in _name else None
      if _cap_edge:
        for _k in range(len(self.pin_oirc)):
          if self.pin_oirc[_k] == _pt:
            self.arc_oirc4measure[_k] = _cap_edge
            break

    # ISS-00135 reorg(U2): val_oirc を pin_oirc + ival から直接構築（target_*port_val 廃止）
    _ival = h.mec.ival
    def _val_of(pos):
        if not pos:
            return ""
        m = re.match(r"([a-zA-Z]+)(\d+)", pos)
        if not m:
            print(f"[Error] illegal pin in pin_oirc: {pos}"); my_exit()
        pin, idx = m.group(1), int(m.group(2))
        vals = _ival.get(pin, [])
        if idx >= len(vals):
            print(f"[Error] ival missing for {pos} (ival={_ival})"); my_exit()
        return vals[idx]
    self.val_oirc    = [_val_of(p) for p in self.pin_oirc]


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
    secant 制御 (tsweep_clk 更新) の後に呼ぶことで `_t_init0..t_clk7` を再計算する。
    ISS-00134: `pin_oirc[i]==""` の phase（VIN/VREL/VCLK 不使用）は加算時間を `tslew_min` に集約し、
    sim 範囲外 breakpoint による ngspice の step 細分化を回避（power_tin 等の sim 時間短縮）。
    呼び出し順序：set_common_value(harness, arc_oirc) → 個別 field 設定 → compute_timing()。
    """
    assert len(self.pin_oirc) == 4, f"pin_oirc must be length 4, got {len(self.pin_oirc)}: {self.pin_oirc}"

    self.t_init0 = self.tslew_min + self.tdelay_init
    self.t_init1 = self.t_init0  + 2*self.tslew_min
    self.t_init2 = self.t_init1  + self.tpulse_init
    self.t_init3 = self.t_init2  + 2*self.tslew_min

    self.t_in0   = self.t_init3  + (self.tdelay_in    if (self.pin_oirc[1]!="" or self.measure_type.startswith("leakage")) else self.tslew_min)
    self.t_in1   = self.t_in0    + (self.tslew_in     if (self.pin_oirc[1]!="" or self.measure_type.startswith("leakage")) else self.tslew_min)

    self.t_rel0  = self.t_in1    + (self.tdelay_rel   if self.pin_oirc[2]!="" else self.tslew_min)
    if self.time_quantize > 0.0:
      self.t_rel0 = math.ceil(self.t_rel0 / self.time_quantize) * self.time_quantize
    self.t_rel1  = self.t_rel0   + (self.tslew_rel    if self.pin_oirc[2]!="" else self.tslew_min)
    self.t_rel2  = self.t_rel1   + (self.tpulse_rel   if self.pin_oirc[2]!="" else self.tslew_min)
    self.t_rel3  = self.t_rel2   + (2*self.tslew_min  if self.pin_oirc[2]!="" else self.tslew_min)

    self.t_clk4  = self.t_rel3   + ((self.tdelay_clk + self.tsweep_clk) if self.pin_oirc[3]!="" else self.tslew_min)
    #-- ISS-00234（2026-08-15、 ダーマツ指示）: 遷移の開始時刻を time_quantize[s] へ切り上げる。
    #   端数（実測 0.3 ps）を持つ PWL 折れ点で LTE が刻みを詰めて delmin を割り
    #   `Timestep too small` で abort する。 1ps 格子に乗せるだけで解消する（実測）。
    #   ⚠ 遷移幅（slew）は変えない。 t_clk5 以降は丸めた t_clk4 からの相対で決まるので、
    #     下の既存式がそのまま「元の幅」を保つ。
    #   ⚠ 丸めるのは **開始側の折れ点だけ**（t_rel0 / t_clk4）。 終了側（t_rel1 / t_clk5）を
    #     丸めると slew が変わってしまう。
    if self.time_quantize > 0.0:
      self.t_clk4 = math.ceil(self.t_clk4 / self.time_quantize) * self.time_quantize
    self.t_clk5  = self.t_clk4   + (self.tslew_clk    if self.pin_oirc[3]!="" else self.tslew_min)
    self.t_clk6  = self.t_clk5   + (self.tpulse_clk   if self.pin_oirc[3]!="" else self.tslew_min)
    self.t_clk7  = self.t_clk6   + (2*self.tslew_min  if self.pin_oirc[3]!="" else self.tslew_min)

  def tsweep_for_clk4_at(self, target_time:float) -> float:
    """ISS-00133: `_t_clk4` を `target_time` にするための `tsweep_clk` を返す。
    `_t_clk4 = t_rel3 + tdelay_clk + tsweep_clk` の式から逆算。
    secant の seg_start/seg_end を物理単位（例 `param.t_init3`）で指定可能にする。
    呼び出し前に `compute_timing()` で `t_rel3, tdelay_clk` を確定しておくこと。
    """
    #return target_time - self.t_rel3 - self.tdelay_clk
    return target_time - self.t_clk4

