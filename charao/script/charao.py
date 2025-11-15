#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
# This file is part of charao.
#
# Based on OriginalProject (https://github.com/snishizawa/libretto)
# Original copyright (C) 2022-2025 Original Author
# Modified by MATSUDA Masahiro, 2025
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
# Originally named: libretto.py in OriginalProject
###############################################################################

import argparse, re, os, shutil, subprocess, sys, inspect
from jsoncomment import JsonComment
from pydantic import BaseModel, ConfigDict
import numpy as np

#from myConditionsAndResults import myConditionsAndResults as mcar
from .myLibrarySetting import MyLibrarySetting as Mls
from .myLogicCell      import MyLogicCell      as Mlc
from .myExpectCell import logic_dict 

from .myExportLib import exportFiles,exitFiles
from .myExportDoc import exportDoc
from .charao_run  import runExpectation
from .myFunc      import my_exit, startup, history

def main():
  parser = argparse.ArgumentParser(description='argument')
  parser.add_argument('-f','--fab_process' , type=str            , default="OSU035" , help='FAB process name(use for only search PATH)')
  parser.add_argument('-v','--cell_vendor' , type=str            , default="VENDOR" , help='CELL type or vendor ID(use for only search PATH)')
  parser.add_argument('-r','--cell_revision', type=str           , default="CB_REV2", help='CELL revision(use for only search PATH)')
  parser.add_argument('-g','--cell_group'  , choices=["std","io"], default="std"    , help='select cell_type(use for only to select macro)')
  parser.add_argument('-u','--usage_voltage',type=str            , default="V5P00"  , help='usage voltage(use for only to create file name)')

  parser.add_argument('-p','--process_corner', type=str         , default="TT"  , help='process condition')
  parser.add_argument('-t','--temp'     , type=float            , default=25.0  , help='temperature.')
  parser.add_argument('--vdd'           , type=float            , default=5.0   , help='VDD voltage.')
  parser.add_argument('--vss'           , type=float            , default=0.0   , help='VSS voltage.')
  parser.add_argument('--vnw'           , type=float            , default=5.0   , help='NWELL voltage')
  parser.add_argument('--vpw'           , type=float            , default=0.0   , help='PWELL voltage')

  parser.add_argument('--target'        , type=str              , default="./target"   , help='PATH to <target> directory')
  
  parser.add_argument('--cells_only'    , type=str, nargs="*"   , default=[]    , help='list of target cell names. blank meas all cells.')
  parser.add_argument('--measures_only' , type=str, nargs="*"   , default=[]    , help='list of measure_type names. blank meas all measure_type.')
  parser.add_argument('-s','--significant_digits'   , type=int  , default=3     , help='significant digits.')
  parser.add_argument('-b','--build_stamp',type=str             , default="b00" , help='build-stamp for output files.')
  parser.add_argument('-w','--work_dir' ,type=str               , default="work", help='work directory.')
  
  args = parser.parse_args()
  #print(args.batch)

  #--- barner
  startup()
  history()

  #--- set json file
  json_config_lib=""
  json_group_list = []
  
  json_path=f"{args.target}/{args.fab_process}/{args.cell_vendor}/{args.cell_revision}"
  for f in os.listdir(json_path):
    
    if not os.path.isfile(f"{json_path}/{f}") :
      continue
    elif f == "config_lib.jsonc":
      json_config_lib = f"{json_path}/{f}"
    elif f.startswith(args.cell_group) and f.endswith(".jsonc"):
      json_group_list.append(f)
    else:
      continue
    #
    print (f" [INF]: detected json={json_path}/{f}")
    
  
  if json_config_lib =="" or len(json_group_list)<1:
    print (f" [ERR]: not valid json files(config_lib.jsonc, {args.cell_group}*.jsonc)")
    my_exit()

  
  #--- read setting from  jsonc(lib_common, char_dict)
  parser=JsonComment()
  with open (json_config_lib, "r") as f:
    config_lib = parser.load(f)
    targetLib = Mls(**config_lib)
    
  #--- targetLib : update from args
  config_from_args={
                    "usage_voltage"       :args.usage_voltage,
                    "cell_group"          :args.cell_group,
                    "process_corner"      :args.process_corner,
                    "temperature"         :args.temp,
                    "vdd_voltage"         :args.vdd,
                    "vss_voltage"         :args.vss,
                    "nwell_voltage"       :args.vnw,
                    "pwell_voltage"       :args.vpw,
                    "cells_only"          :args.cells_only,
                    "measures_only"       :args.measures_only,
                    "significant_digits"  :args.significant_digits,
                    "work_dir"            :args.work_dir
                    }
  targetLib = targetLib.model_copy(update=config_from_args)

  #debug
  #print(targetLib.templates)
  
  #--- targetLib : update & display 
  targetLib.set_build_info(build_stamp=args.build_stamp)
  targetLib.update_name(build_stamp=args.build_stamp)
  targetLib.update_mag()
  targetLib.update_threshold_voltage()
  targetLib.print_variable()

  #--- targetLib : initialize workspace
  initializeFiles(targetLib) 
  targetLib.gen_lut_templates()

  #=====================================================
  # characterization
  num_gen_file = 0
  
  #--- std_comb_xxx.jsonc
  for jsonc in json_group_list:
    if not jsonc.startswith("std_comb"):
      continue
    
    cell_comb_info_list=[]
    parser=JsonComment()
    json_file=f"{json_path}/{jsonc}"
    with open (json_file, "r") as f:
      ## read cell_spice_path, cell
      path_cell=parser.load(f)

      ## sort by "cell" name
      comb_info_list = path_cell["cell_info"]
      cell_comb_info_list = sorted(comb_info_list, key=lambda x: x["cell"])
      
    #  
    for info in cell_comb_info_list:

      #-- for DEBUG
      if (targetLib.cells_only) and (info['cell'] not in targetLib.cells_only):
        continue
      else:
        print(f"[INFO] cell={info['cell']}")

      #
      targetCell = Mlc(mls=targetLib, **info)
      targetCell.set_spice_path(path_cell["spice_path"]) 
      targetCell.set_supress_message() 
      targetCell.add_template()
      targetCell.chk_netlist() 
      targetCell.chk_ports()
      targetCell.add_model() 
      targetCell.add_function()
      targetCell.add_vcode()
  
      ## characterize
      harnessList = characterizeFiles(targetLib, targetCell)
      #os.chdir("../")

      ## export
      exportFiles(targetCell=targetCell, harnessList=harnessList) 
      exportDoc(targetCell=targetCell, harnessList=harnessList) 
      num_gen_file += 1
      
  #--- std_seq_xxx.jsonc
  for jsonc in json_group_list:
    if not jsonc.startswith("std_seq"):
      continue
      
    cell_seq_info_list=[]
    parser=JsonComment()
    json_file=f"{json_path}/{jsonc}"
    with open (json_file, "r") as f:
      ## read cell_spice_path, cell
      path_cell=parser.load(f)
      
      ## sort by "cell" name
      seq_info_list = path_cell["cell_info"]
      cell_seq_info_list = sorted(seq_info_list, key=lambda x: x["cell"])
      
    #
    for info in cell_seq_info_list:

      #-- for DEBUG
      if (targetLib.cells_only) and (info['cell'] not in targetLib.cells_only):
        continue
      else:
        print(f"[INFO] cell={info['cell']}")

      #
      targetCell = Mlc(mls=targetLib, **info)
      targetCell.set_spice_path(path_cell["spice_path"]) 
      targetCell.set_supress_message() 
      targetCell.add_ff()
      targetCell.add_template()
      targetCell.chk_netlist() 
      targetCell.chk_ports()
      targetCell.add_model() 
      targetCell.add_function()
      targetCell.add_vcode()

      ## characterize
      harnessList = characterizeFiles(targetLib, targetCell)
      #os.chdir("../")
      
      ## export
      exportFiles(targetCell=targetCell, harnessList=harnessList) 
      exportDoc(targetCell=targetCell, harnessList=harnessList) 
      num_gen_file += 1

      
  #--- io_xxx.jsonc
  for jsonc in json_group_list:

    if not jsonc.startswith("io_"):
      continue

    cell_io_info_list=[]
    parser=JsonComment()
    json_file=f"{json_path}/{jsonc}"
    with open (json_file, "r") as f:
      ## read cell_spice_path, cell
      path_cell=parser.load(f)
      
      ## sort by "cell" name      
      io_info_list = path_cell["cell_info"]
      cell_io_info_list = sorted(io_info_list, key=lambda x: x["cell"])

    #  
    for info in cell_io_info_list:

      #-- for DEBUG
      if (targetLib.cells_only) and (info['cell'] not in targetLib.cells_only):
        continue
      else:
        print(f"[INFO] cell={info['cell']}")

      #
      targetCell = Mlc(mls=targetLib, **info)
      targetCell.set_spice_path(path_cell["spice_path"]) 
      targetCell.set_supress_message() 
      targetCell.add_io()
      targetCell.add_template()
      targetCell.chk_netlist() 
      targetCell.chk_ports()
      targetCell.add_model() 
      targetCell.add_function()
      targetCell.add_vcode()
  
      ## characterize
      harnessList = characterizeFiles(targetLib, targetCell)
      #os.chdir("../")

      ## export
      exportFiles(targetCell=targetCell, harnessList=harnessList) 
      exportDoc(targetCell=targetCell, harnessList=harnessList) 
      num_gen_file += 1

  #--- 
      
  ## exit
  exitFiles(targetLib, num_gen_file) 



