import argparse, re, os, shutil, subprocess, inspect
import copy
from pydantic import BaseModel, model_validator, Field
from typing import Any, Dict, TYPE_CHECKING, List, Optional
import statistics as st
from itertools import groupby

from myFunc import my_exit

from myLibrarySetting       import MyLibrarySetting as Mls 
from myExpectLogic          import logic_dict
#import myExpectLogic                                as mel
from myItem                 import MyItemTemplate

if TYPE_CHECKING:
  from myConditionsAndResults import MyConditionsAndResults  as Mcar

class MyLogicCell(BaseModel):
  #=====================================
  # class variable
  
  #=====================================
  # instance variable by BaseModel

  #-- reference
  mls: Optional[Mls] = None
  
  cell      : str = None;     ## cell name
  logic     : str = None;     ## logic name
  area      : float= None;    ## set area
  spice     : str  = None;    ## spice file name
  #functions : list[str] = Field(default_factory=list); ## cell function (must be remove )
  functions : Dict[str,str] = Field(default_factory=dict); ## cell function
  ports_dict: Dict[str,str] = Field(default_factory=dict); ## spice-port/name mapper
  inports   : list[str] = Field(default_factory=list); ## inport pins
  outports  : list[str] = Field(default_factory=list); ## outport pins
  biports   : list[str] = Field(default_factory=list); ## inout port pins
  clock     : str= None;      ## clock pin for flop
  set       : str= None;      ## set pin for flop
  reset     : str= None;      ## reset pin for flop 
  vports    : list[str] = Field(default_factory=list); ## vdd/vss port pins
  #cins      : list[float] = Field(default_factory=list); ## inport caps
  cins      : dict[str,float] = Field(default_factory=dict); ## inport caps. cins={"inport",cap}
  
  #cclks     : list[float] = Field(default_factory=list);      ## clock pin cap. for flop
  #csets     : list[float] = Field(default_factory=list);      ## set pin cap. for flop
  #crsts     : list[float] = Field(default_factory=list);      ## reset pin cap. for flop 
  #flops     : list[str]   = Field(default_factory=list);      ## registers 
  #functions : list[str]   = Field(default_factory=list);  ## logic/flop functions 
  #slope     : list[float] = Field(default_factory=list);      ## inport slope
  template_kgn: list[list[str]]= Field(default_factory=list);     ## kind/grid/name of template
  template: dict[str,MyItemTemplate] = Field(default_factory=lambda:{
    "const"  :None,
    "delay"  :None,
    "mpw"    :None,
    "passive":None,
    "power"  :None})
  
  #cslope    : float          = 0;      ## inport clock slope
  #load      : list[float] = Field(default_factory=list);       ## outport load
  #load_name      : str         = "load";  ## load name
  max_load4out: dict[str,float] = Field(default_factory=dict);   ## outport load {"outport",max capacitance}
  max_trans4in: dict[str,float] = Field(default_factory=dict);   ## max transition {"inport",max transition}


  #timestep_res  : float       = 0.1;   ## simulation timestep resolution in slope[0]
  #timestep_res  : float       = 0.001;   ## simulation timestep
  #slope_name : list[str]  = Field(default_factory=list); ## slope name
  #load_name  : list[str]  = Field(default_factory=list);  ## load name
  #simulation_timestep : float = 0;      ## simulation timestep 
  isexport            : int = 0;   ## exported or not
  isexport2doc        : int = 0; ## exported to doc or not
  isflop              : int = 0;     ## DFF or not
  ## setup 
  #sim_setup_lowest    : float = 0.0;    ## fastest simulation edge (pos. val.) 
  #sim_setup_highest   : float = 0.0;   ## lowest simulation edge (pos. val.) 
  #sim_setup_timestep  : float = 0.0;  ## timestep for setup search (pos. val.) 
  ## hold                        
  #sim_hold_lowest     : float = 0.0;     ## fastest simulation edge (pos. val.) 
  #sim_hold_highest    : float = 0.0;    ## lowest simulation edge (pos. val.) 
  #sim_hold_timestep   : float = 0.0;   ## timestep for hold search (pos. val.) 
  ## power
  pleak_cell   : float=0.0;          ## cell leakage power
  pleak_icrs   : dict[str,float] = Field(default_factory=dict);## leakage power with input condition. pleak_icrs={"condition",val}
  #pleak        : list[list[float]] = Field(default_factory=list);   ## cell leak power
  
  #inport_pleak : list[list[float]] = Field(default_factory=list);   ## inport leak power
  #inport_cap   : list[float]       = Field(default_factory=list);   ## inport cap
  ## message
  supress_msg  : str = None;        ## supress message

  #-- local variable
  netlist      : str  = None;    ## spice file name & PATH
  definition   : str  = None;    ## dut subskt name in spice file. 
  instance     : str  = None;    ## DUT instance name in TB.
  model        : str  = "./model/TT.sp";
  
  #constraint_template_name     : str = None
  #recovery_template_name       : str = None
  #removal_template_name        : str = None
  #mpw_constraint_template_name : str = None
  #passive_power_template_name  : str = None
  #delay_template_name          : str = None
  #power_template_name          : str = None 

  #
  #model_config ={"frozen":True};  #-- not writable
  
  #--def __init__ (self):  #-- not use

  lut_names  : list[str]= Field(default_factory=list);     ## template name(const,delay,energy,passive)
  lut_template: Dict[str, MyItemTemplate] = Field(default_factory=lambda: {"const"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "delay"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "energy" : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "passive": MyItemTemplate(name="", index_1=[], index_2=[])})
  
  def print_variable(self):
    for k,v in self.__dict__.items():
      print(f"   {k}={v}")
  
  #--def __init__ (self):

