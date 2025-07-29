import argparse, re, os, shutil, subprocess, sys, inspect, threading 
import copy

from myConditionsAndResults import MyConditionsAndResults  as Mcar
from myLibrarySetting       import MyLibrarySetting        as Mls 
from myLogicCell            import MyLogicCell             as Mlc
from myExpectLogic          import MyExpectLogic           as Mel
from myTbParam              import MyTbParam               as Mtp
import myExport                                            as Me

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
def runExpectation(targetLib:Mls, targetCell:Mlc, expectationdictList:List[Mel]):
  harnessList = []

  size=len(expectationdictList)
  for ii in range(size):
    expectationdict = expectationdictList[ii]
    
    ## spice simulation
    timing_type=expectationdict.tmg_type

    if   timing_type in ["combinational","preset","clear","rising_edge","falling_edge"]:
      rslt_Harness = runSpiceDelayPowerMultiThread(num=ii, mls=targetLib, mlc=targetCell, mel=expectationdict)
      
    elif timing_type in ["setup_rising","setup_falling","removal_rising", "removal_falling"]:
      rslt_Harness = runSpiceSetupPassiveMultiThread(num=ii, mls=targetLib, mlc=targetCell, mel=expectationdict)
      
    elif timing_type in ["hold_rising","hold_falling"]:
      rslt_Harness = runSpiceHoldPassiveMultiThread(num=ii, mls=targetLib, mlc=targetCell, mel=expectationdict)
      
    elif timing_type in ["recovery_rising","recovery_falling"]:
      rslt_Harness = runSpiceRecoveryPassiveMultiThread(num=ii, mls=targetLib, mlc=targetCell, mel=expectationdict)
      
    else:
      print(f"[Error] not support timing_type={timing_type}.")
      my_exit()
      
    ## add result
    #harnessList.append(tmp_Harness)
    harnessList.extend(rslt_Harness)

  
  ## average cin of each harness
  targetCell.set_cin_avg(harnessList=harnessList) 

  ## max pleak in each input condition
  targetCell.set_pleak_icrs(harnessList=harnessList) 

  ## average pleak of each harness & cell 
  targetCell.set_pleak_cell()
  
  #return harnessList2
  return harnessList

#--------------------------------------------------------------------------------------------------
def runSpiceDelayPowerMultiThread(num:int, mls:Mls, mlc:Mlc, mel:Mel)  -> list[Mcar]:

  ## spice file name
  spicef0 = "vt_"+str(mls.vdd_voltage)+"_"+str(mls.temperature)+"_"+str(mlc.cell)
  spicef1 =f"_{num}" + f"typ_{mel.tmg_type}" + "_oir=" + ''.join(mel.pin_oir) + "_arc=" + ''.join(mel.arc_oir)
  spicef = spicef0 + spicef1
  
  # Limit number of threads
  # define semaphore 
  poolg_sema = threading.BoundedSemaphore(mls.num_thread)
  print("Num threads for simulation:"+str(mls.num_thread))

  ###################################################################
  #-- for delay
  thread_id = 0
  threadlist = list()

  h_delay = Mcar(mls=mls, mlc=mlc, mel=mel)
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
                                        "targetharness":h_delay,
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

  h_power = Mcar(mls=mls, mlc=mlc, mel=mel)
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
                                        "targetharness":h_delay,
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

    ## -- hold result in targetHarness
    with targetHarness._lock:
      targetharness.dict_list2["prop" ][index2_load][index1_slope] = rslt["prop"]
      targetharness.dict_list2["trans"][index2_load][index1_slope] = rslt["trans"]

    
#--------------------------------------------------------------------------------------------------
def genFileLogic_DelayTrial1x(targetHarness:Mcar, spicef:str, index1_slope:float, index2_load:float) ->dict:

  # rename
  h=targetHarness

  # create parameter
  arc_c0 = h.mel.arc_oir[2] if (h.mel.pin_oir[2]=="c0") else h.mel.arc_oir[1] if (h.mel.pin_oir[1]=="c0") else "r" if (h.target_clkport_val=="0") else "f"
  arc_oirc=h.mel.arc_oir+[arc_c0]
  tsim_end=1e-6

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
    ,timestep     = h.mls.simulation_timestep * h.mls.time_mag
    ,tsim_end     = tsim_end
    ,tdelay_init  = 1e-9 if h.timing_type=="combinational" else h.mls.sim_d2c_max   * h.mls.time_mag
    ,tpulse_init  = 1e-9 if h.timing_type=="combinational" else h.mls.sim_pulse_max * h.mls.time_mag
    ,tdelay_in    = 1e-9 if h.timing_type=="combinational" else h.mls.sim_c2d_max   * h.mls.time_mag
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
  with open(spicelis,'r') as f:
    
    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub('\=',' ',inline)
      
      # search measure
      res=dict()
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
                             

