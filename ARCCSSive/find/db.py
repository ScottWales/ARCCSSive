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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .model import Base

class DB(object):
    """
    Manage database connection
    """
    def __init__(self, url='sqlite:///:memory:', debug=False):
        """
        Connect to the database and return a session factory
        """
        self.engine = create_engine(url, echo=debug)
        Base.metadata.create_all(self.engine)
        self.sessionmaker = sessionmaker(bind=self.engine)

    def session(self):
        """
        Get a new DB session
        """
        return self.sessionmaker()
