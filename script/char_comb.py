import argparse, re, os, shutil, subprocess, sys, inspect, threading 
import copy

from myConditionsAndResults import MyConditionsAndResults  as Mcar
from myLibrarySetting       import MyLibrarySetting        as Mls 
from myLogicCell            import MyLogicCell             as Mlc
from myExpectLogic          import MyExpectLogic           as Mel
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
tb_template_comb_delay  = env.get_template('./template/temp_comb_delay.sp.j2')
tb_template_comb_energy = env.get_template('./template/temp_comb_energy.sp.j2')

@dataclass
class ParamTbCombDelay:    #-- used for temp_comb_delay
  
  model      :str
  netlist    :str
  temp       :float
  vdd_voltage:float
  vss_voltage:float
  vnw_voltage:float
  vpw_voltage:float
  cap        :float
  slew       :float
  simulation_timestep    :float
  tstart_pre :float
  tend_after :float
  tb_instance:str
  relport_val0    :str
  outport_val0    :str
  relport_arc     :str
  outport_arc     :str
  relport_prop_vth:str
  outport_prop_vth:str
  relport_tran_v0 :str
  relport_tran_v1 :str
  outport_tran_v0 :str
  outport_tran_v1 :str

@dataclass
class ParamTbCombEnergy:    #-- used for temp_comb_energy
  
  model      :str
  netlist    :str
  temp       :float
  vdd_voltage:float
  vss_voltage:float
  vnw_voltage:float
  vpw_voltage:float
  cap        :float
  slew       :float
  simulation_timestep    :float
  tstart_pre :float
  tend_after :float
  tb_instance:str
  relport_val0    :str
  outport_val0    :str
  relport_arc     :str
  outport_arc     :str
  relport_prop_vth:str
  outport_prop_vth:str
  relport_tran_v0 :str
  relport_tran_v1 :str
  outport_tran_v0 :str
  outport_tran_v1 :str
  relport_ener_v0 :str
  relport_ener_v1 :str
  outport_ener_v0 :str
  outport_ener_v1 :str
  meas_energy     :int
  energy_start    :float
  energy_end      :float


  
def runCombInNOut1(targetLib:Mls, targetCell:Mlc, expectationdictList:List[Mel]):
  harnessList = []

  size=len(expectationdictList)
  for ii in range(size):
    expectationdict = expectationdictList[ii]
    
    
    ## spice simulation
    #rslt_Harness = runSpiceCombMultiThread(tmp_Harness, spicef)
    rslt_Harness = runSpiceCombMultiThread(num=ii, mls=targetLib, mlc=targetCell, mel=expectationdict)
    
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

