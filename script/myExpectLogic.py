from dataclasses import dataclass, field

@dataclass
class MyExpectLogic:
  pin_otr     : list[str]      =field(default_factory=list); #pin definition, {"o0", "i0", "c0"} for outport, targetport, relatedport
  arc_otr     : list[str]      =field(default_factory=list); #arc             {"r" ,"r"  , "f"}  for outport, targetport, relatedport
  ival        : dict[str,list[str]]=field(default_factory=list)    ; #initial value  {"o":["0","1",,],"i":["0","1",,],"b":["0""1",,],"c":["0","1",,],"r":["0","1",,],"s":["0","1",,]]
  mondrv_otr  : list[str]      =field(default_factory=list); #new value.     {"0", "0", "1"} for outport, targetport, relatedport
  tmg_type    : str = "combinational"  ; #timing_type for related pin
  tmg_sense   : str = "pos"            ; #timing_sense=pos,neg,non
  tmg_when    : str = ""               ; #when condition in .lib/.v (optional)
  specify     : str = ""               ; #specify code in .v (optional). 

#-----
#--- order of expect is (val1_r=1 -> val1_r=0)
#--- ";;" in specify block means ifnon statement. 
logic_dict={
    "BUF":{"logic_type":"comb",
           "functions":{"o0":"i0"},
           "expect":
           [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
            MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),]
    },

    "DEL":{"logic_type":"comb",
           "functions":{"o0":"i0"},
           "expect":
           [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
            MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),]
    },
    
    "INV":{"logic_type":"comb",
           "functions":{"o0":"!i0"},
           "expect":
           [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
            MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),]
    },
    
    "AND2":{"logic_type":"comb",
            "functions":{"o0":"i0&i1"},
            "expect":                                                     
            [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["0","1"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["1","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),
                                                                                                                                                           
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["1","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["1","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),]
    },
    "AND3":{"logic_type":"comb",
            "functions":{"o0":"i0&i1&i2"},
            "expect":
            [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["0","1","1"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["1","1","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["1","0","1"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["1","1","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["0"],"i":["1","1","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["1"],"i":["1","1","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),]
    },
    "AND4":{"logic_type":"comb",
            "functions":{"o0":"i0&i1&i2&i3"},
            "expect":
            [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["0","1","1","1"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["1","0","1","1"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["0"],"i":["1","1","0","1"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i3"],ival={"o":["0"],"i":["1","1","1","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i3"],ival={"o":["1"],"i":["1","1","1","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i3 => o0) = (0,0);"),]
    },
    
    "OR2":{"logic_type":"comb",
           "functions":{"o0":"i0|i1"},
           "expect":
            [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["0","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["1","0"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["0","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["0","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),]
    },
    "OR3":{"logic_type":"comb",
           "functions":{"o0":"i0|i1|i2"},
           "expect":                                                     
            [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["0","0","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["1","0","0"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["0","0","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["0","1","0"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["0"],"i":["0","0","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["1"],"i":["0","0","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),]
    },
    "OR4":{"logic_type":"comb",
           "functions":{"o0":"i0|i1|i2|i3"},
           "expect":
            [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["1","0","0","0"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["0","1","0","0"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["1"],"i":["0","0","1","0"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i3"],ival={"o":["0"],"i":["0","0","0","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i3"],ival={"o":["1"],"i":["0","0","0","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="", specify="(i3 => o0) = (0,0);"),]
    },
    
    "NAND2":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1)"},
             "expect":                                                     
            [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["0","1"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["1","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["1","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["1","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),]
    },
    "NAND3":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1&i2)"},
             "expect":                                                     
            [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["0","1","1"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["1","1","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["1","0","1"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["1","1","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["1"],"i":["1","1","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["0"],"i":["1","1","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),]
    },
    "NAND4":{"logic_type":"comb",
             "functions":{"o0":"!(i0&i1&i2&i3)"},
             "expect":                                                     
            [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["0","1","1","1"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["1","0","1","1"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["1"],"i":["1","1","0","1"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i3"],ival={"o":["1"],"i":["1","1","1","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i3"],ival={"o":["0"],"i":["1","1","1","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i3 => o0) = (0,0);"),]
    },

    "NOR2":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1)"},
            "expect":
            [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["0","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["1","0"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["0","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["0","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),]
    },
    "NOR3":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1|i2)"},
            "expect":                                                     
            [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["0","0","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["1","0","0"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["0","0","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["0","1","0"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["1"],"i":["0","0","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["0"],"i":["0","0","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),]
    },
    "NOR4":{"logic_type":"comb",
            "functions":{"o0":"!(i0|i1|i2|i3)"},
            "expect":                                                     
            [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["1","0","0","0"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i0 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["0","1","0","0"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i1 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i2"],ival={"o":["0"],"i":["0","0","1","0"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i2 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i3"],ival={"o":["1"],"i":["0","0","0","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i3"],ival={"o":["0"],"i":["0","0","0","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="", specify="(i3 => o0) = (0,0);"),]
    },


    "XOR2":{"logic_type":"comb",
            "functions":{"o0":"i0^i1"},
            "expect":                                                     
            [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["0","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="!i1", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["1","0"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="!i1", specify="(i0 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["0","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="!i0", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["0","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="!i0", specify="(i1 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["0","1"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="i1", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["1","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="i1", specify="(i0 => o0) = (0,0);;"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["1","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="i0", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["1","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="i0", specify="(i1 => o0) = (0,0);;"),]
    },

    "XNOR2":{"logic_type":"comb",
             "functions":{"o0":"!(i0^i1)"},
             "expect":                                                     
            [MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["0","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="!i1", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["1","0"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="!i1", specify="(i0 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["0","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="!i0", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["0","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="!i0", specify="(i1 => o1) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["0"],"i":["0","1"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="i1", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i0"],ival={"o":["1"],"i":["1","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="i1", specify="(i0 => o0) = (0,0);;"),

             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["0"],"i":["1","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="i0", specify=""),
             MyExpectLogic(pin_otr=["o0","o0","i1"],ival={"o":["1"],"i":["1","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="i0", specify="(i1 => o0) = (0,0);;"),]
    },

    "MUX2":{"logic_type":"comb",
            "functions":{"o0":"(i0&!i2)|(i1&i2)"},  #--- o0 = (i2)? i1 : i0
            "expect":                                                     
            [MyExpectLogic(pin_otr=["o0","o0""i0"],ival={"o":["0"],"i":["0","0","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="!i2", specify=""),
             MyExpectLogic(pin_otr=["o0","o0""i0"],ival={"o":["1"],"i":["1","0","0"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="!i2", specify="(i0 => o0) = (0,0);;"),

             MyExpectLogic(pin_otr=["o0","o0""i1"],ival={"o":["0"],"i":["0","0","1"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="!i2", specify=""),
             MyExpectLogic(pin_otr=["o0","o0""i1"],ival={"o":["1"],"i":["0","1","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="!i2", specify="(i1 => o0) = (0,0);;"),

             MyExpectLogic(pin_otr=["o0","o0""i2"],ival={"o":["0"],"i":["0","1","0"]},mondrv_otr=["1","1","1"],tmg_type="combinational",tmg_sense="pos",arc_otr=["r","r","r"],tmg_when="!i0&i1", specify=""),
             MyExpectLogic(pin_otr=["o0","o0""i2"],ival={"o":["1"],"i":["0","1","1"]},mondrv_otr=["0","0","0"],tmg_type="combinational",tmg_sense="pos",arc_otr=["f","f","f"],tmg_when="!i0&i1", specify="(i2 => o0) = (0,0);"),

             MyExpectLogic(pin_otr=["o0","o0""i2"],ival={"o":["1"],"i":["1","0","0"]},mondrv_otr=["0","0","1"],tmg_type="combinational",tmg_sense="neg",arc_otr=["f","f","r"],tmg_when="i0&!i1", specify=""),
             MyExpectLogic(pin_otr=["o0","o0""i2"],ival={"o":["0"],"i":["1","0","1"]},mondrv_otr=["1","1","0"],tmg_type="combinational",tmg_sense="neg",arc_otr=["r","r","f"],tmg_when="i0&!i1", specify="(i2 => o0) = (0,0);;"),]
    },

    
#    "DFF_PC_PR_PS":{
#           "logic_type":"seq",
#           "function":{"o0":"i0"},
#           "cell_footprint":"",
#           "next_state":"",
#           "clocked_on":"c0",
#           "clear":"r0",
#           "preset":"s0",
#           "clear_preset_val1":"L",
#           "clear_preset_val2":"L",
#           "expect":
#           [#--- setup (change to new value)
#            MyExpectLogic(pin_otr={"o":"o0","t":"i0", "rel":"c0"}, ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["0"]}, mondrv_otr={"o":"1","t":"1","rel":"1"}
#                        ,tmg_type="setup_rising" ,tmg_sense="pos",arc_t="r", arc_r="r", tmg_when="", specify="$setup(posedge i0, posedge c0, 0, notifier)"),
#            MyExpectLogic(pin_otr={"o":"o0","t":"i0", "rel":"c0"}, ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["0"]}, mondrv_otr={"o":"0","t":"0","rel":"1"}
#                        ,tmg_type="setup_falling",tmg_sense="pos",arc_t="f", arc_r="r",tmg_when="", specify="$setup(negedge i0, posedge c0, 0, notifier)"),
#            #--- hold (keep current value)
#            MyExpectLogic(pin_otr={"o":"o0","t":"i0", "rel":"c0"}, ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["0"]}, mondrv_otr={"o":"1","t":"0","rel":"1"}
#                        ,tmg_type="hold_rising",tmg_sense="pos",arc_t="r", tmg_when="", specify="$hold(posedge i0, posedge c0, 0, notifier)"),
#            MyExpectLogic(pin_otr={"o":"o0","t":"i0", "rel":"c0"}, ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["0"]}, mondrv_otr={"o":"0","t":"1","rel":"1"}
#                        ,tmg_type="hold_rising",tmg_sense="pos",arc="r", tmg_when="", specify="$hold(negedge i0, posedge c0, 0, notifier)"),
#            #--- recovery reset(changet to new value)
#            MyExpectLogic(pin_otr={"o":"o0","t":"r0", "rel":"c0"}, ival={"o":["0"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["0"]}, mondrv_otr={"o":"1","t":"0","rel":"1"}
#                        ,tmg_type="recovery_rising",tmg_sense="neg",arc="r", tmg_when="", specify="$recovery(posedge r0, posedge c0, 0, notifier)"),
#            #--- removal reset(keep current value)
#            MyExpectLogic(pin_otr={"o":"o0","t":"r0", "rel":"c0"}, ival={"o":["0"],"i":["1"],"b":[],"c":["0"],"r":["1"],"s":["0"]}, mondrv_otr={"o":"0","t":"0","rel":"1"}
#                        ,tmg_type="recovery_rising",tmg_sense="neg",arc="r", tmg_when="", specify="$removal(posedge c0, posedge r0, 0, notifier)"),
#            #--- recovery set(changet to new value)
#            MyExpectLogic(pin_otr={"o":"o0","t":"s0", "rel":"c0"}, ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["1"]}, mondrv_otr={"o":"0","t":"0","rel":"1"}
#                        ,tmg_type="recovery_rising",tmg_sense="neg",arc="r", tmg_when="", specify="$recovery(posedge s0, posedge c0, 0, notifier)"),
#            #--- removal set(keep current value)
#            MyExpectLogic(pin_otr={"o":"o0","t":"s0", "rel":"c0"}, ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["1"]}, mondrv_otr={"o":"1","t":"0","rel":"1"}
#                        ,tmg_type="recovery_rising",tmg_sense="neg",arc="r", tmg_when="", specify="$removal(posedge c0, posedge s0, 0, notifier)"),
#            #--- q delay (clk)
#            MyExpectLogic(pin_otr={"o":"o0","t":"o0", "rel":"c0"}, ival={"o":["0"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["0"]}, mondrv_otr={"o":"1","t":"1","rel":"1"}
#                        ,tmg_type="rising_edge" ,tmg_sense="pos",arc="r", tmg_when="", specify=""),
#            MyExpectLogic(pin_otr={"o":"o0","t":"o0", "rel":"c0"}, ival={"o":["1"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["0"]}, mondrv_otr={"o":"0","t":"0","rel":"1"}
#                        ,tmg_type="rising_edge",tmg_sense="pos",arc="r", tmg_when="", specify="($posedge c0 => (o0 +: i0)) =(0,0)"),
#            #--- clear
#            MyExpectLogic(pin_otr={"o":"o0","t":"o0", "rel":"r0"}, ival={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["0"]}, mondrv_otr={"o":"0","t":"0","rel":"1"}
#                        ,tmg_type="clear"      ,tmg_sense="neg",arc="f", tmg_when="", specify="(posedge r0 => (o0 +: 1'b1)) = (0,0)"),
#            #--- preset
#            MyExpectLogic(pin_otr={"o":"o0","t":"o0", "rel":"s0"}, ival={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["0"]}, mondrv_otr={"o":"1","t":"1","rel":"1"}
#                        ,tmg_type="prset"      ,tmg_sense="pos",arc="r", tmg_when="", specify="(posedge s0 => (o0 +: 1'b1)) = (0,0)"),
#
#               
#            MyExpectLogic(pin_t="o0",pin_r="i0", val0_oibcrs={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["0"]},val1_t="1",val1_r="1"
#                        ,tmg_type="rising_edge",tmg_sense="pos",arc="r", tmg_when="", specify=""),
#            MyExpectLogic(pin_t="o0",pin_r="i0", val0_oibcrs={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["0"]},val1_t="0",val1_r="0"
#                        ,tmg_type="rising_edge",tmg_sense="pos",arc="r", tmg_when="", specify="(posedge c0 => (o0 +: i0) = (0,0))"),
#            MyExpectLogic(pin_t="o0",pin_r="r0", val0_oibcrs={"o":["1"],"i":["1"],"b":[],"c":["0"],"r":["0"],"s":["0"]},val1_t="0",val1_r="1"
#                        ,tmg_type="clear"      ,tmg_sense="neg",arc="f", tmg_when="", specify="(posedge r0 => (o0 -: 1'b1) = (0,0))"),
#            MyExpectLogic(pin_t="o0",pin_r="s0", val0_oibcrs={"o":["0"],"i":["0"],"b":[],"c":["0"],"r":["0"],"s":["0"]},val1_t="1",val1_r="1"
#                        ,tmg_type="clear"      ,tmg_sense="pos",arc="r", tmg_when="", specify="(posedge s0 => (o0 +: 1'b1) = (0,0))"),
#           ]
#    },
}


code_primitive='''
primitive my_mux (q, d0, d1, s);
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
