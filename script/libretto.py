#!/usr/bin/env pytghon
# -*- coding: utf-8 -*-

import argparse, re, os, shutil, subprocess, sys, inspect, datetime 

import myConditionsAndResults as mcar
import myLibrarySetting as mls 
import myLogicCell as mlc

import myExport as me
import myExportDoc as med

import myExpectLogic as mel


import numpy as np

from char_run import runExpectation
#from char_comb import runCombInNOut1
#from char_seq import runFlop, genFileFlop_trial1
from myFunc import my_exit, startup
from jsoncomment import JsonComment
from pydantic import BaseModel, ConfigDict

def main():
  parser = argparse.ArgumentParser(description='argument')
  #parser.add_argument('-b','--batch'      , type=str, default="./cmd/gen_cmd.py", help='inport batch file')
  parser.add_argument('-l','--config_lib' , type=str, default="", help='inport jsonc file for lib')
  parser.add_argument('-m','--cell_comb'  , type=str, default="", help='inport jsonc file for cell_comb')
  parser.add_argument('-s','--cell_seq'   , type=str, default="", help='inport jsonc file for cell_seq')

  parser.add_argument('-f','--fab_process', type=str, default="OSU350" , help='FAB process name')
  parser.add_argument('-v','--cell_vendor', type=str, default="SAMPLE" , help='CELL vendor name')
  
  parser.add_argument('--condition', type=str  , default="TT"  , help='operationg condition name')
  parser.add_argument('--process'  , type=float, default=1.0   , help='process factor.')
  parser.add_argument('--temp'     , type=float, default=25.0  , help='temperature.')
  parser.add_argument('--vdd'      , type=float, default=5.0   , help='VDD voltage.')
  parser.add_argument('--vss'      , type=float, default=0.0   , help='VSS voltage.')
  parser.add_argument('--vnw'      , type=float, default=5.0   , help='NWELL voltage')
  parser.add_argument('--vpw'      , type=float, default=0.0   , help='PWELL voltage')
  
  args = parser.parse_args()
  #print(args.batch)

  #--- set json file
  if args.config_lib == "":
    args.config_lib = "./target/"+args.fab_process + "/" + args.cell_vendor + "/config_lib.jsonc"
  if args.cell_comb == "":
    args.cell_comb = "./target/"+args.fab_process + "/" + args.cell_vendor + "/cell_comb.jsonc"
  if args.cell_seq == "":
    args.cell_seq = "./target/"+args.fab_process + "/" + args.cell_vendor + "/cell_seq.jsonc"
    
  #--- check json file
  if os.path.isfile(args.config_lib):
    print (" [INF]: detected config_lib=" + args.config_lib)
  else:
    print (" [ERR]: not detected config_lib=" + args.config_lib)
    my_exit()
  
  if os.path.isfile(args.cell_comb):
    print (" [INF]: detected cell_comb=" + args.cell_comb)
  else:
    print (" [ERR]: not detected cell_comb=" + args.cell_comb)
    my_exit()

  if os.path.isfile(args.cell_seq):
    print (" [INF]: detected cell_seq=" + args.cell_seq)
  else:
    print (" [ERR]: not detected sell_seq=" + args.cell_seq)
    my_exit()

  
  #--- read setting from  jsonc(lib_common, char_dict)
  targetLib = mls.MyLibrarySetting()
  
  parser=JsonComment()
  with open (args.config_lib, "r") as f:
    config_lib = parser.load(f)
    #targetLib = targetLib.model_copy(update=config_lib)
    targetLib = mls.MyLibrarySetting(**config_lib)
    
  #--- targetLib : update from args
  config_from_args={"operating_conditions":args.condition,
                    "process"             :args.process,
                    "temperature"         :args.temp,
                    "vdd_voltage"         :args.vdd,
                    "vss_voltage"         :args.vss,
                    "nwell_voltage"       :args.vnw,
                    "pwell_voltage"       :args.vpw,
                    }
  targetLib = targetLib.model_copy(update=config_from_args)
  
  #--- targetLib : update & display 
  targetLib.update_name()
  targetLib.update_mag()
  targetLib.update_threshold_voltage()
  targetLib.print_variable()

  #--- targetLib : initialize workspace
  initializeFiles(targetLib) 
  targetLib.gen_lut_templates()

  #=====================================================
  # characterization
  num_gen_file = 0
  
