import argparse, re, os, shutil, subprocess
import numpy as np
import statistics as st
import threading

from pydantic import BaseModel, model_validator, Field, PrivateAttr
from typing import Any, Dict, List, DefaultDict,Annotated,Literal, Optional
from collections import defaultdict


#import myExpectLogic as Mel
from myExpectLogic    import MyExpectLogic as Mel

from myLibrarySetting import MyLibrarySetting as Mls 
from myLogicCell      import MyLogicCell as Mlc
from myItem           import MyItemTemplate

from myFunc import my_exit

DictKey=Literal["prop","trans","setup","hold","removal","recovery",
                #"energy_start","energy_end",
                #"q_in_dyn", "q_out_dyn", "q_vdd_dyn","q_vss_dyn","i_in_leak","i_vdd_leak","i_vss_leak",
                "eintl","ein","cin", "pleak"]
  
LutKey = Literal["prop","trans","setup","hold","recovery","removal","eintl","ein"]

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
  mel: Mel = Field(default_factory=Mel)

  template_kind    : str = ""
  template         : MyItemTemplate = None
  #template_timing  : MyItemTemplate = None
  #template_energy  : MyItemTemplate = None
  
  direction_prop : str = ""
  direction_tran : str = ""
  direction_power: str = ""
  timing_type    : str = ""
  timing_sense   : str = ""
  timing_unate   : str = ""
  timing_when    : str = ""
  constraint     : str = ""

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
    self.set_timing_type()
    self.set_timing_sense()
    self.set_timing_when()
    self.set_direction()
    self.set_target_port()
    self.set_stable_inport()
    self.set_nontarget_outport()
    
  def set_direction(self):

    arc_out=self.mel.arc_oir[0]
    arc_in =self.mel.arc_oir[1]

    ## -- for output
    if   (arc_out == 'r'):
      self.direction_prop  ="cell_rise"
      self.direction_tran  ="rise_transition"
      self.direction_power ="rise_power"
      
    elif (arc_out == 'f'):
      self.direction_prop  ="cell_fall"
      self.direction_tran  ="fall_transition"
      self.direction_power ="fall_power"
      
    else:
      print(f"[Error] unknown arc_out[0]={arc_out}(output).")
      my_exit()

    ## -- for input
    if   (arc_in == 'r'):
      self.constraint = "rise_constraint"
      
    elif (arc_in == 'f'):
      self.constraint = "fall_constraint"

    else:
      if self.template_kind in ["const"]:
        print(f"[Error] unknown arc_out[1]={arc_in}(input).")
        my_exit()
      else:
        self.constraint = "stable(not_support)"; ##-- not used this value
        
      
#  def set_direction_rise(self):
#    self.direction_prop  = "cell_rise"
#    self.direction_tran  = "rise_transition"
#    self.direction_power = "rise_power"
#
#  def set_direction_fall(self):
#    self.direction_prop = "cell_fall"
#    self.direction_tran = "fall_transition"
#    self.direction_power = "fall_power"

  def set_timing_type(self):
    self.timing_type = self.mel.tmg_type

  def set_timing_sense(self):
    if(self.mel.tmg_sense== 'pos'):
      self.timing_sense = "positive_unate"
    elif(self.mel.tmg_sense== 'neg'):
      self.timing_sense = "negative_unate"
    elif(self.mel.tmg_sense == 'non'):
      self.timing_sense = "non_unate"
    else:
      print("Illegal input: " + self.mel.tmg_sense+", check tmg_sense.")
      my_exit()
      
  def set_timing_when(self):
    self.timing_when = self.mel.tmg_when

  def set_function(self):
    self.function = self.mel.function 

  def set_target_port(self):
    self.set_target_outport()
    self.set_target_inport()
    self.set_target_relport()
    self.set_target_clkport()
    
    
  def set_target_outport(self):
    
    #-- get pin name & pin position
    pin_pos=self.mel.pin_oir[0]
    flag=re.match(r"([a-zA-Z]+)(\d+)", pin_pos)
    if flag:
      pin=flag.group(1)
      pos=int(flag.group(2))
    else:
      print(f"  [Error] out port name={pin_pos} is illegal name.")
      my_exit()


    #-- get pin value
    ival = self.mel.ival;          #initial value dict
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
    pin_pos=self.mel.pin_oir[1]
    flag=re.match(r"([a-zA-Z]+)(\d+)", pin_pos)
    if flag:
      pin=flag.group(1)
      pos=int(flag.group(2))
    else:
      print(f"  [Error] target port name={pin_pos} is illegal name.")
      my_exit()

    #-- get pin value
    ival = self.mel.ival;          #initial value dict
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
    pin_pos=self.mel.pin_oir[2]
    flag=re.match(r"([a-zA-Z]+)(\d+)", pin_pos)
    if flag:
      pin=flag.group(1)
      pos=int(flag.group(2))
    else:
      print(f"  [Error] related port name={pin_pos} is illegal name.")
      my_exit()

    #-- get pin value
    ival = self.mel.ival;          #initial value dict
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
      #pin_pos=self.mel.pin_oir[2]
      pin_pos= self.mlc.clock
      flag=re.match(r"([a-zA-Z]+)(\d+)", pin_pos)
      if flag:
        pin=flag.group(1)
        pos=int(flag.group(2))
      else:
        print(f"  [Error] clock port name={pin_pos} is illegal name.")
        my_exit()

      #-- get pin value
      ival = self.mel.ival;          #initial value dict
      val0 = ival[pin][pos] if (pin in ival and pos < len(ival[pin])) else ""

      if val0:
        self.target_clkport      = pin_pos
        self.target_clkport_val  = val0
      else :
        print(f"Error clock port value error(ival={val0}).")
        my_exit();

    #---- role
    self.clk_role= "related" if self.mel.pin_oir[2]=="c0" else "input" if self.mel.pin_oir[1] =="c0" else "nouse"

    
  def set_stable_inport(self):
    in_pin =self.target_inport
    rel_pin=self.target_outport
    clk_pin=self.target_clkport
    
    #for typ in ["i", "b", "c", "r", "s"]:
    for typ in ["i", "b", "r", "s"]: #-- except clock port
      values=self.mel.ival.get(typ,[])
      
      for i in range (len(values)):
        pin=typ+"{:}".format(i)
        if not pin in [rel_pin, in_pin, clk_pin]:
          self.stable_inport_val[pin]=self.mel.ival[typ][i]

  def set_nontarget_outport(self):
    typ="o"
    values=self.mel.ival.get(typ,[])
    out_pin=self.target_outport
    for i in range (len(values)):
      pin=typ+"{:}".format(i)
      if out_pin != pin:
        self.nontarget_outport.append(pin)
        #self.nontarget_outport.append(self.mel.ival[typ][i])



