from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Literal

class MyItemTemplate(BaseModel):
  kind   : Literal["const","delay","mpw","passive","power"]="delay";
  grid   : str ="";         #"7x7"
  name   : str ="";         #"x1" 
  index_1: list[float]=Field(default_factory=list); #slope       , slope  , slope
  index_2: list[float]=Field(default_factory=list); #capacitance , slope  , -
