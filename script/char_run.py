import argparse, re, os, shutil, subprocess, sys, inspect, threading 
import copy

from myConditionsAndResults import MyConditionsAndResults  as Mcar
from myLibrarySetting       import MyLibrarySetting        as Mls 
from myLogicCell            import MyLogicCell             as Mlc
from myExpectCell           import MyExpectCell            as Mec
from myTbParam              import MyTbParam               as Mtp

import numpy as np
from myFunc import my_exit
from typing import List
from jinja2 import Environment, FileSystemLoader
from dataclasses import dataclass

env = Environment(
    loader=FileSystemLoader('.'),
    line_comment_prefix='##',
)
tb_template = env.get_template('./template/temp_testbench.sp.jp2')

  
#--------------------------------------------------------------------------------------------------
def runExpectation(targetLib:Mls, targetCell:Mlc, expectationdictList:List[Mec]):
  harnessList = []

  size=len(expectationdictList)
  for ii in range(size):
    expectationdict = expectationdictList[ii]
    
    ## spice simulation
    measure_type=expectationdict.meas_type

    #--- skip for debug
    if (targetLib.measures_only) and (measure_type not in targetLib.measures_only):
      continue;
    
    #--- do simulation
    if   measure_type in ["combinational","preset","clear","rising_edge","falling_edge"]:
      rslt_Harness = runSpiceDelayPowerMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)
      
    elif measure_type in ["setup_rising","setup_falling","recovery_rising", "recovery_falling"]:
      rslt_Harness = runSpiceSetupMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)
      
    elif measure_type in ["hold_rising","hold_falling","removal_rising","removal_falling"]:
      rslt_Harness = runSpiceHoldMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)
      
    elif measure_type in ["passive"]:
      rslt_Harness = runSpicePassiveMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)
      
    elif measure_type in ["min_pulse_width_low","min_pulse_width_high"]:
      rslt_Harness = runSpiceMinPulseMultiThread(num=ii, mls=targetLib, mlc=targetCell, mec=expectationdict)
      
    else:
      print(f"[Error] not support measure_type={measure_type}.")
      my_exit()
      
    ## add result
    #harnessList.append(tmp_Harness)
    harnessList.extend(rslt_Harness)


  ## average cin of each harness
  targetCell.set_cin_avg(harnessList=harnessList) 

  ## max pleak in each input condition
  #targetCell.set_pleak_icrs(harnessList=harnessList) 

  ## average pleak of each harness & cell 
  targetCell.set_pleak_cell(harnessList=harnessList) 

  ##
  return harnessList

#--------------------------------------------------------------------------------------------------
def runSpiceDelayPowerMultiThread(num:int, mls:Mls, mlc:Mlc, mec:Mec)  -> list[Mcar]:

  ## spice file name
  spicef0 = "vt_"+str(mls.vdd_voltage)+"_"+str(mls.temperature)+"_"+str(mlc.cell)
  spicef1 = f"_{num}" + f"_{mec.meas_type}" + "_oir=" + ''.join(mec.pin_oir) + "_arc=" + ''.join(mec.arc_oir)
  spicef = spicef0 + spicef1
  
  # Limit number of threads
  # define semaphore 
  poolg_sema = threading.BoundedSemaphore(mls.num_thread)
  print("Num threads for simulation:"+str(mls.num_thread))

  ###################################################################
  #-- for delay
  thread_id = 0
  threadlist = list()

  h_delay = Mcar(mls=mls, mlc=mlc, mec=mec)
  h_delay.set_update()
  
  #------ get slopes/loads
  kind="delay"
  temp=mlc.template[kind]

  index1_slopes=temp.index_1
  index2_loads =temp.index_2
  
  h_delay.template_kind  = kind
  h_delay.template       = temp

  if len(index2_loads)<1:
    print(f"[Error] load size is 0 for template.")
    my_exit()
    
  if len(index1_slopes)<1:
    print(f"[Error] slope size is 0 for template.")
    my_exit()
    
  #------ search delay(trans)
  for index2_load in index2_loads:
    for index1_slope in index1_slopes:
      ##--- result is written in h_delay.dict_list2 with _lock
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

  
  ###################################################################
  #-- for power
  thread_id = 0
  threadlist = list()

  h_power = Mcar(mls=mls, mlc=mlc, mec=mec)
  h_power.set_update()
  
  #------ get slopes/loads
  kind="power"
  temp=mlc.template[kind]

  index1_slopes=temp.index_1
  index2_loads =temp.index_2

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
      thread = threading.Thread(target=runSpicePowerSingle,
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
  h_power.set_lut(value_name="ein")

  #------ update max_load/max_trans
  mlc.update_max_load4out(port_name=h_delay.target_outport, new_value=max(index2_loads))
  mlc.update_max_trans4in(port_name=h_delay.target_relport, new_value=max(index1_slopes))

  
  ###################################################################
  return [h_delay, h_power]
  
#--------------------------------------------------------------------------------------------------
def runSpiceDelaySingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope:float, index2_load:float):
                      
  with poolg_sema:
    spicefo  = str(spicef)+"_"+str(index2_load)+"_"+str(index1_slope)+".sp"
 
    ## trial
    rslt=genFileLogic_DelayTrial1x(targetHarness=targetHarness, spicef=spicefo, index1_slope=index1_slope,index2_load=index2_load)

    ## -- result in targetHarness
    with targetHarness._lock:
      targetHarness.dict_list2["prop" ][index1_slope][index2_load] = rslt["prop"]
      targetHarness.dict_list2["trans"][index1_slope][index2_load] = rslt["trans"]

    
