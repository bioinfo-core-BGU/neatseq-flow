#!/usr/bin/env python


""" Create the pipeline scripts

This script inits the 'NeatSeq-Flow' class that does all the script creating
"""

__author__ = "Menachem Sklarz"
__version__ = "1.1.0"


__affiliation__ = "Bioinformatics Core Unit, NIBN, Ben Gurion University"


import os, sys
import argparse
from pprint import pprint as pp

# Remove bin from search path:
sys.path.pop(0)
# Append neatseq_flow path to list (when using installed version, will find it before getting to this search path)
# Problem that might arrise: When trying to run a local copy when it is installed in site-packages/
sys.path.append(os.path.realpath(os.path.expanduser(os.path.dirname(os.path.abspath(__file__))+os.sep+"..")))
sys.path.append(os.path.realpath(os.path.expanduser(os.path.dirname(os.path.abspath(__file__))+os.sep+".."+os.sep+"neatseq_flow")))

from neatseq_flow.PLC_main import neatseq_flow
from neatseq_flow.PLC_step import Step


# Parse arguments:
parser = argparse.ArgumentParser(description = """
This program creates a set of scripts to perform a workflow.

The samples are defined in the --sample_file, the workflow itself in the --param_file.
""", epilog = """
Author: Menachem Sklarz, NIBN
""")
parser.add_argument("-s","--sample_file", help="Location of sample file, in classic or tabular format")
parser.add_argument("-p","--param_file", help="Location of parameter file. Can be a comma-separated list - all will be used as one. Alternatively, -p can be passed many times with different param files", action="append")
parser.add_argument("-d","--home_dir", help="Location of pipeline. Default is currect directory", default=os.getcwd())
parser.add_argument("-m","--message", help="A message describing the pipeline", default="")
# parser.add_argument("-c","--convert2yaml", help="Convert parameter file to yaml format?", action='store_true')
parser.add_argument("-v","--version", help="Convert parameter file to yaml format?", action='store_true')

args = parser.parse_args()


if args.version:
    print "NeatSeq-Flow version %s" % __version__
    print "Installation location: %s" % os.path.dirname(os.path.realpath(__file__))
    sys.exit()

    
if args.sample_file == None or args.param_file==None:
    print "Please supply sample and parameter files...\n"
    parser.print_help()
    sys.exit()


# Checking that sample_file and param_file were passed:
if args.sample_file == None or args.param_file == None:
    print "Don't forget to pass sample and parameter files with the -s and -p flags.\n", parser.print_help()

# Converting list of parameter files into comma-separated list. This is deciphered by the neatseq_flow class.
args.param_file = ",".join(args.param_file)


neatseq_flow(sample_file   = args.sample_file,   \
             param_file    = args.param_file,    \
             home_dir      = args.home_dir,      \
             message       = args.message)
             


