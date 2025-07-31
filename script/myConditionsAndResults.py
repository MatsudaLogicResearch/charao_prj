import argparse, re, os, shutil, subprocess
import numpy as np
import statistics as st
import threading

from pydantic import BaseModel, model_validator, Field, PrivateAttr
from typing import Any, Dict, List, DefaultDict,Annotated,Literal, Optional
from collections import defaultdict


from myExpectCell     import MyExpectCell as Mec

from myLibrarySetting import MyLibrarySetting as Mls 
from myLogicCell      import MyLogicCell      as Mlc
from myItem           import MyItemTemplate

from myFunc import my_exit

DictKey=Literal["prop","trans","setup_hold",
                #"energy_start","energy_end",
                #"q_in_dyn", "q_out_dyn", "q_vdd_dyn","q_vss_dyn","i_in_leak","i_vdd_leak","i_vss_leak",
                "eintl","ein","cin", "pleak"]
  
LutKey = Literal["prop","trans","setup_hold","eintl","ein"]

#AvgKey = Literal["cin","pleak"]

NestedDefaultDict = Annotated[
    DefaultDict[float, float],  # slope -> value
    Field(default_factory=lambda: defaultdict(float))
]

Level2Dict = Annotated[
    DefaultDict[float, NestedDefaultDict],  # load -> (slope -> value)
    Field(default_factory=lambda: defaultdict(lambda: defaultdict(float)))
]

Level3Dict = Annotated[
    DefaultDict[DictKey, Level2Dict],  #Level3Dict["prop"][index_2][index_1] = 1.234
    Field(default_factory=lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))
]

class MyConditionsAndResults(BaseModel):
  #=====================================
  # class variable
  
  #=====================================
  # instance variable by BaseModel
  #self.instance = None          ## instance name

  #-- reference
  mls: Optional[Mls]=None
  mlc: Optional[Mlc]=None
  
  #-- for myExpectLogic
  mec: Mec = Field(default_factory=Mec)

  template_kind    : str = ""
  template         : MyItemTemplate = None
  #template_timing  : MyItemTemplate = None
  #template_energy  : MyItemTemplate = None
  
  measure_type   : str = ""
  direction_prop : str = ""
  direction_tran : str = ""
  direction_power: str = ""
  timing_type    : str = ""
  timing_sense   : str = ""
  timing_unate   : str = ""
  timing_when    : str = ""
  constraint     : str = ""
  passive_power  : str = ""

  target_inport         : str = ""
  target_inport_val     : str = ""
  target_relport        : str = ""
  target_relport_val    : str = ""
  target_outport        : str = ""
  target_outport_val    : str = ""
  target_clkport        : str = ""
  target_clkport_val    : str = ""

  clk_role              : str = "nouse"
  
  #stable_inport         : list[str] = Field(default_factory=list)
  #stable_inport_val     : list[str] = Field(default_factory=list)
  #nontarget_outport     : list[str] = Field(default_factory=list)
  #nontarget_outport_val : list[str] = Field(default_factory=list)
  stable_inport_val      : dict[str,str] = Field(default_factory=dict); ## {"i0":"1"}
  nontarget_outport      : list[str] = Field(default_factory=list)

  #-- hold result from spice simulation ([load][slope])
  dict_list2: Level3Dict  ; # initial value is set in Level3Dict
    
  #
  lut: dict[LutKey, list[float]] = Field(
    default_factory=lambda: {key: [] for key in LutKey.__args__}
  )

  lut_min2max: dict[LutKey, list[float]] = Field(
    default_factory=lambda: {key: [] for key in LutKey.__args__}
  )

  #
