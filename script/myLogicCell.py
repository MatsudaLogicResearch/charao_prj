import argparse, re, os, shutil, subprocess, inspect
import copy
from pydantic import BaseModel, model_validator, Field
from typing import Any, Dict, TYPE_CHECKING
import statistics as st

from myFunc import my_exit

from myLibrarySetting       import MyLibrarySetting as Mls 
from myExpectLogic          import logic_dict
#import myExpectLogic                                as mel


if TYPE_CHECKING:
  from myConditionsAndResults import MyConditionsAndResults  as Mcar

class MyLogicCell(BaseModel):
  #=====================================
  # class variable
  
  #=====================================
  # instance variable by BaseModel

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
  cins      : list[float] = Field(default_factory=list); ## inport caps
  cclks     : list[float] = Field(default_factory=list);      ## clock pin cap. for flop
  csets     : list[float] = Field(default_factory=list);      ## set pin cap. for flop
  crsts     : list[float] = Field(default_factory=list);      ## reset pin cap. for flop 
  flops     : list[str]   = Field(default_factory=list);      ## registers 
  #functions : list[str]   = Field(default_factory=list);  ## logic/flop functions 
  slope     : list[float] = Field(default_factory=list);      ## inport slope
  cslope    : float          = 0;      ## inport clock slope
  load      : list[float] = Field(default_factory=list);       ## outport load
  timestep_res  : float       = 0.1;   ## simulation timestep resolution in slope[0]
  #slope_name : list[str]  = Field(default_factory=list); ## slope name
  #load_name  : list[str]  = Field(default_factory=list);  ## load name
  slope_name : str         = "slope"; ## slope name
  load_name  : str         = "load";  ## load name
  simulation_timestep : float = 0;      ## simulation timestep 
  isexport            : int = 0;   ## exported or not
  isexport2doc        : int = 0; ## exported to doc or not
  isflop              : int = 0;     ## DFF or not
  ## setup 
  sim_setup_lowest    : float = 0.0;    ## fastest simulation edge (pos. val.) 
  sim_setup_highest   : float = 0.0;   ## lowest simulation edge (pos. val.) 
  sim_setup_timestep  : float = 0.0;  ## timestep for setup search (pos. val.) 
  ## hold                        
  sim_hold_lowest     : float = 0.0;     ## fastest simulation edge (pos. val.) 
  sim_hold_highest    : float = 0.0;    ## lowest simulation edge (pos. val.) 
  sim_hold_timestep   : float = 0.0;   ## timestep for hold search (pos. val.) 
  ## power
  pleak        : list[list[float]] = Field(default_factory=list);        ## cell leak power
  inport_pleak : list[list[float]] = Field(default_factory=list); ## inport leak power
  inport_cap   : list[float]       = Field(default_factory=list);   ## inport cap
  ## message
  supress_msg  : str = None;        ## supress message

  #-- local variable
  netlist      : str  = None;    ## spice file name & PATH
  definition   : str  = None;    ## dut subskt name in spice file. 
  instance     : str  = None;    ## DUT instance name in TB.
  model        : str  = "./model/TT.sp";
  
  constraint_template_name     : str = None
  recovery_template_name       : str = None
  removal_template_name        : str = None
  mpw_constraint_template_name : str = None
  passive_power_template_name  : str = None
  delay_template_name          : str = None
  power_template_name          : str = None 

  #
  #model_config ={"frozen":True};  #-- not writable
  
  #--def __init__ (self):  #-- not use

  
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

  def set_supress_message(self, targetLib):
    self.supress_msg = targetLib.supress_msg 

  def print_msg(self, message=""):
    if((self.supress_msg.lower() == "false")or(self.supress_msg.lower() == "f")):
      print(message)

  #def add_slope(self, targetLib, line="tmp"):
  #  tmp_array = line.split()
  #  for w in tmp_array:
  #    self.slope.append(float(w))
  #  #print (self.slope)

  def add_slope(self, targetLib):
    flag_match = 0
    jlist = []
    # search slope name from 2D slope array
    for jlist in targetLib.slope:
        if (jlist[-1] != self.slope_name):
          continue
        else:
          flag_match = 1
          break
    if (flag_match == 0): # exit loop w/o match
      print("cannot find slope: "+self.slope_name)
      print(targetLib.slope)
      my_exit()
    self.slope = copy.deepcopy(jlist)
    self.slope.pop(-1) # delete slope name
    self.print_msg("add slope "+self.slope_name) 

  def add_load(self, targetLib):
    flag_match = 0
    jlist = []
    # search load name from 2D load array
    for jlist in targetLib.load:
        if (jlist[-1] != self.load_name):
          continue
        else:
          flag_match = 1
          break
    if (flag_match == 0): # exit loop w/o match
      print("cannot find load: "+self.load_name)
      my_exit()
    self.load = copy.deepcopy(jlist)
    self.load.pop(-1) # delete load name
    self.print_msg("add load "+self.load_name) 

  def return_slope(self):
    jlist = self.slope
    outline = "(\""
    #mmm self.lut_prop = []
    for j in range(len(jlist)-1):
      outline += str(jlist[j])+", " 
    outline += str(jlist[len(jlist)-1])+"\");" 
    return outline

  def return_load(self):
    jlist = self.load
    outline = "(\""
    #mmm self.lut_prop = []
    for j in range(len(jlist)-1):
      outline += str(jlist[j])+", " 
    outline += str(jlist[len(jlist)-1])+"\");" 
    return outline

  #def add_area(self, line="tmp"):
  #  tmp_array = line.split()
  #  self.area = float(tmp_array[1]) 

  def chk_netlist(self, targetLib):
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
    
  def add_model(self, targetLib):
    self.model = targetLib.model_path +"/.model_"+targetLib.process_name +"_"+targetLib.operating_conditions+".sp"

    if not os.path.exists(self.model):
      print("  model file is not exits. {0}".format(self.model))
      my_exit()
      
  def add_simulation_timestep(self):
    self.simulation_timestep =self.slope[0] * self.timestep_res 

  def set_exported(self):
    self.isexport = 1 

  def set_exported2doc(self):
    self.isexport2doc = 1
        
  def set_inport_cap_pleak(self, index, harness):
    ## average leak power of all harness
    #self.pleak += harness.pleak 
    self.pleak += harness.avg["pleak"] 

    
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
    
  def add_clock_slope(self, line="tmp"):
    tmp_array = line.split()
    ## if auto, amd slope is defined, use mininum slope
    if (tmp_array[1] == 'auto'):
      self.cslope = float(self.slope[0]) 
      self.print_msg ("auto set clock slope as mininum slope.")
    else:
      self.cslope = float(tmp_array[1]) 

  def gen_lut_templates(self):
    if ((not self.slope_name) and (not self.load_name)):
      print("slope / load are not registered!\n")
      my_exit()
    else:
      self.constraint_template_name = "constraint_template_"+self.slope_name
      self.recovery_template_name = "recovery_template_"+self.slope_name
      self.removal_template_name = "removal_template_"+self.slope_name
      self.mpw_constraint_template_name = "mpw_constraint_template_"+self.slope_name
      self.passive_power_template_name = "passive_power_template_"+self.slope_name
      self.delay_template_name = "delay_template_"+self.load_name+"_"+self.slope_name
      self.power_template_name = "power_template_"+self.load_name+"_"+self.slope_name
      #print("Done targetCell.gen_lut_template\n")

  ## this defines lowest limit of setup edge
  def add_simulation_setup_lowest(self, line="tmp"):
    tmp_array = line.split()
    ## if auto, amd slope is defined, use 10x of max slope 
    ## "10" should be the same value of tstart1 and tclk5 in spice 
    if ((tmp_array[1] == 'auto') and (self.slope[-1] != None)):
      self.sim_setup_lowest = float(self.slope[-1]) * -10 
      self.print_msg ("auto set setup simulation time lowest limit")
    else:
      self.sim_setup_lowest = float(tmp_array[1]) 
      
  ## this defines highest limit of setup edge
  def add_simulation_setup_highest(self, line="tmp"):
    tmp_array = line.split()
    ## if auto, amd slope is defined, use 10x of max slope 
    if ((tmp_array[1] == 'auto') and (self.slope[-1] != None)):
      self.sim_setup_highest = float(self.slope[-1]) * 10 
      self.print_msg ("auto set setup simulation time highest limit")
    else:
      self.sim_setup_highest = float(tmp_array[1])
      
  def add_simulation_setup_timestep(self, line="tmp"):
    tmp_array = line.split()
    ## if auto, amd slope is defined, use 1/10x min slope
    if ((tmp_array[1] == 'auto') and (self.slope[0] != None)):
      self.sim_setup_timestep = float(self.slope[0])/10
      self.print_msg ("auto set setup simulation timestep")
    else:
      self.sim_setup_timestep = float(tmp_array[1])
      
  ## this defines lowest limit of hold edge
  def add_simulation_hold_lowest(self, line="tmp"):
    tmp_array = line.split()
    ## if auto, amd slope is defined, use very small val. 
    #remove# if hold is less than zero, pwl time point does not be incremental
    #remove# and simulation failed
    if ((tmp_array[1] == 'auto') and (self.slope[-1] != None)):
      #self.sim_hold_lowest = float(self.slope[-1]) * -5 
      self.sim_hold_lowest = float(self.slope[-1]) * -10 
      #self.sim_hold_lowest = float(self.slope[-1]) * 0.001 
      self.print_msg ("auto set hold simulation time lowest limit")
    else:
      self.sim_hold_lowest = float(tmp_array[1])
      
  ## this defines highest limit of hold edge
  def add_simulation_hold_highest(self, line="tmp"):
    tmp_array = line.split()
    ## if auto, amd slope is defined, use 5x of max slope 
    ## value should be smaller than "tmp_max_val_loop" in holdSearchFlop
    if ((tmp_array[1] == 'auto') and (self.slope[-1] != None)):
      #self.sim_hold_highest = float(self.slope[-1]) * 5 
      self.sim_hold_highest = float(self.slope[-1]) * 10 
      self.print_msg ("auto set hold simulation time highest limit")
    else:
      self.sim_hold_highest = float(tmp_array[1])
      
  def add_simulation_hold_timestep(self, line="tmp"):
    tmp_array = line.split()
    ## if auto, amd slope is defined, use 1/10x min slope
    if ((tmp_array[1] == 'auto') and (self.slope[0] != None)):
      self.sim_hold_timestep = float(self.slope[0])/10 
      self.print_msg ("auto set hold simulation timestep")
    else:
      self.sim_hold_timestep = float(tmp_array[1])

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
  def set_cin_avg(self, targetLib:Mls, harnessList:"Mcar"):

    self.cins=[]
    for inport in self.inports:
      index = self.inports.index(inport)

      cin_avg= st.mean( h.avg["cin"] for h in harnessList if h.target_relport == inport)
      self.cins.append(cin_avg)

      
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