#def runSpiceCombMultiThread(targetHarness:Mcar, spicef:str)  -> list[Mcar]:
def runSpiceCombMultiThread(num:int, mls:Mls, mlc:Mlc, mel:Mel)  -> list[Mcar]:

  ## spice file name
  spicef0 = "vt_"+str(mls.vdd_voltage)+"_"+str(mls.temperature)+"_"+"delay1_"+str(mlc.cell)
  spicef1 =f"_{num}" + "_otr=" + ''.join(mel.pin_otr) + "_typ=" + mel.tmg_type + "_arc=" + ''.join(mel.arc_otr)
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
  h_delay.template_timing  = temp

  if len(index2_loads)<1:
    print(f"[Error] load size is 0 for template_{kind}.")
    my_exit()
    
  if len(index1_slopes)<1:
    print(f"[Error] slope size is 0 for template_{kind}.")
    my_exit()
    
  #------ search delay(trans)
  for index2_load in index2_loads:
    for index1_slope in index1_slopes:
      ##--- result is written in h_delay.dict_list2 with _lock
      thread = threading.Thread(target=runSpiceCombDelaySingle,
                                args=([poolg_sema, h_delay, spicef, index1_slope, index2_load]),
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

  h_power.template_energy  = temp
  
  if len(index2_loads)<1:
    print(f"[Error] load size is 0 for template_{kind}.")
    my_exit()
    
  if len(index1_slopes)<1:
    print(f"[Error] slope size is 0 for template_{kind}.")
    my_exit()
    
  #------ energy
  for index2_load in index2_loads:
    for index1_slope in index1_slopes:
      thread = threading.Thread(target=runSpiceCombEnergySingle,
                                args=([poolg_sema, h_power, spicef, index1_slope, index2_load]),
                                name="%d" % thread_id)
      
      threadlist.append(thread)
      thread_id += 1

  for thread in threadlist:
    thread.start() 

  for thread in threadlist:
    thread.join() 

  h_power.set_lut(value_name="eintl")
  h_power.set_lut(value_name="ein")

  #h_power.set_average(value_name="cin")
  #h_power.set_average(value_name="pleak")

  #------ update max_load/max_trans
  mlc.update_max_load4out(port_name=h_delay.target_outport, new_value=max(index2_loads))
  mlc.update_max_trans4in(port_name=h_delay.target_relport, new_value=max(index1_slopes))

  
  ###################################################################
  return [h_delay, h_power]
  
def runSpiceCombDelaySingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope:float, index2_load:float):
                      
  with poolg_sema:
    spicefo  = str(spicef)+"_"+str(index2_load)+"_"+str(index1_slope)+".sp"
    spicefoe = str(spicef)+"_"+str(index2_load)+"_"+str(index1_slope)+"_energy.sp"
 
    ## 1st trial
    genFileLogic_CombDelayTrial1x(targetHarness=targetHarness, index2_load=index2_load, index1_slope=index1_slope, spicef=spicefo)
                             
