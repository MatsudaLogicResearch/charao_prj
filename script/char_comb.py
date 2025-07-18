import argparse, re, os, shutil, subprocess, sys, inspect, threading 

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
template = env.get_template('./template/temp_comb.sp.j2')

@dataclass
class ParamTbComb:
  model      :str
  netlist    :str
  temp       :float
  vdd_voltage:float
  vss_voltage:float
  vnw_voltage:float
  vpw_voltage:float
  cap        :float
  slew       :float
  #energy_meas_time_extent:int
  simulation_timestep    :float
  tb_instance            :str
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
  #energy_end_extent      :float

def runCombInNOut1(targetLib:Mls, targetCell:Mlc, expectationdictList:List[Mel]):
  harnessList = []
  harnessList2 = []

  #for trial in range(len(expectationdictList)):
  #for expectationdict in expectationdictList:
  size=len(expectationdictList)
  for ii in range(size):
    expectationdict = expectationdictList[ii]
    
    #tmp_Harness = mcar.MyConditionsAndResults(mel=expectationdict)
    tmp_Harness = Mcar(mls=targetLib, mlc=targetCell, mel=expectationdict)
    tmp_Harness.set_update()
    
    #tmp_Harness = mcar.MyConditionsAndResults()
    #tmp_Harness.set_timing_type_comb()
    #tmp_Harness.set_timing_sense(expectationdict.tmg_sense)
    #
    #tmp_Harness.set_direction(expectationdict.arc)
    #
    #tmp_Harness.set_timing_when(expectationdict.tmg_when)
    #
    ##
    #pin_r  = expectationdict.pin_r
    #pin_t  = expectationdict.pin_t
    #val1_r = expectationdict.val1_r
    #val1_t = expectationdict.val1_t
    #  
    ##-- set target(outport)
    #for i in range (len(expectationdict.val0_o)):
    #  pin_o="o{:}".format(i)
    #  if pin_t == pin_o:
    #    #tmp_Harness.set_target_outport (pin_o, targetCell.functions[0], expectationdict.val0_o[i]+val1_t)
    #    if pin_t in targetCell.functions.keys():
    #      tmp_Harness.set_target_outport (pin_o, targetCell.functions[pin_t], expectationdict.val0_o[i]+val1_t)          
    #    else:
    #      print(f"Error: function is not exist for {pin_t} in {targetCell.logic}.")
    #      my_exit()
    #
    #      
    ##-- set target(ioport)
    #for i in range (len(expectationdict.val0_b)):
    #  pin_b="b{:}".format(i)
    #  if pin_t == pin_b:
    #    #tmp_Harness.set_target_outport (pin_t, targetCell.functions[0], expectationdict.val0_b[i]+val1_t)
    #    if pin_t in targetCell.functions.keys():
    #      tmp_Harness.set_target_outport (pin_t, targetCell.functions[pin_t], expectationdict.val0_b[i]+val1_t)          
    #    else:
    #      print(f"Error: function is not exist for {pin_t} in {targetCell.logic}.")
    #      my_exit()
    #
    ##-- set reference(inport)
    #for i in range (len(expectationdict.val0_i)):
    #  pin_i="i{:}".format(i)
    #  if pin_r == pin_i:
    #    tmp_Harness.set_target_inport (pin_i, expectationdict.val0_i[i]+val1_r)
    #  else:
    #    tmp_Harness.set_stable_inport (pin_i, expectationdict.val0_i[i])
    #
    ##-- set reference(ioport)
    #for i in range (len(expectationdict.val0_b)):
    #  pin_b="b{:}".format(i)
    #  if pin_r == pin_b:
    #    tmp_Harness.set_target_inport (pin_b, expectationdict.val0_b[i]+val1_r)
    #  else:
    #    tmp_Harness.set_stable_inport (pin_b, expectationdict.val0_b[i])
    

    #spicef = "vt_"+str(targetLib.vdd_voltage)+"_"+str(targetLib.temperature)+"_"\
    #  +"delay1_"+str(targetCell.cell)+"_"\
    #  +str(targetCell.inports[0])+str(tmp_inp0_val)\
    #  +"_"+str(targetCell.inports[1])+str(tmp_inp1_val)\
    #  +"_"+str(targetCell.inports[2])+str(tmp_inp2_val)\
    #  +"_"+str(targetCell.inports[3])+str(tmp_inp3_val)\
    #  +"_"+str(targetCell.outports[0])+str(tmp_outp0_val)

    #-- spcie file name
    pin_o  = expectationdict.pin_otr[0]
    pin_t  = expectationdict.pin_otr[1]
    pin_r  = expectationdict.pin_otr[2]

    val_o  = expectationdict.mondrv_otr[0]
    val_t  = expectationdict.mondrv_otr[1]
    val_r  = expectationdict.mondrv_otr[2]
    
    spicef0 = "vt_"+str(targetLib.vdd_voltage)+"_"+str(targetLib.temperature)+"_"\
      +"delay1_"+str(targetCell.cell)

    #spicef1=""
    #for i in range (len(expectationdict.val0_i)):
    #  pin_i="i{:}".format(i)
    #  spicef1 +="_" + pin_i + expectationdict.val0_i[i]
    #  if pin_i == pin_r:
    #    spicef1 +=val1_r
    #  
    #for i in range (len(expectationdict.val0_b)):
    #  pin_b="b{:}".format(i)
    #  spicef1 +="_" + pin_b + expectationdict.val0_b[i]
    #  if pin_b == pin_r:
    #    spicef1 +=val1_r
    #  elif pin_b == pin_t:
    #    spicef1 +=val1_t
    #    
    #for i in range (len(expectationdict.val0_o)):
    #  pin_o="o{:}".format(i)
    #  spicef1 += "_" + pin_o + expectationdict.val0_o[i]
    #  if pin_o == pin_t:
    #    spicef1 +=val1_t
    #  spicef1 +="_"

    spicef1 =f"_{ii}"
    spicef1+="_otr=" + ''.join(expectationdict.pin_otr)
    spicef1+="_typ=" + expectationdict.tmg_type
    spicef1+="_arc=" + ''.join(expectationdict.arc_otr)

    
    spicef = spicef0 + spicef1

    #print(targetCell.__dict__)
    #print(expectationdict)
    #print(tmp_Harness.__dict__)
    #my_exit()
    
    # run spice and store result
    #runSpiceCombDelayMultiThread(targetLib, targetCell, tmp_Harness, spicef)
    runSpiceCombDelayMultiThread(tmp_Harness, spicef)
    
    harnessList.append(tmp_Harness)
    #harnessList2.append(harnessList)
  
  ## average cin of each harness
  #targetCell.set_cin_avg(targetLib, harnessList) 
  targetCell.set_cin_avg(targetLib, harnessList) 

  #return harnessList2
  return harnessList