#  #--- cell_comb.jsonc
#  cell_comb_info_list=[]
#  parser=JsonComment()
#  with open (args.cell_comb, "r") as f:
#    cell_comb_info_list = parser.load(f)
#    for info in cell_comb_info_list:
#      print(info)
#      
#      targetCell = mlc.MyLogicCell(mls=targetLib, **info)
#      targetCell.set_supress_message() 
#      targetCell.add_template()
#      targetCell.chk_netlist() 
#      targetCell.chk_ports()
#      targetCell.add_model() 
#      targetCell.add_function()
#      
#      #targetCell.print_variable()
#  
#      ## characterize
#      #harnessList2 = characterizeFiles(targetLib, targetCell)
#      harnessList = characterizeFiles(targetLib, targetCell)
#      os.chdir("../")
#
#      ## export
#      #me.exportFiles(targetLib, targetCell, harnessList2) 
#      #med.exportDoc(targetLib, targetCell, harnessList2)
#      
#      me.exportFiles(harnessList) 
#      med.exportDoc(harnessList) 
#      num_gen_file += 1
      
  #--- cell_seq.jsonc
  cell_seq_info_list=[]
  parser=JsonComment()
  with open (args.cell_seq, "r") as f:
    
    cell_seq_info_list = parser.load(f)
    for info in cell_seq_info_list:
      print(info)

      targetCell = mlc.MyLogicCell(mls=targetLib, **info)
      targetCell.set_supress_message() 
      targetCell.add_template()
      targetCell.chk_netlist() 
      targetCell.chk_ports()
      targetCell.add_model() 
      targetCell.add_function()

      ## characterize
      #harnessList2 = characterizeFiles(targetLib, targetCell)
      harnessList = characterizeFiles(targetLib, targetCell)
      os.chdir("../")

      ## export
      #me.exportFiles(targetLib, targetCell, harnessList2) 
      #med.exportDoc(targetLib, targetCell, harnessList2)
      
      me.exportFiles(harnessList) 
      med.exportDoc(harnessList) 
      num_gen_file += 1
      
  ## exit
  me.exitFiles(targetLib, num_gen_file) 


#def initializeFiles(targetLib, targetCell):
def initializeFiles(targetLib):
  ## initialize working directory
  if (targetLib.runsim.lower() == "true"):
    if os.path.exists(targetLib.work_dir):
      shutil.rmtree(targetLib.work_dir)
    os.mkdir(targetLib.work_dir)
  elif (targetLib.runsim.lower() == "false"):
    print("save past working directory and files\n")
  else:
    print ("illigal setting for set_runsim option: "+targetLib.runsim+"\n")
    my_exit()
  

