#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
# This file is part of charao.
#
# Copyright (C) 2025 MATSUDA Masahiro
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
###############################################################################
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Literal

class MyItemTemplate(BaseModel):
  kind   : Literal["leakage","const","delay","delay_c2c","delay_i2c","delay_c2i","delay_i2i","mpw","passive","power","power_c2c","power_i2c","power_c2i","power_i2i"]="delay";
  grid   : str ="";         #"7x7"
  name   : str ="";         #"x1" 
  index_1: list[float]=Field(default_factory=list); #slope       , slope  , slope
  index_2: list[float]=Field(default_factory=list); #capacitance , slope  , -
