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

import inspect
import os
from .db import DB
from .model import Path, Content
from .checksum import sha1
from .ingest import load_file

class FindCommand(object):
    """
    CLI to find files within the DB
    """

    def register(self, superparser):
        parser = superparser.add_parser('find',description=inspect.getdoc(self.call))
        parser.set_defaults(func=self.call)

    def call(self, args):
        """
        Find files
        """
        db = DB()
        session = db.session()

class SpiderCommand(object):
    """
    CLI to add paths to the DB
    """

    def register(self, superparser):
        parser = superparser.add_parser('spider',description=inspect.getdoc(self.call))
        parser.set_defaults(func=self.call)
        parser.add_argument('path', help='Path to scan')

    def call(self, args):
        """
        Add paths to the database
        """
        db = DB()
        session = db.session()

        for root, dirs, files in os.walk(args.path):
            for f in files:
                p = os.path.realpath(os.path.join(root,f))
                path = session.query(Path).filter(Path.path == p).one_or_none()
                if path is not None:
                    path.update()
                else:
                    path = Path(p)
                    session.add(path)
                session.commit()

        # Update content
        for path in session.query(Path).filter(Path.content_id == None):
            checksum = sha1(path.path)  
            content = session.query(Content).filter(Content.sha1 == checksum).one_or_none()
            if content is None:
                content = Content(path.path, sha1=checksum)
                session.add(content)
                load_content(content, session)
            path.content = content
            session.commit()

        session.close()