#--def characterizeFiles(targetLib, targetCell):
#--  print ("characterize\n")
#--  os.chdir(targetLib.work_dir)
#--
#--  ## Register lut_template
#--  targetLib.gen_lut_templates(targetCell)
#--  targetCell.gen_lut_templates()
#--
#--  ## Branch to each logic function
#--  if(targetCell.logic == 'INV'):
#--    print ("INV\n")
#--    ## [in0, out0]
#--    expectationList2 = [['01','10'],['10','01']]
#--    return runCombIn1Out1(targetLib, targetCell, expectationList2,"neg")
#--
#--  elif(targetCell.logic == 'BUF'):
#--    print ("BUF\n")
#--    ## [in0, out0]
#--    expectationList2 = [['01','01'],['10','10']]
#--    return runCombIn1Out1(targetLib, targetCell, expectationList2,"pos")
#--
#--  elif(targetCell.logic == 'DEL'):
#--    print ("DEL\n")
#--    ## [in0, out0]
#--    expectationList2 = [['01','01'],['10','10']]
#--    return runCombIn1Out1(targetLib, targetCell, expectationList2,"pos")
#--
#--  elif(targetCell.logic == 'AND2'):
#--    print ("AND2\n")
#--    ## [in0, in1, out0]
#--    expectationList2 = [['01','1','01'],['10','1','10'],['1','01','01'],['1','10','10']]
#--    return runCombIn2Out1(targetLib, targetCell, expectationList2,"pos")
#--
#--  elif(targetCell.logic == 'AND3'):
#--    print ("AND3\n")
#--    ## [in0, in1, in2, in3, out0]
#--    expectationList2 = [['01','1','1','01'],['10','1','1','10'],\
#--                        ['1','01','1','01'],['1','10','1','10'],\
#--                        ['1','1','01','01'],['1','1','10','10']]
#--    return runCombIn3Out1(targetLib, targetCell, expectationList2,"pos")
#--
#--  elif(targetCell.logic == 'AND4'):
#--    print ("AND4\n")
#--    ## [in0, in1, in2, in3,  out0]
#--    expectationList2 = [['01','1','1','1','01'],['10','1','1','1','10'],\
#--                        ['1','01','1','1','01'],['1','10','1','1','10'],\
#--                        ['1','1','01','1','01'],['1','1','10','1','10'],\
#--                        ['1','1','1','01','01'],['1','1','1','10','10']]
#--    return runCombIn4Out1(targetLib, targetCell, expectationList2,"pos")
#--  
#--  elif(targetCell.logic == 'OR2'):
#--    print ("OR2\n")
#--    ## [in0, in1, out0]
#--    expectationList2 = [['01','0','01'],['10','0','10'],['0','01','01'],['0','10','10']]
#--    return runCombIn2Out1(targetLib, targetCell, expectationList2,"pos")
#--
#--  elif(targetCell.logic == 'OR3'):
#--    print ("OR3\n")
#--    ## [in0, in1, in2, out0]
#--    expectationList2 = [['01','0','0','01'],['10','0','0','10'],\
#--                        ['0','01','0','01'],['0','10','0','10'],\
#--                        ['0','0','01','01'],['0','0','10','10']]
#--    return runCombIn3Out1(targetLib, targetCell, expectationList2,"pos")
#--
#--  elif(targetCell.logic == 'OR4'):
#--    print ("OR4\n")
#--    ## [in0, in1, in2, in3, out0]
#--    expectationList2 = [['01','0','0','0','01'],['10','0','0','0','10'],\
#--                        ['0','01','0','0','01'],['0','10','0','0','10'],\
#--                        ['0','0','01','0','01'],['0','0','10','0','10'],\
#--                        ['0','0','0','01','01'],['0','0','0','10','10']]
#--    return runCombIn4Out1(targetLib, targetCell, expectationList2,"pos")
#--
#--  elif(targetCell.logic == 'NAND2'):
#--    print ("NAND2\n")
#--    ## [in0, in1, out0]
#--    expectationList2 = [['01','1','10'],\
#--                        ['10','1','01'],\
#--                        ['1','01','10'],\
#--                        ['1','10','01']]
#--    return runCombIn2Out1(targetLib, targetCell, expectationList2,"neg")
#--
#--  elif(targetCell.logic == 'NAND3'):
#--    print ("NAND3\n")
#--    ## [in0, in1, in2, out0]
#--    expectationList2 = [['01','1','1','10'],['10','1','1','01'],\
#--                        ['1','01','1','10'],['1','10','1','01'],\
#--                        ['1','1','01','10'],['1','1','10','01']]
#--    return runCombIn3Out1(targetLib, targetCell, expectationList2,"neg")
#--
#--  elif(targetCell.logic == 'NAND4'):
#--    print ("NAND4\n")
#--    ## [in0, in1, in2, out0]
#--    expectationList2 = [['01','1','1','1','10'],['10','1','1','1','01'],\
#--                        ['1','01','1','1','10'],['1','10','1','1','01'],\
#--                        ['1','1','01','1','10'],['1','1','10','1','01'],\
#--                        ['1','1','1','01','10'],['1','1','1','10','01']]
#--    return runCombIn4Out1(targetLib, targetCell, expectationList2,"neg")
#--
#--  elif(targetCell.logic == 'NOR2'):
#--    print ("NOR2\n")
#--    ## [in0, in1, out0]
#--    expectationList2 = [['01','0','10'],['10','0','01'],['0','01','10'],['0','10','01']]
#--    return runCombIn2Out1(targetLib, targetCell, expectationList2,"neg")
#--
#--  elif(targetCell.logic == 'NOR3'):
#--    print ("NOR3\n")
#--    ## [in0, in1, in2, out0]
#--    expectationList2 = [['01','0','0','10'],['10','0','0','01'],\
#--                        ['0','01','0','10'],['0','10','0','01'],\
#--                        ['0','0','01','10'],['0','0','10','01']]
#--    return runCombIn3Out1(targetLib, targetCell, expectationList2,"neg")
#--
#--  elif(targetCell.logic == 'NOR4'):
#--    print ("NOR4\n")
#--    ## [in0, in1, in2, in3, out0]
#--    expectationList2 = [['01','0','0','0','10'],['10','0','0','0','01'],\
#--                        ['0','01','0','0','10'],['0','10','0','0','01'],\
#--                        ['0','0','01','0','10'],['0','0','10','0','01'],\
#--                        ['0','0','0','01','10'],['0','0','0','10','01']]
#--    return runCombIn4Out1(targetLib, targetCell, expectationList2,"neg")
#--
#--  elif(targetCell.logic == 'AO21'):
#--    print ("AO21\n")
#--    ## [in0, in1, out0]
#--    expectationList2 = [['10','1','0','10'],['01','1','0','01'],\
#--                        ['1','10','0','10'],['1','01','0','01'],\
#--                        ['0','0','10','10'],['0','0','01','01']]
#--    return runCombIn3Out1(targetLib, targetCell, expectationList2,"pos")
#--
#--  elif(targetCell.logic == 'AO22'):
#--    print ("AO22\n")
#--    ## [in0, in1, out0]
#--    expectationList2 = [['10','1','0','0','10'],['01','1','0','0','01'],\
#--                        ['1','10','0','0','10'],['1','01','0','0','01'],\
#--                        ['0','0','10','1','10'],['0','0','01','1','01'],\
#--                        ['0','0','1','10','10'],['0','0','1','01','01']]
#--    return runCombIn4Out1(targetLib, targetCell, expectationList2,"pos")
#--
#--  elif(targetCell.logic == 'OA21'):
#--    print ("OA21\n")
#--    ## [in0, in1, out0]
#--    expectationList2 = [['10','0','1','10'],['01','0','1','01'],\
#--                        ['0','10','1','10'],['0','01','1','01'],\
#--                        ['0','1','10','10'],['0','1','01','01']]
#--    return runCombIn3Out1(targetLib, targetCell, expectationList2,"pos")
#--
#--  elif(targetCell.logic == 'OA22'):
#--    print ("OA22\n")
#--    ## [in0, in1, out0]
#--    expectationList2 = [['10','1','0','1','10'],['01','1','0','1','01'],\
#--                        ['0','10','0','1','10'],['0','01','0','1','01'],\
#--                        ['0','1','10','0','10'],['0','1','01','0','01'],\
#--                        ['0','1','0','10','10'],['0','1','0','10','01']]
#--    return runCombIn4Out1(targetLib, targetCell, expectationList2,"pos")
#--
#--  elif(targetCell.logic == 'AOI21'):
#--    print ("AOI21\n")
#--    ## [in0, in1, out0]
#--    expectationList2 = [['10','1','0','01'],['01','1','0','10'],\
#--                        ['1','10','0','01'],['1','01','0','10'],\
#--                        ['0','0','10','01'],['0','0','01','10']]
#--    return runCombIn3Out1(targetLib, targetCell, expectationList2,"neg")
#--
#--  elif(targetCell.logic == 'AOI22'):
#--    print ("AOI22\n")
#--    ## [in0, in1, out0]
#--    expectationList2 = [['10','1','0','0','01'],['01','1','0','0','10'],\
#--                        ['1','10','0','0','01'],['1','01','0','0','10'],\
#--                        ['0','0','10','1','01'],['0','0','01','1','10'],\
#--                        ['0','0','1','10','01'],['0','0','1','01','10']]
#--    return runCombIn4Out1(targetLib, targetCell, expectationList2,"neg")
#--
#--  elif(targetCell.logic == 'OAI21'):
#--    print ("OAI21\n")
#--    ## [in0, in1, out0]
#--    expectationList2 = [['10','0','1','01'],['01','0','1','10'],\
#--                        ['0','10','1','01'],['0','01','1','10'],\
#--                        ['0','1','10','01'],['0','1','01','10']]
#--    return runCombIn3Out1(targetLib, targetCell, expectationList2,"neg")
#--
#--  elif(targetCell.logic == 'OAI22'):
#--    print ("OAI22\n")
#--    ## [in0, in1, in2, out0]
#--    expectationList2 = [['10','0','1','1','01'],['01','0','1','1','10'],\
#--                        ['0','10','1','1','01'],['0','01','1','1','10'],\
#--                        ['1','1','10','0','01'],['1','1','01','0','10'],\
#--                        ['1','1','0','10','01'],['1','1','0','01','10']]
#--    return runCombIn4Out1(targetLib, targetCell, expectationList2,"neg")
#--
#--  elif(targetCell.logic == 'XOR2'):
#--    print ("XOR2\n")
#--    ## [in0, in1, out0]
#--    expectationList2 = [['01','0','01'],['10','0','10'],\
#--                        ['01','1','10'],['10','1','01'],\
#--                        ['0','01','01'],['0','10','10'],\
#--                        ['1','01','10'],['1','10','01']]
#--    return runCombIn2Out1(targetLib, targetCell, expectationList2,"pos")
#--
#--  elif(targetCell.logic == 'XNOR2'):
#--    print ("XNOR2\n")
#--    ## [in0, in1, out0]
#--    expectationList2 = [['01','0','10'],['10','0','01'],\
#--                        ['01','1','01'],['10','1','10'],\
#--                        ['0','01','10'],['0','10','01'],\
#--                        ['1','01','01'],['1','10','10']]
#--    return runCombIn2Out1(targetLib, targetCell, expectationList2,"pos")
#--
#--  elif(targetCell.logic == 'SEL2'):
#--    print ("SEL2\n")
#--    ## [in0, in1, sel, out]
#--    expectationList2 = [['01','0','0','01'],['10','0','0','10'],\
#--                        ['0','01','1','01'],['0','10','1','10'],\
#--                        ['1','0','01','10'],['1','0','10','01'],\
#--                        ['0','1','01','01'],['0','1','10','10']]
#--    return runCombIn3Out1(targetLib, targetCell, expectationList2,"pos")
#--
#--
#--  ## Branch to sequencial logics
#--  elif(targetCell.logic == 'DFF_PCPU'):
#--    print ("DFF, positive clock, positive unate\n")
#--    ## D1 & C01 -> Q01
#--    ## D0 & C01 -> Q10
#--    ##                   [D,   C,     Q]
#--    expectationList2 = [['01','0101', '01'], \
#--                        ['10','0101', '10']] 
#--    ## run spice deck for flop
#--    return runFlop(targetLib, targetCell, expectationList2)
#--
#--  elif(targetCell.logic == 'DFF_PCNU'):
#--    print ("DFF, positive clock, negative unate\n")
#--    ## D1 & C01 -> Q01
#--    ## D0 & C01 -> Q10
#--    ##                   [D,   C,     Q]
#--    expectationList2 = [['01','0101', '10'], \
#--                        ['10','0101', '01']] 
#--    ## run spice deck for flop
#--    return runFlop(targetLib, targetCell, expectationList2)
#--
#--  elif(targetCell.logic == 'DFF_NCPU'):
#--    print ("DFF, negative clock, positive unate\n")
#--    ## D1 & C01 -> Q01
#--    ## D0 & C01 -> Q10
#--    ##                   [D,   C,     Q]
#--    expectationList2 = [['01','1010', '01'], \
#--                        ['10','1010', '10']] 
#--    ## run spice deck for flop
#--    return runFlop(targetLib, targetCell, expectationList2)
#--
#--  elif(targetCell.logic == 'DFF_NCNU'):
#--    print ("DFF, negative clock, negative unate\n")
#--    ## D1 & C01 -> Q01
#--    ## D0 & C01 -> Q10
#--    ##                   [D,   C,     Q]
#--    expectationList2 = [['01','1010', '10'], \
#--                        ['10','1010', '01']] 
#--    ## run spice deck for flop
#--    return runFlop(targetLib, targetCell, expectationList2)
#--
#--  elif(targetCell.logic == 'DFF_PCPU_NR'):
#--    print ("DFF, positive clock, positive unate, async neg-reset\n")
#--    ## D1 & C01 -> Q01
#--    ## D0 & C01 -> Q10
#--    ## R10      -> Q10
#--    ##                   [D,   C,    R,    Q]
#--    expectationList2 = [['01','0101', '1', '01'], \
#--                        ['10','0101', '1', '10'], \
#--                        [ '1', '0101','10', '10']]
#--    ## run spice deck for flop
#--    return runFlop(targetLib, targetCell, expectationList2)
#--
#--  ## Not checked yet 24/05/15
#--  elif(targetCell.logic == 'DFF_PCPU_PR'):
#--    print ("DFF, positive clock, positive unate, async pos-reset\n")
#--    ## D1 & C01 -> Q01
#--    ## D0 & C01 -> Q10
#--    ## R01      -> Q10
#--    ##                   [D,   C,    R,    Q]
#--    expectationList2 = [['01','0101', '0', '01'], \
#--                        ['10','0101', '0', '10'], \
#--                        [ '1', '0101','01', '10']]
#--    ## run spice deck for flop
#--    return runFlop(targetLib, targetCell, expectationList2)
#--
#--  elif(targetCell.logic == 'DFF_NCPU_NR'):
#--    print ("DFF, negative clock, positive unate, async neg-reset\n")
#--    ## D1 & C01 -> Q01
#--    ## D0 & C01 -> Q10
#--    ## R10      -> Q10
#--    ##                   [D,   C,    R,    Q]
#--    expectationList2 = [['01', '1010', '1', '01'], \
#--                        ['10', '1010', '1', '10'], \
#--                        [ '1', '1010','10', '10']]
#--    ## run spice deck for flop
#--    return runFlop(targetLib, targetCell, expectationList2)
#--
#--  ## Not checked yet 24/05/15
#--  elif(targetCell.logic == 'DFF_NCPU_PR'):
#--    print ("DFF, negative clock, positive unate, async pos-reset\n")
#--    ## D1 & C01 -> Q01
#--    ## D0 & C01 -> Q10
#--    ## R01      -> Q10
#--    ##                   [D,   C,    R,    Q]
#--    expectationList2 = [['01', '1010', '0', '01'], \
#--                        ['10', '1010', '0', '10'], \
#--                        [ '1', '1010','01', '10']]
#--    ## run spice deck for flop
#--    return runFlop(targetLib, targetCell, expectationList2)
#--
#--  elif(targetCell.logic == 'DFF_PCPU_NS'):
#--    print ("DFF, positive clock, positive unate, async neg-set\n")
#--    ## D1 & C01 -> Q01
#--    ## D0 & C01 -> Q10
#--    ## S10      -> Q10
#--    ##                   [D,   C,    S,    Q]
#--    expectationList2 = [['01','0101', '1', '01'], \
#--                        ['10','0101', '1', '10'], \
#--                        [ '0', '0101','10', '01']]
#--    ## run spice deck for flop
#--    return runFlop(targetLib, targetCell, expectationList2)
#--
#--  ## Not checked yet 24/05/15
#--  elif(targetCell.logic == 'DFF_PCPU_PS'):
#--    print ("DFF, positive clock, positive unate, async pos-set\n")
#--    ## D1 & C01 -> Q01
#--    ## D0 & C01 -> Q10
#--    ## S01      -> Q10
#--    ##                   [D,   C,    S,    Q]
#--    expectationList2 = [['01','0101', '0', '01'], \
#--                        ['10','0101', '0', '10'], \
#--                        [ '0', '0101','01', '01']]
#--    ## run spice deck for flop
#--    return runFlop(targetLib, targetCell, expectationList2)
#--
#--  elif(targetCell.logic == 'DFF_NCPU_NS'):
#--    print ("DFF, positive clock, positive unate, async neg-set\n")
#--    ## D1 & C01 -> Q01
#--    ## D0 & C01 -> Q10
#--    ## S10      -> Q10
#--    ##                   [D,   C,    S,    Q]
#--    expectationList2 = [['01', '1010', '1', '01'], \
#--                        ['10', '1010', '1', '10'], \
#--                        [ '0', '1010','10', '01']]
#--    ## run spice deck for flop
#--    return runFlop(targetLib, targetCell, expectationList2)
#--
#--  ## Not checked yet 24/05/15
#--  elif(targetCell.logic == 'DFF_NCPU_PS'):
#--    print ("DFF, positive clock, positive unate, async pos-set\n")
#--    ## D1 & C01 -> Q01
#--    ## D0 & C01 -> Q10
#--    ## S01      -> Q10
#--    ##                   [D,   C,    S,    Q]
#--    expectationList2 = [['01', '1010', '0', '01'], \
#--                        ['10', '1010', '0', '10'], \
#--                        [ '0', '1010','01', '01']]
#--    ## run spice deck for flop
#--    return runFlop(targetLib, targetCell, expectationList2)
#--
#--  elif(targetCell.logic == 'DFF_PCPU_NRNS'):
#--    print ("DFF, positive clock, positive unate, async neg-reset, async neg-set\n")
#--    ## D1 & C01 -> Q01 QN10
#--    ## D0 & C01 -> Q10 QN01
#--    ## S10      -> Q01 QN10
#--    ## R10      -> Q10 QN01
#--    ##                   [D,   C,  S,   R,    Q]
#--    expectationList2 = [['01','0101', '1', '1', '01'], \
#--                        ['10','0101', '1', '1', '10'], \
#--                        ['0', '0101','10', '1', '01'], \
#--                        ['1', '0101', '1','10', '10']]
#--
#--    ## run spice deck for flop
#--    return runFlop(targetLib, targetCell, expectationList2)
#--
#--
#--  elif(targetCell.logic == 'DFF_NCPU_NRNS'):
#--    print ("DFF, negative clock, positive unate, async neg-reset, async neg-set\n")
#--    ## D1 & C01 -> Q01 QN10
#--    ## D0 & C01 -> Q10 QN01
#--    ## S10      -> Q01 QN10
#--    ## R10      -> Q10 QN01
#--    ##                   [D,   C,  S,   R,    Q]
#--    expectationList2 = [['01','1010','1',  '1', '01'], \
#--                        ['10','1010','1',  '1', '10'], \
#--                        ['0' ,'1010','10', '1', '01'], \
#--                        ['1' ,'1010', '1','10', '10']]
#--
#--    ## run spice deck for flop
#--    return runFlop(targetLib, targetCell, expectationList2)
#--
#--  else:
#--    print ("Target logic:"+targetCell.logic+" is not registered for characterization!\n")
#--    print ("Add characterization function for this program! -> die\n")
#--    my_exit()

