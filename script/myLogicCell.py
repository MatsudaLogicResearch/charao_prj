import argparse, re, os, shutil, subprocess, inspect
import copy
from pydantic import BaseModel, model_validator, Field
from typing import Any, Dict, TYPE_CHECKING, List, Optional
import statistics as st
from itertools import groupby

from myFunc import my_exit

from myLibrarySetting       import MyLibrarySetting as Mls 
from myExpectCell           import logic_dict
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
  functions : Dict[str,str] = Field(default_factory=dict); ## cell function
  vcode     : str = None;     ## verilog code
  ff        : Dict[str,str] = Field(default_factory=dict); ## ff infomation
  #io        : Dict[str,str] = Field(default_factory=dict); ## io infomation
  #pin       : Dict[str,str] = Field(default_factory=dict); ## pin infomation for IO cell
  ports_dict: Dict[str,str] = Field(default_factory=dict); ## spice-port/name mapper

  cell_infos: Dict[str,Any]= Field(default_factory=dict); ## additional cell infomation
  rail_connections:Dict[str,str]= Field(default_factory=dict); ## additional cell infomation
  pad_infos : Dict[str,Dict[str,Any]]= Field(default_factory=dict); ## PAD infomation
  oe_infos  : Dict[str,Dict[str,Any]]= Field(default_factory=dict); ## OE infomation
  vdd2_voltage:list[str] = Field(default_factory=list);       ## list of CORE2_VOLTAGE(vdd2)
  io_voltage:list[str] = Field(default_factory=list);       ## list of IO_VOLTAGE(vddio)
  
  inports   : list[str] = Field(default_factory=list); ## inport pins
  outports  : list[str] = Field(default_factory=list); ## outport pins
  biports   : list[str] = Field(default_factory=list); ## inout port pins
  clock     : str= None;      ## clock pin for flop
  #set       : str= None;      ## set pin for flop
  #reset     : str= None;      ## reset pin for flop 
  vports    : list[str] = Field(default_factory=list); ## vdd/vss port pins

  cins      : dict[str,float] = Field(default_factory=dict); ## inport caps. cins={"inport",cap}
  
  template_kgn: list[list[str]]= Field(default_factory=list);     ## kind/grid/name of template
  template: dict[str,MyItemTemplate] = Field(default_factory=lambda:{
    "leakage":None,
    "const"  :None,
    "delay"  :None,
    "delay_c2c"  :None,
    "delay_i2c"  :None,
    "delay_c2i"  :None,
    "delay_i2i"  :None,
    "mpw"    :None,
    "passive":None,
    "power"  :None,
    "power_c2c"  :None,
    "power_i2c"  :None,
    "power_c2i"  :None,
    "power_i2i"  :None})
  
  max_load4out: dict[str,float] = Field(default_factory=dict);   ## outport load {"outport",max capacitance}
  max_trans4in: dict[str,float] = Field(default_factory=dict);   ## max transition {"inport",max transition}

  isexport            : int = 0;   ## exported or not
  isexport2doc        : int = 0; ## exported to doc or not
  isflop              : int = 0;     ## DFF or not
  isio                : int = 0;     ## IO or not
  pleak_icrs   : dict[str,float] = Field(default_factory=dict);## leakage power with input condition. pleak_icrs={"condition",val}
  pleak_cell   : float=0.0;          ## cell leakage power

  min_pulse_width_low : dict[str,float] = Field(default_factory=dict); #mini_pulse_width
  min_pulse_width_high: dict[str,float] = Field(default_factory=dict); #mini_pulse_width
  
  supress_msg  : str = None;        ## supress message

  #-- local variable
  netlist      : str  = None;    ## spice file name & PATH
  definition   : str  = None;    ## dut subskt name in spice file. 
  instance     : str  = None;    ## DUT instance name in TB.
  model        : str  = "./model/TT.sp";
  
  #
  #model_config ={"frozen":True};  #-- not writable
  
  lut_names  : list[str]= Field(default_factory=list);     ## template name(const,delay,energy,passive)
  lut_template: Dict[str, MyItemTemplate] = Field(default_factory=lambda: {"const"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "delay"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "delay_c2c"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "delay_i2c"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "delay_c2i"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "delay_i2i"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           #"energy" : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "delay"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "power_c2c"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "power_i2c"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "power_c2i"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "power_i2i"  : MyItemTemplate(name="", index_1=[], index_2=[]),
                                                                           "passive": MyItemTemplate(name="", index_1=[], index_2=[])})
  #--def __init__ (self):  #-- not use

  def print_variable(self):
    for k,v in self.__dict__.items():
      print(f"   {k}={v}")
  
  def set_supress_message(self):
    self.supress_msg = self.mls.supress_msg 

  def print_msg(self, message=""):
    if((self.supress_msg.lower() == "false")or(self.supress_msg.lower() == "f")):
      print(message)

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

      if idx_src is None:
        print(f"[Error] unique template ={k}/{g}/{n} is not exist in targetLib.templates.")
        my_exit()
        
      # check kind in targetCell
      #print(self.template.keys())
      
      if k in self.template.keys():
        self.template[k] = self.mls.templates[idx_src]
        print(f"   [Info] add template={k}{g}{n}.")

      else:
        print(f"   [Error] unknown template kind={k}.")
        my_exit()
        
  def update_max_trans4in(self, port_name:str, new_value:float):

    ## check port
    #if not port_name in self.inports + [self.clock]:    
    if not port_name in [p for p in (self.inports + [self.clock] + self.biports) if p is not None]:
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
    if not port_name in (self.outports + self.biports):
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
    if self.isio:
      self.netlist = targetLib.io_spice_path +"/"+self.spice
    else:
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
          print(f"   [INFO]: Cell definition found for {str(self.cell)} in netlist/")
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
        self.clock = name_tb.lower()
      elif name_tb.upper().startswith("S"):
        #self.set = name_tb.lower()
        self.inports.append(name_tb.lower())
      elif name_tb.upper().startswith("R"):
        #self.reset = name_tb.lower()
        self.inports.append(name_tb.lower())
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
    self.model = targetLib.model_path +"/.model_"+targetLib.process_name +"_"+targetLib.process_corner+".sp"

    if not os.path.exists(self.model):
      print("  model file is not exits. {0}".format(self.model))
      my_exit()
      
  #def add_simulation_timestep(self):
  #  self.simulation_timestep =self.slope[0] * self.timestep_res 

  def set_exported(self):
    self.isexport = 1 

  def set_exported2doc(self):
    self.isexport2doc = 1
        
  def add_function(self):
    if not self.logic in logic_dict.keys():
      print(f"[Error] logic="+self.logic + " is not exist in MyExpectCell.py.");
      my_exit();

    self.functions = logic_dict[self.logic]["functions"]
          
    print("add function: " + str(self.functions))

  def add_vcode(self):
    if "vcode" in logic_dict[self.logic].keys():
      if logic_dict[self.logic]["vcode"]:
        self.vcode = self.replace_by_portmap(logic_dict[self.logic]["vcode"])
        print("add vcode")

  def add_ff(self):
    if not self.logic in logic_dict.keys():
      print(f"[Error] logic="+self.logic + " is not exist in MyExpectCell.py.");
      my_exit();

    self.ff = logic_dict[self.logic]["ff"]
    self.isflop=1

  def add_io(self):
    if not self.logic in logic_dict.keys():
      print(f"[Error] logic="+self.logic + " is not exist in MyExpectCell.py.");
      my_exit();

    self.isio=1

  ## average of cin in all harness.dict_list2["cin"]["index_2"]["index_1"]
  def set_cin_avg(self, harnessList:list["Mcar"]):

    ports=(self.inports + [self.clock] + self.biports)
    for inport in list(filter(lambda x: x is not None, ports)):
      
      cin_all=[]
      for h in harnessList:
        #print(f"inport={inport}, relport={h.target_relport}")
        
        if h.target_relport == inport:
        #if h.target_inport == inport:
          #-- list of dict_list2["cin"]["index_1"]["index_2"]
          cin_list=[v for index_1 in h.dict_list2["cin"].values() for v in index_1.values()]
          cin_all.extend(cin_list)
          #print(f"{inport}:{cin_all}")
          
      if len(cin_all)<1:
        self.cins[inport]=0.0; #-- default value?
        continue
        #print(f'[Error] dict_list2["cin"] size is 0.')
        #my_exit()

      #
      mag=self.mls.capacitance_mag
      val_avr=st.mean(cin_all)/mag
      self.cins[inport]=val_avr

  def set_cin_max(self, harnessList:list["Mcar"]):

    ports=(self.inports + [self.clock] + self.biports)
    for inport in list(filter(lambda x: x is not None, ports)):

      max_cin = 0.0
      for h in [x for x in harnessList if x.target_relport == inport and x.dict_list2["cin"]]:
        ## dict_list2["cin"][index1][index2] --- dict_list2["cin"]=[,,,,,,]
        cin_list=[v for index_1 in h.dict_list2["cin"].values() for v in index_1.values()]

        ## update in every harness
        new_cin = max(cin_list)
        if max_cin < new_cin:
          max_cin = new_cin
          
      mag=self.mls.capacitance_mag
      self.cins[inport]=max_cin/mag
      
  ## cell_cleak=max leakage
  def set_max_pleak(self, harnessList:list["Mcar"]):

    max_pleak = 0.0
    for h in [x for x in harnessList if x.measure_type == "leakage"]:
      if max_pleak < h.pleak:
        max_pleak = h.pleak
        
    #--
    self.pleak_cell=max_pleak

      
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

    
  def set_min_pulse_width(self, port_name:str, value:float, measure_type:str):

    ## check port
    if not port_name in [p for p in (self.inports + [self.clock]) if p is not None]:
      print(f"[Error] inport={port_name} is not exist in logic={self.logic}.")
      my_exit()

    ## check measure_type
    measure_type_list=["min_pulse_width_high","min_pulse_width_low"]
    if not measure_type in measure_type_list:
      print(f"[Error] measure_typ={measure_type} is not in {measure_type_list}")
      
    ## set value
    if measure_type=="min_pulse_width_high":
      self.min_pulse_width_high[port_name] = value/self.mls.time_mag
    else:
      self.min_pulse_width_low[port_name] = value/self.mls.time_mag
      
    ##
    #print(f"[Info] min_pulse_width={value} for {port_name}")
