from dataclasses import dataclass, field

@dataclass
class MyExpectLogic:
    pin_t    : str = "i0"             ; #target pin
    pin_r    : str = "o0"             ; #related pin
    arc      : str = "r"              ; #cell/transition arc=r,f. 
    val0_o   : list[str]=field(default_factory=list)        ; #initial value of o0,o1,,, ports.
    val0_i   : list[str]=field(default_factory=list)    ; #initial value of i0,i1,,, ports.
    val0_b   : list[str]=field(default_factory=list)           ; #initial value of b0,b1,,, ports. 
    val1_t   : str = "1"              ; #result  value of target pin.
    val1_r   : str = "1"              ; #result  value of related pin.
    tmg_type : str = "comb"           ; #timing_type =comb,three_e,three_d,comb_r,comb_f
    tmg_sense: str = "pos"            ; #timing_sense=pos,neg,non
    tmg_when : str = ""               ; #when condition in .lib/.v (optional)
    specify  : str = ""               ; #specify code in .v (optional). 
    
#-----
logic_dict={
    "BUF":{"functions":{"o0":"i0"},
           "expect":
           [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
            MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i0 => o0) = (0,0);"),]
    },
    
    "DEL":{"functions":{"o0":"i0"},
           "expect":
           [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
            MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i0 => o0) = (0,0);"),]
    },
    
    "INV":{"functions":{"o0":"!i0"},
           "expect":
           [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
            MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i0 => o0) = (0,0);"),]
    },
    
    "AND2":{"functions":{"o0":"i0&i1"},
            "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["0","1"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["1","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["1","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["1","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i1 => o0) = (0,0);"),]
    },
    "AND3":{"functions":{"o0":"i0&i1&i2"},
            "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["0","1","1"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["1","1","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["1","0","1"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["1","1","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i1 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="r", val0_o=["0"],val0_i=["1","1","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="f", val0_o=["1"],val0_i=["1","1","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i2 => o0) = (0,0);"),]
    },
    "AND4":{"functions":{"o0":"i0&i1&i2&i3"},
            "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["0","1","1","1"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="("),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["1","1","1","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["1","0","1","1"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="("),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["1","1","1","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i1 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="r", val0_o=["0"],val0_i=["1","1","0","1"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="("),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="f", val0_o=["1"],val0_i=["1","1","1","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i2 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i3",arc="r", val0_o=["0"],val0_i=["1","1","1","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i3",arc="f", val0_o=["1"],val0_i=["1","1","1","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i3 => o0) = (0,0);"),]
    },
    
    "OR2":{"functions":{"o0":"i0|i1"},
           "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["0","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["1","0"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["0","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["0","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i1 => o0) = (0,0);"),]
    },
    "OR3":{"functions":{"o0":"i0|i1|i2"},
           "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["0","0","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["1","0","0"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["0","0","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["0","1","0"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i1 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="r", val0_o=["0"],val0_i=["0","0","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="f", val0_o=["1"],val0_i=["0","0","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i2 => o0) = (0,0);"),]
    },
    "OR4":{"functions":{"o0":"i0|i1|i2|i3"},
            "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["0","0","0","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["1","0","0","0"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["0","0","0","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["0","1","0","0"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i1 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="r", val0_o=["0"],val0_i=["0","0","0","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="f", val0_o=["1"],val0_i=["0","0","1","0"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i2 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i3",arc="r", val0_o=["0"],val0_i=["0","0","0","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i3",arc="f", val0_o=["1"],val0_i=["0","0","0","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="", specify="(i3 => o0) = (0,0);"),]
    },
    
    "NAND2":{"functions":{"o0":"!(i0&i1)"},
             "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["1","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["0","1"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["1","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["1","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i1 => o0) = (0,0);"),]
    },
    "NAND3":{"functions":{"o0":"!(i0&i1&i2)"},
             "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o="0",val0_i=["1","1","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o="1",val0_i=["0","1","1"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o="0",val0_i=["1","1","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o="1",val0_i=["1","0","1"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="i1 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="r", val0_o="0",val0_i=["1","1","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="f", val0_o="1",val0_i=["1","1","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="i2 => o0) = (0,0);"),]
    },
    "NAND4":{"functions":{"o0":"!(i0&i1&i2&i3)"},
             "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o="0",val0_i=["1","1","1","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o="1",val0_i=["0","1","1","1"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o="0",val0_i=["1","1","1","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o="1",val0_i=["1","0","1","1"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i1 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="r", val0_o="0",val0_i=["1","1","1","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="f", val0_o="1",val0_i=["1","1","0","1"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i2 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i3",arc="r", val0_o="0",val0_i=["1","1","1","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i3",arc="f", val0_o="1",val0_i=["1","1","1","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i3 => o0) = (0,0);"),]
    },

    "NOR2":{"functions":{"o0":"!(i0|i1)"},
            "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["1","0"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["0","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["0","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["0","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i1 => o0) = (0,0);"),]
    },
    "NOR3":{"functions":{"o0":"!(i0|i1|i2)"},
            "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["1","0","0"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["0","0","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["0","1","0"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["0","0","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i1 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="r", val0_o=["0"],val0_i=["0","0","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="f", val0_o=["1"],val0_i=["0","0","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i2 => o0) = (0,0);"),]
    },
    "NOR4":{"functions":{"o0":"!(i0|i1|i2|i3)"},
            "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["1","0","0","0"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["0","0","0","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["0","1","0","0"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["0","0","0","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i1 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="r", val0_o=["0"],val0_i=["0","0","1","0"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="f", val0_o=["1"],val0_i=["0","0","0","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i2 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i3",arc="r", val0_o=["0"],val0_i=["0","0","0","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i3",arc="f", val0_o=["1"],val0_i=["0","0","0","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="", specify="(i3 => o0) = (0,0);"),]
    },


    "XOR2":{"functions":{"o0":"i0^i1"},
            "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["0","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="!i1", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["1","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="i1" , specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["0","1"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="i1" , specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["1","0"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="!i1", specify="(i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["0","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="!i0", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["1","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="i0" , specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["1","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="neg", tmg_when="i0" , specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["0","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="!i0", specify="(i1 => o0) = (0,0);"),]
    },

    "XNOR2":{"functions":{"o0":"!(i0^i1)"},
             "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["0","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="!i1", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["0","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="!i0", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["1","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="i1" , specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["1","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="i0" , specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["0","1"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="i1" , specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["1","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="i0" , specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["1","0"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="!i1", specify="(i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["0","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="neg", tmg_when="!i0", specify="(i1 => o0) = (0,0);"),]
    },

    "MUX2":{"functions":{"o0":"(i0&!i2)|(i1&i2)"},  #--- o0 = (i2)? i1 : i0
             "expect":                                                     
             [MyExpectLogic(pin_t="o0",pin_r="i0",arc="r", val0_o=["0"],val0_i=["0","0","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="!i2", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i0",arc="f", val0_o=["1"],val0_i=["1","0","0"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="!i2", specify="(i0 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="r", val0_o=["0"],val0_i=["0","0","1"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="i2" , specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i1",arc="f", val0_o=["1"],val0_i=["0","1","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="i2" , specify="(i1 => o0) = (0,0);"),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="r", val0_o=["0"],val0_i=["0","1","0"],val0_b=[], val1_t="1",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="!i0&i1", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="f", val0_o=["1"],val0_i=["0","1","1"],val0_b=[], val1_t="0",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="!i0&i1", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="r", val0_o=["0"],val0_i=["1","0","1"],val0_b=[], val1_t="1",val1_r="0",tmg_type="comb",tmg_sense="pos", tmg_when="i0&!i1", specify=""),
              MyExpectLogic(pin_t="o0",pin_r="i2",arc="f", val0_o=["1"],val0_i=["1","0","0"],val0_b=[], val1_t="0",val1_r="1",tmg_type="comb",tmg_sense="pos", tmg_when="i0&!i1", specify="(i2 => o0) = (0,0);"),]
    },

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
