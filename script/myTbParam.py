from dataclasses import dataclass
from pydantic import BaseModel, Field

from myLibrarySetting       import MyLibrarySetting        as Mls 
from myLogicCell            import MyLogicCell             as Mlc
from myConditionsAndResults import MyConditionsAndResults  as Mcar


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
  arc_oirc     :list[str]=Field(default_factory=list);
  val0_oirc    :list[str]=Field(default_factory=list);

  clk_role     :str        ="nouse"
  meas_energy  :int        =0;  # 0:No Meas for Energy/ 1:Meas Only Time/ 2:Meas all
  time_energy  :list[float]=Field(default_factory=list); #[start,end]
  
  timestep     :float      =1e-9;
  tsim_end     :float      =1e-9;
  tdelay_init  :float      =1e-9;  #-- for VCLK
  tpulse_init  :float      =1e-9;  #-- for VCLK
  tdelay_in    :float      =1e-9;  #-- for VIN(inport)
  tslew_in     :float      =1e-9;  #-- for VIN(inport)
  tdelay_rel   :float      =1e-9;  #-- for VREL(relport)
  tslew_rel    :float      =1e-9;  #-- for VREL(relport)
  tpulse_rel   :float      =1e-9;  #-- for VREL(relport)
  tsweep_rel   :float      =0;  #-- for VREL(relport), setup/hold timing


  def set_common_value(self, harness:Mcar, arc_oirc:list[str]):
    h=harness

    #--
    self.tb_instance  = h.gen_instance_for_tb()
    self.model        = h.mlc.model   if h.mlc.model.startswith("/")   else "../" + h.mlc.model
    self.netlist      = h.mlc.netlist if h.mlc.netlist.startswith("/") else "../" + h.mlc.netlist

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


    
