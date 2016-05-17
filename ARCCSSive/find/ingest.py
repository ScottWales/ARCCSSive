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
import xarray
import pandas
from .model import *

"""
Functions to load stuff into the database
"""
def one_or_add(session, klass, **kwargs):
    one = session.query(klass).filter_by(**kwargs).one_or_none()
    if one is None:
        one = klass(**kwargs)
        session.add(one)
    return one

def load_file(path, content, session):
    """
    High-level file loader
    """
    with xarray.open_dataset(path,decode_cf=True) as data:
        content.format = one_or_add(session, Format, name='cf-netcdf')
        load_fields(data, session)
        session.commit()
#    except ValueError:
#        session.rollback()

def load_fields(data, session):
    """
    Load all fields within a file
    """
    for name,var in data.data_vars.iteritems():
        bounds = FieldBounds()
        meta = FieldMeta()
        meta.variable = one_or_add(session, Variable, name=name)
        print(var.coords)

        if 'lat' in var.dims:
            bounds.minLat = var.coords['lat'].min()
            bounds.maxLat = var.coords['lat'].max()
        if 'lon' in var.dims:
            bounds.minLon = var.coords['lon'].min()
            bounds.maxLon = var.coords['lon'].max()

        session.add(bounds)
        meta.bounds = bounds
        session.add(meta)