#def runSpiceCombDelayMultiThread(targetLib, targetCell, targetHarness, spicef):
def runSpiceCombDelayMultiThread(targetHarness, spicef):
  #list2_prop =   []
  #list2_tran =   []
  #list2_estart = []
  #list2_eend =   []
  #list2_eintl =   []
  #list2_ein =   []
  #list2_cin =   []
  #list2_pleak =   []
  ## calculate whole slope length from logic threshold
  tmp_slope_mag = 1 / (targetHarness.mls.logic_threshold_high - targetHarness.mls.logic_threshold_low)

  thread_id = 0

  # Limit number of threads
  # define semaphore 
  poolg_sema = threading.BoundedSemaphore(targetHarness.mls.num_thread)
  targetHarness.mls.print_msg("Num threads for simulation:"+str(targetHarness.mls.num_thread))

  #results_prop_in_out  = dict()
  #results_trans_out    = dict()
  #results_energy_start = dict()
  #results_energy_end   = dict()
  #results_q_in_dyn     = dict()
  #results_q_out_dyn    = dict()
  #results_q_vdd_dyn    = dict()
  #results_q_vss_dyn    = dict()
  #results_i_in_leak    = dict()
  #results_i_vdd_leak   = dict()
  #results_i_vss_leak   = dict()
  threadlist = list()
  for load in targetHarness.mlc.load:
    for slope in targetHarness.mlc.slope:
      thread = threading.Thread(target=runSpiceCombDelaySingle, \
              args=([poolg_sema, targetHarness, spicef, slope, load]),
              name="%d" % thread_id)
      
      threadlist.append(thread)
      thread_id += 1

  for thread in threadlist:
    thread.start() 

  for thread in threadlist:
    thread.join() 
    
#  thread_id = 0
#  for tmp_load in targetCell.load:
#    tmp_list_prop =   []
#    tmp_list_tran =   []
#    tmp_list_estart = []
#    tmp_list_eend =   []
#    tmp_list_eintl =   []
#    tmp_list_ein =   []
#    tmp_list_cin =   []
#    tmp_list_pleak =   []
#    for tmp_slope in targetCell.slope:
##      targetLib.print_msg(str(thread_id))
##      targetLib.print_msg(str(results_prop_in_out))
##      targetLib.print_msg(str(results_prop_in_out[str(thread_id)]))
#      tmp_list_prop.append(results_prop_in_out[str(thread_id)])
#      tmp_list_tran.append(results_trans_out[str(thread_id)])
#
#      ## intl. energy calculation
#      ## intl. energy is the sum of short-circuit energy and drain-diffusion charge/discharge energy
#      ## larger Ql: intl. Q, load Q 
#      ## smaller Qs: intl. Q
#      ## Eintl = QsV
#      if(abs(results_q_vdd_dyn[str(thread_id)]) < abs(results_q_vss_dyn[str(thread_id)])):
#        res_q = results_q_vdd_dyn[str(thread_id)]
#      else:
#        res_q = results_q_vss_dyn[str(thread_id)]
#      tmp_list_eintl.append(abs(res_q*targetLib.vdd_voltage*targetLib.energy_meas_high_threshold \
#        - abs((results_energy_end[str(thread_id)] - results_energy_start[str(thread_id)])*((abs(results_i_vdd_leak[str(thread_id)]) \
#        + abs(results_i_vss_leak[str(thread_id)]))/2)*(targetLib.vdd_voltage*targetLib.energy_meas_high_threshold))))
#
#      ## input energy
#      tmp_list_ein.append(abs(results_q_in_dyn[str(thread_id)])*targetLib.vdd_voltage)
#
#      ## Cin = Qin / V
#      tmp_list_cin.append(abs(results_q_in_dyn[str(thread_id)])/(targetLib.vdd_voltage))
#
#      ## Pleak = average of Pleak_vdd and Pleak_vss
#      ## P = I * V
#      tmp_list_pleak.append(((abs(results_i_vdd_leak[str(thread_id)])+abs(results_i_vss_leak[str(thread_id)]))/2)*(targetLib.vdd_voltage)) #
#      thread_id += 1
#
#    list2_prop.append(tmp_list_prop)
#    list2_tran.append(tmp_list_tran)
#    #list2_estart.append(tmp_list_estart)
#    #list2_eend.append(tmp_list_eend)
#    list2_eintl.append(tmp_list_eintl)
#    list2_ein.append(tmp_list_ein)
#    list2_cin.append(tmp_list_cin)
#    list2_pleak.append(tmp_list_pleak)

  targetHarness.set_lut(name="prop")
  targetHarness.set_lut(name="trans")
  targetHarness.set_lut(name="eintl")
  targetHarness.set_lut(name="ein")

  targetHarness.set_average(name="cin")
  targetHarness.set_average(name="pleak")

  

  