#  def write_list2_prop(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_prop = []
#    self.lut_prop_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_prop.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_prop.append(outline)
#    ## values
#    self.lut_prop.append("values ( \\")
#    #print(self.list2_prop)
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_prop[i][j])+", "
#        #print("i,j"+str(i)+","+str(j))
#        #print(len(ilist))
#        #print(len(jlist)-1)
#        #print(len(self.list2_prop))
#        #print([len(v) for v in self.list2_prop])
#        #print(self.list2_prop[i][j])
#        tmp_line = str("{:5f}".format(self.list2_prop[i][j]/targetLib.time_mag))
#        outline += tmp_line+", "
#      ## do not add "," for last line
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_prop[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_prop[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_prop[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_prop[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\", \\"
#      self.lut_prop.append(outline)
#    self.lut_prop.append(");")
#    
#    # store min/center/max for doc
#    # min
#    #self.lut_prop_mintomax.append(str("{:5f}".format(self.list2_prop[0][0]/targetLib.time_mag)))
#    self.lut_prop_mintomax.append(str("{:5f}".format(np.amin(self.list2_prop)/targetLib.time_mag)))
#    
#    # center
#    #self.lut_prop_mintomax.append(str("{:5f}".format(self.list2_prop[int(len(ilist))-1][int(len(jlist))-1]/targetLib.time_mag)))
#    self.lut_prop_mintomax.append(str("{:5f}".format(np.median(self.list2_prop)/targetLib.time_mag)))
#
#    # max
#    #self.lut_prop_mintomax.append(str("{:5f}".format(self.list2_prop[-1][-1]/targetLib.time_mag)))
#    self.lut_prop_mintomax.append(str("{:5f}".format(np.amax(self.list2_prop)/targetLib.time_mag)))

#  def write_list2_prop(self, targetLib, tergetCell):
#    ## index_1
#    outline = ""
#    self.lut_prop = []
#    self.lut_prop_mintomax = []
#
#    ## index_1
#    outline = "index_1(\"" + ','.join(targetCell.slope) + "\");"
#    self.lut_prop.append(outline)
#    
#    ## index_2
#    outline = "index_2(\"" + ','.join(targetCell.load) + "\");"
#    self.lut_prop.append(outline)
#    
#    ## values
#    self.lut_prop.append("values ( \\")
#
#    for i,load in enumerate(targetCell.load):
#      outline = "\""
#
#      ## do not add "," 
#      str_colon=""
#      for slope in targetCell.slope:
#        tmp_line = str_colon + str("{:5f}".format(self.dict_prop_in_out[load][slope]/targetLib.time_mag))
#        outline += tmp_line
#
#        str_colon = ","
#        
#      ## do not add \ for last line
#      if i == len(targetCell.load - 1):
#        outline += tmp_line + "\""
#      else:
#        outline += tmp_line + "\",\\"
#
#      ## 
#      self.lut_prop.append(outline)
#
#      
#    self.lut_prop.append(");")
#    
#    # store min/center/max in middle load for doc
#    load_index=int(len(targetCell.load)/2)
#    load=targetCell.load[load_index]
#    
#    # min
#    #self.lut_prop_mintomax.append(str("{:5f}".format(self.list2_prop[0][0]/targetLib.time_mag)))
#    #self.lut_prop_mintomax.append(str("{:5f}".format(np.amin(self.list2_prop)/targetLib.time_mag)))
#    self.lut_prop_mintomax.append(str("{:5f}".format(min(self.dict_prop_in_out[load].values())/targetLib.time_mag)))
#    
#    # center
#    #self.lut_prop_mintomax.append(str("{:5f}".format(self.list2_prop[int(len(ilist))-1][int(len(jlist))-1]/targetLib.time_mag)))
#    #self.lut_prop_mintomax.append(str("{:5f}".format(np.median(self.list2_prop)/targetLib.time_mag)))
#    self.lut_prop_mintomax.append(str("{:5f}".format(median(self.dict_prop_in_out[load].values())/targetLib.time_mag)))
#
#    # max
#    #self.lut_prop_mintomax.append(str("{:5f}".format(self.list2_prop[-1][-1]/targetLib.time_mag)))
#    #self.lut_prop_mintomax.append(str("{:5f}".format(np.amax(self.list2_prop)/targetLib.time_mag)))
#    self.lut_prop_mintomax.append(str("{:5f}".format(max(self.dict_prop_in_out[load].values())/targetLib.time_mag)))
#
    
  ## transient delay table
  #def set_list2_tran(self, list2_tran=[]):
  #  self.list2_tran = list2_tran 

  #def print_list2_tran(self, ilist, jlist):
  #  for i in range(len(ilist)):
  #    for j in range(len(jlist)):
  #      print(self.list2_tran[i][j])
  
  #def print_lut_tran(self):
  #  for i in range(len(self.lut_tran)):
  #    print(self.lut_tran[i])

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
    
    
#    # store min/center/max for doc
#    load_index=int(len(self.mlc.load)/2)
#    load=self.mlc.load[load_index]
#    
#    # min
#    #self.lut_tran_mintomax.append(str("{:5f}".format(np.amin(self.list2_tran)/targetLib.time_mag)))
#    self.lut_min2max[name].append(str("{:5f}".format(min(self.dict_list2[name][load].values())/mag)))
#    
#    # center
#    #self.lut_tran_mintomax.append(str("{:5f}".format(np.median(self.list2_tran)/targetLib.time_mag)))
#    self.lut_min2max[name].append(str("{:5f}".format(st.median(self.dict_list2[name][load].values())/mag)))
#    
#    # max
#    #self.lut_tran_mintomax.append(str("{:5f}".format(np.amax(self.list2_tran)/targetLib.time_mag)))
#    self.lut_min2max[name].append(str("{:5f}".format(max(self.dict_list2[name][load].values())/mag)))

  
  
#  def write_list2_tran(self, targetLib, targetCell):
#    outline=""
#    self.lut_tran = []
#    self.lut_tran_mintomax = []
#
#    ## index_1
#    outline = "index_1(\"" + ','.join(targetCell.slope) + "\");"
#    self.lut_tran.append(outline)
#    
#    ## index_2
#    outline = "index_1(\"" + ','.join(targetCell.load) + "\");"
#    self.lut_tran.append(outline)
#    
#    ## values
#    self.lut_tran.append("values ( \\")
#
#    for i,load in enumerate(targetCell.load):
#      outline = "\""
#    
#      ## do not add "," 
#      str_colon=""
#      for slope in targetCell.slope:
#        tmp_line = str_colon + str("{:5f}".format(self.dict_trans_out[load][slope]/targetLib.time_mag))
#        outline += tmp_line
#        
#        str_colon = ","
#
#      ## do not add \ for last line
#      if i == len(targetCell.load - 1):
#        outline += tmp_line + "\""
#      else:
#        outline += tmp_line + "\",\\"
#
#      ##
#      self.lut_tran.append(outline)
#      
#    self.lut_tran.append(");")
#    
#    # store min/center/max for doc
#    load_index=int(len(targetCell.load)/2)
#    load=targetCell.load[load_index]
#    
#    # min
#    #self.lut_tran_mintomax.append(str("{:5f}".format(np.amin(self.list2_tran)/targetLib.time_mag)))
#    self.lut_tran_mintomax.append(str("{:5f}".format(min(self.dict_tran_out[load].values())/targetLib.time_mag)))
#    
#    # center
#    #self.lut_tran_mintomax.append(str("{:5f}".format(np.median(self.list2_tran)/targetLib.time_mag)))
#    self.lut_tran_mintomax.append(str("{:5f}".format(median(self.dict_tran_out[load].values())/targetLib.time_mag)))
#    
#    # max
#    #self.lut_tran_mintomax.append(str("{:5f}".format(np.amax(self.list2_tran)/targetLib.time_mag)))
#    self.lut_tran_mintomax.append(str("{:5f}".format(max(self.dict_tran_out[load].values())/targetLib.time_mag)))

  ## propagation delay table for set
  #def set_list2_prop_set(self, list2_prop_set=[]):
  #  self.list2_prop_set = list2_prop_set 

  #def print_list2_prop_set(self, ilist, jlist):
  #  for i in range(len(ilist)):
  #    for j in range(len(jlist)):
  #      print(self.list2_prop_set[i][j])
  
#  def print_lut_prop_set(self):
#    for i in range(len(self.lut_prop_set)):
#      print(self.lut_prop_set[i])
#
#  def write_list2_prop_set(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_prop_set = []
#    self.lut_prop_set_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_prop_set.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_prop_set.append(outline)
#    ## values
#    self.lut_prop_set.append("values ( \\")
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_prop_set[i][j])+", "
#        tmp_line = str("{:5f}".format(self.list2_prop_set[i][j]/targetLib.time_mag))
#        outline += tmp_line+", "
#      ## do not add "," for last line
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_prop_set[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_prop_set[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_prop_set[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_prop_set[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\", \\"
#      self.lut_prop_set.append(outline)
#    self.lut_prop_set.append(");")
#    
#    # store min/center/max for doc
#    # min
#    self.lut_prop_set_mintomax.append(str("{:5f}".format(np.amin(self.list2_prop_set)/targetLib.time_mag)))
#    # center
#    self.lut_prop_set_mintomax.append(str("{:5f}".format(np.median(self.list2_prop_set)/targetLib.time_mag)))
#    # max
#    self.lut_prop_set_mintomax.append(str("{:5f}".format(np.amax(self.list2_prop_set)/targetLib.time_mag)))
#
#  ## transient delay table for set
#  def set_list2_tran_set(self, list2_tran_set=[]):
#    self.list2_tran_set = list2_tran_set 
#
#  def print_list2_tran_set(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_tran_set[i][j])
#  
#  def print_lut_tran_set(self):
#    for i in range(len(self.lut_tran_set)):
#      print(self.lut_tran_set[i])
#
#  def write_list2_tran_set(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_tran_set = []
#    self.lut_tran_set_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_tran_set.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_tran_set.append(outline)
#    ## values
#    self.lut_tran_set.append("values ( \\")
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_tran_set[i][j])+", "
#        tmp_line = str("{:5f}".format(self.list2_tran_set[i][j]/targetLib.time_mag))
#        outline += tmp_line+", "
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_tran_set[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_tran_set[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_tran_set[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_tran_reset[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\", \\"
#      self.lut_tran_set.append(outline)
#    self.lut_tran_set.append(");")
#    
#    # store min/center/max for doc
#    # min
#    self.lut_tran_set_mintomax.append(str("{:5f}".format(np.amin(self.list2_tran_set)/targetLib.time_mag)))
#    # center
#    self.lut_tran_set_mintomax.append(str("{:5f}".format(np.median(self.list2_tran_set)/targetLib.time_mag)))
#    # max
#    self.lut_tran_set_mintomax.append(str("{:5f}".format(np.amax(self.list2_tran_set)/targetLib.time_mag)))
#
#  ## propagation delay table for reset
#  def set_list2_prop_reset(self, list2_prop_reset=[]):
#    self.list2_prop_reset = list2_prop_reset 
#
#  def print_list2_prop_reset(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_prop_reset[i][j])
#  
#  def print_lut_prop_reset(self):
#    for i in range(len(self.lut_prop_reset)):
#      print(self.lut_prop_reset[i])
#
#  def write_list2_prop_reset(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_prop_reset = []
#    self.lut_prop_reset_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_prop_reset.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_prop_reset.append(outline)
#    ## values
#    self.lut_prop_reset.append("values ( \\")
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_prop_reset[i][j])+", "
#        tmp_line = str("{:5f}".format(self.list2_prop_reset[i][j]/targetLib.time_mag))
#        outline += tmp_line+", "
#      ## do not add "," for last line
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_prop_reset[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_prop_reset[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_prop_reset[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_prop_reset[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\", \\"
#      self.lut_prop_reset.append(outline)
#    self.lut_prop_reset.append(");")
#    
#    # store min/center/max for doc
#    # min
#    self.lut_prop_reset_mintomax.append(str("{:5f}".format(np.amin(self.list2_prop_reset)/targetLib.time_mag)))
#    # center
#    self.lut_prop_reset_mintomax.append(str("{:5f}".format(np.median(self.list2_prop_reset)/targetLib.time_mag)))
#    # max
#    self.lut_prop_reset_mintomax.append(str("{:5f}".format(np.amax(self.list2_prop_reset)/targetLib.time_mag)))
#
#  ## transient delay table for set
#  def set_list2_tran_set(self, list2_tran_set=[]):
#    self.list2_tran_set = list2_tran_set 
#
#  def print_list2_tran_set(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_tran_set[i][j])
#  
#  def print_lut_tran_set(self):
#    for i in range(len(self.lut_tran_set)):
#      print(self.lut_tran_set[i])
#
#  def write_list2_tran_set(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_tran_set = []
#    self.lut_tran_set_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_tran_set.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_tran_set.append(outline)
#    ## values
#    self.lut_tran_set.append("values ( \\")
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_tran_set[i][j])+", "
#        tmp_line = str("{:5f}".format(self.list2_tran_set[i][j]/targetLib.time_mag))
#        outline += tmp_line+", "
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_tran_set[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_tran_set[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_tran_set[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_tran_reset[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\", \\"
#      self.lut_tran_set.append(outline)
#    self.lut_tran_set.append(");")
#
#    # store min/center/max for doc
#    # min
#    self.lut_tran_set_mintomax.append(str("{:5f}".format(np.amin(self.list2_tran_set)/targetLib.time_mag)))
#    # center
#    self.lut_tran_set_mintomax.append(str("{:5f}".format(np.median(self.list2_tran_set)/targetLib.time_mag)))
#    # max
#    self.lut_tran_set_mintomax.append(str("{:5f}".format(np.amax(self.list2_tran_set)/targetLib.time_mag)))
    
#  ## internal power (energy) table 
#  def set_list2_eintl(self, list2_eintl=[]):
#    self.list2_eintl = list2_eintl 
#
#  def print_list2_eintl(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_eintl[i][j])
#  
#  def print_lut_eintl(self):
#    for i in range(len(self.lut_eintl)):
#      print(self.lut_eintl[i])

#  def write_list2_eintl(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_eintl = []
#    self.lut_eintl_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_eintl.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_eintl.append(outline)
#    ## values
#    self.lut_eintl.append("values ( \\")
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_eintl[i][j])+", "
#        tmp_line = str("{:5f}".format(self.list2_eintl[i][j]*targetLib.voltage_mag/targetLib.energy_mag))
#        outline += tmp_line+", "
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_eintl[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_eintl[i][len(jlist)-1]*targetLib.voltage_mag/targetLib.energy_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_eintl[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_eintl[i][len(jlist)-1]*targetLib.voltage_mag/targetLib.energy_mag))
#        outline += tmp_line+"\" \\"
#      self.lut_eintl.append(outline)
#    self.lut_eintl.append(");")
#    
#    # store min/center/max for doc
#    # min
#    self.lut_eintl_mintomax.append(str("{:5f}".format(np.amin(self.list2_eintl)*targetLib.voltage_mag/targetLib.energy_mag)))
#    # center
#    self.lut_eintl_mintomax.append(str("{:5f}".format(np.median(self.list2_eintl)*targetLib.voltage_mag/targetLib.energy_mag)))
#    # max
#    self.lut_eintl_mintomax.append(str("{:5f}".format(np.amax(self.list2_eintl)*targetLib.voltage_mag/targetLib.energy_mag)))
#
#  ## propagation delay table for reset
#  def set_list2_prop_reset(self, list2_prop_reset=[]):
#    self.list2_prop_reset = list2_prop_reset 
#
#  def print_list2_prop_reset(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_prop_reset[i][j])
#  
#  def print_lut_prop_reset(self):
#    for i in range(len(self.lut_prop_reset)):
#      print(self.lut_prop_reset[i])
#
#  def write_list2_prop_reset(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_prop_reset = []
#    self.lut_prop_reset_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_prop_reset.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_prop_reset.append(outline)
#    ## values
#    self.lut_prop_reset.append("values ( \\")
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_prop_reset[i][j])+", "
#        tmp_line = str("{:5f}".format(self.list2_prop_reset[i][j]/targetLib.time_mag))
#        outline += tmp_line+", "
#      ## do not add "," for last line
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_prop_reset[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_prop_reset[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_prop_reset[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_prop_reset[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\", \\"
#      self.lut_prop_reset.append(outline)
#    self.lut_prop_reset.append(");")
#
#    # store min/center/max for doc
#    # min
#    self.lut_prop_reset_mintomax.append(str("{:5f}".format(np.amin(self.list2_prop_reset)/targetLib.time_mag)))
#    # center
#    self.lut_prop_reset_mintomax.append(str("{:5f}".format(np.median(self.list2_prop_reset)/targetLib.time_mag)))
#    # max
#    self.lut_prop_reset_mintomax.append(str("{:5f}".format(np.amax(self.list2_prop_reset)/targetLib.time_mag)))
#
#    
#  ## transient delay table for reset
#  def set_list2_tran_reset(self, list2_tran_reset=[]):
#    self.list2_tran_reset = list2_tran_reset 
#
#  def print_list2_tran_reset(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_tran_reset[i][j])
#  
#  def print_lut_tran_reset(self):
#    for i in range(len(self.lut_tran_reset)):
#      print(self.lut_tran_reset[i])
#
#  def write_list2_tran_reset(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_tran_reset = []
#    self.lut_tran_reset_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_tran_reset.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_tran_reset.append(outline)
#    ## values
#    self.lut_tran_reset.append("values ( \\")
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_tran_reset[i][j])+", "
#        tmp_line = str("{:5f}".format(self.list2_tran_reset[i][j]/targetLib.time_mag))
#        outline += tmp_line+", "
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_tran_reset[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_tran_reset[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_tran_reset[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_tran_reset[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\", \\"
#      self.lut_tran_reset.append(outline)
#    self.lut_tran_reset.append(");")
#
#    # store min/center/max for doc
#    # min
#    self.lut_tran_reset_mintomax.append(str("{:5f}".format(np.amin(self.list2_tran_reset)/targetLib.time_mag)))
#    # center
#    self.lut_tran_reset_mintomax.append(str("{:5f}".format(np.median(self.list2_tran_reset)/targetLib.time_mag)))
#    # max
#    self.lut_tran_reset_mintomax.append(str("{:5f}".format(np.amax(self.list2_tran_reset)/targetLib.time_mag)))
#    
#  ## propagation delay table for set
#  def set_list2_prop_set(self, list2_prop_set=[]):
#    self.list2_prop_set = list2_prop_set 
#
#  def print_list2_prop_set(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_prop_set[i][j])
#  
#  def print_lut_prop_set(self):
#    for i in range(len(self.lut_prop_set)):
#      print(self.lut_prop_set[i])
#
#  def write_list2_prop_set(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_prop_set = []
#    self.lut_prop_set_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_prop_set.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_prop_set.append(outline)
#    ## values
#    self.lut_prop_set.append("values ( \\")
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_prop_set[i][j])+", "
#        tmp_line = str("{:5f}".format(self.list2_prop_set[i][j]/targetLib.time_mag))
#        outline += tmp_line+", "
#      ## do not add "," for last line
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_prop_set[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_prop_set[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_prop_set[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_prop_set[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\", \\"
#      self.lut_prop_set.append(outline)
#    self.lut_prop_set.append(");")
#
#    # store min/center/max for doc
#    # min
#    self.lut_prop_set_mintomax.append(str("{:5f}".format(np.amin(self.list2_prop_set)/targetLib.time_mag)))
#    # center
#    self.lut_prop_set_mintomax.append(str("{:5f}".format(np.median(self.list2_prop_set)/targetLib.time_mag)))
#    # max
#    self.lut_prop_set_mintomax.append(str("{:5f}".format(np.amax(self.list2_prop_set)/targetLib.time_mag)))
#    
#  ## transient delay table for set
#  def set_list2_tran_set(self, list2_tran_set=[]):
#    self.list2_tran_set = list2_tran_set 
#
#  def print_list2_tran_set(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_tran_set[i][j])
#  
#  def print_lut_tran_set(self):
#    for i in range(len(self.lut_tran_set)):
#      print(self.lut_tran_set[i])
#
#  def write_list2_tran_set(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_tran_set = []
#    self.lut_tran_set_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_tran_set.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_tran_set.append(outline)
#    ## values
#    self.lut_tran_set.append("values ( \\")
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_tran_set[i][j])+", "
#        tmp_line = str("{:5f}".format(self.list2_tran_set[i][j]/targetLib.time_mag))
#        outline += tmp_line+", "
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_tran_set[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_tran_set[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_tran_set[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_tran_set[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\", \\"
#      self.lut_tran_set.append(outline)
#    self.lut_tran_set.append(");")
#    
#    # store min/center/max for doc
#    # min
#    self.lut_tran_set_mintomax.append(str("{:5f}".format(np.amin(self.list2_tran_set)/targetLib.time_mag)))
#    # center
#    self.lut_tran_set_mintomax.append(str("{:5f}".format(np.median(self.list2_tran_set)/targetLib.time_mag)))
#    # max
#    self.lut_tran_set_mintomax.append(str("{:5f}".format(np.amax(self.list2_tran_set)/targetLib.time_mag)))
#
#
#  ## internal power (energy) table 
#  def set_list2_eintl(self, list2_eintl=[]):
#    self.list2_eintl = list2_eintl 
#
#  def print_list2_eintl(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_eintl[i][j])
#  
#  def print_lut_eintl(self):
#    for i in range(len(self.lut_eintl)):
#      print(self.lut_eintl[i])
#
#  def write_list2_eintl(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_eintl = []
#    self.lut_eintl_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_eintl.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_eintl.append(outline)
#    ## values
#    self.lut_eintl.append("values ( \\")
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_eintl[i][j])+", "
#        tmp_line = str("{:5f}".format(self.list2_eintl[i][j]*targetLib.voltage_mag/targetLib.energy_mag))
#        outline += tmp_line+", "
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_eintl[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_eintl[i][len(jlist)-1]*targetLib.voltage_mag/targetLib.energy_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_eintl[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_eintl[i][len(jlist)-1]*targetLib.voltage_mag/targetLib.energy_mag))
#        outline += tmp_line+"\" \\"
#      self.lut_eintl.append(outline)
#    self.lut_eintl.append(");")
#    # store min/center/max for doc
#    # min
#    self.lut_eintl_mintomax.append(str("{:5f}".format(np.amin(self.list2_eintl)*targetLib.voltage_mag/targetLib.energy_mag)))
#    # center
#    self.lut_eintl_mintomax.append(str("{:5f}".format(np.median(self.list2_eintl)*targetLib.voltage_mag/targetLib.energy_mag)))
#    # max
#    self.lut_eintl_mintomax.append(str("{:5f}".format(np.amax(self.list2_eintl)*targetLib.voltage_mag/targetLib.energy_mag)))
#    
#  ## input energy 
#  def set_list2_ein(self, list2_ein=[]):
#    self.list2_ein = list2_ein 
#
#  def print_list2_ein(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_ein[i][j])
#  
#  def print_lut_ein(self):
#    for i in range(len(self.lut_ein)):
#      print(self.lut_ein[i])
#
#  def write_list2_ein(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_ein = []
#    self.lut_ein_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_ein.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_ein.append(outline)
#    ## values
#    self.lut_ein.append("values ( \\")
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_ein[i][j])+", "
#        tmp_line = str("{:5f}".format(self.list2_ein[i][j]*targetLib.voltage_mag/targetLib.energy_mag))
#        outline += tmp_line+", "
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_ein[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_ein[i][len(jlist)-1]*targetLib.voltage_mag/targetLib.energy_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_ein[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_ein[i][len(jlist)-1]*targetLib.voltage_mag/targetLib.energy_mag))
#        outline += tmp_line+"\", \\"
#      self.lut_ein.append(outline)
#    self.lut_ein.append(");")
#    # store min/center/max for doc
#    # min
#    self.lut_ein_mintomax.append(str("{:5f}".format(np.amin(self.list2_ein)*targetLib.voltage_mag/targetLib.energy_mag)))
#    # center
#    self.lut_ein_mintomax.append(str("{:5f}".format(np.median(self.list2_ein)*targetLib.voltage_mag/targetLib.energy_mag)))
#    # max
#    self.lut_ein_mintomax.append(str("{:5f}".format(np.amax(self.list2_ein)*targetLib.voltage_mag/targetLib.energy_mag)))
#
#  ## input capacitance 
#  def set_list2_cin(self, list2_cin=[]):
#    self.list2_cin = list2_cin 
#
#  def print_list2_cin(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_cin[i][j])
#  
#  def print_lut_cin(self):
#    for i in range(len(self.lut_cin)):
#      print(self.lut_cin[i])

#  def average_list2_cin(self, targetLib, ilist, jlist):
#    ## output average of input capacitance
#    ## (do not write table)
#    self.lut_cin = 0;
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        self.lut_cin += self.list2_cin[i][j]
#    #self.cin = str(self.lut_cin / (len(ilist) * len(jlist))/targetLib.capacitance_mag) ## use average
#    self.cin = str(self.lut_cin / (len(ilist) * len(jlist))) ## use average
#      
#    #print("store cin:"+str(self.cin))


#  def set_average(self, value_name:str):
#    ## output average of input capacitance
#    ## (do not write table)
#
#    ## select mag
#    mag = self.mls.capacitance_mag if value_name in ["cin"] else self.mls.energy_mag
#
#    ## select template
#    temp = self.template_energy;
#
#    ## get index
#    index_1_list=temp.index_1
#    index_2_list=temp.index_2
#
#    avg_list=[]
#    if len(index_2_list)<1:
#      index_2_list=[0];  #-- dummy
#
#
#    ## average for list2
#    for index2 in index_2_list:
#      avg_list.append(st.mean(self.dict_list2[value_name][index2].values()))
#    
#    ## avarage for all
#    self.avg[value_name] = st.mean(avg_list)/mag
    

    
#  ## clock input energy 
#  def set_list2_eclk(self, list2_eclk=[]):
#    self.list2_eclk = list2_eclk 
#
#  def print_list2_eclk(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_eclk[i][j])
#  
#  def print_lut_eclk(self):
#    for i in range(len(self.lut_eclk)):
#      print(self.lut_eclk[i])
#
#  def write_list2_eclk(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_eclk = []
#    self.lut_eclk_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_eclk.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_eclk.append(outline)
#    ## values
#    self.lut_eclk.append("values ( \\")
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_eclk[i][j])+", "
#        tmp_line = str("{:5f}".format(self.list2_eclk[i][j]*targetLib.voltage_mag/targetLib.energy_mag))
#        outline += tmp_line+", "
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_eclk[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_eclk[i][len(jlist)-1]*targetLib.voltage_mag/targetLib.energy_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_eclk[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_eclk[i][len(jlist)-1]*targetLib.voltage_mag/targetLib.energy_mag))
#        outline += tmp_line+"\", \\"
#      self.lut_eclk.append(outline)
#    self.lut_eclk.append(");")
#    # store min/center/max for doc
#    # min
#    self.lut_eclk_mintomax.append(str("{:5f}".format(np.amin(self.list2_eclk)*targetLib.voltage_mag/targetLib.energy_mag)))
#    # center
#    self.lut_eclk_mintomax.append(str("{:5f}".format(np.median(self.list2_eclk)*targetLib.voltage_mag/targetLib.energy_mag)))
#    # max
#    self.lut_eclk_mintomax.append(str("{:5f}".format(np.amax(self.list2_eclk)*targetLib.voltage_mag/targetLib.energy_mag)))
#
#  ## clock input capacitance 
#  def set_list2_cclk(self, list2_cclk=[]):
#    self.list2_cclk = list2_cclk 
#
#  def print_list2_cclk(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_cclk[i][j])
#  
#  def print_lut_cclk(self):
#    for i in range(len(self.lut_cclk)):
#      print(self.lut_cclk[i])
#
#  def average_list2_cclk(self, targetLib, ilist, jlist):
#    ## output average of input capacitance
#    ## (do not write table)
#    self.lut_cclk = 0;
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        self.lut_cclk += self.list2_cclk[i][j]
#    #self.cclk = str(self.lut_cclk / (len(ilist) * len(jlist))/targetLib.capacitance_mag) ## use average
#    self.cclk = str(self.lut_cclk / (len(ilist) * len(jlist))) ## use average
#    #print("store cclk:"+str(self.cclk))
#
#  ## leak power
#  def set_list2_pleak(self, list2_pleak=[]):
#    self.list2_pleak = list2_pleak 
#
#  def print_list2_pleak(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_pleak[i][j])
#  
#  def print_lut_pleak(self):
#    for i in range(len(self.lut_pleak)):
#      print(self.lut_pleak[i])
#
#  def write_list2_pleak(self, targetLib, ilist, jlist):
#    ## output average of leak power
#    ## (do not write table)
#    self.lut_pleak = 0;
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        self.lut_pleak += self.list2_pleak[i][j]
#    #self.pleak = str(self.lut_pleak / (len(ilist) * len(jlist))/targetLib.leakage_power_mag) # use average
#    self.pleak = str("{:5f}".format(self.lut_pleak / (len(ilist) * len(jlist))/targetLib.leakage_power_mag)) # use average
#  
#  ## setup (for flop)
#  def set_list2_setup(self, list2_setup=[]):
#    self.list2_setup = list2_setup 
#
#  def print_list2_setup(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_setup[i][j])
#  
#  def print_lut_setup(self):
#    for i in range(len(self.lut_setup)):
#      print(self.lut_setup[i])
#
#  def write_list2_setup(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_setup = []
#    self.lut_setup_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_setup.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_setup.append(outline)
#    ## values
#    self.lut_setup.append("values ( \\")
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_setup[i][j])+", "
##        targetLib.print_msg(str(i)+" "+str(j))
##        targetLib.print_msg(self.list2_setup)
##        targetLib.print_msg(str("{:5f}".format(self.list2_setup[i][j]/targetLib.time_mag)))
#        tmp_line = str("{:5f}".format(self.list2_setup[i][j]/targetLib.time_mag))
#        outline += tmp_line+", "
#
#      ## do not add "," for last line
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_setup[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_setup[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_setup[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_setup[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\", \\"
#
#      self.lut_setup.append(outline)
#
#    self.lut_setup.append(");")
#    # store min/center/max for doc
#    # min
#    self.lut_setup_mintomax.append(str("{:5f}".format(np.amin(self.list2_setup)/targetLib.time_mag)))
#    # center
#    self.lut_setup_mintomax.append(str("{:5f}".format(np.median(self.list2_setup)/targetLib.time_mag)))
#    # max
#    self.lut_setup_mintomax.append(str("{:5f}".format(np.amax(self.list2_setup)/targetLib.time_mag)))
#
#  ## hold (for flop)
#  def set_list2_hold(self, list2_hold=[]):
#    self.list2_hold = list2_hold 
#
#  def print_list2_hold(self, ilist, jlist):
#    for i in range(len(ilist)):
#      for j in range(len(jlist)):
#        print(self.list2_hold[i][j])
#  
#  def print_lut_hold(self):
#    for i in range(len(self.lut_hold)):
#      print(self.lut_hold[i])
#
#  def write_list2_hold(self, targetLib, ilist, jlist):
#    ## index_1
#    outline = "index_1(\""
#    self.lut_hold = []
#    self.lut_hold_mintomax = []
#    for j in range(len(jlist)-1):
#      outline += str(jlist[j])+", " 
#    outline += str(jlist[len(jlist)-1])+"\");" 
#    #print(outline)
#    self.lut_hold.append(outline)
#    ## index_2
#    outline = "index_2(\""
#    for i in range(len(ilist)-1):
#      outline += str(ilist[i])+", " 
#    outline += str(ilist[len(ilist)-1])+"\");" 
#    self.lut_hold.append(outline)
#    ## values
#    self.lut_hold.append("values ( \\")
#    for i in range(len(ilist)):
#      outline = "\""
#      for j in range(len(jlist)-1):
#        #outline += str(self.list2_hold[i][j])+", "
#        tmp_line = str("{:5f}".format(self.list2_hold[i][j]/targetLib.time_mag))
#        outline += tmp_line+", "
#
#      ## do not add "," for last line
#      if(i == (len(ilist)-1)): 
#        #outline += str(self.list2_hold[i][len(jlist)-1])+"\" \\"
#        tmp_line = str("{:5f}".format(self.list2_hold[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\" \\"
#      ##  add "," for else 
#      else: 
#        #outline += str(self.list2_hold[i][len(jlist)-1])+"\", \\"
#        tmp_line = str("{:5f}".format(self.list2_hold[i][len(jlist)-1]/targetLib.time_mag))
#        outline += tmp_line+"\", \\"
#
#      self.lut_hold.append(outline)
#
#    self.lut_hold.append(");")
#
#    # store min/center/max for doc
#    # min
#    self.lut_hold_mintomax.append(str("{:5f}".format(np.amin(self.list2_hold)/targetLib.time_mag)))
#    # center
#    self.lut_hold_mintomax.append(str("{:5f}".format(np.median(self.list2_hold)/targetLib.time_mag)))
#    # max
#    self.lut_hold_mintomax.append(str("{:5f}".format(np.amax(self.list2_hold)/targetLib.time_mag)))

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
    