def initializeFiles(targetLib):
  ## initialize working directory
  if (targetLib.runsim.lower() == "true"):
    if os.path.exists(targetLib.work_dir):
      shutil.rmtree(targetLib.work_dir)
    #os.mkdir(targetLib.work_dir)
    os.makedirs(targetLib.work_dir, exist_ok=True)
  elif (targetLib.runsim.lower() == "false"):
    print("save past working directory and files\n")
  else:
    print ("illigal setting for set_runsim option: "+targetLib.runsim+"\n")
    my_exit()
  
def characterizeFiles(targetLib, targetCell):

  current_dir = os.getcwd()
  rslt=None
  
  try:
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
      rslt=runExpectation(targetLib, targetCell, logic_dict[targetCell.logic]["expect"])
    elif logic_type  == "seq":
      rslt=runExpectation(targetLib, targetCell, logic_dict[targetCell.logic]["expect"])
    elif logic_type  == "io":
      rslt=runExpectation(targetLib, targetCell, logic_dict[targetCell.logic]["expect"])
    else:
      print(f"[Error] unknown logic_type={logic_type}.")
      my_exit()

  except Exception as e:
    print(f"[Error] An exception occurred: {str(e)}")

  finally:
    os.chdir(current_dir)

  #
  return rslt


if __name__ == '__main__':
 main()