#--------------------------------------------------------------------------------------------------
def genFileLogic_DelayTrial1x(targetHarness:Mcar, spicef:str, index1_slope:float, index2_load:float) ->dict:

  # rename
  h=targetHarness

  # create parameter
  arc_c0 = h.mec.arc_oir[2] if (h.mec.pin_oir[2]=="c0") else h.mec.arc_oir[1] if (h.mec.pin_oir[1]=="c0") else "r" if (h.target_clkport_val=="0") else "f"
  arc_oirc=h.mec.arc_oir+[arc_c0]
  tsim_end=1e-6

  #sim_c2d_max = h.mls.sim_c2d_max_per_unit * index2_load
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * index2_load, h.mls.sim_c2d_min)
  #--
  param = Mtp(
    #model         = model
    #,netlist      = netlist
    #,tb_instance  = tb_instance
    #,temp         = h.mls.temperature
    #,voltage_vsnp =[]
    #,prop_vth_oirc=[]
    #,tran_v0_oirc =[]
    #,tran_v1_oirc =[]
    #,ener_v0_oirc =[]
    #,ener_v1_oirc =[]
    #,arc_oirc     =[]
    #,val0_oirc    =[]
     cap          = index2_load  * h.mls.capacitance_mag
    ,clk_role     = h.clk_role
    ,meas_energy  = 0      # 0:No Meas for Energy/ 1:Meas Only Time/ 2:Meas all
    ,time_energy  = [0,0]  #[start,end]
    ,meas_o_max_min=0
    ,timestep     = h.mls.simulation_timestep * h.mls.time_mag
    ,tsim_end     = tsim_end
    ,tdelay_init  = 1e-9 if h.measure_type=="combinational" else h.mls.sim_d2c_max   * h.mls.time_mag
    ,tpulse_init  = 1e-9 if h.measure_type=="combinational" else h.mls.sim_pulse_max * h.mls.time_mag
    #,tdelay_in    = 1e-9 if h.measure_type=="combinational" else h.mls.sim_c2d_max   * h.mls.time_mag
    ,tdelay_in    = 1e-9 if h.measure_type=="combinational" else sim_c2d_max   * h.mls.time_mag
    ,tslew_in     = h.mls.simulation_timestep * h.mls.time_mag
    ,tdelay_rel   = h.mls.sim_prop_max        * h.mls.time_mag
    ,tslew_rel    = index1_slope              * h.mls.time_mag
    ,tpulse_rel   = tsim_end
    ,tsweep_rel   = 0.0
  );

  param.set_common_value(harness=h, arc_oirc=arc_oirc)
    
  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
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
        inline = re.sub('\=',' ',inline)
      
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

  #-- result
  rslt=dict()
  rslt["prop"] =float(res["prop_in_out"])
  rslt["trans"]=float(res["trans_out"])

  
  return (rslt)


#--------------------------------------------------------------------------------------------------
def runSpicePowerSingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope:float, index2_load:float):
                      
  with poolg_sema:
    spicefoe1 = str(spicef)+"_"+str(index2_load)+"_"+str(index1_slope)+"_energy1.sp"
    spicefoe2 = str(spicef)+"_"+str(index2_load)+"_"+str(index1_slope)+"_energy2.sp"
 
    ## 1st trial, extract energy_start and energy_end
    rslt1= genFileLogic_PowerTrial1x(targetHarness=targetHarness, spicef=spicefoe1, meas_energy=1, index1_slope=index1_slope, index2_load=index2_load, estart=0.0, eend=0.0)
                             

    ## 2nd trial, extract energy
    estart = rslt1["estart"]
    eend   = rslt1["eend"]
    rslt2= genFileLogic_PowerTrial1x(targetHarness=targetHarness, spicef=spicefoe2, meas_energy=2, index1_slope=index1_slope, index2_load=index2_load, estart=estart, eend=eend)

    #
    print(f'  [DEBUG] pleak={rslt2["pleak"]}, load={index2_load}, slope={index1_slope}')
    
    ## -- result in targetHarness
    with targetHarness._lock:
      targetHarness.dict_list2["eintl"][index1_slope][index2_load] = rslt2["eintl"]
      targetHarness.dict_list2["ein"  ][index1_slope][index2_load] = rslt2["ein"  ]
      targetHarness.dict_list2["cin"  ][index1_slope][index2_load] = rslt2["cin"  ]
      targetHarness.dict_list2["pleak"][index1_slope][index2_load] = rslt2["pleak"]
    
    
  
