#!/usr/bin/env python
"""
Copyright 2016 ARC Centre of Excellence for Climate Systems Science

author: Scott Wales <scott.wales@unimelb.edu.au>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from argparse import ArgumentParser, RawTextHelpFormatter
import sys
import inspect
import logging

# Sub-commands
from ARCCSSive.find.command import FindCommand
commands = [FindCommand()]

def main(argv):
    """
    ARCCSS Data Archive Tool

    Allows users to query the data stored on the NCI filesystem
    """
    parser = ArgumentParser(
            description=inspect.getdoc(main),
            formatter_class=RawTextHelpFormatter,
            )
    parser.add_argument('--debug', action='store_true',
            help="Print database actions")
    subparsers = parser.add_subparsers()

    for c in commands:
        c.register(subparsers)

    args = parser.parse_args(argv[1:])

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    args.func(args)

if __name__ == '__main__':
    main(sys.argv)
