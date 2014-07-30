#!/usr/bin/env python

"""Setup script for the SoundTouch module distribution."""

import os, re, sys, string

from distutils.core import setup
from distutils.extension import Extension

os.environ['CC'] = 'g++'
os.environ['CXX'] = 'g++'
#os.environ['CPP'] = 'g++'
#os.environ['LDSHARED'] = 'g++'

VERSION_MAJOR = 0
VERSION_MINOR = 1.0
pysoundtouch_version = str(VERSION_MAJOR) + "." + str(VERSION_MINOR)

def get_setup():
    data = {}
    r = re.compile(r'(\S+)\s*=\s*(.+)')
    
    if not os.path.isfile('Setup'):
        print "No 'Setup' file. Perhaps you need to run the configure script."
        sys.exit(1)
        
    f = open('Setup', 'r')
        
    for line in f.readlines():
        m = r.search(line)
        if not m:
            print "Error in setup file:", line
            sys.exit(1)
        key = m.group(1)
        val = m.group(2)
        data[key] = val
        
    return data

data = get_setup()

defines = [('VERSION_MAJOR', VERSION_MAJOR),
           ('VERSION_MINOR', VERSION_MINOR),
           ('VERSION', '"%s"' % pysoundtouch_version)]

soundtouchmodule = Extension(
    name='soundtouchmodule',
    sources=['src/soundtouchmodule.c', 'src/pysoundtouch.cpp', 'src/pybpmdetect.cpp', 'src/WavFile.cpp'],
    define_macros = defines,
    include_dirs=[data['soundtouch_include_dir']],
    library_dirs=[data['soundtouch_lib_dir']],
    libraries=string.split(data['soundtouch_libs']))

setup ( # Distribution metadata
    name = "pysoundtouch",
    version = pysoundtouch_version,
    description = "A wrapper for the SoundTouch libraries.",
    author = "James Rising",
    author_email = "jarising@gmail.com",
    url = "http://existencia.org/pro/",
    license = "GPL",
    
    ext_modules = [soundtouchmodule])
