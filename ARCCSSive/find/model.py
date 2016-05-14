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
import os
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Text, DateTime, Boolean, String, ForeignKey
from sqlalchemy.orm import relationship

from . import checksum

Base = declarative_base()

class Path(Base):
    """
    Represents a path on the filesystem. Has no knowledge about the file's
    contents
    """
    __tablename__ = 'path'
    id            = Column(Integer, primary_key = True)
    path          = Column(Text, index=True, unique=True)
    last_seen     = Column(DateTime)
    last_modified = Column(DateTime)
    size          = Column(Integer)
    missing       = Column(Boolean)

    content_id    = Column(Integer, ForeignKey('content.id'), index=True)
    content       = relationship('Content', back_populates='paths')

    def __init__(self, path):
        self.path = path
        self._update()
        self.last_seen = datetime.now()

    def update(self):
        """
        Check if the file has been modified since we last saw it
        """
        if not os.path.isfile(self.path):
            self.missing = True
            return

        last_modified = datetime.fromtimestamp(os.path.getmtime(self.path))
        if last_modified > self.last_seen:
            self._update()
        self.last_seen = datetime.now()

    def _update(self):
        """
        Update helper
        """
        path = self.path
        self.last_modified = datetime.fromtimestamp(os.path.getmtime(path))
        self.size          = os.path.getsize(path)
        self.missing       = False
        # Clear content_id, will be updated separately
        self.content_id    = None

class Content(Base):
    """
    Represents a file's contents. Multiple paths may point to the same contents
    due to duplication
    """
    __tablename__ = 'content'
    id            = Column(Integer, primary_key = True)
    # Checksums
    sha1          = Column(String, index=True, unique=True)
    md5           = Column(String)

    paths         = relationship('Path', order_by=Path.path, back_populates='content')

    format_id     = Column(Integer, ForeignKey('format.id'), index=True)
    format        = relationship('Format')

    def __init__(self, path, sha1):
        self.sha1 = sha1
        self.md5  = checksum.md5(path)

def detect_format(path):
    """
    Return a mime type matching the file
    """
    with open(path,'rb') as f:
        buf  = f.read(4096)
        mime = magic.from_buffer(path, mime=True)

        if mime == 'application/octet-stream; charset=binary':
            with open(path,'rb') as f:
                buf = f.read(1024)

                if 
        else:
            return mime


class Format(Base):
    """
    Represents a file format (e.g. netcdf, GRIB)
    """
    __tablename__ = 'format'
    id            = Column(Integer, primary_key=True)
    name          = Column(String, index=True, unique=True)
    mime          = Column(String)
    description   = Column(String)