#--------------------------------------------------------------------------------------------------
def genFileLogic_PowerTrial1x(targetHarness:Mcar, spicef:str, meas_energy:int, index1_slope:float, index2_load:float, estart:float, eend:float):

  # rename
  h=targetHarness

  # create parameter
  arc_c0 = h.mec.arc_oir[2] if (h.mec.pin_oir[2]=="c0") else h.mec.arc_oir[1] if (h.mec.pin_oir[1]=="c0") else "r" if (h.target_clkport_val=="0") else "f"
  arc_oirc=h.mec.arc_oir+[arc_c0]

  tsim_end=eend + 1e-9 if meas_energy == 2 else 1e-6
  
  #sim_c2d_max = h.mls.sim_c2d_max_per_unit * index2_load
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * index2_load, h.mls.sim_c2d_min)

  param = Mtp(
    #model         = model
    #,netlist      = netlist
    #,tb_instance  = tb_instance
    #--,temp         = 
    #--,voltage_vsnp =[]
    #--,prop_vth_oirc=[]
    #--,tran_v0_oirc =[]
    #--,tran_v1_oirc =[]
    #--,ener_v0_oirc =[]
    #--,ener_v1_oirc =[]
    #--,arc_oirc     =[]
    #--,val0_oirc    =[]
     cap          = index2_load  * h.mls.capacitance_mag
    ,clk_role     = h.clk_role
    ,meas_energy  = meas_energy     # 0:No Meas for Energy/ 1:Meas Only Time/ 2:Meas all
    ,time_energy  = [estart,eend]  if meas_energy == 1 else [0,0]  #[start,end]
    ,meas_o_max_min=0
    ,timestep     = h.mls.simulation_timestep * h.mls.time_mag
    ,tsim_end     = tsim_end
    ,tdelay_init  = 1e-9 if h.measure_type=="combinational" else h.mls.sim_d2c_max   * h.mls.time_mag
    ,tpulse_init  = 1e-9 if h.measure_type=="combinational" else h.mls.sim_pulse_max * h.mls.time_mag
    #,tdelay_in    = 1e-9 if h.measure_type=="combinational" else h.mls.sim_c2d_max   * h.mls.time_mag
    ,tdelay_in    = 1e-9 if h.measure_type=="combinational" else sim_c2d_max   * h.mls.time_mag
    ,tslew_in     = 10*h.mls.simulation_timestep * h.mls.time_mag
    ,tdelay_rel   = h.mls.sim_prop_max        * h.mls.time_mag
    ,tslew_rel    = index1_slope              * h.mls.time_mag
    ,tpulse_rel   = tsim_end
    ,tsweep_rel   = 0.0
  );

  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  
  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
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
  if(meas_energy == 2):
    res_list += ["q_in_dyn","q_rel_dyn","q_clk_dyn","q_out_dyn","q_vdd_dyn","i_vdd_leak","i_in_leak","i_rel_leak","i_clk_leak"]
    
  with open(spicelis,'r') as f:
    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub('\=',' ',inline)
      
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


  # calculate resut
  rslt=dict()
  rslt["estart"]=float(res["energy_start"])
  rslt["eend"]  =float(res["energy_end"])

  energy_time=rslt["eend"] - rslt["estart"]
  
  if(meas_energy == 2):

    q_in_dyn=res["q_clk_dyn"] if h.target_relport=="c0" else res["q_rel_dyn"]
    
    ## Pleak = average of Pleak_vdd and Pleak_vss
    ## P = I * V
    #pleak= (((abs(res_i_vdd_leak])+abs(res_i_vss_leak))/2)*(targetLib.vdd_voltage))
    pleak=abs(float(res["i_vdd_leak"])) * h.mls.vdd_voltage
    
    ## input energy(=relport energy)
    #ein = abs(float(res["q_in_dyn"])) * h.mls.vdd_voltage
    ein = abs(float(q_in_dyn)) * h.mls.vdd_voltage

    ## Cin = Qin / V
    #cin = abs(float(res["q_in_dyn"]))/(h.mls.vdd_voltage)
    cin = abs(float(q_in_dyn))/(h.mls.vdd_voltage)
    
    ## intl. energy calculation
    ## intl. energy is the sum of short-circuit energy and drain-diffusion charge/discharge energy
    ## larger Ql: intl. Q, load Q 
    ## smaller Qs: intl. Q
    ## Eintl = QsV
    #--res_q = res_q_vdd_dyn if(abs(res_q_vdd_dyn) < abs(res_q_vss_dyn)) else res_q_vss_dyn
    #--eintl=abs(res_q*targetLib.vdd_voltage*targetLib.energy_meas_high_threshold \
    #--          - abs((res_energy_end - res_energy_start)*
    #--          ((abs(res_i_vdd_leak) + abs(res_i_vss_leak))/2)*(targetLib.vdd_voltage*targetLib.energy_meas_high_threshold))))
                

    e_all  = abs(float(res["q_vdd_dyn"])) * h.mls.vdd_voltage
    #e_load = abs(0.5*float(res_q_out_dyn)*targetHarness.mls.energy_meas_high_threshold_voltage) if (float(res_q_out_dyn) > 0) else 0.0; #-- dynamic power of Cload(E=0.5*C*V*V=0.5*Q*V)
    e_load =  float(res["q_out_dyn"])*(h.mls.energy_meas_high_threshold_voltage) if (float(res["q_out_dyn"]) > 0) else 0.0; #-- dynamic power of Cload(E=C*V*V=Q*V)
    
    e_leak = pleak *energy_time
    eintl  = e_all - e_load - e_leak

    #
    rslt["eintl"]=eintl
    rslt["pleak"]=pleak
    rslt["ein"  ]=ein
    rslt["cin"  ]=cin

  #
  return (rslt)



