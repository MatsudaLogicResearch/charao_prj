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
  meas_type   : str = "combinational"  ; #measure_type( )
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
#--- order of expect is (val1_r=1 -> val1_r=0)
#--- ";;" in specify block means ifnon statement. 
logic_dict={
    "BUF":{"logic_type":"comb",
           "functions":{"o0":"i0"},
           "expect":
           [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),]
    },

    "DEL":{"logic_type":"comb",
           "functions":{"o0":"i0"},
           "expect":
           [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),]
    },
    
    "INV":{"logic_type":"comb",
           "functions":{"o0":"!i0"},
           "expect":
           [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
            MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),]
    },
    
    "AND2":{"logic_type":"comb",
            "functions":{"o0":"i0&i1"},
            "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","1"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),
                                                                                                                                                           
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),]
    },
    "AND3":{"logic_type":"comb",
            "functions":{"o0":"i0&i1&i2"},
            "expect":
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","1","1"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","1","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","0","1"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","1","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["1","1","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["1","1","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),]
    },
    "AND4":{"logic_type":"comb",
            "functions":{"o0":"i0&i1&i2&i3"},
            "expect":
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","1","1","1"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","0","1","1"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["1","1","0","1"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["0"],"i":["1","1","1","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i3 => o0) = (0,0);"),]
    },
    
    "OR2":{"logic_type":"comb",
           "functions":{"o0":"i0|i1"},
           "expect":
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","0"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),]
    },
    "OR3":{"logic_type":"comb",
           "functions":{"o0":"i0|i1|i2"},
           "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","0","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","0","0"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","0","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","1","0"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["0","0","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["0","0","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),]
    },
    "OR4":{"logic_type":"comb",
           "functions":{"o0":"i0|i1|i2|i3"},
           "expect":
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","0","0","0"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","1","0","0"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["0","0","1","0"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["1"],"i":["0","0","0","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="", specify="(i3 => o0) = (0,0);"),]
    },
    
    "NAND2":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1)"},
             "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","1"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),]
    },
    "NAND3":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1&i2)"},
             "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","1","1"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","1","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","0","1"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","1","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["1","1","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["1","1","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),]
    },
    "NAND4":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1&i2&i3)"},
             "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","1","1","1"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","0","1","1"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["1","1","0","1"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["1"],"i":["1","1","1","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i3 => o0) = (0,0);"),]
    },

    "NOR2":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1)"},
            "expect":
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","0"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),]
    },
    "NOR3":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1|i2)"},
            "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","0","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","0","0"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","0","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","1","0"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["0","0","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["0","0","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),]
    },
    "NOR4":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1|i2|i3)"},
            "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","0","0","0"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","1","0","0"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["0","0","1","0"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","i3","i3"],ival={"o":["0"],"i":["0","0","0","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="", specify="(i3 => o0) = (0,0);"),]
    },


    "XOR2":{"logic_type":"comb",
            "functions":{"o0":"i0^i1"},
            "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","0"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="!i1", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="!i0", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="!i0", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","1"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="i1", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="i0", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="i0", specify="(i1 => o0) = (0,0);;"),]
    },

    "XNOR2":{"logic_type":"comb",
             "functions":{"o0":"!(i0^i1)"},
             "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["0","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["1","0"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="!i1", specify="(i0 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="!i0", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="!i0", specify="(i1 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","1"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="i1", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="i1", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["1","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="i0", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["1","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="i0", specify="(i1 => o0) = (0,0);;"),]
    },

    "MUX2":{"logic_type":"comb",
            "functions":{"o0":"(i0&!i2)|(i1&i2)"},  #--- o0 = (i2)? i1 : i0
            "expect":                                                     
            [MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["0"],"i":["0","0","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i0","i0"],ival={"o":["1"],"i":["1","0","0"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="!i2", specify="(i0 => o0) = (0,0);;"),

             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["0"],"i":["0","0","1"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="!i2", specify=""),
             MyExpectCell(pin_oir=["o0","i1","i1"],ival={"o":["1"],"i":["0","1","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="!i2", specify="(i1 => o0) = (0,0);;"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["0","1","0"]},mondrv_oir=["1","1","1"],meas_type="combinational",tmg_sense="pos",arc_oir=["r","r","r"],tmg_when="!i0&i1", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["0","1","1"]},mondrv_oir=["0","0","0"],meas_type="combinational",tmg_sense="pos",arc_oir=["f","f","f"],tmg_when="!i0&i1", specify="(i2 => o0) = (0,0);"),

             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["1"],"i":["1","0","0"]},mondrv_oir=["0","0","1"],meas_type="combinational",tmg_sense="neg",arc_oir=["f","r","r"],tmg_when="i0&!i1", specify=""),
             MyExpectCell(pin_oir=["o0","i2","i2"],ival={"o":["0"],"i":["1","0","1"]},mondrv_oir=["1","1","0"],meas_type="combinational",tmg_sense="neg",arc_oir=["r","f","f"],tmg_when="i0&!i1", specify="(i2 => o0) = (0,0);;"),]
    },

    
  #==========================================================================================================================================================
  #Q
    "DFF_PC_NR_NS":{
           "logic_type":"seq",
           "functions":{"o0":"Io0"},
           "ff":{"out":"Io0",
                 "next_state":"i0",
                 "clocked_on":"c0",
                 "clear":"(!r0)",
                 "preset":"(!s0)",
                 "clear_preset_var1":"X",
                 "clear_preset_var2":"X"},
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
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","f","s"], tmg_when="", specify=""),
             #--- passive power(preset)
             MyExpectCell(pin_oir=["o0","s0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","s0","c0"], ival={"o":["1","0"],"i":["1"],"b":[],"c":["0"],"s":["0"]}, mondrv_oir=["1","1","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","f","s"], tmg_when="", specify=""),
             
             #--- passive power(clk)
             MyExpectCell(pin_oir=["o0","c0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["0"]}, mondrv_oir=["0","1","1"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","r","s"], tmg_when="", specify=""),
             MyExpectCell(pin_oir=["o0","c0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["1"],"s":["0"]}, mondrv_oir=["0","0","0"]
                        ,meas_type="passive"      ,tmg_sense="non",arc_oir=["s","f","s"], tmg_when="", specify=""),
             
             #--- min_pulse(clk)
             MyExpectCell(pin_oir=["o0","i0","c0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","1","1"]
                        ,meas_type="min_pulse_width_high",tmg_sense="non",arc_oir=["r","r","r"], tmg_when="", specify="$width(posedge c0, 0, 0, notifier);"),
             #--- min_pulse(preset)
             MyExpectCell(pin_oir=["o0","i0","s0"], ival={"o":["0","1"],"i":["0"],"b":[],"c":["0"],"s":["1"]}, mondrv_oir=["1","0","0"]
                        ,meas_type="min_pulse_width_low" ,tmg_sense="non",arc_oir=["r","s","f"], tmg_when="", specify="$width(negedge s0, 0, 0, notifier);"),
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
