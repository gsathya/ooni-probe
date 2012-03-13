#!/usr/bin/env python
###############
# fix-top-1m.py
###############
# Removes the 'N,' from the default top-1m.txt.
# ::author:: Isis Lovecruft

from __future__ import with_statement
from contextlib import nested
import os
import re
import tempfile

def remove_cruft():
    print 'Opening list of top webservers for parsing...'
    in_file = os.path.abspath('top-1m.txt')
    print 'Creating temporary file for parsing purposes...'
    outfile = os.path.abspath('top-1m.txt~')
    tempfile.NamedTemporaryFile('w+b', 1000, '.txt~', 'top-1m',
                                os.getcwd())
    with open(in_file, 'r+') as in_, open('top-1m.txt~', 'w+') as out_:
        lines = in_.readlines()
        print 'Replacing cruft with nothingness...'
        for line in lines:
            out_.write(re.sub('^(\d+),', '', line))
        print 'Removing write access to temp file...'
    out_.close()
    in_.close()
    print 'Renaming parsed temp file as orginal file...'
    os.rename('top-1m.txt~', 'top-1m.txt')
    print 'List of webservers now ready for use!'

if __name__=="__main__":
    remove_cruft()