#--------------------------------------------------------------------------------------------------
def runSpiceSetupMultiThread(num:int, mls:Mls, mlc:Mlc, mec:Mec)  -> list[Mcar]:

  ## spice file name
  spicef0 = "vt_"+str(mls.vdd_voltage)+"_"+str(mls.temperature)+"_"+str(mlc.cell)
  spicef1 = f"_{num}" + f"_{mec.meas_type}" + "_oir=" + ''.join(mec.pin_oir) + "_arc=" + ''.join(mec.arc_oir)
  spicef = spicef0 + spicef1
  
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

  index1_slopes_rel  =temp.index_1
  index2_slopes_const=temp.index_2
  
  h_const.template_kind  = kind
  h_const.template       = temp

  if len(index1_slopes_rel)<1:
    print(f"[Error] slope for relateed (index_1) size is 0 for template.")
    my_exit()
    
  if len(index2_slopes_const)<1:
    print(f"[Error] slope for constraint(index_2) size is 0 for template.")
    my_exit()
    
  #------ search delay(trans)
  for index2_slope_const in index2_slopes_const:
    for index1_slope_rel in index1_slopes_rel:
      ##--- result is written in h_delay.dict_list2 with _lock
      thread = threading.Thread(target=runSpiceSetupSingle,
                                kwargs={"poolg_sema":poolg_sema,
                                        "targetHarness":h_const,
                                        "spicef":spicef,
                                        "index1_slope_rel":index1_slope_rel,
                                        "index2_slope_const":index2_slope_const},
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
  mlc.update_max_trans4in(port_name=h_const.target_relport, new_value=max(index1_slopes_rel))

    
  ###################################################################
  return [h_const]

#--------------------------------------------------------------------------------------------------
def runSpiceSetupSingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope_rel:float, index2_slope_const:float):
                      
  # rename
  h=targetHarness
  
  #sim_c2d_max = targetHarness.mls.sim_c2d_max_per_unit * 0.1
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * 0.1, h.mls.sim_c2d_min)
    
  with poolg_sema:

    seg_start  = 0.0
    #seg_end    = (targetHarness.mls.sim_c2d_max + targetHarness.mls.sim_d2c_max + index1_slope_rel + index2_slope_const) * targetHarness.mls.time_mag
    #seg_end    = (sim_c2d_max + h.mls.sim_d2c_max + index1_slope_rel + index2_slope_const) * h.mls.time_mag
    seg_end    = (sim_c2d_max + h.mls.sim_d2c_max + index1_slope_rel + index2_slope_const) * h.mls.time_mag
    tstep_min  = h.mls.sim_segment_timestep_min   * h.mls.time_mag
    ratio      = h.mls.sim_segment_timestep_ratio
    threshold  = h.mls.sim_time_const_threshold * h.mls.time_mag
    
    tsweep_pass=seg_start
    setup_pass =0
    
    tsim_end=1.0E-6
    prop_min=1.0
   
    tstep = h.mls.sim_segment_timestep_start   * h.mls.time_mag
    cnt=0
    while tstep> tstep_min:
      cnt=cnt+1
      
      #-- generate tsweep list
      tsweep_list=np.arange(seg_start, seg_end, tstep)
      #print(f"pass={tsweep_pass}, list={tsweep_list}")
      
      #-- search setup and check trans while prop is valid
      for id,tsweep in enumerate(tsweep_list):

        spicefo  = f"{spicef}_c{index2_slope_const}_r{index1_slope_rel}_s{cnt*100+id}.sp"
        
        rslt=genFileLogic_Setup1x(targetHarness=h, spicef=spicefo, index1_slope_rel=index1_slope_rel, index2_slope_const=index2_slope_const, tsweep=tsweep*-1.0, tsim_end=tsim_end)

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

      #-- update step/list range
      tstep_old=tstep
      tstep    =tstep*ratio

      #seg_start = tsweep_pass - 1.0*tstep_old
      seg_start = tsweep_pass - 2*tstep
      seg_end   = tsweep_pass + 1.0*tstep_old

    #
    #print(f"tstep={tstep}, tsweep={tsweep_pass}, setup/hold={setup_pass}/{hold_pass}")
      
    #-- result in targetHarness
    with h._lock:
      if h.measure_type in ["setup_rising","setup_falling","recovery_rising","recovery_falling"]:
        h.dict_list2["setup_hold" ][index1_slope_rel][index2_slope_const] = setup_pass

      else:
        print(f"[Error] not support measure_type={h.measure_type}")
        my_exit()
      

        