def characterizeFiles(targetLib, targetCell):
  print ("characterize\n")
  os.chdir(targetLib.work_dir)

  ## Branch to each logic function
  if not targetCell.logic in mel.logic_dict.keys():
    print ("Target logic:"+targetCell.logic+" is not registered for characterization(not exist in myExpectLogic.py)!\n")
    print ("Add characterization function for this program! -> die\n")
    my_exit()

  #--
  print("cell=" + targetCell.cell + "(" + targetCell.logic + ")");

  logic_type=mel.logic_dict[targetCell.logic]["logic_type"]
  if   logic_type  == "comb":
    #rslt=runCombInNOut1(targetLib, targetCell, mel.logic_dict[targetCell.logic]["expect"])
    rslt=runExpectation(targetLib, targetCell, mel.logic_dict[targetCell.logic]["expect"])
  elif logic_type  == "seq":
    rslt=runExpectation(targetLib, targetCell, mel.logic_dict[targetCell.logic]["expect"])
  else:
    print(f"[Error] unknown logic_type={logic_type}.")
    my_exit()
    
  #
  return rslt

  #expectationList2 = [['01','10'],['10','01']]
  #return runCombIn1Out1(targetLib, targetCell, expectationList2,"neg")

  


if __name__ == '__main__':
 main()