#--------------------------------------------------------------------------------------------------
def genFileLogic_PowerTrial1x(targetHarness:Mcar, spicef:str, meas_energy:int, index1_slope:float, index2_load:float, estart:float, eend:float):

  # rename
  h=targetHarness

  # create parameter
  arc_c0 = h.mel.arc_oir[2] if (h.mel.pin_oir[2]=="c0") else h.mel.arc_oir[1] if (h.mel.pin_oir[1]=="c0") else "r" if (h.target_clkport_val=="0") else "f"
  arc_oirc=h.mel.arc_oir+[arc_c0]

  tsim_end=1e-6 if meas_energy == 0 else eend + 1e-9
  
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
    ,timestep     = h.mls.simulation_timestep * h.mls.time_mag
    ,tsim_end     = tsim_end
    ,tdelay_init  = 1e-9 if h.timing_type=="combinational" else h.mls.sim_d2c_max   * h.mls.time_mag
    ,tpulse_init  = 1e-9 if h.timing_type=="combinational" else h.mls.sim_pulse_max * h.mls.time_mag
    ,tdelay_in    = 1e-9 if h.timing_type=="combinational" else h.mls.sim_c2d_max   * h.mls.time_mag
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

  #-- parse results
  res_list=["energy_start","energy_end"]
  if(meas_energy == 2):
    res_list.append(["q_in_dyn","q_rel_dyn","q_clk_dyn","q_out_dyn","q_vdd_dyn","i_vdd_leak","i_in_leak","i_rel_leak","i_clk_leak"])
    
  with open(spicelis,'r') as f:
    for inline in f:
      if(re.search("hspice", h.mls.simulator)):
        inline = re.sub('\=',' ',inline)
      
      # search measure
      res=dict()
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

    
    ## Pleak = average of Pleak_vdd and Pleak_vss
    ## P = I * V
    #pleak= (((abs(res_i_vdd_leak])+abs(res_i_vss_leak))/2)*(targetLib.vdd_voltage))
    pleak=abs(float(res_i_vdd_leak)) * h.mls.vdd_voltage
    
    ## input energy
    ein = abs(float(res_q_in_dyn)) * h.mls.vdd_voltage

    ## Cin = Qin / V
    cin = abs(float(res_q_in_dyn))/(h.mls.vdd_voltage)
    
    ## intl. energy calculation
    ## intl. energy is the sum of short-circuit energy and drain-diffusion charge/discharge energy
    ## larger Ql: intl. Q, load Q 
    ## smaller Qs: intl. Q
    ## Eintl = QsV
    #--res_q = res_q_vdd_dyn if(abs(res_q_vdd_dyn) < abs(res_q_vss_dyn)) else res_q_vss_dyn
    #--eintl=abs(res_q*targetLib.vdd_voltage*targetLib.energy_meas_high_threshold \
    #--          - abs((res_energy_end - res_energy_start)*
    #--          ((abs(res_i_vdd_leak) + abs(res_i_vss_leak))/2)*(targetLib.vdd_voltage*targetLib.energy_meas_high_threshold))))
                

    e_all  = abs(float(res_q_vdd_dyn)) * h.mls.vdd_voltage
    #e_load = abs(0.5*float(res_q_out_dyn)*targetHarness.mls.energy_meas_high_threshold_voltage) if (float(res_q_out_dyn) > 0) else 0.0; #-- dynamic power of Cload(E=0.5*C*V*V=0.5*Q*V)
    e_load =  float(res_q_out_dyn)*(h.mls.energy_meas_high_threshold_voltage) if (float(res_q_out_dyn) > 0) else 0.0; #-- dynamic power of Cload(E=C*V*V=Q*V)
    
    e_leak = pleak *energy_time
    eintl  = e_all - e_load - e_leak

    #
    rslt["eintl"]=eintl
    rslt["ein"  ]=ein
    rslt["cin"  ]=cin
    rslt["pleak"]=pleak

  #
  return (rslt)