#--------------------------------------------------------------------------------------------------
def genFileLogic_Setup1x(targetHarness:Mcar, spicef:str, index1_slope_rel:float, index2_slope_const:float, tsweep:float, tsim_end:float) -> dict:

  # rename
  h=targetHarness

  # create parameter
  arc_c0 = h.mec.arc_oir[2] if (h.mec.pin_oir[2]=="c0") else h.mec.arc_oir[1] if (h.mec.pin_oir[1]=="c0") else "r" if (h.target_clkport_val=="0") else "f"
  arc_oirc=h.mec.arc_oir + [arc_c0]

  #sim_c2d_max = h.mls.sim_c2d_max_per_unit * 0.1
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * 0.1, h.mls.sim_c2d_min)
  
  # create parameter
  param = Mtp(
    #--model         = model
    #--,netlist      = netlist
    #--,tb_instance  = tb_instance
    #--,temp         = 0.0
    #--,voltage_vsnp =[]
    #--,prop_vth_oirc=[]
    #--,tran_v0_oirc =[]
    #--,tran_v1_oirc =[]
    #--,ener_v0_oirc =[]
    #--,ener_v1_oirc =[]
    #--,arc_oirc     =[]
    #--,val0_oirc    =[]
    cap           = 0.0
    ,clk_role     =h.clk_role
    ,meas_energy  =0      # 0:No Meas for Energy/ 1:Meas Only Time/ 2:Meas all
    ,time_energy  =[0,0]  #[start,end]
    ,meas_o_max_min=0
    ,timestep     =h.mls.simulation_timestep * h.mls.time_mag
    ,tsim_end     =tsim_end
    ,tdelay_init  =1e-9 if h.measure_type=="combinational" else h.mls.sim_d2c_max   * h.mls.time_mag
    ,tpulse_init  =1e-9 if h.measure_type=="combinational" else h.mls.sim_pulse_max * h.mls.time_mag
    #,tdelay_in    =1e-9 if h.measure_type=="combinational" else h.mls.sim_c2d_max   * h.mls.time_mag
    ,tdelay_in    =1e-9 if h.measure_type=="combinational" else sim_c2d_max   * h.mls.time_mag
    ,tslew_in     =index2_slope_const * h.mls.time_mag
    ,tdelay_rel   =h.mls.sim_d2c_max  * h.mls.time_mag
    ,tslew_rel    =index1_slope_rel   * h.mls.time_mag
    ,tpulse_rel   =tsim_end
    ,tsweep_rel   =tsweep
  );

  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  
  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
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
        inline = re.sub('\=',' ',inline)
      
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

  ## spice file name
  spicef0 = "vt_"+str(mls.vdd_voltage)+"_"+str(mls.temperature)+"_"+str(mlc.cell)
  spicef1 = f"_{num}" + f"_{mec.meas_type}" + "_oir=" + ''.join(mec.pin_oir) + "_arc=" + ''.join(mec.arc_oir)
  spicef = spicef0 + spicef1
  
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

  index1_slopes_rel  =temp.index_1
  index2_slopes_const=temp.index_2
  
  h_const.template_kind  = kind
  h_const.template       = temp

  if len(index1_slopes_rel)<1:
    print(f"[Error] slope for relateed (index_1) size is 0 for template.")
    my_exit()
    
  if len(index2_slopes_const)<1:
    print(f"[Error] slope for constraint(index_2) size is 0 for template.")
    my_exit()
    
  #------ search hold
  for index2_slope_const in index2_slopes_const:
    for index1_slope_rel in index1_slopes_rel:
      ##--- result is written in h_delay.dict_list2 with _lock
      thread = threading.Thread(target=runSpiceHoldSingle,
                                kwargs={"poolg_sema":poolg_sema,
                                        "targetHarness":h_const,
                                        "spicef":spicef,
                                        "index1_slope_rel":index1_slope_rel,
                                        "index2_slope_const":index2_slope_const},
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
def runSpiceHoldSingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope_rel:float, index2_slope_const:float):
                      
  # rename
  h=targetHarness
  
  #sim_c2d_max = targetHarness.mls.sim_c2d_max_per_unit * 0.1
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * 0.1, h.mls.sim_c2d_min)
  
  with poolg_sema:
    #seg_start  = -1.0*(targetHarness.mls.sim_c2d_max + targetHarness.mls.sim_d2c_max + index1_slope_rel + index2_slope_const) * targetHarness.mls.time_mag
    #seg_start  = -1.0*(sim_c2d_max + h.mls.sim_d2c_max + index1_slope_rel + index2_slope_const) * targetHarness.mls.time_mag
    seg_start  = -1.0*(sim_c2d_max + h.mls.sim_d2c_max) * h.mls.time_mag
    seg_end    = 0
    tstep_min  = h.mls.sim_segment_timestep_min   * h.mls.time_mag
    ratio      = h.mls.sim_segment_timestep_ratio
    threshold_high  = h.mls.hold_meas_high_threshold * h.mls.vdd_voltage
    threshold_low   = h.mls.hold_meas_low_threshold  * h.mls.vdd_voltage
    ival_o          = h.target_outport_val
    
    tsweep_pass=seg_start
    hold_pass  =0
    
    #tsim_end=1.0E-6
    #tsim_end=h.mls.sim_tsim_end4hold  * h.mls.time_mag
    #----- same as t_in1 + alpha
    tsim_end  = (5*h.mls.simulation_timestep + h.mls.sim_d2c_max + h.mls.sim_pulse_max) * h.mls.time_mag
    tsim_end += (  h.mls.simulation_timestep + 2*sim_c2d_max ) * h.mls.time_mag
    tsim_end += (2 * h.mls.sim_d2c_max + index1_slope_rel) * h.mls.time_mag
   
    tstep = h.mls.sim_segment_timestep_start   * h.mls.time_mag
    cnt=0
    while tstep> tstep_min:
      cnt=cnt+1
      
      #-- generate tsweep list
      tsweep_list=np.arange(seg_start, seg_end, tstep)
      #print(f"pass={tsweep_pass}, list={tsweep_list}")
      
      #-- search hold and check v_
      for id,tsweep in enumerate(tsweep_list):

        spicefo  = f"{spicef}_c{index2_slope_const}_r{index1_slope_rel}_s{cnt*100+id}.sp"
        
        rslt=genFileLogic_Hold1x(targetHarness=h, spicef=spicefo, index1_slope_rel=index1_slope_rel, index2_slope_const=index2_slope_const, tsweep=tsweep*1.0, tsim_end=tsim_end)

        #-- get result
        hold_last =rslt["hold_rel_in"]
        #print(f"min={rslt["o_min_v"]}, max={rslt["o_max_v"]}, hold={hold_last}")
        
        #- check metastable(outport=stable)
        if   (ival_o=="0" ) and (threshold_low < rslt["o_max_v"]):
            break
        elif (ival_o=="1" ) and (threshold_high > rslt["o_min_v"]):
            break
        
        #- keep successfull result
        tsweep_pass=tsweep
        hold_pass  =hold_last

      #-- update step/list range
      tstep_old=tstep
      tstep    =tstep*ratio

      #seg_start = tsweep_pass - 1.0*tstep_old
      seg_start = tsweep_pass - 2*tstep
      seg_end   = tsweep_pass + 1.0*tstep_old

    #
    #print(f"tstep={tstep}, tsweep={tsweep_pass}, setup/hold={setup_pass}/{hold_pass}")
      
    #-- result in targetHarness
    with h._lock:
      if  h.measure_type in ["hold_rising","hold_falling","removal_rising","removal_falling"]:
        h.dict_list2["setup_hold" ][index1_slope_rel][index2_slope_const] = hold_pass
      else:
        print(f"[Error] not support measure_type={h.measure_type}")
        my_exit()
      
    #--
    print(f"  [DEBUG]hold={hold_pass}")
        