#--  ##                                                #
#--  ##-- add functions for both comb. and seq. cell --#   
#--  ##                                                #
#--  def add_cell(self, line="tmp"):
#--    tmp_array = line.split('-')
#--    ## expected format : add_cell -n(name) AND_X1 
#--    ##                            -l(logic) AND2 
#--    ##                             -i(inports) A B 
#--    ##                             -o(outports) YB
#--    ##                             -f(function) YB=A*B
#--    for options in tmp_array:
#--
#--      ## add_cell command 
#--      if(re.match("^add_cell", options)):
#--        continue
#--      ## -n option
#--      elif(re.match("^n ", options)):
#--        tmp_array2 = options.split() 
#--        self.cell = tmp_array2[1] 
#--        #print (self.cell)
#--      ## -l option
#--      elif(re.match("^l ", options)):
#--        tmp_array2 = options.split() 
#--        self.logic = tmp_array2[1] 
#--        #print (self.logic)
#--      ## -i option
#--      elif(re.match("^i ", options)):
#--        tmp_array2 = options.split() 
#--        for w in tmp_array2:
#--          self.inports.append(w)
#--        self.inports.pop(0) # delete first object("-i")
#--        #print (self.inports)
#--      ## -o option
#--      ## -f option override -o option
#--      ## currently, -o is not used
#--      elif(re.match("^o ", options)):
#--        tmp_array2 = options.split() 
#--        #for w in tmp_array2:
#--        # self.outports.append(w)
#--        #self.outports.pop(0) # delete first object("-o")
#--        #print (self.outports)
#--      ## -f option
#--      elif(re.match("^f ", options)):
#--        tmp_array2 = options.split() 
#--        #print (tmp_array2)
#--        tmp_array2.pop(0) # delete first object("-f")
#--        for w in tmp_array2:
#--          tmp_array3 = w.split('=') 
#--          self.outports.append(tmp_array3[0])
#--          self.functions.append(tmp_array3[1])
#--#       print ("func:"+str(self.functions))
#--#       print ("outp:"+str(self.outports))
#--#       print (self.functions)
#--#       print (self.outports)
#--      ## undefined option 
#--      else:
#--        print("ERROR: undefined option:"+options) 
#--        my_exit()
#--    # do not use print_msg 
#--    print ("finish add_cell")

  def set_supress_message(self):
    self.supress_msg = self.mls.supress_msg 

  def print_msg(self, message=""):
    if((self.supress_msg.lower() == "false")or(self.supress_msg.lower() == "f")):
      print(message)

  #def add_slope(self, targetLib, line="tmp"):
  #  tmp_array = line.split()
  #  for w in tmp_array:
  #    self.slope.append(float(w))
  #  #print (self.slope)

  def add_template(self):

    for kgn in self.template_kgn:
      k=kgn[0]
      g=kgn[1]
      n=kgn[2]

      # check kind/grid/name in library
      idx_src = next(
        (i for i, t in enumerate(self.mls.templates) if t.kind == k and t.grid == g and t.name == n),
        None  # no entry
      )

      if not idx_src:
        print(f"[Error] unique template ={k}/{g}/{n} is not exist in targetLib.templates.")
        my_exit()
        
      # check kind in targetCell
      if k in self.template.keys():
        self.template[k] = self.mls.templates[idx_src]
        print(f"   [Info] add template={k}{g}{n}.")

      else:
        print(f"   [Error] unknown template kind{k}.")
        my_exit()
        
        
  
