from py2exe.build_exe import py2exe
from distutils.core import setup
import os
import zmq
import numpy
import matplotlib

os.environ["PATH"] = \
    os.environ["PATH"] + \
    os.path.pathsep + os.path.split(zmq.__file__)[0]

excludes = ['_gtkagg', '_tkagg', 'bsddb', 'curses', 'pywin.debugger',
            'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl',
            'Tkconstants', 'Tkinter', 'pydoc', 'doctest', 'test', 
            "scipy.linalg.__cvs_version__","numpy.linalg.__cvs_version__" ]


setup( console=[{"script": "xml_process_v7.py"}],
    data_files=matplotlib.get_py2exe_datafiles(),
    zipfile = None,
       options={ 
           "py2exe": { 
               "compressed": True,
               "optimize": 1,
                #"bundle_files": 1,
                "includes": 
               ["zmq.utils", "zmq.utils.jsonapi", 
                "zmq.utils.strtypes",
                "matplotlib.backends.backend_qt4agg",
                "lxml.etree",
                "lxml._elementpath"], 
               "excludes":excludes
                } } )