#!/usr/bin/env pytghon
# -*- coding: utf-8 -*-

import argparse, re, os, shutil, subprocess, sys, inspect, datetime 
from jsoncomment import JsonComment
from pydantic import BaseModel, ConfigDict
import numpy as np

#from myConditionsAndResults import myConditionsAndResults as mcar
from myLibrarySetting import MyLibrarySetting as Mls
from myLogicCell      import MyLogicCell      as Mlc
from myExpectCell import logic_dict 

from myExportLib import exportFiles,exitFiles
from myExportDoc import exportDoc
from char_run    import runExpectation
from myFunc      import my_exit, startup, history

def main():
  parser = argparse.ArgumentParser(description='argument')
  parser.add_argument('-g','--cell_group'  , choices=["std","io"], default="std", help='select cell_type')
  parser.add_argument('-f','--fab_process' , type=str            , default="OSU035" , help='FAB process name')
  parser.add_argument('-v','--cell_vendor' , type=str            , default="SAMPLE" , help='CELL vendor name')
  parser.add_argument('-u','--usage_voltage',type=float          , default=5.0      , help='usage voltage')

  parser.add_argument('-p','--process_corner', type=str         , default="TT"  , help='process condition')
  parser.add_argument('-t','--temp'     , type=float            , default=25.0  , help='temperature.')
  parser.add_argument('--vdd'           , type=float            , default=5.0   , help='VDD voltage.')
  parser.add_argument('--vss'           , type=float            , default=0.0   , help='VSS voltage.')
  parser.add_argument('--vnw'           , type=float            , default=5.0   , help='NWELL voltage')
  parser.add_argument('--vpw'           , type=float            , default=0.0   , help='PWELL voltage')

  parser.add_argument('--cells_only'    , type=str, nargs="*"   , default=[]    , help='list of target cell names. blank meas all cells.')
  parser.add_argument('--measures_only' , type=str, nargs="*"   , default=[]    , help='list of measure_type names. blank meas all measure_type.')
  parser.add_argument('-s','--significant_digits'   , type=int  , default=3     , help='significant digits.')
  
  args = parser.parse_args()
  #print(args.batch)

  #--- barner
  startup()
  history()

  #--- set json file
  json_config_lib = "./target/"+args.fab_process + "/" + args.cell_vendor + "/config_lib.jsonc"
  json_cell_comb  = "./target/"+args.fab_process + "/" + args.cell_vendor + "/cell_comb.jsonc"
  json_cell_seq   = "./target/"+args.fab_process + "/" + args.cell_vendor + "/cell_seq.jsonc"
  json_cell_io    = "./target/"+args.fab_process + "/" + args.cell_vendor + "/cell_io.jsonc"
    
  #--- check json file
  if args.cell_group == "std":
    json_list=[json_config_lib,json_cell_comb, json_cell_seq]
  else:
    json_list=[json_config_lib,json_cell_io]
    
  for j in json_list:
    if os.path.isfile(j):
      print (" [INF]: detected json=" + j)
    else:
      print (" [ERR]: not json=" + j)
      my_exit()

  
  #--- read setting from  jsonc(lib_common, char_dict)
  parser=JsonComment()
  with open (json_config_lib, "r") as f:
    config_lib = parser.load(f)
    targetLib = Mls(**config_lib)
    
  #--- targetLib : update from args
  config_from_args={"usage_voltage"       :args.usage_voltage,
                    "process_corner"      :args.process_corner,
                    "temperature"         :args.temp,
                    "vdd_voltage"         :args.vdd,
                    "vss_voltage"         :args.vss,
                    "nwell_voltage"       :args.vnw,
                    "pwell_voltage"       :args.vpw,
                    "cells_only"          :args.cells_only,
                    "measures_only"       :args.measures_only,
                    "significant_digits"  :args.significant_digits
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
  
  #--- cell_comb.jsonc
  if args.cell_group == "std":
    
    cell_comb_info_list=[]
    parser=JsonComment()
    with open (json_cell_comb, "r") as f:
      cell_comb_info_list = parser.load(f)

    #  
    for info in cell_comb_info_list:

      #-- for DEBUG
      if (targetLib.cells_only) and (info['cell'] not in targetLib.cells_only):
        continue
      else:
        print(f"[INFO] cell={info['cell']}")

      #
      targetCell = Mlc(mls=targetLib, **info)
      targetCell.set_supress_message() 
      targetCell.add_template()
      targetCell.chk_netlist() 
      targetCell.chk_ports()
      targetCell.add_model() 
      targetCell.add_function()
  
      ## characterize
      harnessList = characterizeFiles(targetLib, targetCell)
      os.chdir("../")

      ## export
      exportFiles(harnessList=harnessList) 
      exportDoc(harnessList=harnessList) 
      num_gen_file += 1
      
  #--- cell_seq.jsonc
  if args.cell_group == "std":
      
    cell_seq_info_list=[]
    parser=JsonComment()
    with open (json_cell_seq, "r") as f:  
      cell_seq_info_list = parser.load(f)

    #
    for info in cell_seq_info_list:

      #-- for DEBUG
      if (targetLib.cells_only) and (info['cell'] not in targetLib.cells_only):
        continue
      else:
        print(f"[INFO] cell={info['cell']}")

      #
      targetCell = Mlc(mls=targetLib, **info)
      targetCell.set_supress_message() 
      targetCell.add_template()
      targetCell.chk_netlist() 
      targetCell.chk_ports()
      targetCell.add_model() 
      targetCell.add_function()
      targetCell.add_ff()

      ## characterize
      harnessList = characterizeFiles(targetLib, targetCell)
      os.chdir("../")
      
      ## export
      exportFiles(harnessList) 
      exportDoc(harnessList) 
      num_gen_file += 1

      
  #--- cell_io.jsonc
  if args.cell_group == "io":

    print(f"[Error] io is not supported.")
    my_exit()
    
    cell_io_info_list=[]
    parser=JsonComment()
    with open (json_cell_io, "r") as f:    
      cell_io_info_list = parser.load(f)

    #
    for info in cell_io_info_list:
      
      #-- for DEBUG
      if (targetLib.cells_only) and (info['cell'] not in targetLib.cells_only):
        continue
      else:
        print(f"[INFO] cell={info['cell']}")

      #--
        
  ## exit
  exitFiles(targetLib, num_gen_file) 



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
  
def characterizeFiles(targetLib, targetCell):
  print ("characterize\n")
  os.chdir(targetLib.work_dir)

  ## Branch to each logic function
  if not targetCell.logic in logic_dict.keys():
    print ("Target logic:"+targetCell.logic+" is not registered for characterization(not exist in myExpectLogic.py)!\n")
    print ("Add characterization function for this program! -> die\n")
    my_exit()

  #--
  print("cell=" + targetCell.cell + "(" + targetCell.logic + ")");

  logic_type=logic_dict[targetCell.logic]["logic_type"]
  if   logic_type  == "comb":
    #rslt=runCombInNOut1(targetLib, targetCell, logic_dict[targetCell.logic]["expect"])
    rslt=runExpectation(targetLib, targetCell, logic_dict[targetCell.logic]["expect"])
  elif logic_type  == "seq":
    rslt=runExpectation(targetLib, targetCell, logic_dict[targetCell.logic]["expect"])
  else:
    print(f"[Error] unknown logic_type={logic_type}.")
    my_exit()
    
  #
  return rslt


if __name__ == '__main__':
 main()