#--------------------------------------------------------------------------------------------------
def genFileLogic_Hold1x(targetHarness:Mcar, spicef:str, index1_slope_rel:float, index2_slope_const:float, tsweep:float, tsim_end:float) -> dict:

  # rename
  h=targetHarness

  # create parameter
  arc_c0 = h.mec.arc_oir[2] if (h.mec.pin_oir[2]=="c0") else h.mec.arc_oir[1] if (h.mec.pin_oir[1]=="c0") else "r" if (h.target_clkport_val=="0") else "f"
  arc_oirc=h.mec.arc_oir + [arc_c0]
  
  #sim_c2d_max = h.mls.sim_c2d_max_per_unit * 0.1
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * 0.1, h.mls.sim_c2d_min)
  
  # create parameter
  param = Mtp(
    #--model         = model
    #--,netlist      = netlist
    #--,tb_instance  = tb_instance
    #--,temp         = 0.0
    #--,voltage_vsnp =[]
    #--,prop_vth_oirc=[]
    #--,tran_v0_oirc =[]
    #--,tran_v1_oirc =[]
    #--,ener_v0_oirc =[]
    #--,ener_v1_oirc =[]
    #--,arc_oirc     =[]
    #--,val0_oirc    =[]
    cap           = 0.0
    ,clk_role     =h.clk_role
    ,meas_energy  =0      # 0:No Meas for Energy/ 1:Meas Only Time/ 2:Meas all
    ,time_energy  =[0,0]  #[start,end]
    ,meas_o_max_min=1
    ,timestep     =h.mls.simulation_timestep * h.mls.time_mag
    ,tsim_end     =tsim_end
    ,tdelay_init  =h.mls.sim_d2c_max   * h.mls.time_mag
    ,tpulse_init  =h.mls.sim_pulse_max * h.mls.time_mag
    #,tdelay_in    =2*h.mls.sim_c2d_max   * h.mls.time_mag
    ,tdelay_in    =2*sim_c2d_max   * h.mls.time_mag
    ,tslew_in     =index2_slope_const * h.mls.time_mag
    ,tdelay_rel   =h.mls.sim_d2c_max  * h.mls.time_mag
    ,tslew_rel    =index1_slope_rel   * h.mls.time_mag
    ,tpulse_rel   =tsim_end
    ,tsweep_rel   =tsweep
  );

  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  
  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
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
        inline = re.sub('\=',' ',inline)
      
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

  ## spice file name
  spicef0 = "vt_"+str(mls.vdd_voltage)+"_"+str(mls.temperature)+"_"+str(mlc.cell)
  spicef1 =  f"_{num}" + f"_{mec.meas_type}" + "_oir=" + ''.join(mec.pin_oir) + "_arc=" + ''.join(mec.arc_oir)
  spicef = spicef0 + spicef1
  
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

  index1_slopes_in=temp.index_1
  index2_unuse =temp.index_2

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

  h_passive.set_lut(value_name="eintl")
  h_passive.set_lut(value_name="ein")

  #------ update max_trans_in
  mlc.update_max_trans4in(port_name=h_passive.target_inport, new_value=max(index1_slopes_in))

  #--- generate lut table
  h_passive.set_lut(value_name="eintl")
  h_passive.set_lut(value_name="ein")
  
  ###################################################################
  return [h_passive]


