import re
import copy

from dataclasses import dataclass, field

@dataclass
class MyExpectCell:
  pin_oir     : list[str]      =field(default_factory=list); #pin definition, {"o0", "i0", "c0"} for outport, inport, relatedport
  arc_oir     : list[str]      =field(default_factory=list); #arc             {"r" ,"r"  , "f"}  for outport, inport, relatedport
  ival        : dict[str,list[str]]=field(default_factory=lambda:{"o":[],"i":[],"b":[],"c":[],"r":[],"s":[]});#initial value  {"o":["0","1",,],"i":["0","1",,],"b":["0""1",,],"c":["0","1",,],"r":["0","1",,],"s":["0","1",,]]
  mondrv_oir  : list[str]      =field(default_factory=list); #new value.     {"0", "0", "1"} for outport, inport, relatedport
  rval        : dict[str,list[str]]=field(default_factory=dict); #result value {"o":["0","1",,],"i":["0","1",,],"b":["0""1",,],"c":["0","1",,],"r":["0","1",,],"s":["0","1",,]]
  meas_type   : str = "delay"          ; #measure_type( )
  tmg_sense   : str = "pos"            ; #timing_sense=pos,neg,non
  tmg_when    : str = ""               ; #when condition in .lib/.v (optional)
  specify     : str = ""               ; #specify code in .v (optional). 

  def __post_init__(self):

    ##-- generate rval(result value) from ival/mondrv_oir
    tval=copy.deepcopy(self.ival); # copy initial value

    for i, pin_pos in  enumerate(self.pin_oir):
      #-- get new value
      val_new=self.mondrv_oir[i];
      
      #-- get output/input/related port name
      flag=re.match(r"([oibcrs])([0-9]+)", pin_pos)
      pin=flag.group(1)
      pos=flag.group(2)
      if not flag:
        print(f"[Error] unknown pin name={pin} in pin_oir.")
        my_exit()

      #-- change value
      tval[pin][int(pos)]=val_new

    #
    self.rval=tval.copy()
    #print(f"ival1 ={self.ival}")
    #print(f"rval ={self.rval}\n")
      