#  avg: dict[AvgKey, float] = Field(
#    default_factory=lambda: {key: [] for key in AvgKey.__args__}
#  )

  min_pulse_width : float = 0.0

  # lock はモデルフィールドにしない（検証やシリアライズ対象に含めない）
  _lock: threading.Lock = PrivateAttr(default_factory=threading.Lock)
    
  #def __init__ (self):

  #@property
  #def mls(self) -> Mls:
  #  return self._mls;  #--- no setter
  #
  #@property
  #def mlc(self) -> Mlc:
  #  return self._mlc;  #--- no setter
  
  def set_update(self):
    self.set_measure_type()
    self.set_timing_type()
    self.set_timing_sense()
    self.set_timing_when()
    self.set_direction()
    self.set_target_port()
    self.set_stable_inport()
    self.set_nontarget_outport()
    
  def set_direction(self):

    arc_out=self.mec.arc_oir[0]
    arc_in =self.mec.arc_oir[1]

    ## -- for output
    if   (arc_out == 'r'):
      self.direction_prop  ="cell_rise"
      self.direction_tran  ="rise_transition"
      self.direction_power ="rise_power"
      
    elif (arc_out == 'f'):
      self.direction_prop  ="cell_fall"
      self.direction_tran  ="fall_transition"
      self.direction_power ="fall_power"
      
    elif (arc_out == 's'):
      self.direction_prop  ="stable"
      self.direction_tran  ="stable"
      self.direction_power ="stable"
      
    else:
      print(f"[Error] unknown arc_out={arc_out}(output).")
      my_exit()

    ## -- for input
    if   (arc_in == 'r'):
      self.constraint    = "rise_constraint"
      self.passive_power = "rise_power"
      
    elif (arc_in == 'f'):
      self.constraint = "fall_constraint"
      self.passive_power = "fall_power"
      
    elif (arc_in == 's'):
      self.constraint    = "stable"
      self.passive_power = "stable"
      
    else:
      print(f"[Error] unknown arc_in={arc_in}(input).")
      my_exit()
      
  def set_measure_type(self):
    if self.mec.meas_type in ["combinational","rising_edge","fallin_edge",
                              "setup_rising","setup_falling","hold_rising","hold_falling",
                              "removal_rising","removal_falling","recovery_rising","recovery_falling",
                              "clear", "preset",
                              "min_pulse_width_low", "min_pulse_width_high",
                              "passive"]:
      self.measure_type = self.mec.meas_type
    else:
      print(f"[Error] unkown meas_type={self.mec.meas_type}")
      my_exit()

      
  def set_timing_type(self):
    if self.mec.meas_type in ["min_pulse_width_low","min_pulse_width_high","passive"]:
      self.timing_type = "no_type"
    else:
      self.timing_type = self.mec.meas_type

  def set_timing_sense(self):
    if(self.mec.tmg_sense== 'pos'):
      self.timing_sense = "positive_unate"
    elif(self.mec.tmg_sense== 'neg'):
      self.timing_sense = "negative_unate"
    elif(self.mec.tmg_sense == 'non'):
      self.timing_sense = "non_unate"
    else:
      print("Illegal input: " + self.mec.tmg_sense+", check tmg_sense.")
      my_exit()
      
  def set_timing_when(self):
    self.timing_when = self.mec.tmg_when

  def set_function(self):
    self.function = self.mec.function 

  def set_target_port(self):
    self.set_target_outport()
    self.set_target_inport()
    self.set_target_relport()
    self.set_target_clkport()
    
    
  def set_target_outport(self):
    
    #-- get pin name & pin position
    pin_pos=self.mec.pin_oir[0]
    flag=re.match(r"([a-zA-Z]+)(\d+)", pin_pos)
    if flag:
      pin=flag.group(1)
      pos=int(flag.group(2))
    else:
      print(f"  [Error] out port name={pin_pos} is illegal name.")
      my_exit()


    #-- get pin value
    ival = self.mec.ival;          #initial value dict
    val0 = ival[pin][pos] if (pin in ival and pos < len(ival[pin])) else ""

    #if val0 and  nval:
    #  self.target_outport      = pin_pos
    #  self.target_outport_val  = val0 + nval
    if val0 :
      self.target_outport      = pin_pos
      self.target_outport_val  = val0
    else :
      print(f"Error out port value error(ival={val0},mondrv={nval}).")
      my_exit();

  def set_target_inport(self):
    
    #-- get pin name & pin position
    pin_pos=self.mec.pin_oir[1]
    flag=re.match(r"([a-zA-Z]+)(\d+)", pin_pos)
    if flag:
      pin=flag.group(1)
      pos=int(flag.group(2))
    else:
      print(f"  [Error] target port name={pin_pos} is illegal name.")
      my_exit()

    #-- get pin value
    ival = self.mec.ival;          #initial value dict
    val0 = ival[pin][pos] if (pin in ival and pos < len(ival[pin])) else ""

    #if val0 and  nval:
    #  self.target_inport      = pin_pos
    #  self.target_inport_val  = val0 + nval
    if val0 :
      self.target_inport      = pin_pos
      self.target_inport_val  = val0
    else :
      print(f"Error target port value error(ival={val0},mondrv={nval}).")
      my_exit();

  def set_target_relport(self):

    #-- get pin name & pin position
    pin_pos=self.mec.pin_oir[2]
    flag=re.match(r"([a-zA-Z]+)(\d+)", pin_pos)
    if flag:
      pin=flag.group(1)
      pos=int(flag.group(2))
    else:
      print(f"  [Error] related port name={pin_pos} is illegal name.")
      my_exit()

    #-- get pin value
    ival = self.mec.ival;          #initial value dict
    val0 = ival[pin][pos] if (pin in ival and pos < len(ival[pin])) else ""

    if val0:
      self.target_relport      = pin_pos
      self.target_relport_val  = val0
    else :
      print(f"Error related port value error(ival={val0},mondrv={nval}).")
      my_exit();

  def set_target_clkport(self):

    #----val
    if self.mlc.clock != None:
      
      #-- get pin name & pin position
      #pin_pos=self.mec.pin_oir[2]
      pin_pos= self.mlc.clock
      flag=re.match(r"([a-zA-Z]+)(\d+)", pin_pos)
      if flag:
        pin=flag.group(1)
        pos=int(flag.group(2))
      else:
        print(f"  [Error] clock port name={pin_pos} is illegal name.")
        my_exit()

      #-- get pin value
      ival = self.mec.ival;          #initial value dict
      val0 = ival[pin][pos] if (pin in ival and pos < len(ival[pin])) else ""

      if val0:
        self.target_clkport      = pin_pos
        self.target_clkport_val  = val0
      else :
        print(f"Error clock port value error(ival={val0}).")
        my_exit();

    #---- role
    self.clk_role= "related" if self.mec.pin_oir[2]=="c0" else "input" if self.mec.pin_oir[1] =="c0" else "nouse"

    
  def set_stable_inport(self):
    in_pin =self.target_inport
    rel_pin=self.target_outport
    clk_pin=self.target_clkport
    
    #for typ in ["i", "b", "c", "r", "s"]:
    for typ in ["i", "b", "r", "s"]: #-- except clock port
      values=self.mec.ival.get(typ,[])
      
      for i in range (len(values)):
        pin=typ+"{:}".format(i)
        if not pin in [rel_pin, in_pin, clk_pin]:
          self.stable_inport_val[pin]=self.mec.ival[typ][i]

  def set_nontarget_outport(self):
    typ="o"
    values=self.mec.ival.get(typ,[])
    out_pin=self.target_outport
    for i in range (len(values)):
      pin=typ+"{:}".format(i)
      if out_pin != pin:
        self.nontarget_outport.append(pin)
        #self.nontarget_outport.append(self.mec.ival[typ][i])

  #def set_lut(self, template_kind:str, value_name:str):
  def set_lut(self, value_name:str):
    
    ## select mag
    mag = self.mls.energy_mag if value_name in ["eintl","ein"] else self.mls.time_mag

    ## get index
    if value_name in ["eintl", "ein"]:
      if not self.template_kind in ["power","passive"]:
        print(f"[Error] value_name={value_name}/template_kind={self.template_kind} are missmatch.")
        my_exit()
    else:
      if not self.template_kind in ["delay","const"]:
        print(f"[Error] value_name={value_name}/template_kind={self.template_kind} are missmatch.")
        my_exit()

    ## skip if not dict_list2
    if not value_name in self.dict_list2.keys():
      print(f"[ERROR] dict_list2[{value_name}] is not exist.")
      my_exit()

    ##
    outline=""
    self.lut[value_name]         = []
    self.lut_min2max[value_name] = []

    index_1_list=self.template.index_1
    index_2_list=self.template.index_2
    
    ## index_1
    outline = 'index_1("' + ','.join(map(str, index_1_list)) + '");'
    self.lut[value_name].append(outline)
    
    ## index_2
    if len(index_2_list)>0:
      outline = 'index_2("' + ','.join(map(str, index_2_list)) + '");'
      self.lut[value_name].append(outline)
    
    ## values
    self.lut[value_name].append("values ( \\")
    
    if len(index_2_list)<1:
      index_2_list=[0];  #-- dummy

    str_colon=""
    outline=""
    for index2 in index_2_list:
      #tmp      =",".join(str("{:5f}".format(x/mag)) for x in self.dict_list2[value_name][index2].values())
      tmp      =", ".join(str("{:.4g}".format(x/mag)) for x in self.dict_list2[value_name][index2].values())
      #tmp      =",".join(str("{:7.4f}".format(x/mag)) for x in self.dict_list2[value_name][index2].values())
      outline +=str_colon+'"' + tmp + '"'

      str_colon = ",\\\n          "

    self.lut[value_name].append(outline+");")

    # store min/center/max for doc
    index_2_center=index_2_list[int(len(index_2_list)/2)]
    values=list(self.dict_list2[value_name][index_2_center].values())

    val_min=np.amin  (values)
    val_mid=np.median(values)
    val_max=np.amax  (values)
    
    self.lut_min2max[value_name].append(str("{:5f}".format(val_min/mag)))
    self.lut_min2max[value_name].append(str("{:5f}".format(val_mid/mag)))
    self.lut_min2max[value_name].append(str("{:5f}".format(val_max/mag)))
    

  #def gen_instance_for_tb(self, targetLib:Mls, targetCell:Mlc) -> str :
  def gen_instance_for_tb(self) -> str :

    # parse subckt definition
    tmp_array = self.mlc.instance.split()

    #tmp_line = tmp_array[0] # remove XDUT
    tmp_line = tmp_array.pop(0)
    cell_name = tmp_array.pop(-1); # remove cell name
    
    #targetLib.print_msg(tmp_line)
    
    for w1 in tmp_array:

      # match tmp_array and harness 
      # search target inport
      is_matched = 0

      # DO NOT CHANGE ORDER(CLK->REL->IN)
      if(w1 == self.target_clkport):
        tmp_line += ' CLK'
        is_matched += 1
        continue
      
      if(w1 == self.target_relport):
        tmp_line += ' REL'
        is_matched += 1
        continue
      
      if(w1 == self.target_inport):
        tmp_line += ' IN'
        is_matched += 1
        continue
      
      # search stable inport
      is_matched2=0
      for w2 in self.stable_inport_val.keys():
        if(w1 == w2):
          val = self.stable_inport_val[w2]
          if(val == '1'):
            tmp_line += ' HIGH'
            is_matched += 1
            is_matched2  =1
          elif(val == '0'):
            tmp_line += ' LOW'
            is_matched += 1
            is_matched2  =1
          else:
            print(f'Illigal input value for stable input({w1})={val}')
            my_exit()

      if is_matched2:
        continue
            
      # one target outport for one simulation
      if(w1 == self.target_outport):
        tmp_line += ' OUT'
        is_matched += 1
        continue
        
      # search non-terget outport
      for w2 in self.nontarget_outport:
        if(w1 == w2):
          # this is non-terget outport
          # search outdex for this port
          tmp_line += ' WFLOAT'
          is_matched += 1
          continue

      # VDD/VSS
      if(w1.upper() == self.mls.vdd_name.upper()):
          # tmp_line += ' '+w1.upper() 
          tmp_line += ' VDD' 
          is_matched += 1
          continue
        
      if(w1.upper() == self.mls.vss_name.upper()):
          # tmp_line += ' '+w1.upper() 
          tmp_line += ' VSS' 
          is_matched += 1
          continue
        
      if(w1.upper() == self.mls.pwell_name.upper()):
          # tmp_line += ' '+w1.upper() 
          tmp_line += ' VPW' 
          is_matched += 1
          continue
        
      if(w1.upper() == self.mls.nwell_name.upper()):
          # tmp_line += ' '+w1.upper() 
          tmp_line += ' VNW' 
          is_matched += 1
          continue

      #
      print(f"[Error] not used port name={w1} in XDUT")
      my_exit()
        
    ## show error if this port has not matched
    if(is_matched == 0):
      ## if w1 is wire name, abort
      ## check this is instance tmp_array[0] or circuit name tmp_array[-1]
      if((w1 != tmp_array[0]) and (w1 != tmp_array[-1])): 
        print("port: "+str(w1)+" has not matched in netlist parse!! " + tmp_array[0] + " or " + tmp_array[-1])
        my_exit()
          
    #tmp_line += " "+str(tmp_array[len(tmp_array)-1])+"\n" # CIRCUIT NAME
    tmp_line += " "+cell_name+"\n"

    return(tmp_line)
    