#  def add_slope_load(self, targetLib:Mls):
#                                                     
#    for typ in ["out","in_tmg","in_pwr"]:
#      if (typ in self.slope_load_name.keys())  and (self.slope_load_name[typ] != ""):
#        name=self.slope_load_name[typ];
#        if not name in targetLib.slope_loads.keys():
#          print(f"[Error] slope_load name ={name} is not exist in targetLib.load_sopes.")
#          my_exit()
#        else:
#          self.slope_load_val[typ]=targetLib.slope_loads[name]; #--- reference copy
#          self.print_msg(f" add slope/load name={name} for {typ} analyze.") 

#nouse  def return_index_str(self, typ:str, kind:str):
#nouse    typ_list=self.slope_load_val.keys() 
#nouse    if not typ in typ_list:
#nouse      print(f"[Error] typ ={typ} is not exist in targetCell.slope_load_val.")
#nouse      my_exit()
#nouse      
#nouse    kind_list=["slope","load"]
#nouse    if not kind in kind_list:
#nouse      print(f"[Error] kind ={kind} is not exist in targetCell.slope_load_val.")
#nouse      my_exit()
#nouse
#nouse    index_list=self.slope_load_val[typ][kind]
#nouse    outline = '("' + ','.join(str(x) for x in index_list) + '");'
#nouse
#nouse    return outline
      
#  def add_load(self, targetLib):
#    flag_match = 0
#    jlist = []
#    # search load name from 2D load array
#    for jlist in targetLib.load:
#        if (jlist[-1] != self.load_name):
#          continue
#        else:
#          flag_match = 1
#          break
#    if (flag_match == 0): # exit loop w/o match
#      print("cannot find load: "+self.load_name)
#      my_exit()
#    self.load = copy.deepcopy(jlist)
#    self.load.pop(-1) # delete load name
#    self.print_msg("add load "+self.load_name) 