#-----
#--- ";;" in specify block means ifnon statement. 
logic_dict={
    "BUF":{"logic_type":"comb",
           "functions":{"o0":"i0"},
           "expect":
           [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),
             #--- leakage
            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0", specify=""),
            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0", specify=""),
            ]
    },

    "DEL":{"logic_type":"comb",
           "functions":{"o0":"i0"},
           "expect":
           [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),
             #--- leakage
            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0", specify=""),
            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0", specify=""),
            ]
    },
    
    "INV":{"logic_type":"comb",
           "functions":{"o0":"!i0"},
           "expect":
           [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0"]},mondrv_oir=["0","1","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1"]},mondrv_oir=["1","0","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),
             #--- leakage
            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0", specify=""),
            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0", specify=""),
            ]
    },
    
    "AND2":{"logic_type":"comb",
            "functions":{"o0":"i0&i1"},
            "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","1"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1", specify=""),
             ]
    },
    "AND3":{"logic_type":"comb",
            "functions":{"o0":"i0&i1&i2"},
            "expect":
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","1","1"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","1","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","0","1"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","1","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["1","1","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["1","1","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0","0"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1","0"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&i2", specify=""),
             ]
    },
    "AND4":{"logic_type":"comb",
            "functions":{"o0":"i0&i1&i2&i3"},
            "expect":
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","1","1","1"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","0","1","1"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["1","1","0","1"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["0"],"i":["1","1","1","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i3 => o0) = (0,0);"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0","0","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0","0","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0","1","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0","1","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1","0","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1","0","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1","1","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1","1","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0","0","0"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0","0","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0","1","0"]},mondrv_oir=["0","1","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0","1","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1","0","0"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1","0","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1","1","0"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1","1","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&i2&i3", specify=""),
             ]
    },
    
    "OR2":{"logic_type":"comb",
           "functions":{"o0":"i0|i1"},
           "expect":
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","0"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1", specify=""),
             ]
    },
    "OR3":{"logic_type":"comb",
           "functions":{"o0":"i0|i1|i2"},
           "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","0","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","0","0"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","0","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","1","0"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["0","0","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["0","0","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0","0"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1","0"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&i2", specify=""),
             ]
    },
    "OR4":{"logic_type":"comb",
           "functions":{"o0":"i0|i1|i2|i3"},
           "expect":
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","0","0","0"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","1","0","0"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["0","0","1","0"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["1"],"i":["0","0","0","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i3 => o0) = (0,0);"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0","0","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0","0","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0","1","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0","1","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1","0","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1","0","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1","1","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1","1","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0","0","0"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0","0","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0","1","0"]},mondrv_oir=["1","1","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0","1","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1","0","0"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1","0","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1","1","0"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1","1","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&i2&i3", specify=""),
             ]
    },
    
    "NAND2":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1)"},
             "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","1"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","1"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","0"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","1"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1", specify=""),
             ]
    },
    "NAND3":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1&i2)"},
             "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","1","1"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","1","1"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","0","1"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","1","1"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["1","1","0"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["1","1","1"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0","0"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1","0"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&i2", specify=""),
             ]
    },
    "NAND4":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1&i2&i3)"},
             "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","1","1","1"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","0","1","1"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["1","1","0","1"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["1"],"i":["1","1","1","0"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i3 => o0) = (0,0);"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0","0","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0","0","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0","1","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0","1","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1","0","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1","0","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1","1","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1","1","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0","0","0"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0","0","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0","1","0"]},mondrv_oir=["1","1","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0","1","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1","0","0"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1","0","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1","1","0"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1","1","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&i2&i3", specify=""),
             ]
    },

    "NOR2":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1)"},
            "expect":
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","0"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","0"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","0"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","1"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1", specify=""),
             ]
    },
    "NOR3":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1|i2)"},
            "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","0","0"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","0","0"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","0","0"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","1","0"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["0","0","0"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["0","0","1"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0","0"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1","0"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&i2", specify=""),
             ]
    },
    "NOR4":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1|i2|i3)"},
            "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","0","0","0"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","1","0","0"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["0","0","1","0"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["0"],"i":["0","0","0","1"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i3 => o0) = (0,0);"),
             #--- leakag1
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0","0","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0","0","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0","1","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0","1","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1","0","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1","0","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1","1","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1","1","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0","0","0"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0","0","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0","1","0"]},mondrv_oir=["0","1","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0","1","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1","0","0"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1","0","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1","1","0"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1","1","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&i2&i3", specify=""),
             ]
    },


    "XOR2":{"logic_type":"comb",
            "functions":{"o0":"i0^i1"},
            "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","0"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="!i1", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="!i0", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="!i0", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","1"]},mondrv_oir=["0","1","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","1"]},mondrv_oir=["1","0","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="i1", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","0"]},mondrv_oir=["0","1","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="i0", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","1"]},mondrv_oir=["1","0","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="i0", specify="(i1 => o0) = (0,0);;"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","1"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1", specify=""),
            ]
    },

    "XNOR2":{"logic_type":"comb",
             "functions":{"o0":"!(i0^i1)"},
             "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","0"]},mondrv_oir=["0","1","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","0"]},mondrv_oir=["1","0","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="!i1", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","0"]},mondrv_oir=["0","1","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="!i0", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","1"]},mondrv_oir=["1","0","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="!i0", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","1"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="i1", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="i0", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="i0", specify="(i1 => o0) = (0,0);;"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1", specify=""),
            ]
    },

    "MUX2":{"logic_type":"comb",
            "functions":{"o0":"(i0&!i2)|(i1&i2)"},  #--- o0 = (i2)? i1 : i0
            "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","0","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","0","0"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="!i2", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","0","1"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","1","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="!i2", specify="(i1 => o0) = (0,0);;"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["0","1","0"]},mondrv_oir=["1","1","1"],meas_type="delay",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["0","1","1"]},mondrv_oir=["0","0","0"],meas_type="delay",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="!i0&i1", specify="(i2 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["1","0","0"]},mondrv_oir=["0","0","1"],meas_type="delay",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["1","0","1"]},mondrv_oir=["1","1","0"],meas_type="delay",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="i0&!i1", specify="(i2 => o0) = (0,0);;"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0","0"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","0","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["0","1","0"]},mondrv_oir=["0","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["0","1","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","0","0"]},mondrv_oir=["1","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["d"],"i":["1","0","1"]},mondrv_oir=["0","0","0"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!i1&i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1","0"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["u"],"i":["1","1","1"]},mondrv_oir=["1","1","1"],meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&i1&i2", specify=""),
            ]
    },

    
  #==========================================================================================================================================================
  #Q
    "DFF_PC_NR_NS":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0,IQB",
                 "next_state":"i0",
                 "clocked_on":"c0",
                 "clear":"(!r0)",
                 "preset":"(!s0)",
                 "clear_preset_var1":"L",
                 "clear_preset_var2":"H"},
           "expect":
           [
             #--- q delay (clk)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="rising_edge" ,tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","0","1"]
                         ,meas_type="rising_edge" ,tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             #--- clear
             MyExpectCell(pin_oir=["o0","i0","r0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","1","0"]
                        ,meas_type="clear"       ,tmg_sense="pos",arc_oir=["f","s","f"], tmg_when="", specify="(negedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- preset
             MyExpectCell(pin_oir=["o0","i0","s0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_type="preset"      ,tmg_sense="neg",arc_oir=["r","s","f"], tmg_when="", specify="(negedge s0 => (o0 -: 1'b1)) = (0,0);"),
             
             #--- setup
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_type="setup_rising" ,tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","0","1"]
                        ,meas_type="setup_rising" ,tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             #--- hold (arc_oir is same as setup)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_type="hold_rising",tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","0","1"]
                        ,meas_type="hold_rising",tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery reset
             MyExpectCell(pin_oir=["o0","r0", "c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oir=["1","1","1"]
                       ,meas_type="recovery_rising",tmg_sense="pos",arc_oir=["r","r","r"], tmg_when="", specify="$recovery(posedge r0, posedge c0, 0, notifier);"),
             #--- recovery set
             MyExpectCell(pin_oir=["o0","s0", "c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oir=["0","1","1"]
                       ,meas_type="recovery_rising",tmg_sense="pos",arc_oir=["f","r","r"], tmg_when="", specify="$recovery(posedge s0, posedge c0, 0, notifier);"),
             #--- removal reset(arc_oir is same as recovery)
             MyExpectCell(pin_oir=["o0","r0","c0"], ival={"o":["0"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oir=["0","1","1"]
                        ,meas_type="removal_rising",tmg_sense="non",arc_oir=["s","r","r"], tmg_when="", specify="$hold(posedge c0, posedge r0, 0, notifier);"),
             #--- removal set(arc_oir is same as recovery)
             MyExpectCell(pin_oir=["o0","s0","c0"], ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oir=["1","0","1"]
                        ,meas_type="removal_rising",tmg_sense="non",arc_oir=["s","r","r"], tmg_when="", specify="$hold(posedge c0, posedge s0, 0, notifier);"),
             
             #--- passive power(data)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","1","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","f","s"], tmg_when="", specify=""),
             #--- passive power(reset)
             MyExpectCell(pin_oir=["o0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","0","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","f","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","r0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["1"]}, mondrv_oir=["0","1","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","r","s"], tmg_when="", specify=""),
             #--- passive power(set)
             MyExpectCell(pin_oir=["o0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","f","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","s0","c0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["0"]}, mondrv_oir=["1","1","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","r","s"], tmg_when="", specify=""),
             #--- passive power(clk)
             MyExpectCell(pin_oir=["o0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","1","1"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","f","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","c0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["1"],"r":["1"],"s":["1"]}, mondrv_oir=["0","0","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","r","s"], tmg_when="", specify=""),
             #--- min_pulse(clk)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_type="min_pulse_width_high",tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse(reset)
             MyExpectCell(pin_oir=["o0","i0","r0"], ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["0","1","0"]
                        ,meas_type="min_pulse_width_low" ,tmg_sense="non",arc_oir=["f","s","f"], tmg_when="", specify="$width(negedge r0, 0, 0, notifier);"),
             #--- min_pulse(set)
             MyExpectCell(pin_oir=["o0","i0","s0"], ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["1"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_type="min_pulse_width_low" ,tmg_sense="non",arc_oir=["r","s","f"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
           ]
    },

  #==========================================================================================================================================================
  #Q,QB
    "DFFB_PC_PR":{
           "logic_type":"seq",
           "functions":{"o0":"Io0","o1":"Io1"},
           "ff":{"out":"Io0,Io1",
                 "next_state":"i0",
                 "clocked_on":"c0",
                 "clear":"(r0)"},
           "expect":
           [
             #--- q delay (clk)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["1","1","1"]
                        ,meas_type="rising_edge" ,tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","0","1"]
                        ,meas_type="rising_edge" ,tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             
             MyExpectCell(pin_oir=["o1","i0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["1","0","1"]
                        ,meas_type="rising_edge" ,tmg_sense="non",arc_oir=["r","f","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o1","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","1","1"]
                        ,meas_type="rising_edge" ,tmg_sense="non",arc_oir=["f","r","r"], tmg_when="", specify="(posedge c0 => (o1 +: i0)) =(0,0);"),
             #--- clear(q)
             MyExpectCell(pin_oir=["o0","i0","r0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","1","1"]
                       ,meas_type="clear"       ,tmg_sense="neg",arc_oir=["f","s","r"], tmg_when="", specify="(posedge r0 => (o0 +: 1'b0)) = (0,0);"),
             #--- clear(q)-->preset(qb)
             MyExpectCell(pin_oir=["o1","i0","r0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["1","1","1"]
                       ,meas_type="preset"       ,tmg_sense="pos",arc_oir=["r","s","r"], tmg_when="", specify="(posedge r0 => (o1 +: 1'b1)) = (0,0);"),
             
             #--- setup
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["1","1","1"]
                        ,meas_type="setup_rising" ,tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","0","1"]
                        ,meas_type="setup_rising" ,tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),

             #--- hold (arc_oir is same as setup)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["1","1","1"]
                        ,meas_type="hold_rising",tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1","1"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","0","1"]
                        ,meas_type="hold_rising",tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),
             #--- recovery reset
             MyExpectCell(pin_oir=["o0","r0", "c0"], ival={"o":["0","1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oir=["1","0","1"]
                       ,meas_type="recovery_rising",tmg_sense="pos",arc_oir=["r","f","r"], tmg_when="", specify="$recovery(negedge r0, posedge c0, 0, notifier);"),
             #--- removal reset(arc_oir is same as recovery)
             MyExpectCell(pin_oir=["o0","r0", "c0"], ival={"o":["0","1"],"i":["1"],"b":[],"c":["0"],"r":["1"]}, mondrv_oir=["0","0","1"]
                        ,meas_type="removal_rising",tmg_sense="non",arc_oir=["r","f","r"], tmg_when="", specify="$hold(posedge c0, negedge r0, 0, notifier);"),
             
             #--- passive power(data)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","1","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["1","0","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","f","s"], tmg_when="", specify=""),
             #--- passive power(reset)
             MyExpectCell(pin_oir=["o0","r0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","1","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","f","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","r0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["1"]}, mondrv_oir=["0","0","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","r","s"], tmg_when="", specify=""),
             
             #--- passive power(clk)
             MyExpectCell(pin_oir=["o0","c0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","1","1"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","c0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["1"],"r":["0"]}, mondrv_oir=["0","0","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","f","s"], tmg_when="", specify=""),
             #--- min_pulse(clk)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["1","1","1"]
                        ,meas_type="min_pulse_width_high",tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse(reset)
             MyExpectCell(pin_oir=["o0","i0","r0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"r":["0"]}, mondrv_oir=["0","1","1"]
                        ,meas_type="min_pulse_width_high",tmg_sense="non",arc_oir=["f","s","r"], tmg_when="", specify="$width(posedge r0, 0, 0, notifier);"),
             #--- leakage(clock->inputport & mondrv_oir[1]=clock value )
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"]},mondrv_oir=["0","0","0"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!c0&!r0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["1"]},mondrv_oir=["0","0","0"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!c0&r0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["0"]},mondrv_oir=["0","1","0"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","r","s"],tmg_when="!i0&c0&!r0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["d","u"],"i":["0"],"c":["0"],"r":["1"]},mondrv_oir=["0","1","0"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","r","s"],tmg_when="!i0&c0&r0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"]},mondrv_oir=["1","0","1"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!c0&!r0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["d","u"],"i":["1"],"c":["0"],"r":["1"]},mondrv_oir=["0","0","1"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!c0&r0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"r":["0"]},mondrv_oir=["1","1","1"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","r","s"],tmg_when="i0&c0&!r0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["d","u"],"i":["1"],"c":["0"],"r":["1"]},mondrv_oir=["0","1","1"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","r","s"],tmg_when="i0&c0&r0", specify=""),
           ]
    },

    "DFFB_PC_NS":{
           "logic_type":"seq",
           "functions":{"o0":"Io0","o1":"Io1"},
           "ff":{"out":"Io0,Io1",
                 "next_state":"i0",
                 "clocked_on":"c0",
                 "preset":"(!s0)"},
           "expect":
           [
             #--- q delay (clk)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_type="rising_edge" ,tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","0","1"]
                        ,meas_type="rising_edge" ,tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="(posedge c0 => (o0 +: i0)) =(0,0);"),
             
             MyExpectCell(pin_oir=["o1","i0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","0","1"]
                        ,meas_type="rising_edge" ,tmg_sense="non",arc_oir=["r","f","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o1","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","1","1"]
                        ,meas_type="rising_edge" ,tmg_sense="non",arc_oir=["f","r","r"], tmg_when="", specify="(posedge c0 => (o1 +: i0)) =(0,0);"),
             
             #--- preset(q)
             MyExpectCell(pin_oir=["o0","i0","s0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","0","0"]
                       ,meas_type="preset"      ,tmg_sense="neg",arc_oir=["r","s","f"], tmg_when="", specify="(negedge s0 => (o0 +: 1'b1)) = (0,0);"),
             #--- preset(q)-->clear(qb)
             MyExpectCell(pin_oir=["o1","i0","s0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","1","0"]
                       ,meas_type="clear"       ,tmg_sense="pos",arc_oir=["f","s","f"], tmg_when="", specify="(negedge s0 => (o1 +: 1'b0)) = (0,0);"),
             
             #--- setup
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_type="setup_rising" ,tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier);"),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","0","1"]
                        ,meas_type="setup_rising" ,tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier);"),
             
             #--- hold (arc_oir is same as setup)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_type="hold_rising",tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$hold(posedge c0, negedge i0, 0, notifier);"),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1","1"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","0","1"]
                        ,meas_type="hold_rising",tmg_sense="non",arc_oir=["f","f","r"], tmg_when="", specify="$hold(posedge c0, posedge i0, 0, notifier);"),

             #--- recovery preset
             MyExpectCell(pin_oir=["o0","s0", "c0"], ival={"o":["1","0"],"i":["0"],"b":[],"c":["0"],"s":["0"]}, mondrv_oir=["0","1","1"]
                       ,meas_type="recovery_rising",tmg_sense="pos",arc_oir=["f","r","r"], tmg_when="", specify="$recovery(posedge s0, posedge c0, 0, notifier);"),
             #--- removal preset(arc_oir is same as recovery)
             MyExpectCell(pin_oir=["o0","s0", "c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["0"]}, mondrv_oir=["0","1","1"]
                        ,meas_type="removal_rising",tmg_sense="pos",arc_oir=["f","r","r"], tmg_when="", specify="$hold(posedge c0, posedge s0, 0, notifier);"),
             
             #--- passive power(data)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","1","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","f","f"], tmg_when="", specify=""),
             #--- passive power(preset)
             MyExpectCell(pin_oir=["o0","s0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["0"]}, mondrv_oir=["1","1","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","s0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","f","s"], tmg_when="", specify=""),
             
             #--- passive power(clk)
             MyExpectCell(pin_oir=["o0","c0","s0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["0","1","1"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","c0","s0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["1"],"s":["1"]}, mondrv_oir=["0","0","1"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","f","s"], tmg_when="", specify=""),
             
             #--- min_pulse(clk)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_type="min_pulse_width_high",tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse(preset)
             MyExpectCell(pin_oir=["o0","i0","s0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_type="min_pulse_width_low" ,tmg_sense="non",arc_oir=["r","s","f"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
             
             #--- leakage(clock->inputport & mondrv_oir[1]=clock value )
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["0"],"c":["0"],"s":["0"]},mondrv_oir=["1","0","0"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!c0&!s0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["d","s"],"i":["0"],"c":["0"],"s":["1"]},mondrv_oir=["0","0","0"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="!i0&!c0&s0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["0"],"c":["0"],"s":["0"]},mondrv_oir=["1","1","0"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","r","s"],tmg_when="!i0&c0&!s0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["0"],"c":["0"],"s":["1"]},mondrv_oir=["1","1","0"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","r","s"],tmg_when="!i0&c0&s0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["0"]},mondrv_oir=["1","0","1"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!c0&!s0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["1"]},mondrv_oir=["1","0","1"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","s","s"],tmg_when="i0&!c0&s0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["0"]},mondrv_oir=["1","1","1"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","r","s"],tmg_when="i0&c0&!s0", specify=""),
             MyExpectCell(pin_oir=["o0","c0","i0"], ival={"o":["u","d"],"i":["1"],"c":["0"],"s":["1"]},mondrv_oir=["1","1","1"]
                        ,meas_type="leakage",tmg_sense="non",arc_oir=["s","r","s"],tmg_when="i0&c0&s0", specify=""),

           ]
    },
  

  #==========================================================================================================================================================
  #P_I[X|A|P|N]_SMT[X|A|S]_PU[X|A|P|N]_PD[X|A|P|N]_R[nm]_O[X|A|P|N]_SLW[X|S]_HD[X|P|N]_LD[X|P|N]_DUMP[nm]_DRV[nn]
  #
  #  I: input 
  #    IX: no function
  #    IA: always (no enable pin)
  #    IP: controled by enable(active High)
  #    IN: controled by enable(active Low)
  #  SMT: schumit
  #    SMTX: no function
  #    SMTA: always (no enable pin)
  #    SMTS: on/off by select pin
  #  PU: input pull-up 
  #    PUX: no function
  #    PUA: always (no enable pin)
  #    PUP: controled by enable(active High)
  #    PUN: controled by enable(active Low)
  #  PD: input pull-down
  #    PDX: no function
  #    PDA: always (no enable pin)
  #    PDP: controled by enable(active High)
  #    PDN: controled by enable(active Low)
  #  R: input registor
  #    R12: 100 Ohm (= n x 10^m)
  #  O: output
  #    OX: no function
  #    OA: always (no enable pin)
  #    OP: controled by enable(active High)
  #    ON: controled by enable(active Low)
  #  SLW: slew rate control
  #    SLWX: no function
  #    SLWS: change by select pin
  #  HD: output driver for High level
  #    HDX: no driver
  #    HDP: use PMOS driver
  #    HDN: use NMOS driver
  #  LD: output driver for Low level
  #    LDX: no driver
  #    LDP: use PMOS driver
  #    LDN: use NMOS driver
  #  DUMP: output dumping resistor
  #    DUMP51 : 50 Ohm(=n x 10^m)
  #  DRV: output driving current in mA
  #    DRV04: 4mA
  #
  #==========================================================================================================================================================
  # io-cell
  # P_I[X|A|P|N]_SMT[X|A|S]_PU[X|A|P|N]_PD[X|A|P|N]_O[X|A|P|N]_SLW[X|S]_HD[X|P|N]_LD[X|P|N]

  #---------------------------------------------------------------------------------------
  # PVDD (PAD:VDD)
  "P_VDD":{ 
    "logic_type":"io",
    "functions":{},
    "expect":
           [
             #--- no spice simulation
           ]
  },
  # PVSS (PAD:VSS)
  "P_VSS":{ 
    "logic_type":"io",
    "functions":{},
    "expect":
           [
             #--- no spice simulation
           ]
  },
  #---------------------------------------------------------------------------------------
  # PANA (PAD:b0)
  "P_ANA1":{ 
    "logic_type":"io",
    "functions":{},
    "expect":
           [
             #--- leakage
             MyExpectCell(pin_oir=["b0","b0","b0"], ival={"o":[],"i":[],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!b0", specify=""),
             MyExpectCell(pin_oir=["b0","b0","b0"], ival={"o":[],"i":[],"b":["1"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="b0", specify=""),
           ]
  },
  #---------------------------------------------------------------------------------------
  # PIC (PAD:b0, C:o0, IE:i0, PU_N:i1, PD_P:i2)
  "P_IP_SMTX_PUN_PDP_OX_SLWX_HDX_LDX":{ 
    "logic_type":"io",
    "functions":{"o0":"i0&b0"},
    "expect":
           [
             #--- PAD to CORE
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["1","1","0"],"b":["0"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="delay_i2c" ,tmg_sense="pos",arc_oir=["r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["1"],"i":["1","1","0"],"b":["1"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="delay_i2c" ,tmg_sense="pos",arc_oir=["f","f","f"], tmg_when="", specify="(b0 => o0)=(0,0);"),
             #--- IE to CORE
             MyExpectCell(pin_oir=["o0","i0","i0"], ival={"o":["0"],"i":["0","1","0"],"b":["1"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="delay_c2c" ,tmg_sense="pos",arc_oir=["r","s","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"], ival={"o":["1"],"i":["1","1","0"],"b":["1"]}, mondrv_oir=["0","1","0"]
                         ,meas_type="delay_c2c" ,tmg_sense="pos",arc_oir=["f","s","f"], tmg_when="", specify="(i0 => o0)=(0,0);"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["0","0","0"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&!i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["0","0","0"],"b":["1"]}, mondrv_oir=["0","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&!i1&!i2&b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["0","1","0"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["0","1","0"],"b":["1"]}, mondrv_oir=["0","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&!i2&b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["0","1","1"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&i2&!b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["0","1","1"],"b":["1"]}, mondrv_oir=["0","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&i2&b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["1","0","0"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="i0&!i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["1","0","0"],"b":["1"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="i0&!i1&!i2&b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["1","1","0"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="i0&i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["1","1","0"],"b":["1"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="i0&i1&!i2&b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["1","1","1"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="i0&i1&i2&!b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["1","1","1"],"b":["1"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="i0&i1&i2&b0", specify=""),
           ]
  },
  # PICS (PAD:b0, C:o0, IE:i0, PU_N:i1, PD_P:i2)
  "P_IP_SMTA_PUN_PDP_OX_SLWX_HDX_LDX":{ 
    "logic_type":"io",
    "functions":{"o0":"i0&b0"},
    "expect":
           [
             #--- PAD to CORE
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["1","1","0"],"b":["0"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="delay_i2c" ,tmg_sense="pos",arc_oir=["r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["1"],"i":["1","1","0"],"b":["1"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="delay_i2c" ,tmg_sense="pos",arc_oir=["f","f","f"], tmg_when="", specify="(b0 => o0)=(0,0);"),
             #--- IE to CORE
             MyExpectCell(pin_oir=["o0","i0","i0"], ival={"o":["0"],"i":["0","1","0"],"b":["1"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="delay_c2c" ,tmg_sense="pos",arc_oir=["r","s","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"], ival={"o":["1"],"i":["1","1","0"],"b":["1"]}, mondrv_oir=["0","1","0"]
                         ,meas_type="delay_c2c" ,tmg_sense="pos",arc_oir=["f","s","f"], tmg_when="", specify="(i0 => o0)=(0,0);"),
             #--- leakage
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["0","0","0"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&!i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["0","0","0"],"b":["1"]}, mondrv_oir=["0","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&!i1&!i2&b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["0","1","0"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["0","1","0"],"b":["1"]}, mondrv_oir=["0","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&!i2&b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["0","1","1"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&i2&!b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["0","1","1"],"b":["1"]}, mondrv_oir=["0","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&i2&b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["1","0","0"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&!i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["1","0","0"],"b":["1"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&!i1&!i2&b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["1","1","0"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&!i2&!b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["1","1","0"],"b":["1"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&!i2&b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["1","1","1"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&i2&!b0", specify=""),
             MyExpectCell(pin_oir=["o0","b0","b0"], ival={"o":["0"],"i":["1","1","1"],"b":["1"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&i2&b0", specify=""),
           ]
  },
  # POC (PAD:b0, OEN:i0, PU_N:i1, PD_P:i2, I:i3)
  "P_IX_SMTX_PUN_PDP_ON_SLWX_HDA_LDA":{ 
    "logic_type":"io",
    "functions":{"b0":"i3"},
    "expect":
           [
             #--- I to PAD
             MyExpectCell(pin_oir=["b0","i3","i3"], ival={"o":[],"i":["0","1","0","0"],"b":["0"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="delay_c2i" ,tmg_sense="pos",arc_oir=["r","r","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["b0","i3","i3"], ival={"o":[],"i":["0","1","0","1"],"b":["1"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="delay_c2i" ,tmg_sense="pos",arc_oir=["f","f","f"], tmg_when="", specify="(i3 => b0)=(0,0);"),
             #--- OE to PAD(enable)
             MyExpectCell(pin_oir=["b0","i3","i0"], ival={"o":[],"i":["1","1","0","1"],"b":["0"]}, mondrv_oir=["1","1","0"]
                         ,meas_type="three_state_enable_c2i" ,tmg_sense="neg",arc_oir=["r","s","f"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["b0","i3","i0"], ival={"o":[],"i":["1","1","0","0"],"b":["1"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="three_state_enable_c2i" ,tmg_sense="neg",arc_oir=["f","s","f"], tmg_when="", specify=""),
             #--- OE to PAD(disable)
             MyExpectCell(pin_oir=["b0","i3","i0"], ival={"o":[],"i":["0","1","0","0"],"b":["0"]}, mondrv_oir=["1","0","1"]
                         ,meas_type="three_state_disable_c2i" ,tmg_sense="pos",arc_oir=["r","s","r"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["b0","i3","i0"], ival={"o":[],"i":["0","1","0","1"],"b":["1"]}, mondrv_oir=["0","1","1"]
                         ,meas_type="three_state_disable_c2i" ,tmg_sense="pos",arc_oir=["f","s","r"], tmg_when="", specify="(i0 => b0)=(0,0,0,0,0,0);"),
             #--- leakage
             MyExpectCell(pin_oir=["b0","i3","i3"], ival={"o":[]  ,"i":["0","0","0","0"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["b0","i3","i3"], ival={"o":[]  ,"i":["0","0","0","1"],"b":["1"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["b0","i3","i3"], ival={"o":[]  ,"i":["0","1","0","0"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["b0","i3","i3"], ival={"o":[]  ,"i":["0","1","0","1"],"b":["1"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["b0","i3","i3"], ival={"o":[]  ,"i":["0","1","1","0"],"b":["0"]}, mondrv_oir=["0","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["b0","i3","i3"], ival={"o":[]  ,"i":["0","1","1","1"],"b":["1"]}, mondrv_oir=["1","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="!i0&i1&i2&i3", specify=""),
             MyExpectCell(pin_oir=["b0","i3","i3"], ival={"o":[]  ,"i":["1","0","0","0"],"b":["u"]}, mondrv_oir=["u","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="i0&!i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["b0","i3","i3"], ival={"o":[]  ,"i":["1","0","0","1"],"b":["u"]}, mondrv_oir=["u","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="i0&!i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["b0","i3","i3"], ival={"o":[]  ,"i":["1","1","0","0"],"b":["z"]}, mondrv_oir=["z","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="i0&i1&!i2&!i3", specify=""),
             MyExpectCell(pin_oir=["b0","i3","i3"], ival={"o":[]  ,"i":["1","1","0","1"],"b":["z"]}, mondrv_oir=["z","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="i0&i1&!i2&i3", specify=""),
             MyExpectCell(pin_oir=["b0","i3","i3"], ival={"o":[]  ,"i":["1","1","1","0"],"b":["d"]}, mondrv_oir=["d","0","0"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="i0&i1&i2&!i3", specify=""),
             MyExpectCell(pin_oir=["b0","i3","i3"], ival={"o":[]  ,"i":["1","1","1","1"],"b":["d"]}, mondrv_oir=["d","1","1"]
                         ,meas_type="leakage" ,tmg_sense="non",arc_oir=["s","s","s"], tmg_when="i0&i1&i2&i3", specify=""),
           ]
  },


}


code_primitive='''
primitive lr_dff (q, d, cp, cdn, sdn, notifier);
`protect
   output q;
   input d, cp, cdn, sdn, notifier;
   reg q;

   table
      ?   ?   0   ?   ? : ? : 0 ; // CDN dominate SDN
      ?   ?   1   0   ? : ? : 1 ; // SDN is set
      ?   ?   1   x   ? : 0 : x ; // SDN affect Q

      0 (01)  ?   1   ? : ? : 0 ; // Latch 0
      0   *   ?   1   ? : 0 : 0 ; // Keep 0 (D==Q)

      1 (01)  1   ?   ? : ? : 1 ; // Latch 1
      1   *   1   ?   ? : 1 : 1 ; // Keep 1 (D==Q)

      ? (1?)  1   1   ? : ? : - ; // ignore negative edge of clock
      ? (?0)  1   1   ? : ? : - ; // ignore negative edge of clock
      ?   ? (?1)  ?   ? : ? : - ; // ignore positive edge of CDN
      ?   ?   ? (?1)  ? : ? : - ; // ignore posative edge of SDN
      *   ?   ?   ?   ? : ? : - ; // ignore data change on steady clock

      ?   ?   ?   ?   * : ? : x ; // timing check violation
   endtable
`endprotect
endprimitive


primitive lr_mux (q, d0, d1, s);
   output q;
   input s, d0, d1;
`protect
   table
   // d0  d1  s   : q 
      0   ?   0   : 0 ;
      1   ?   0   : 1 ;
      ?   0   1   : 0 ;
      ?   1   1   : 1 ;
      0   0   x   : 0 ;
      1   1   x   : 1 ;
   endtable
`endprotect
endprimitive

'''