def runSpiceCombDelaySingle(poolg_sema, targetHarness, spicef, slope, load):
                      
 
  with poolg_sema:
    #targetLib.print_msg("start thread :"+str(threading.current_thread().name))
    #print("start thread ")
 
    spicefo  = str(spicef)+"_"+str(load)+"_"+str(slope)+".sp"
    spicefoe = str(spicef)+"_"+str(load)+"_"+str(slope)+"_energy.sp"
 
    ## 1st trial, extract energy_start and energy_end
    res_energy_start, res_energy_end \
      = genFileLogic_trial1x(targetHarness=targetHarness,meas_energy=0, load=load, slope=slope, estart=0.0, eend=0.0, spicef=spicefo)
                             

    energy_start = res_energy_start
    energy_end = res_energy_end
    ## 2nd trial, extract energy
    res_energy_start, res_energy_end \
      = genFileLogic_trial1x(targetHarness=targetHarness,meas_energy=1, load=load, slope=slope, estart=energy_start, eend=energy_end, spicef=spicefoe)
                             

    ## result is stored in targetharness.
    
    #--#targetLib.print_msg(str(res_prop_in_out)+" "+str(res_trans_out)+" "+str(res_energy_start)+" "+str(res_energy_end))
    #--results_prop_in_out[threading.current_thread().name] = res_prop_in_out
    #--results_trans_out[threading.current_thread().name]   = res_trans_out
    #--results_energy_start[threading.current_thread().name]= res_energy_start
    #--results_energy_end[threading.current_thread().name]  = res_energy_end
    #--results_q_in_dyn[threading.current_thread().name]    = res_q_in_dyn
    #--results_q_out_dyn[threading.current_thread().name]   = res_q_out_dyn
    #--results_q_vdd_dyn[threading.current_thread().name]   = res_q_vdd_dyn
    #--results_q_vss_dyn[threading.current_thread().name]   = res_q_vss_dyn
    #--results_i_in_leak[threading.current_thread().name]   = res_i_in_leak
    #--results_i_vdd_leak[threading.current_thread().name]  = res_i_vdd_leak
    #--results_i_vss_leak[threading.current_thread().name]  = res_i_vss_leak
 
    #--#targetLib.print_msg("end thread :"+str(threading.current_thread().name))