def genFileLogic_CombDelayTrial1x(targetHarness:Mcar, spicef:str, index2_load:float, index1_slope:float):

  spicelis = spicef
  spicelis += ".lis"
  
  targetHarness.mls.print_msg("generate file: "+str(spicef))
  
  tb_instance      = targetHarness.gen_instance_for_tb()

  model  =targetHarness.mlc.model   if targetHarness.mlc.model.startswith("/")   else "../" + targetHarness.mlc.model
  netlist=targetHarness.mlc.netlist if targetHarness.mlc.netlist.startswith("/") else "../" + targetHarness.mlc.netlist
  
  param = ParamTbCombDelay(
      model       = model
      ,netlist    = netlist
      ,temp       = targetHarness.mls.temperature
      ,vdd_voltage= targetHarness.mls.vdd_voltage
      ,vss_voltage= targetHarness.mls.vss_voltage
      ,vnw_voltage= targetHarness.mls.nwell_voltage
      ,vpw_voltage= targetHarness.mls.pwell_voltage
      ,cap        = index2_load  * targetHarness.mls.capacitance_mag
      ,slew       = index1_slope * targetHarness.mls.time_mag
      ,simulation_timestep         = targetHarness.mls.simulation_timestep * targetHarness.mls.time_mag
      ,tstart_pre                  = targetHarness.mls.sim_prop_max * targetHarness.mls.time_mag
      #,tend_after                  = targetHarness.mls.sim_prop_max * targetHarness.mls.time_mag
      ,tend_after                  = targetHarness.mls.sim_prop_max * targetHarness.mls.time_mag * targetHarness.mls.sim_time_end_extent
      ,tb_instance                 = tb_instance
      ,relport_val0                = targetHarness.target_relport_val[0]
      ,outport_val0                = targetHarness.target_outport_val[0]
      ,relport_arc                 = "rise" if targetHarness.mel.arc_otr[2]=="r" else "fall"
      ,outport_arc                 = "rise" if targetHarness.mel.arc_otr[0]=="r" else "fall"
      ,relport_prop_vth            = targetHarness.mls.logic_low_to_high_threshold_voltage if targetHarness.mel.arc_otr[2]=="r" else targetHarness.mls.logic_high_to_low_threshold_voltage 
      ,outport_prop_vth            = targetHarness.mls.logic_low_to_high_threshold_voltage if targetHarness.mel.arc_otr[0]=="r" else targetHarness.mls.logic_high_to_low_threshold_voltage 
      ,relport_tran_v0             = targetHarness.mls.logic_threshold_low_voltage  if targetHarness.mel.arc_otr[2]=="r" else targetHarness.mls.logic_threshold_high_voltage
      ,relport_tran_v1             = targetHarness.mls.logic_threshold_high_voltage if targetHarness.mel.arc_otr[2]=="r" else targetHarness.mls.logic_threshold_low_voltage 
      ,outport_tran_v0             = targetHarness.mls.logic_threshold_low_voltage  if targetHarness.mel.arc_otr[0]=="r" else targetHarness.mls.logic_threshold_high_voltage
      ,outport_tran_v1             = targetHarness.mls.logic_threshold_high_voltage if targetHarness.mel.arc_otr[0]=="r" else targetHarness.mls.logic_threshold_low_voltage 
  );

  #-- generate testbench
  rendered = tb_template_comb_delay.render(param=param)
  open(spicef, 'w').write(rendered)
  #print(param)
  #print(rendered)
    
  #---
  spicelis = spicef
  spicelis += ".lis"
  
  spicerun = spicef
  spicerun += ".run"
  
  if(re.search("ngspice", targetHarness.mls.simulator)):
    cmd = "nice -n "+str(targetHarness.mls.sim_nice)+" "+str(targetHarness.mls.simulator)+" -b "+str(spicef)+" > "+str(spicelis)+" 2>&1 \n"
  elif(re.search("hspice", targetHarness.mls.simulator)):
    cmd = "nice -n "+str(targetHarness.mls.sim_nice)+" "+str(targetHarness.mls.simulator)+" "+str(spicef)+" -o "+str(spicelis)+" 2> /dev/null \n"
  elif(re.search("Xyce", targetHarness.mls.simulator)):
    cmd = "nice -n "+str(targetHarness.mls.sim_nice)+" "+str(targetHarness.mls.simulator)+" "+str(spicef)+" -hspice-ext all 1> "+str(spicelis)

  #-- create execute file
  with open(spicerun,'w') as f:
    outlines = []
    outlines.append(cmd) 
    f.writelines(outlines)
  #f.close()

  #- do spice simulation
  cmd = ['sh', spicerun]
 
  if(targetHarness.mls.runsim == "true"):
    try:
      res = subprocess.check_call(cmd)
    except:
      print ("Failed to lunch spice")

  # read .mt0 for Xyce
  if(re.search("Xyce", targetHarness.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  # read results
  with open(spicelis,'r') as f:
    for inline in f:
      if(re.search("hspice", targetHarness.mls.simulator)):
        inline = re.sub('\=',' ',inline)
      #targetLib.print_msg(inline)
      
      # search measure
      if((re.search("prop_in_out", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
        res_prop_in_out = "{:e}".format(float(sparray[2].strip()))
      elif((re.search("trans_out", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
        res_trans_out = "{:e}".format(float(sparray[2].strip()))

  #f.close()

  # check spice finish successfully
  try:
    res_prop_in_out
  except NameError:
    targetHarness.mls.print_msg(f"Value res_prop_in_out is not defined!!")
    targetHarness.mls.print_msg(f"Check simulation result in work directory. tb={spicelis}")
    sys.exit()
    
  try:
    res_trans_out
  except NameError:
    targetHarness.mls.print_msg(f"Value res_trans_out is not defined!!")
    targetHarness.mls.print_msg(f"Check simulation result in work directory. tb={spicelis}")
    sys.exit()
    

  #-- hold result in targetHarness
  with targetHarness._lock:
    targetHarness.dict_list2["prop"        ][index2_load][index1_slope] = float(res_prop_in_out )
    targetHarness.dict_list2["trans"       ][index2_load][index1_slope] = float(res_trans_out   )

  #
  return (0)


def runSpiceCombEnergySingle(poolg_sema, targetHarness:Mcar, spicef:str, index1_slope:float, index2_load:float):
                      
  with poolg_sema:
    spicefo  = str(spicef)+"_"+str(index2_load)+"_"+str(index1_slope)+"_energy1.sp"
    spicefoe = str(spicef)+"_"+str(index2_load)+"_"+str(index1_slope)+"_energy2.sp"
 
    ## 1st trial, extract energy_start and energy_end
    res_energy_start, res_energy_end \
      = genFileLogic_CombEnergyTrial1x(targetHarness=targetHarness,meas_energy=0, index2_load=index2_load, index1_slope=index1_slope, estart=0.0, eend=0.0, spicef=spicefo)
                             

    energy_start = res_energy_start
    energy_end = res_energy_end
    ## 2nd trial, extract energy
    res_energy_start, res_energy_end \
      = genFileLogic_CombEnergyTrial1x(targetHarness=targetHarness,meas_energy=1, index2_load=index2_load, index1_slope=index1_slope, estart=energy_start, eend=energy_end, spicef=spicefoe)
                             

def genFileLogic_CombEnergyTrial1x(targetHarness:Mcar, meas_energy:int, index2_load:float, index1_slope:float, estart:float, eend:float, spicef:str):

  spicelis = spicef
  spicelis += ".lis"
  
  targetHarness.mls.print_msg("generate file: "+str(spicef))
  
  tb_instance      = targetHarness.gen_instance_for_tb()

  model  =targetHarness.mlc.model   if targetHarness.mlc.model.startswith("/")   else "../" + targetHarness.mlc.model
  netlist=targetHarness.mlc.netlist if targetHarness.mlc.netlist.startswith("/") else "../" + targetHarness.mlc.netlist
    
  param = ParamTbCombEnergy(
      model       = model
      ,netlist    = netlist
      ,temp       = targetHarness.mls.temperature
      ,vdd_voltage= targetHarness.mls.vdd_voltage
      ,vss_voltage= targetHarness.mls.vss_voltage
      ,vnw_voltage= targetHarness.mls.nwell_voltage
      ,vpw_voltage= targetHarness.mls.pwell_voltage
      ,cap        = index2_load  * targetHarness.mls.capacitance_mag
      ,slew       = index1_slope * targetHarness.mls.time_mag
      ,simulation_timestep         = targetHarness.mls.simulation_timestep * targetHarness.mls.time_mag
      ,tstart_pre                  = targetHarness.mls.sim_prop_max * targetHarness.mls.time_mag
      #,tend_after                  = targetHarness.mls.sim_prop_max * targetHarness.mls.time_mag
      ,tend_after                  = targetHarness.mls.sim_prop_max * targetHarness.mls.time_mag * targetHarness.mls.sim_time_end_extent
      ,tb_instance                 = tb_instance
      ,relport_val0                = targetHarness.target_relport_val[0]
      ,outport_val0                = targetHarness.target_outport_val[0]
      ,relport_arc                 = "rise" if targetHarness.mel.arc_otr[2]=="r" else "fall"
      ,outport_arc                 = "rise" if targetHarness.mel.arc_otr[0]=="r" else "fall"
      ,relport_prop_vth            = targetHarness.mls.logic_low_to_high_threshold_voltage if targetHarness.mel.arc_otr[2]=="r" else targetHarness.mls.logic_high_to_low_threshold_voltage 
      ,outport_prop_vth            = targetHarness.mls.logic_low_to_high_threshold_voltage if targetHarness.mel.arc_otr[0]=="r" else targetHarness.mls.logic_high_to_low_threshold_voltage 
      ,relport_tran_v0             = targetHarness.mls.logic_threshold_low_voltage  if targetHarness.mel.arc_otr[2]=="r" else targetHarness.mls.logic_threshold_high_voltage
      ,relport_tran_v1             = targetHarness.mls.logic_threshold_high_voltage if targetHarness.mel.arc_otr[2]=="r" else targetHarness.mls.logic_threshold_low_voltage 
      ,outport_tran_v0             = targetHarness.mls.logic_threshold_low_voltage  if targetHarness.mel.arc_otr[0]=="r" else targetHarness.mls.logic_threshold_high_voltage
      ,outport_tran_v1             = targetHarness.mls.logic_threshold_high_voltage if targetHarness.mel.arc_otr[0]=="r" else targetHarness.mls.logic_threshold_low_voltage 
      ,relport_ener_v0             = targetHarness.mls.energy_meas_low_threshold_voltage    if targetHarness.mel.arc_otr[2]=="r" else targetHarness.mls.energy_meas_high_threshold_voltage  
      ,relport_ener_v1             = targetHarness.mls.energy_meas_high_threshold_voltage   if targetHarness.mel.arc_otr[2]=="r" else targetHarness.mls.energy_meas_low_threshold_voltage   
      ,outport_ener_v0             = targetHarness.mls.energy_meas_low_threshold_voltage    if targetHarness.mel.arc_otr[0]=="r" else targetHarness.mls.energy_meas_high_threshold_voltage  
      ,outport_ener_v1             = targetHarness.mls.energy_meas_high_threshold_voltage   if targetHarness.mel.arc_otr[0]=="r" else targetHarness.mls.energy_meas_low_threshold_voltage    
      ,meas_energy                 = meas_energy
      ,energy_start                = estart
      ,energy_end                  = eend
  );
    
  rendered = tb_template_comb_energy.render(param=param)
  open(spicef, 'w').write(rendered)
  #print(param)
  #print(rendered)
    
  #---
  spicelis = spicef
  spicelis += ".lis"
  
  spicerun = spicef
  spicerun += ".run"
  
  if(re.search("ngspice", targetHarness.mls.simulator)):
    cmd = "nice -n "+str(targetHarness.mls.sim_nice)+" "+str(targetHarness.mls.simulator)+" -b "+str(spicef)+" > "+str(spicelis)+" 2>&1 \n"
  elif(re.search("hspice", targetHarness.mls.simulator)):
    cmd = "nice -n "+str(targetHarness.mls.sim_nice)+" "+str(targetHarness.mls.simulator)+" "+str(spicef)+" -o "+str(spicelis)+" 2> /dev/null \n"
  elif(re.search("Xyce", targetHarness.mls.simulator)):
    cmd = "nice -n "+str(targetHarness.mls.sim_nice)+" "+str(targetHarness.mls.simulator)+" "+str(spicef)+" -hspice-ext all 1> "+str(spicelis)
    
  with open(spicerun,'w') as f:
    outlines = []
    outlines.append(cmd) 
    f.writelines(outlines)
  #f.close()
 
  cmd = ['sh', spicerun]
 
  if(targetHarness.mls.runsim == "true"):
    try:
      res = subprocess.check_call(cmd)
    except:
      print ("Failed to lunch spice")

  # read .mt0 for Xyce
  if(re.search("Xyce", targetHarness.mls.simulator)):
    spicelis = spicelis[:-3]+"mt0" 

  # read results
  with open(spicelis,'r') as f:
    for inline in f:
      if(re.search("hspice", targetHarness.mls.simulator)):
        inline = re.sub('\=',' ',inline)
        
      if((re.search("energy_start", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
        res_energy_start = "{:e}".format(float(sparray[2].strip()))
      elif((re.search("energy_end", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
        res_energy_end = "{:e}".format(float(sparray[2].strip()))

          
      if(meas_energy == 1):
        if((re.search("q_in_dyn", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res_q_in_dyn = "{:e}".format(float(sparray[2].strip()))
        elif((re.search("q_out_dyn", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res_q_out_dyn = "{:e}".format(float(sparray[2].strip()))
        elif((re.search("q_vdd_dyn", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res_q_vdd_dyn = "{:e}".format(float(sparray[2].strip()))
        elif((re.search("q_vss_dyn", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res_q_vss_dyn = "{:e}".format(float(sparray[2].strip()))
        elif((re.search("i_vdd_leak", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res_i_vdd_leak = "{:e}".format(float(sparray[2].strip()))
        elif((re.search("i_vss_leak", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res_i_vss_leak = "{:e}".format(float(sparray[2].strip()))
        elif((re.search("i_in_leak", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
          res_i_in_leak = "{:e}".format(float(sparray[2].strip()))

  #f.close()

  try:
    res_energy_start
  except NameError:
    targetHarness.mls.print_msg(f"Value res_energy_start is not defined!!")
    targetHarness.mls.print_msg(f"Check simulation result in work directory. rslt={spicelis}")
    sys.exit()
    
  try:
    res_energy_end
  except NameError:
    targetHarness.mls.print_msg(f"Value res_energy_end is not defined!!")
    targetHarness.mls.print_msg(f"Check simulation result in work directory. rslt={spicelis}")
    sys.exit()
    
  #-- hold result in targetHarness when meas_enrgy==1
  if(meas_energy == 1):
    ## Pleak = average of Pleak_vdd and Pleak_vss
    ## P = I * V
    #pleak= (((abs(res_i_vdd_leak])+abs(res_i_vss_leak))/2)*(targetLib.vdd_voltage))
    pleak=abs(float(res_i_vdd_leak)) * targetHarness.mls.vdd_voltage
    
    ## input energy
    ein = abs(float(res_q_in_dyn)) * targetHarness.mls.vdd_voltage

    ## Cin = Qin / V
    cin = abs(float(res_q_in_dyn))/(targetHarness.mls.vdd_voltage)
    
    ## intl. energy calculation
    ## intl. energy is the sum of short-circuit energy and drain-diffusion charge/discharge energy
    ## larger Ql: intl. Q, load Q 
    ## smaller Qs: intl. Q
    ## Eintl = QsV
    #--res_q = res_q_vdd_dyn if(abs(res_q_vdd_dyn) < abs(res_q_vss_dyn)) else res_q_vss_dyn
    #--eintl=abs(res_q*targetLib.vdd_voltage*targetLib.energy_meas_high_threshold \
    #--          - abs((res_energy_end - res_energy_start)*
    #--          ((abs(res_i_vdd_leak) + abs(res_i_vss_leak))/2)*(targetLib.vdd_voltage*targetLib.energy_meas_high_threshold))))
                

    e_all  = abs(float(res_q_vdd_dyn)) * targetHarness.mls.vdd_voltage
    #e_load = abs(0.5*float(res_q_out_dyn)*targetHarness.mls.energy_meas_high_threshold_voltage) if (float(res_q_out_dyn) > 0) else 0.0; #-- dynamic power of Cload(E=0.5*C*V*V=0.5*Q*V)
    e_load =  float(res_q_out_dyn)*(targetHarness.mls.energy_meas_high_threshold_voltage) if (float(res_q_out_dyn) > 0) else 0.0; #-- dynamic power of Cload(E=C*V*V=Q*V)
    
    e_leak = pleak *(float(res_energy_end) - float(res_energy_end))
    eintl  = e_all - e_load - e_leak

    #
    with targetHarness._lock:
      targetHarness.dict_list2["energy_start"][index2_load][index1_slope] = float(res_energy_start)
      targetHarness.dict_list2["energy_end"  ][index2_load][index1_slope] = float(res_energy_end  )
      targetHarness.dict_list2["q_in_dyn"    ][index2_load][index1_slope] = float(res_q_in_dyn    )
      targetHarness.dict_list2["q_out_dyn"   ][index2_load][index1_slope] = float(res_q_out_dyn   )
      targetHarness.dict_list2["q_vdd_dyn"   ][index2_load][index1_slope] = float(res_q_vdd_dyn   )
      targetHarness.dict_list2["q_vss_dyn"   ][index2_load][index1_slope] = float(res_q_vss_dyn   )
      targetHarness.dict_list2["i_in_leak"   ][index2_load][index1_slope] = float(res_i_in_leak   )
      targetHarness.dict_list2["i_vdd_leak"  ][index2_load][index1_slope] = float(res_i_vdd_leak  )
      targetHarness.dict_list2["i_vss_leak"  ][index2_load][index1_slope] = float(res_i_vss_leak  )
      
      targetHarness.dict_list2["eintl"][index2_load][index1_slope]=eintl
      targetHarness.dict_list2["ein"  ][index2_load][index1_slope]=ein
      targetHarness.dict_list2["cin"  ][index2_load][index1_slope]=cin
      targetHarness.dict_list2["pleak"][index2_load][index1_slope]=pleak

  #
  return float(res_energy_start), float(res_energy_end)
