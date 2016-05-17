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

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import DDL, DDLElement, MetaData, Table, Column
from sqlalchemy import event, Integer, Float

class CreateRTreeTable(DDLElement):
    def __init__(self, name, columns):
        self.name = name
        self.columns = columns

@compiles(CreateRTreeTable)
def compileCreateRTreeTable(element, compiler, **kwargs):
    return 'CREATE VIRTUAL TABLE %s USING rtree(%s)'%(element.name, ','.join(['id']+element.columns))

def create_rtree(name, columns, metadata):
    meta = MetaData() # Dummy name & metadata for ORM
    table = Table(name, meta)
    table.append_column(Column('id', Integer, primary_key=True))
    for c in columns:
        table.append_column(Column(c,Float))

    event.listen(metadata, 'after_create', CreateRTreeTable(name, columns))
    event.listen(metadata, 'before_drop', DDL('DROP TABLE IF EXISTS %s'%name))

    return table