#def runSpiceCombDelaySingle(pool_sema, targetLib, targetCell, targetHarness, spicef, \
#                      tmp_slope, tmp_load, tmp_slope_mag, \
#                      results_prop_in_out, results_trans_out,\
#                      results_energy_start, results_energy_end,\
#                      results_q_in_dyn, results_q_out_dyn, results_q_vdd_dyn, results_q_vss_dyn, \
#                      results_i_in_leak, results_i_vdd_leak, results_i_vss_leak):
# 
#  with pool_sema:
#    #targetLib.print_msg("start thread :"+str(threading.current_thread().name))
#    #print("start thread ")
# 
#    cap_line = ".param cap ="+str(tmp_load*targetLib.capacitance_mag)+"\n"
#    #slew_line = ".param slew ="+str(tmp_slope*tmp_slope_mag*targetLib.time_mag)+"\n"
#    slew_line = ".param slew ="+str(tmp_slope*targetLib.time_mag)+"\n"
#    temp_line = ".temp "+str(targetLib.temperature)+"\n"
#    spicefo  = str(spicef)+"_"+str(tmp_load)+"_"+str(tmp_slope)+".sp"
#    spicefoe = str(spicef)+"_"+str(tmp_load)+"_"+str(tmp_slope)+"_energy.sp"
# 
#    ## 1st trial, extract energy_start and energy_end
#    res_prop_in_out, res_trans_out, res_energy_start, res_energy_end, \
#      = genFileLogic_trial1x(targetLib=targetLib, targetCell=targetCell, targetHarness=targetHarness,
#                             meas_energy=0, load=tmp_load, slope=tmp_slope, estart=0.0, eend=0.0, spicef=spicefo)
#
#    energy_start = res_energy_start
#    energy_end = res_energy_end
#    ## 2nd trial, extract energy
#    res_prop_in_out, res_trans_out, \
#      res_q_in_dyn, res_q_out_dyn, res_q_vdd_dyn, res_q_vss_dyn, \
#      res_i_in_leak, res_i_vdd_leak, res_i_vss_leak \
#      = genFileLogic_trial1x(targetLib=targetLib, targetCell=targetCell, targetHarness=targetHarness,
#                             meas_energy=1, load=tmp_load, slope=tmp_slope, estart=energy_start, eend=energy_end, spicef=spicefoe)
#    
#    #targetLib.print_msg(str(res_prop_in_out)+" "+str(res_trans_out)+" "+str(res_energy_start)+" "+str(res_energy_end))
#    results_prop_in_out[threading.current_thread().name] = res_prop_in_out
#    results_trans_out[threading.current_thread().name]   = res_trans_out
#    results_energy_start[threading.current_thread().name]= res_energy_start
#    results_energy_end[threading.current_thread().name]  = res_energy_end
#    results_q_in_dyn[threading.current_thread().name]    = res_q_in_dyn
#    results_q_out_dyn[threading.current_thread().name]   = res_q_out_dyn
#    results_q_vdd_dyn[threading.current_thread().name]   = res_q_vdd_dyn
#    results_q_vss_dyn[threading.current_thread().name]   = res_q_vss_dyn
#    results_i_in_leak[threading.current_thread().name]   = res_i_in_leak
#    results_i_vdd_leak[threading.current_thread().name]  = res_i_vdd_leak
#    results_i_vss_leak[threading.current_thread().name]  = res_i_vss_leak
# 
#    #targetLib.print_msg("end thread :"+str(threading.current_thread().name))

    
#--def genFileLogic_trial1(targetLib, targetCell, targetHarness, meas_energy, cap_line, slew_line, temp_line, estart_line, eend_line, spicef):
#--
#--  spicelis = spicef
#--  spicelis += ".lis"
#--
#--  # if file is not exist, create spice file and run spice
#--  if(os.path.isfile(spicelis)):
#--    targetLib.print_msg("skip file: "+str(spicef))
#--  else:
#--    targetLib.print_msg("generate file: "+str(spicef))
#--
#--    with open(spicef,'w') as f:
#--      outlines = []
#--      outlines.append("*title: delay meas.\n")
#--      outlines.append(".option brief nopage nomod post=1 ingold=2 autostop\n")
#--      
#--      if targetCell.model.startswith('/'):
#--        outlines.append(".inc '"+targetCell.model+"'\n")
#--      else:
#--        outlines.append(".inc '../"+targetCell.model+"'\n")
#--      if targetCell.netlist.startswith('/'):
#--        outlines.append(".inc '"+targetCell.netlist+"'\n")
#--      else:
#--        outlines.append(".inc '../"+targetCell.netlist+"'\n")
#--        
#--      outlines.append(temp_line)
#--      outlines.append(".param _vdd = "+str(targetLib.vdd_voltage)+"\n")
#--      outlines.append(".param _vss = "+str(targetLib.vss_voltage)+"\n")
#--      outlines.append(".param _vnw = "+str(targetLib.nwell_voltage)+"\n")
#--      outlines.append(".param _vpw = "+str(targetLib.pwell_voltage)+"\n")
#--      outlines.append(".param cap = 10f \n")
#--      outlines.append(".param slew = 100p \n")
#--      outlines.append(".param _tslew = slew\n")
#--      outlines.append(".param _tstart = slew\n")
#--      outlines.append(".param _tend = '_tstart + _tslew'\n")
#--                  #outlines.append(".param _tsimend = '_tslew * 10000' \n")
#--      outlines.append(".param _tsimend = '10 * _tslew + 1us' \n")
#--    
#--      outlines.append(".param _Energy_meas_end_extent = "+str(targetLib.energy_meas_time_extent)+"\n")
#--      outlines.append(" \n")
#--      outlines.append("VDD_DYN VDD_DYN 0 DC '_vdd' \n")
#--      outlines.append("VSS_DYN VSS_DYN 0 DC '_vss' \n")
#--      outlines.append("VNW_DYN VNW_DYN 0 DC '_vnw' \n")
#--      outlines.append("VPW_DYN VPW_DYN 0 DC '_vpw' \n")
#--      outlines.append("* output load calculation\n")
#--      outlines.append("VOCAP VOUT WOUT DC 0\n")
#--      #outlines.append("VDD_LEAK VDD_LEAK 0 DC '_vdd' \n")
#--      #outlines.append("VSS_LEAK VSS_LEAK 0 DC '_vss' \n")
#--      #outlines.append("VNW_LEAK VNW_LEAK 0 DC '_vnw' \n")
#--      #outlines.append("VPW_LEAK VPW_LEAK 0 DC '_vpw' \n")
#--      outlines.append(" \n")
#--      ## in auto mode, simulation timestep is 1/10 of min. input slew
#--      ## simulation runs 1000x of input slew time
#--      #outlines.append(".tran "+str(targetCell.simulation_timestep)+str(targetLib.time_unit)+" '_tsimend'\n")
#--      outlines.append(".tran "+str(targetCell.simulation_timestep * targetCell.slope[0] * targetLib.time_mag)+" '_tsimend'\n")
#--      outlines.append(" \n")
#--    
#--      if(targetHarness.target_inport_val == "01"):
#--        outlines.append("VIN VIN 0 PWL(1p '_vss' '_tstart' '_vss' '_tend' '_vdd' '_tsimend' '_vdd') \n")
#--      elif(targetHarness.target_inport_val == "10"):
#--        outlines.append("VIN VIN 0 PWL(1p '_vdd' '_tstart' '_vdd' '_tend' '_vss' '_tsimend' '_vss') \n")
#--      elif(targetHarness.target_inport_val == "11"):
#--        outlines.append("VIN VIN 0 DC '_vdd' \n")
#--      elif(targetHarness.target_inport_val == "00"):
#--        outlines.append("VIN VIN 0 DC '_vss' \n")
#--      outlines.append("VHIGH VHIGH 0 DC '_vdd' \n")
#--      outlines.append("VLOW VLOW 0 DC '_vss' \n")
#--    
#--      ##
#--      ## delay measurement 
#--      outlines.append("** Delay \n")
#--      outlines.append("* Prop delay \n")
#--      if(targetHarness.target_inport_val == "01"):
#--        outlines.append(".measure Tran PROP_IN_OUT trig v(VIN) VAL='"+str(targetLib.logic_low_to_high_threshold_voltage)+"' rise=1 \n")
#--      elif(targetHarness.target_inport_val == "10"):
#--        outlines.append(".measure Tran PROP_IN_OUT trig v(VIN) VAL='"+str(targetLib.logic_high_to_low_threshold_voltage)+"' fall=1 \n")
#--    
#--      if(targetHarness.target_outport_val == "10"):
#--        outlines.append("+ targ v(VOUT) val='"+str(targetLib.logic_high_to_low_threshold_voltage)+"' fall=1 \n")
#--      elif(targetHarness.target_outport_val == "01"):
#--        outlines.append("+ targ v(VOUT) val='"+str(targetLib.logic_low_to_high_threshold_voltage)+"' rise=1 \n")
#--        
#--      outlines.append("* Trans delay \n")
#--    
#--      if(targetHarness.target_outport_val == "10"):
#--        outlines.append(".measure Tran TRANS_OUT trig v(VOUT) VAL='"+str(targetLib.logic_threshold_high_voltage)+"' fall=1\n")
#--        outlines.append("+ targ v(VOUT) val='"+str(targetLib.logic_threshold_low_voltage)+"' fall=1 \n")
#--      elif(targetHarness.target_outport_val == "01"):
#--        outlines.append(".measure Tran TRANS_OUT trig v(VOUT) VAL='"+str(targetLib.logic_threshold_low_voltage)+"' rise=1\n")
#--        outlines.append("+ targ v(VOUT) val='"+str(targetLib.logic_threshold_high_voltage)+"' rise=1 \n")
#--    
#--      # get ENERGY_START and ENERGY_END for energy calculation in 2nd round 
#--      if(meas_energy == 0):
#--        outlines.append("* For energy calculation \n")
#--        if(targetHarness.target_inport_val == "01"):
#--          outlines.append(".measure Tran ENERGY_START when v(VIN)='"+str(targetLib.energy_meas_low_threshold_voltage)+"' rise=1 \n")
#--        elif(targetHarness.target_inport_val == "10"):
#--          outlines.append(".measure Tran ENERGY_START when v(VIN)='"+str(targetLib.energy_meas_high_threshold_voltage)+"' fall=1 \n")
#--        if(targetHarness.target_outport_val == "01"):
#--          outlines.append(".measure Tran ENERGY_END when v(VOUT)='"+str(targetLib.energy_meas_high_threshold_voltage)+"' rise=1 \n")
#--        elif(targetHarness.target_outport_val == "10"):
#--          outlines.append(".measure Tran ENERGY_END when v(VOUT)='"+str(targetLib.energy_meas_low_threshold_voltage)+"' fall=1 \n")
#--    
#--      ##
#--      ## energy measurement 
#--      elif(meas_energy == 1):
#--        outlines.append(estart_line)
#--        outlines.append(eend_line)
#--        outlines.append("* \n")
#--        outlines.append("** In/Out Q, Capacitance \n")
#--        outlines.append("* \n")
#--        outlines.append(".measure Tran Q_IN_DYN integ i(VIN) from='ENERGY_START' to='ENERGY_END'  \n")
#--        outlines.append(".measure Tran Q_OUT_DYN integ i(VOCAP) from='ENERGY_START' to='ENERGY_END*_Energy_meas_end_extent' \n")
#--        outlines.append(" \n")
#--        outlines.append("* \n")
#--        outlines.append("** Energy \n")
#--        outlines.append("*  (Total charge, Short-Circuit Charge) \n")
#--        outlines.append(".measure Tran Q_VDD_DYN integ i(VDD_DYN) from='ENERGY_START' to='ENERGY_END*_Energy_meas_end_extent'  \n")
#--        outlines.append(".measure Tran Q_VSS_DYN integ i(VSS_DYN) from='ENERGY_START' to='ENERGY_END*_Energy_meas_end_extent'  \n")
#--        outlines.append(" \n")
#--        outlines.append("* Leakage current \n")
#--        outlines.append(".measure Tran I_VDD_LEAK avg i(VDD_DYN) from='_tstart*0.1' to='_tstart'  \n")
#--        outlines.append(".measure Tran I_VSS_LEAK avg i(VSS_DYN) from='_tstart*0.1' to='_tstart'  \n")
#--        outlines.append(" \n")
#--        outlines.append("* Gate leak current \n")
#--        outlines.append(".measure Tran I_IN_LEAK avg i(VIN) from='_tstart*0.1' to='_tstart'  \n")
#--      else:
#--        targetLib.print_msg("Error, meas_energy should 0 (disable) or 1 (enable)")
#--        my_error()
#--    
#--      ## for ngspice batch mode 
#--      outlines.append("*comment out .control for ngspice batch mode \n")
#--      outlines.append("*.control \n")
#--      outlines.append("*run \n")
#--      outlines.append("*plot V(VIN) V(VOUT) \n")
#--      outlines.append("*.endc \n")
#--    
#--      outlines.append("XINV VIN VOUT VHIGH VLOW VDD_DYN VSS_DYN VNW_DYN VPW_DYN DUT \n")
#--      outlines.append("C0 WOUT VSS_DYN 'cap'\n")
#--      outlines.append(" \n")
#--      outlines.append(".SUBCKT DUT IN OUT HIGH LOW VDD VSS VNW VPW \n")
#--      # parse subckt definition
#--      tmp_array = targetCell.instance.split()
#--      tmp_line = tmp_array[0] # XDUT
#--      #targetLib.print_msg(tmp_line)
#--      for w1 in tmp_array:
#--        # match tmp_array and harness 
#--        # search target inport
#--        is_matched = 0
#--        w2 = targetHarness.target_inport
#--        if(w1 == w2):
#--          tmp_line += ' IN'
#--          is_matched += 1
#--        # search stable inport
#--        for w2 in targetHarness.stable_inport:
#--          if(w1 == w2):
#--            # this is stable inport
#--            # search index for this port
#--            index_val = targetHarness.stable_inport_val[targetHarness.stable_inport.index(w2)]
#--            if(index_val == '1'):
#--              tmp_line += ' HIGH'
#--              is_matched += 1
#--            elif(index_val == '0'):
#--              tmp_line += ' LOW'
#--              is_matched += 1
#--            else:
#--              targetLib.print_msg('Illigal input value for stable input')
#--        # one target outport for one simulation
#--        w2 = targetHarness.target_outport
#--        #targetLib.print_msg(w1+" "+w2+"\n")
#--        if(w1 == w2):
#--          tmp_line += ' OUT'
#--          is_matched += 1
#--        # search non-terget outport
#--        for w2 in targetHarness.nontarget_outport:
#--          if(w1 == w2):
#--            # this is non-terget outport
#--            # search outdex for this port
#--            index_val = targetHarness.nontarget_outport_val[targetHarness.nontarget_outport.index(w2)]
#--            tmp_line += ' WFLOAT'+str(index_val)
#--            is_matched += 1
#--        if(w1.upper() == targetLib.vdd_name.upper()):
#--            # tmp_line += ' '+w1.upper() 
#--            tmp_line += ' VDD' 
#--            is_matched += 1
#--        if(w1.upper() == targetLib.vss_name.upper()):
#--            # tmp_line += ' '+w1.upper() 
#--            tmp_line += ' VSS' 
#--            is_matched += 1
#--        if(w1.upper() == targetLib.pwell_name.upper()):
#--            # tmp_line += ' '+w1.upper() 
#--            tmp_line += ' VPW' 
#--            is_matched += 1
#--        if(w1.upper() == targetLib.nwell_name.upper()):
#--            # tmp_line += ' '+w1.upper() 
#--            tmp_line += ' VNW' 
#--            is_matched += 1
#--        ## show error if this port has not matched
#--        if(is_matched == 0):
#--          ## if w1 is wire name, abort
#--          ## check this is instance tmp_array[0] or circuit name tmp_array[-1]
#--          if((w1 != tmp_array[0]) and (w1 != tmp_array[-1])): 
#--            targetLib.print_error("port: "+str(w1)+" has not matched in netlist parse!!")
#--            
#--      tmp_line += " "+str(tmp_array[len(tmp_array)-1])+"\n" # CIRCUIT NAME
#--      outlines.append(tmp_line)
#--      #targetLib.print_msg(tmp_line)
#--    
#--      outlines.append(".ends \n")
#--      outlines.append(" \n")
#--      outlines.append(cap_line)
#--      outlines.append(slew_line)
#--          
#--      outlines.append(".end \n") 
#--      f.writelines(outlines)
#--    f.close()
#-- 
#--    spicelis = spicef
#--    spicelis += ".lis"
#--    spicerun = spicef
#--    spicerun += ".run"
#--    if(re.search("ngspice", targetLib.simulator)):
#--      cmd = "nice -n "+str(targetLib.sim_nice)+" "+str(targetLib.simulator)+" -b "+str(spicef)+" > "+str(spicelis)+" 2>&1 \n"
#--    elif(re.search("hspice", targetLib.simulator)):
#--      cmd = "nice -n "+str(targetLib.sim_nice)+" "+str(targetLib.simulator)+" "+str(spicef)+" -o "+str(spicelis)+" 2> /dev/null \n"
#--    elif(re.search("Xyce", targetLib.simulator)):
#--      cmd = "nice -n "+str(targetLib.sim_nice)+" "+str(targetLib.simulator)+" "+str(spicef)+" -hspice-ext all 1> "+str(spicelis)
#--    with open(spicerun,'w') as f:
#--      outlines = []
#--      outlines.append(cmd) 
#--      f.writelines(outlines)
#--    f.close()
#-- 
#--    cmd = ['sh', spicerun]
#-- 
#--    if(targetLib.runsim == "true"):
#--      try:
#--        res = subprocess.check_call(cmd)
#--      except:
#--        print ("Failed to lunch spice")
#--
#--  # read .mt0 for Xyce
#--  if(re.search("Xyce", targetLib.simulator)):
#--    spicelis = spicelis[:-3]+"mt0" 
#--
#--  # read results
#--  with open(spicelis,'r') as f:
#--    for inline in f:
#--      if(re.search("hspice", targetLib.simulator)):
#--        inline = re.sub('\=',' ',inline)
#--      #targetLib.print_msg(inline)
#--      # search measure
#--      if((re.search("prop_in_out", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
#--        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
#--        res_prop_in_out = "{:e}".format(float(sparray[2].strip()))
#--      elif((re.search("trans_out", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
#--        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
#--        res_trans_out = "{:e}".format(float(sparray[2].strip()))
#--      if(meas_energy == 0):
#--        if((re.search("energy_start", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
#--          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
#--          res_energy_start = "{:e}".format(float(sparray[2].strip()))
#--        elif((re.search("energy_end", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
#--          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
#--          res_energy_end = "{:e}".format(float(sparray[2].strip()))
#--      if(meas_energy == 1):
#--        if((re.search("q_in_dyn", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
#--          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
#--          res_q_in_dyn = "{:e}".format(float(sparray[2].strip()))
#--        elif((re.search("q_out_dyn", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
#--          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
#--          res_q_out_dyn = "{:e}".format(float(sparray[2].strip()))
#--        elif((re.search("q_vdd_dyn", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
#--          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
#--          res_q_vdd_dyn = "{:e}".format(float(sparray[2].strip()))
#--        elif((re.search("q_vss_dyn", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
#--          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
#--          res_q_vss_dyn = "{:e}".format(float(sparray[2].strip()))
#--        elif((re.search("i_vdd_leak", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
#--          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
#--          res_i_vdd_leak = "{:e}".format(float(sparray[2].strip()))
#--        elif((re.search("i_vss_leak", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
#--          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
#--          res_i_vss_leak = "{:e}".format(float(sparray[2].strip()))
#--        elif((re.search("i_in_leak", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
#--          sparray = re.split(" +", inline) # separate words with spaces (use re.split)
#--          res_i_in_leak = "{:e}".format(float(sparray[2].strip()))
#--
#--  f.close()
#--  #targetLib.print_msg(str(res_prop_in_out)+" "+str(res_trans_out)+" "+str(res_energy_start)+" "+str(res_energy_end))
#--  # check spice finish successfully
#--  try:
#--    res_prop_in_out
#--  except NameError:
#--    targetLib.print_msg("Value res_prop_in_out is not defined!!")
#--    targetLib.print_msg("Check simulation result in work directory")
#--    sys.exit()
#--  try:
#--    res_trans_out
#--  except NameError:
#--    targetLib.print_msg("Value res_trans_out is not defined!!")
#--    targetLib.print_msg("Check simulation result in work directory")
#--    sys.exit()
#--  if(meas_energy == 0):
#--    return float(res_prop_in_out), float(res_trans_out), float(res_energy_start), float(res_energy_end)
#--  elif(meas_energy == 1):
#--    return float(res_prop_in_out), float(res_trans_out), \
#--        float(res_q_in_dyn), float(res_q_out_dyn), float(res_q_vdd_dyn), float(res_q_vss_dyn), \
#--        float(res_i_in_leak), float(res_i_vdd_leak), float(res_i_vss_leak)