#  def return_slope(self):
#    jlist = self.slope
#    outline = "(\""
#    #mmm self.lut_prop = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    return outline
#
#  def return_load(self):
#    jlist = self.load
#    outline = "(\""
#    #mmm self.lut_prop = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    return outline

  #def add_area(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.area = float(tmp_array[1]) 

  def update_max_trans4in(self, port_name:str, new_value:float):

    ## check port
    if not port_name in self.inports:
      print(f"[Error] inport={port_name} is not exist in logic={self.logic}.")
      my_exit()
      
    ## initialize
    if not port_name in self.max_trans4in.keys():
      self.max_trans4in[port_name]=0.0

    ## update value
    #mag=self.mls.time_mag
    #self.max_trans4in[port_name] = max(new_value/mag, self.max_trans4in[port_name])
    self.max_trans4in[port_name] = max(new_value, self.max_trans4in[port_name])


    
  def update_max_load4out(self, port_name:str, new_value:float):

    ## check port
    if not port_name in self.outports:
      print(f"[Error] outport={port_name} is not exist in logic={self.logic}.")
      my_exit()
      
    ## initialize
    if not port_name in self.max_load4out.keys():
      self.max_load4out[port_name]=0.0

    ## update value
    #mag=self.mls.capacitance_mag
    #self.max_load4out[port_name] = max(new_value/mag, self.max_load4out[port_name])
    self.max_load4out[port_name] = max(new_value, self.max_load4out[port_name])



    
  def chk_netlist(self):
    targetLib=self.mls
    self.netlist = targetLib.cell_spice_path +"/"+self.spice
    self.definition = None

    ## search cell name in the netlist
    if not os.path.exists(self.netlist):
      print("  netlist is not exits. {0}".format(self.netlist))
      my_exit()
      
    with open(self.netlist, 'r') as f:
      for line in f:

        #print("self.cell.lower:"+str(self.cell.lower()))
        #print("line.lower:"+str(line.lower()))
        if((self.cell.lower() in line.lower()) and (".subckt" in line.lower())):
          print("Cell definition found for: "+str(self.cell))
          #print(line)
          self.definition = line
        
    ## if cell name is not found, show error
    if(self.definition == None):
      if((self.cell == None) and (self.cell == None)):
        print("Cell definition not found. Please use add_cell command to add your cell")
      elif(self.cell == None):
        print("Cell is not defined by add_cell. Please use add_cell command to add your cell")
      elif(self.logic == None):
        print("Logic is not defined by add_cell. Please use add_cell command to add your cell")
      else:
        print("Options for add_cell command might be wrong")
        print("Defined cell: "+self.cell)
        print("Defined logic: "+self.logic)
      my_exit()

  def chk_ports(self):
    self.instance = ""
    
    #-- get port name from spice file
    ports_s=self.definition.split(); # .subckt NAND2_1X A B YB VDD VSS VNW VPW
    ports_s.pop(0);                   # NAND2_1X A B YB VDD VSS VNW VPW
    cell_name=ports_s.pop(0);                   # A B YB VDD VSS VNW VPW

    #-- check port_map in cell_comb.json
    pos_s=0
    for name_j,name_tb in self.ports_dict.items():
      pos_s=pos_s + 1
      name_s = ports_s.pop(0);
      #print("pos={0}, spice={1}, json={2}.".format(pos_s, name_s, name_j))
      if name_s.upper() != name_j.upper():
        print("  Pin Name missmatch in PinPos={0}. spice={1}/json={2}.".format(pos_s,name_s,name_j))
        my_exit()

      #--- check name_tb
      if name_tb.upper().startswith("I"):
        self.inports.append(name_tb.lower())
      elif name_tb.upper().startswith("O"):
        self.outports.append(name_tb.lower())
      elif name_tb.upper().startswith("B"):
        self.biports.append(name_tb.lower())
      elif name_tb.upper().startswith("C"):
        self.clock.append(name_tb.lower())
      elif name_tb.upper().startswith("S"):
        self.set.append(name_tb.lower())
      elif name_tb.upper().startswith("R"):
        self.reset.append(name_tb.lower())
      elif name_tb.upper().startswith("V"):
        self.vports.append(name_tb.lower())
      else:
        print("  UnKnown port-name for TB in ports_dict(JSON file). {0}:{1}.".format(name_j,name_tb))
        my_exit()

      #--- 
      self.instance += ' ' + name_tb.lower()
      
    self.instance = 'XDUT' + self.instance + " " + cell_name
    
  def add_model(self):
    targetLib=self.mls
    self.model = targetLib.model_path +"/.model_"+targetLib.process_name +"_"+targetLib.operating_conditions+".sp"

    if not os.path.exists(self.model):
      print("  model file is not exits. {0}".format(self.model))
      my_exit()
      
  #def add_simulation_timestep(self):
  #  self.simulation_timestep =self.slope[0] * self.timestep_res 

  def set_exported(self):
    self.isexport = 1 

  def set_exported2doc(self):
    self.isexport2doc = 1
        