#--------------------------------------------------------------------------------------------------
def runSpiceSetupPassiveMultiThread(num:int, mls:Mls, mlc:Mlc, mel:Mel)  -> list[Mcar]:

  ## spice file name
  spicef0 = "vt_"+str(mls.vdd_voltage)+"_"+str(mls.temperature)+"_"+str(mlc.cell)
  spicef1 =f"_{num}" + f"typ_{mel.tmg_type}" + "_oir=" + ''.join(mel.pin_oir) + "_arc=" + ''.join(mel.arc_oir)
  spicef = spicef0 + spicef1
  
  # Limit number of threads
  # define semaphore 
  poolg_sema = threading.BoundedSemaphore(mls.num_thread)
  print("Num threads for simulation:"+str(mls.num_thread))

  ###################################################################
  #-- for setup
  thread_id = 0
  threadlist = list()

  h_const = Mcar(mls=mls, mlc=mlc, mel=mel)
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
  if h_const.timing_type in ["setup_rising","setup_falling"]:
    h_const.set_lut(value_name="setup")
  else:
    h_const.set_lut(value_name="removal")

  
  ###################################################################
  #-- for passive
  thread_id = 0
  threadlist = list() 

  h_passive = Mcar(mls=mls, mlc=mlc, mel=mel)
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
                              args=([poolg_sema, h_passive, spicef, index1_slope_rel]),
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

  
  ###################################################################
  return [h_const, h_passive]


#--------------------------------------------------------------------------------------------------
def runSpiceSetupSingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope_rel:float, index2_slope_const:float):
                      
  with poolg_sema:
    seg_start  = 0.0
    seg_end    = (targetHarness.mls.sim_c2d_max + targetHarness.mls.sim_d2c_max + index1_slope_rel + index2_slope_const) * targetHarness.mls.time_mag
    tstep_min  = targetHarness.mls.sim_segment_timestep_min   * targetHarness.mls.time_mag
    ratio      = targetHarness.mls.sim_segment_timestep_ratio
    threshold  = targetHarness.mls.sim_time_const_threshold * targetHarness.mls.time_mag
    
    tsweep_pass=seg_start
    setup_pass =0
    hold_pass  =0
    
    tsim_end=1.0E-6
    prop_min=1.0
   
    tstep = targetHarness.mls.sim_segment_timestep_start   * targetHarness.mls.time_mag
    cnt=0
    while tstep> tstep_min:
      cnt=cnt+1
      
      #-- generate tsweep list
      tsweep_list=np.arange(seg_start, seg_end, tstep)
      #print(f"pass={tsweep_pass}, list={tsweep_list}")
      
      #-- search setup and check trans while prop is valid
      for id,tsweep in enumerate(tsweep_list):

        spicefo  = f"{spicef}_c{index2_slope_const}_r{index1_slope_rel}_s{cnt*100+id}.sp"
        
        rslt=genFileLogic_Setup1x(targetHarness=targetHarness, spicef=spicefo, index1_slope_rel=index1_slope_rel, index2_slope_const=index2_slope_const, tsweep=tsweep*-1.0, tsim_end=tsim_end)

        #- check prop_in_out
        prop_last=abs(rslt["prop_in_out"])
        setup_last=rslt["setup_in_rel"]
        hold_last =rslt["hold_rel_in"]

        prop_min=min(prop_min, prop_last)
        
        #- check metastable
        if prop_last > prop_min + threshold:
          break;

        #- keep successfull result
        
        tsim_end=rslt["chg_out"] + 10e-9
        tsweep_pass=tsweep
        setup_pass =setup_last
        hold_pass  =hold_last

      #-- update step/list range
      tstep_old=tstep
      tstep    =tstep*ratio

      #seg_start = tsweep_pass - 1.0*tstep_old
      seg_start = tsweep_pass - 2*tstep
      seg_end   = tsweep_pass + 1.0*tstep_old

    #
    #print(f"tstep={tstep}, tsweep={tsweep_pass}, setup/hold={setup_pass}/{hold_pass}")
      
    #-- hold result in targetHarness
    with targetHarness._lock:
      if targetHarness.timing_type in ["setup_rising","setup_falling"]:
        targetHarness.dict_list2["setup" ][index2_slope_const][index1_slope_rel] = setup_pass
      
      elif targetHarness.timing_type in ["removal_rising","removal_falling"]:
        targetHarness.dict_list2["removal" ][index2_slope_const][index1_slope_rel] = hold_pass

      else:
        print(f"[Error] not support timing_type={targetHarness.timing_type}")
        my_exit()
      

        
