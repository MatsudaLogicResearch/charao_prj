from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Literal

class MyItemTemplate(BaseModel):
  kind   : Literal["leakage","const","delay","delay_c2c","delay_i2c","delay_c2i","delay_i2i","mpw","passive","power","power_c2c","power_i2c","power_c2i","power_i2i"]="delay";
  grid   : str ="";         #"7x7"
  name   : str ="";         #"x1" 
  index_1: list[float]=Field(default_factory=list); #slope       , slope  , slope
  index_2: list[float]=Field(default_factory=list); #capacitance , slope  , -
