#!/usr/bin/env python
# Copyright 2016 ARC Centre of Excellence for Climate Systems Science
# author: Scott Wales <scott.wales@unimelb.edu.au>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import print_function
from fixtures import *
from ARCCSSive.find.model import *
from ARCCSSive.find.ingest import *
from netcdftime import JulianDayFromDate
from netCDF4 import num2date

def test_ingest(find_session):
    """
    Try loading a sample file
    """
    content = Content()
    load_file('tests/data/sresa1b_ncar_ccsm3-example.nc',
            content,
            find_session)
    field = find_session.query(FieldMeta).join(Variable).filter(Variable.name=='air_temperature').one()

    # This field has spatial bounds
    assert field.bounds.max_lon == 358.59375
    assert field.bounds.min_lat == -88.927734375

    # This field has temporal bounds
    assert field.min_date == num2date(730135.5,units="days since 0000-1-1",calendar="noleap")
    assert field.max_date == num2date(730135.5,units="days since 0000-1-1",calendar="noleap")
    assert field.bounds.min_year == 2000
    assert field.bounds.max_year == 2000