#  def set_inport_cap_pleak(self, index, harness):
#    ## average leak power of all harness
#    #self.pleak += harness.pleak 
#    self.pleak += harness.avg["pleak"] 
#
#    
##                                 #
##-- add functions for seq. cell --#    
##                                 #
  def add_flop(self, line="tmp"):
    tmp_array = line.split('-')
    ## expected format : add_floop -n(name) DFFRS_X1 /
    ##                             -l(logic)    DFFARAS : DFF w async RST and async SET
    ##                              -i(inports)  DATA 
    ##                              -c(clock)    CLK 
    ##                              -s(set)      SET   (if used) 
    ##                              -r(reset)    RESET (if used)
    ##                              -o(outports) Q QN
    ##                              -q(flops)    IQ IQN
    ##                              -f(function) Q=IQ QN=IQN
    self.isflop = 1  ## set as flop
    for options in tmp_array:

      ## add_flop command 
      if(re.match("^add_flop", options)):
        continue
      ## -n option (subckt name)
      elif(re.match("^n ", options)):
        tmp_array2 = options.split() 
        self.cell = tmp_array2[1] 
        #print (self.cell)
      ## -l option (logic type)
      elif(re.match("^l ", options)):
        tmp_array2 = options.split() 
        self.logic = tmp_array2[1] 
        #print (self.logic)
      ## -i option (input name)
      elif(re.match("^i ", options)):
        tmp_array2 = options.split() 
        for w in tmp_array2:
          self.inports.append(w)
        self.inports.pop(0) # delete first object("-i")
        #print (self.inports)
      ## -c option (clock name)
      elif(re.match("^c ", options)):
        tmp_array2 = options.split() 
        self.clock = tmp_array2[1] 
        #print (self.clock)
      ## -s option (set name)
      elif(re.match("^s ", options)):
        tmp_array2 = options.split() 
        self.set = tmp_array2[1] 
        #print (self.set)
      ## -r option (reset name)
      elif(re.match("^r ", options)):
        tmp_array2 = options.split() 
        self.reset = tmp_array2[1] 
        print (self.reset)
      ## -o option (output name)
      elif(re.match("^o ", options)):
        tmp_array2 = options.split() 
        for w in tmp_array2:
          self.outports.append(w)
        self.outports.pop(0) ## delete first object("-o")
        #print (self.outports)
      ## -q option (storage name)
      elif(re.match("^q ", options)):
        tmp_array2 = options.split() 
        for w in tmp_array2:
          self.flops.append(w)
        self.flops.pop(0) ## delete first object("-q")
        #print (self.flops)
      ## -f option (function name)
      elif(re.match("^f ", options)):
        tmp_array2 = options.split() 
        #print (tmp_array2)
        tmp_array2.pop(0) ## delete first object("-f")
        for w in tmp_array2:
          tmp_array3 = w.split('=') 
          for o in self.outports:
            if(o == tmp_array3[0]):
              self.functions.append(tmp_array3[1])
        #print (self.functions)
      ## undefined option 
      else:
        print("ERROR: undefined option:"+options+"\n")  
        my_exit() 
    # do not use print_msg 
    print ("finish add_flop")

  def add_function(self):
    if not self.logic in logic_dict.keys():
      print("  logic="+self.logic + " is not exist in MyExpectLogic.py.");
      my_exit();


    self.functions = logic_dict[self.logic]["functions"]
    #for k,v in logic_dict["functions"].items():
    #  print(k , v)
    #  for o in self.outports:
    #    if(o.upper() == k.upper()):
    #      self.functions.append(v)
    
    #tmp_array1 = logic_dict["function"].split(',')
    #for f in tmp_array1:
    #  tmp_array3 = f.split("=")
    #  for o in self.outports:
    #    if(o.upper() == tmp_array3[0].upper()):
    #      #self.functions.append(tmp_array3[1])
    #      self.functions.append(f)
          
    print("add function: " + str(self.functions))
    