#def genFileLogic_trial1x(targetLib, targetCell, targetHarness, meas_energy, load, slope, estart, eend, spicef):
def genFileLogic_trial1x(targetHarness, meas_energy, load, slope, estart, eend, spicef):

  spicelis = spicef
  spicelis += ".lis"
  
  # if file is not exist, create spice file and run spice
  #if(os.path.isfile(spicelis)):
  #  targetLib.print_msg("skip file: "+str(spicef))
  #else:
  #  targetLib.print_msg("generate file: "+str(spicef))

  targetHarness.mls.print_msg("generate file: "+str(spicef))
  
  #tb_instance      = targetHarness.gen_instance_for_tb(targetLib=targetLib, targetCell=targetCell)
  tb_instance      = targetHarness.gen_instance_for_tb()

  model  =targetHarness.mlc.model   if targetHarness.mlc.model.startswith("/")   else "../" + targetHarness.mlc.model
  netlist=targetHarness.mlc.netlist if targetHarness.mlc.netlist.startswith("/") else "../" + targetHarness.mlc.netlist
    
  param = ParamTbComb(
      model       = model
      ,netlist    = netlist
      ,temp       = targetHarness.mls.temperature
      ,vdd_voltage= targetHarness.mls.vdd_voltage
      ,vss_voltage= targetHarness.mls.vss_voltage
      ,vnw_voltage= targetHarness.mls.nwell_voltage
      ,vpw_voltage= targetHarness.mls.pwell_voltage
      ,cap        = load  * targetHarness.mls.capacitance_mag
      ,slew       = slope * targetHarness.mls.time_mag
      ,simulation_timestep         = targetHarness.mlc.simulation_timestep * targetHarness.mlc.slope[0] * targetHarness.mls.time_mag
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
    
  rendered = template.render(param=param)
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
      #targetLib.print_msg(inline)
      
      # search measure
      if((re.search("prop_in_out", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
        res_prop_in_out = "{:e}".format(float(sparray[2].strip()))
      elif((re.search("trans_out", inline, re.IGNORECASE))and not (re.search("failed",inline)) and not (re.search("Error",inline))):
        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
        res_trans_out = "{:e}".format(float(sparray[2].strip()))
        
      #if(meas_energy == 0):
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

  
  #targetLib.print_msg(str(res_prop_in_out)+" "+str(res_trans_out)+" "+str(res_energy_start)+" "+str(res_energy_end))
  # check spice finish successfully
  try:
    res_prop_in_out
  except NameError:
    targetHarness.mls.print_msg("Value res_prop_in_out is not defined!!")
    targetHarness.mls.print_msg("Check simulation result in work directory")
    sys.exit()
    
  try:
    res_trans_out
  except NameError:
    targetHarness.mls.print_msg("Value res_trans_out is not defined!!")
    targetHarness.mls.print_msg("Check simulation result in work directory")
    sys.exit()
    
  #if(meas_energy == 0):
  #  return float(res_prop_in_out), float(res_trans_out), float(res_energy_start), float(res_energy_end)
  #elif(meas_energy == 1):
  #  return float(res_prop_in_out), float(res_trans_out), \
  #      float(res_q_in_dyn), float(res_q_out_dyn), float(res_q_vdd_dyn), float(res_q_vss_dyn), \
  #      float(res_i_in_leak), float(res_i_vdd_leak), float(res_i_vss_leak)

  #-- hold result in targetHarness when meas_enrgy==1
  if(meas_energy == 1):
    targetHarness.dict_list2["prop"        ][load][slope] = float(res_prop_in_out )
    targetHarness.dict_list2["trans"       ][load][slope] = float(res_trans_out   )
    targetHarness.dict_list2["energy_start"][load][slope] = float(res_energy_start)
    targetHarness.dict_list2["energy_end"  ][load][slope] = float(res_energy_end  )
    targetHarness.dict_list2["q_in_dyn"    ][load][slope] = float(res_q_in_dyn    )
    targetHarness.dict_list2["q_out_dyn"   ][load][slope] = float(res_q_out_dyn   )
    targetHarness.dict_list2["q_vdd_dyn"   ][load][slope] = float(res_q_vdd_dyn   )
    targetHarness.dict_list2["q_vss_dyn"   ][load][slope] = float(res_q_vss_dyn   )
    targetHarness.dict_list2["i_in_leak"   ][load][slope] = float(res_i_in_leak   )
    targetHarness.dict_list2["i_vdd_leak"  ][load][slope] = float(res_i_vdd_leak  )
    targetHarness.dict_list2["i_vss_leak"  ][load][slope] = float(res_i_vss_leak  )

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

    targetHarness.dict_list2["eintl"][load][slope]=eintl
    targetHarness.dict_list2["ein"  ][load][slope]=ein
    targetHarness.dict_list2["cin"  ][load][slope]=cin
    targetHarness.dict_list2["pleak"][load][slope]=pleak

    #print(f"eintl={eintl}")
  #
  return float(res_energy_start), float(res_energy_end)