#--------------------------------------------------------------------------------------------------
def genFileLogic_Setup1x(targetHarness:Mcar, spicef:str, index1_slope_rel:float, index2_slope_const:float, tsweep:float, tsim_end:float) -> dict:

  # rename
  h=targetHarness

  # create parameter
  tb_instance      = h.gen_instance_for_tb()
  model  =h.mlc.model   if h.mlc.model.startswith("/")   else "../" + h.mlc.model
  netlist=h.mlc.netlist if h.mlc.netlist.startswith("/") else "../" + h.mlc.netlist

  #-- create clock info
  arc_c0 = h.mel.arc_oir[2] if (h.mel.pin_oir[2]=="c0") else h.mel.arc_oir[1] if (h.mel.pin_oir[1]=="c0") else "r" if (h.target_clkport_val=="0") else "f"
  arc_oirc=h.mel.arc_oir + [arc_c0]
  
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
    ,timestep     =h.mls.simulation_timestep * h.mls.time_mag
    ,tsim_end     =tsim_end
    ,tdelay_init  =1e-9 if h.timing_type=="combinational" else h.mls.sim_d2c_max   * h.mls.time_mag
    ,tpulse_init  =1e-9 if h.timing_type=="combinational" else h.mls.sim_pulse_max * h.mls.time_mag
    ,tdelay_in    =1e-9 if h.timing_type=="combinational" else h.mls.sim_c2d_max   * h.mls.time_mag
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
    "setup_in_rel" :float(res["setup_in_rel"]),
    "hold_rel_in"  :float(res["hold_rel_in"]),
    "prop_in_out"  :float(res["prop_in_out"])}

  return (rslt)


#--------------------------------------------------------------------------------------------------
def runSpicePassiveSingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope_in:float):
                      
  with poolg_sema:
    
    spicefoe = f"{spicef}_c{index1_slope_in}_energy.sp"
        
    ## extract energy_start and energy_end
    rslt=genFileLogic_PassiveTrial1x(targetHarness=targetHarness, spicef=spicefoe, index1_slope_in=index1_slope_in)

    #
    with targetHarness._lock:
      targetHarness.dict_list2["eintl"][0][index1_slope_in]=rslt["eintl"]
      targetHarness.dict_list2["ein"  ][0][index1_slope_in]=rslt["ein"]
      targetHarness.dict_list2["cin"  ][0][index1_slope_in]=rslt["cin"]
      targetHarness.dict_list2["pleak"][0][index1_slope_in]=rslt["pleak"]


    
#--------------------------------------------------------------------------------------------------
def genFileLogic_PassiveTrial1x(targetHarness:Mcar, spicef:str, index1_slope_in:float):

  # rename
  h=targetHarness

  # create parameter
  arc_oirc=h.mel.arc_oir + ["n"]

  #esatrt=_t0/ eend=t1
  estart  = (5 * h.mls.simulation_timestep + h.mls.sim_d2c_max +h.mls.sim_pulse_max+ h.mls.sim_c2d_max)* h.mls.time_mag
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
    ,timestep     =h.mls.simulation_timestep * h.mls.time_mag
    ,tsim_end     =tsim_end
    ,tdelay_init  =1e-9 if h.timing_type=="combinational" else h.mls.sim_d2c_max   * h.mls.time_mag
    ,tpulse_init  =1e-9 if h.timing_type=="combinational" else h.mls.sim_pulse_max * h.mls.time_mag
    ,tdelay_in    =1e-9 if h.timing_type=="combinational" else h.mls.sim_c2d_max   * h.mls.time_mag
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
    
  # hold resul
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