#  def add_clock_slope(self, line="tmp"):
#    tmp_array = line.split()
#    ## if auto, amd slope is defined, use mininum slope
#    if (tmp_array[1] == 'auto'):
#      self.cslope = float(self.slope[0]) 
#      self.print_msg ("auto set clock slope as mininum slope.")
#    else:
#      self.cslope = float(tmp_array[1]) 

#  def gen_lut(self):
#
#    if ((not self.slope_name) and (not self.load_name)):
#      print("slope / load are not registered!\n")
#      my_exit()
#    else:
#      self.constraint_template_name = "constraint_template_"+self.slope_name
#      self.recovery_template_name = "recovery_template_"+self.slope_name
#      self.removal_template_name = "removal_template_"+self.slope_name
#      self.mpw_constraint_template_name = "mpw_constraint_template_"+self.slope_name
#      self.passive_power_template_name = "passive_power_template_"+self.slope_name
#      self.delay_template_name = "delay_template_"+self.load_name+"_"+self.slope_name
#      self.power_template_name = "power_template_"+self.load_name+"_"+self.slope_name
#      #print("Done targetCell.gen_lut_template\n")

#nouse?  ## this defines lowest limit of setup edge
#nouse?  def add_simulation_setup_lowest(self, line="tmp"):
#nouse?    tmp_array = line.split()
#nouse?    ## if auto, amd slope is defined, use 10x of max slope 
#nouse?    ## "10" should be the same value of tstart1 and tclk5 in spice 
#nouse?    if ((tmp_array[1] == 'auto') and (self.slope[-1] != None)):
#nouse?      self.sim_setup_lowest = float(self.slope[-1]) * -10 
#nouse?      self.print_msg ("auto set setup simulation time lowest limit")
#nouse?    else:
#nouse?      self.sim_setup_lowest = float(tmp_array[1]) 
#nouse?      
#nouse?  ## this defines highest limit of setup edge
#nouse?  def add_simulation_setup_highest(self, line="tmp"):
#nouse?    tmp_array = line.split()
#nouse?    ## if auto, amd slope is defined, use 10x of max slope 
#nouse?    if ((tmp_array[1] == 'auto') and (self.slope[-1] != None)):
#nouse?      self.sim_setup_highest = float(self.slope[-1]) * 10 
#nouse?      self.print_msg ("auto set setup simulation time highest limit")
#nouse?    else:
#nouse?      self.sim_setup_highest = float(tmp_array[1])
#nouse?      
#nouse?  def add_simulation_setup_timestep(self, line="tmp"):
#nouse?    tmp_array = line.split()
#nouse?    ## if auto, amd slope is defined, use 1/10x min slope
#nouse?    if ((tmp_array[1] == 'auto') and (self.slope[0] != None)):
#nouse?      self.sim_setup_timestep = float(self.slope[0])/10
#nouse?      self.print_msg ("auto set setup simulation timestep")
#nouse?    else:
#nouse?      self.sim_setup_timestep = float(tmp_array[1])
#nouse?      
#nouse?  ## this defines lowest limit of hold edge
#nouse?  def add_simulation_hold_lowest(self, line="tmp"):
#nouse?    tmp_array = line.split()
#nouse?    ## if auto, amd slope is defined, use very small val. 
#nouse?    #remove# if hold is less than zero, pwl time point does not be incremental
#nouse?    #remove# and simulation failed
#nouse?    if ((tmp_array[1] == 'auto') and (self.slope[-1] != None)):
#nouse?      #self.sim_hold_lowest = float(self.slope[-1]) * -5 
#nouse?      self.sim_hold_lowest = float(self.slope[-1]) * -10 
#nouse?      #self.sim_hold_lowest = float(self.slope[-1]) * 0.001 
#nouse?      self.print_msg ("auto set hold simulation time lowest limit")
#nouse?    else:
#nouse?      self.sim_hold_lowest = float(tmp_array[1])
#nouse?      
#nouse?  ## this defines highest limit of hold edge
#nouse?  def add_simulation_hold_highest(self, line="tmp"):
#nouse?    tmp_array = line.split()
#nouse?    ## if auto, amd slope is defined, use 5x of max slope 
#nouse?    ## value should be smaller than "tmp_max_val_loop" in holdSearchFlop
#nouse?    if ((tmp_array[1] == 'auto') and (self.slope[-1] != None)):
#nouse?      #self.sim_hold_highest = float(self.slope[-1]) * 5 
#nouse?      self.sim_hold_highest = float(self.slope[-1]) * 10 
#nouse?      self.print_msg ("auto set hold simulation time highest limit")
#nouse?    else:
#nouse?      self.sim_hold_highest = float(tmp_array[1])
#nouse?      
#nouse?  def add_simulation_hold_timestep(self, line="tmp"):
#nouse?    tmp_array = line.split()
#nouse?    ## if auto, amd slope is defined, use 1/10x min slope
#nouse?    if ((tmp_array[1] == 'auto') and (self.slope[0] != None)):
#nouse?      self.sim_hold_timestep = float(self.slope[0])/10 
#nouse?      self.print_msg ("auto set hold simulation timestep")
#nouse?    else:
#nouse?      self.sim_hold_timestep = float(tmp_array[1])

  ## calculate ave of cin for each inports
  ## cin is measured two times and stored into 
  ## neighborhood harness, so cin of (2n)th and 
  ## (2n+1)th harness are averaged out
  #def set_cin_avg(self, targetLib, harnessList, port="data"):
  #  tmp_cin = 0;
  #  tmp_index = 0;
  #  for targetHarness in harnessList:
  #    if((port.lower() == 'clock')or(port.lower() == 'clk')):
  #      tmp_cin += float(targetHarness.cclk)
  #      ## if this is (2n+1) then store averaged 
  #      ## cin into targetCell.cins
  #      if((tmp_index % 2) == 1):
  #        #self.cclks.append(str((tmp_cin / 2)/targetLib.capacitance_mag))
  #        self.cclks.append(str("{:5f}".format((tmp_cin / 2)/targetLib.capacitance_mag)))
  #        tmp_cin = 0
  #      tmp_index += 1
  #      #self.print_msg("stored cins:"+str(tmp_index)+" for clk")
  #    elif((port.lower() == 'reset')or(port.lower() == 'rst')):
  #      tmp_cin += float(targetHarness.cin) # .cin stores rst cap. 
  #      ## if this is (2n+1) then store averaged 
  #      ## cin into targetCell.cins
  #      if((tmp_index % 2) == 1):
  #        #self.crsts.append(str((tmp_cin / 2)/targetLib.capacitance_mag))
  #        self.crsts.append(str("{:5f}".format((tmp_cin / 2)/targetLib.capacitance_mag)))
  #        tmp_cin = 0
  #      tmp_index += 1
  #      #self.print_msg("stored cins:"+str(tmp_index)+" for rst")
  #    elif(port.lower() == 'set'):
  #      tmp_cin += float(targetHarness.cin) # .cin stores set cap.
  #      ## if this is (2n+1) then store averaged 
  #      ## cin into targetCell.cins
  #      if((tmp_index % 2) == 1):
  #        #self.csets.append(str((tmp_cin / 2)/targetLib.capacitance_mag))
  #        self.csets.append(str("{:5f}".format((tmp_cin / 2)/targetLib.capacitance_mag)))
  #        tmp_cin = 0
  #      tmp_index += 1
  #      #self.print_msg("stored cins:"+str(tmp_index)+" for set")
  #    else: 
  #      #tmp_cin += float(targetHarness.cin) # else, .cin stores inport cap.
  #      tmp_cin += float(targetHarness.avg["cin"]) # else, .cin stores inport cap.
  #      
  #      ## if this is (2n+1) then store averaged 
  #      ## cin into targetCell.cins
  #      if((tmp_index % 2) == 1):
  #        #self.cins.append(str((tmp_cin / 2)/targetLib.capacitance_mag))
  #        self.cins.append(str("{:5f}".format((tmp_cin / 2)/targetLib.capacitance_mag)))
  #        tmp_cin = 0
  #      tmp_index += 1
  #      #self.print_msg("stored cins:"+str(tmp_index)+" for data")
  #    #self.print_msg("stored cins:"+str(tmp_index))

  #def set_cin_avg(self, targetLib:Mls, harnessList:Mcar):

  ## average of cin in all harness.dict_list2["cin"]["index_2"]["index_1"]
  def set_cin_avg(self, harnessList:list["Mcar"]):

    for inport in self.inports:
      cin_all=[]
      for h in harnessList:
        if h.target_relport == inport:
          #-- list of dict_list2["cin"]["index_1"]["index_2"]
          cin_list=[v for index_1 in h.dict_list2["cin"].values() for v in index_1.values()]
          cin_all.extend(cin_list)
          #print(f"{inport}:{cin_all}")
          
      if len(cin_all)<1:
        print(f'[Error] dict_list2["cin"] size is 0.')
        my_exit()

      #
      mag=self.mls.capacitance_mag
      val_avr=st.mean(cin_all)/mag
      self.cins[inport]=val_avr

  ## leak_power=max(i_vdd_leak) in all harness.dict_list2["i_vdd_leak"]["index_2"]["index_1"]
  def set_pleak_icrs(self, harnessList:list["Mcar"]):

    #-- sort by when-condition
    sorted_harnessList=sorted(harnessList, key=lambda x: (tuple(x.mel.rval.get("i",[])),
                                                          tuple(x.mel.rval.get("c",[])),
                                                          tuple(x.mel.rval.get("r",[])),
                                                          tuple(x.mel.rval.get("s",[]))))

    #-- generate pleak by when-condition
    for (i,c,r,s),group in groupby(
        sorted_harnessList, key=lambda x:(tuple(x.mel.rval.get("i",[])),
                                          tuple(x.mel.rval.get("c",[])),
                                          tuple(x.mel.rval.get("r",[])),
                                          tuple(x.mel.rval.get("s",[])))):
      rval={"i":i, "c":c, "r":r, "s":s}
      h_group=list(group);
      size=len(h_group)
      #print(rval)

      ##-- generate when condition from harnessList.mel
      ##---  str_when = "i0","!i1","c0","r1"
      cond_when=[]
      for port_type in ["i", "c", "r", "s"]:
        for index,val in enumerate(rval[port_type]):
          neg_str="!" if val=="0" else ""
          cond_when.append(f"{neg_str}{port_type}{index}")

      str_when=" ".join(cond_when)
      
      ##-- get max(pleak) when same input condition
      pleak_all=[]
      for h in h_group:
        pleak_list=[v for index_1 in h.dict_list2["i_vdd_leak"].values() for v in index_1.values()]
        pleak_all.extend(pleak_list)

      if len(pleak_all)<1:
        continue

      mag=self.mls.leakage_power_mag
      pleak_max=max(abs(x/mag) for x in pleak_all)
      
      ##-- update
      if not str_when in self.pleak_icrs.keys():
        self.pleak_icrs[str_when]=0.0

      self.pleak_icrs[str_when]=max(pleak_max, self.pleak_icrs[str_when])

    #--
    #print(f"[DEBUG] pleak_icrs={self.pleak_icrs}.")

  ## cell_cleak=average of leak_power
  def set_pleak_cell(self):

    if len(self.pleak_icrs)<1:
      print(f"[Error] pleak_icrs is empty.")
      my_exit()
      
    self.pleak_cell=st.mean(self.pleak_icrs.values())
    #print(f"[DEBUG] pleak_cell={self.pleak_cell}.")
      
  #--- convert from local port name(i0) to spice port name(A).
  def rvs_portmap(self, local_ports:list):
    rvs_dict={v:k for k,v in self.ports_dict.items()}
    return [rvs_dict[v] for v in local_ports if v in rvs_dict]
  
  #--- replace local port name in local_str to spice port name.
  def replace_by_portmap(self, local_str):
    new_str=local_str
    for k,v in self.ports_dict.items():
      new_str = new_str.replace(v, k)
    return(new_str)