#--------------------------------------------------------------------------------------------------
def runSpicePassiveSingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope_in:float):
                      
  with poolg_sema:
    
    spicefoe = f"{spicef}_i{index1_slope_in}_energy.sp"
        
    ## extract energy_start and energy_end
    rslt=genFileLogic_PassiveTrial1x(targetHarness=targetHarness, spicef=spicefoe, index1_slope_in=index1_slope_in)

    #
    with targetHarness._lock:
      targetHarness.dict_list2["eintl"][index1_slope_in][0]=rslt["eintl"]
      targetHarness.dict_list2["ein"  ][index1_slope_in][0]=rslt["ein"]
      targetHarness.dict_list2["cin"  ][index1_slope_in][0]=rslt["cin"]
      targetHarness.dict_list2["pleak"][index1_slope_in][0]=rslt["pleak"]


    
#--------------------------------------------------------------------------------------------------
def genFileLogic_PassiveTrial1x(targetHarness:Mcar, spicef:str, index1_slope_in:float):

  # rename
  h=targetHarness

  # create parameter
  arc_oirc=h.mec.arc_oir + ["n"]
  
  #sim_c2d_max = h.mls.sim_c2d_max_per_unit * 0.1
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * 0.1, h.mls.sim_c2d_min)

  #esatrt=_t0/ eend=t1
  #estart  = (5 * h.mls.simulation_timestep + h.mls.sim_d2c_max +h.mls.sim_pulse_max+ h.mls.sim_c2d_max)* h.mls.time_mag  
  estart  = (5 * h.mls.simulation_timestep + h.mls.sim_d2c_max +h.mls.sim_pulse_max+ sim_c2d_max)* h.mls.time_mag
  eend    = estart + (index1_slope_in * h.mls.time_mag)
  tsim_end= eend + 1e-9 

  
  param = Mtp(
    #model         = model
    #,netlist      = netlist
    #,tb_instance  = tb_instance
    #--,temp         = 
    #--,voltage_vsnp =[]
    #--,prop_vth_oirc=[]
    #--,tran_v0_oirc =[]
    #--,tran_v1_oirc =[]
    #--,ener_v0_oirc =[]
    #--,ener_v1_oirc =[]
    #--,arc_oirc     =[]
    #--,val0_oirc    =[]
     cap          =0.0
    ,clk_role     =h.clk_role
    ,meas_energy  =2
    ,time_energy  =[estart,eend]  
    ,meas_o_max_min=0
    ,timestep     =h.mls.simulation_timestep * h.mls.time_mag
    ,tsim_end     =tsim_end
    ,tdelay_init  =1e-9 if h.measure_type=="combinational" else h.mls.sim_d2c_max   * h.mls.time_mag
    ,tpulse_init  =1e-9 if h.measure_type=="combinational" else h.mls.sim_pulse_max * h.mls.time_mag
    #,tdelay_in    =1e-9 if h.measure_type=="combinational" else h.mls.sim_c2d_max   * h.mls.time_mag
    ,tdelay_in    =1e-9 if h.measure_type=="combinational" else sim_c2d_max   * h.mls.time_mag
    ,tslew_in     =index1_slope_in       * h.mls.time_mag
    ,tdelay_rel   =h.mls.sim_prop_max    * h.mls.time_mag
    ,tslew_rel    =index1_slope_in       * h.mls.time_mag
    ,tpulse_rel   =tsim_end
    ,tsweep_rel   =0.0
  );

  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  
  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
  print(f"  [INFO] generate tb={spicef}")
  
  #-- execute spice
  spicelis=h.mls.exec_spice(spicef=spicef)
                              
  #-- read result
  # read .mt0 for Xyce
  if(re.search("Xyce", h.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  #-- parse results
  res=dict()
  res_list=["q_rel_dyn","q_in_dyn","q_vdd_dyn","i_vdd_leak"]
  with open(spicelis,'r') as f:
    
    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub('\=',' ',inline)
      
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
    
  # result
  rslt={
    ## pleak
    "pleak": abs(float(res["i_vdd_leak"])) * h.mls.vdd_voltage,
    ## input energy
    "ein"  : abs(float(res["q_in_dyn"])) * h.mls.vdd_voltage,
    ## Cin = Qin / V
    "cin"  : abs(float(res["q_in_dyn"]))/h.mls.vdd_voltage,
    ## intl. energy calculation
    "eintl": abs(float(res["q_vdd_dyn"])) * h.mls.vdd_voltage
  }
  
  return (rslt)


#--------------------------------------------------------------------------------------------------
def runSpiceMinPulseMultiThread(num:int, mls:Mls, mlc:Mlc, mec:Mec)  -> list[Mcar]:

  ## spice file name
  spicef0 = "vt_"+str(mls.vdd_voltage)+"_"+str(mls.temperature)+"_"+str(mlc.cell)
  spicef1 =  f"_{num}" + f"_{mec.meas_type}" + "_oir=" + ''.join(mec.pin_oir) + "_arc=" + ''.join(mec.arc_oir)
  spicef = spicef0 + spicef1
  
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
  
  with poolg_sema:
    seg_start  = targetHarness.mls.sim_pulse_max              * targetHarness.mls.time_mag
    seg_end    = 0.0
    tstep_min  = targetHarness.mls.sim_segment_timestep_min   * targetHarness.mls.time_mag
    ratio      = targetHarness.mls.sim_segment_timestep_ratio
    threshold  = targetHarness.mls.sim_time_const_threshold   * targetHarness.mls.time_mag

    tsweep_pass=seg_start
    pulse_pass =seg_start
    prop_min   =1.0
    
    tsim_end   =1.0E-6
    pulse_width=seg_start
   
    tstep = targetHarness.mls.sim_segment_timestep_start   * targetHarness.mls.time_mag
    cnt=0
    while tstep> tstep_min:
      cnt=cnt+1
      
      #-- generate tsweep list
      tsweep_list=np.arange(seg_start, seg_end, -1.0*tstep)
      tsweep_list=np.append(tsweep_list, 0.0)
      #print(f"pass={tsweep_pass}, start={seg_start}, end={seg_end}, list={tsweep_list}")
      
      #-- search setup and check trans while prop is valid
      for id,tsweep in enumerate(tsweep_list):

        spicefo  = f"{spicef}_s{cnt*100+id}.sp"
        
        rslt=genFileLogic_MinPulse1x(targetHarness=targetHarness, spicef=spicefo, tpulse_rel=tsweep, tsim_end=tsim_end)

        #- check prop_in_out
        prop_last=abs(rslt["prop_in_out"])
        prop_min=min(prop_min, prop_last)
        
        #- check metastable
        if prop_last > prop_min + threshold:
          break;

        #- keep successfull result
        tsweep_pass=tsweep
        tsim_end   =rslt["chg_out"] + 10e-9
        pulse_pass =rslt["pulse"]

      #-- update step/list range
      tstep_old=tstep
      tstep    =tstep*ratio

      seg_start = tsweep_pass + 2*tstep
      #seg_end   = tsweep_pass + 1.0*tstep_old

    #
    #print(f"tstep={tstep}, tsweep={tsweep_pass}, setup/hold={setup_pass}/{hold_pass}")
      
    #-- result in targetHarness
    with targetHarness._lock:
      targetHarness.min_pulse_width = pulse_pass

        
#--------------------------------------------------------------------------------------------------
def genFileLogic_MinPulse1x(targetHarness:Mcar, spicef:str, tpulse_rel:float, tsim_end:float) -> dict:

  # rename
  h=targetHarness

  # create parameter
  arc_c0 = h.mec.arc_oir[2] if (h.mec.pin_oir[2]=="c0") else h.mec.arc_oir[1] if (h.mec.pin_oir[1]=="c0") else "r" if (h.target_clkport_val=="0") else "f"
  arc_oirc=h.mec.arc_oir + [arc_c0]

  #sim_c2d_max = h.mls.sim_c2d_max_per_unit * 0.1
  sim_c2d_max = max(h.mls.sim_c2d_max_per_unit * 0.1, h.mls.sim_c2d_min)
  
  # create parameter
  tslew = 5*h.mls.simulation_timestep * h.mls.time_mag
  
  param = Mtp(
    #--model         = model
    #--,netlist      = netlist
    #--,tb_instance  = tb_instance
    #--,temp         = 0.0
    #--,voltage_vsnp =[]
    #--,prop_vth_oirc=[]
    #--,tran_v0_oirc =[]
    #--,tran_v1_oirc =[]
    #--,ener_v0_oirc =[]
    #--,ener_v1_oirc =[]
    #--,arc_oirc     =[]
    #--,val0_oirc    =[]
    cap           = 0.0
    ,clk_role     =h.clk_role
    ,meas_energy  =0      # 0:No Meas for Energy/ 1:Meas Only Time/ 2:Meas all
    ,time_energy  =[0,0]  #[start,end]
    ,meas_o_max_min=0
    ,timestep     =h.mls.simulation_timestep * h.mls.time_mag
    ,tsim_end     =tsim_end
    ,tdelay_init  =1e-9 if h.measure_type=="combinational" else h.mls.sim_d2c_max   * h.mls.time_mag
    ,tpulse_init  =1e-9 if h.measure_type=="combinational" else h.mls.sim_pulse_max * h.mls.time_mag
    #,tdelay_in    =1e-9 if h.measure_type=="combinational" else h.mls.sim_c2d_max   * h.mls.time_mag
    ,tdelay_in    =1e-9 if h.measure_type=="combinational" else sim_c2d_max   * h.mls.time_mag
    ,tslew_in     =tslew
    ,tdelay_rel   =  h.mls.sim_d2c_max         * h.mls.time_mag
    ,tslew_rel    =tslew
    ,tpulse_rel   =tpulse_rel
    ,tsweep_rel   =0.0
  );

  param.set_common_value(harness=h, arc_oirc=arc_oirc)
  
  #-- generate testbench
  rendered = tb_template.render(param=param)
  with open(spicef, 'w') as f:
    f.write(rendered)
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
        inline = re.sub('\=',' ',inline)
      
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
    "pulse"        :tslew + tpulse_rel}

  return (rslt)

