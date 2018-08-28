#!/usr/bin/env python


""" Create the pipeline scripts

This script inits the 'NeatSeq-Flow' class that does all the script creating
"""

__author__ = "Menachem Sklarz"
__version__ = "1.1.0"


__affiliation__ = "Bioinformatics Core Unit, NIBN, Ben Gurion University"


import os
import sys
import shutil
import argparse

# Remove bin from search path:
sys.path.pop(0)
# Append neatseq_flow path to list (when using installed version, will find it before getting to this search path)
# Problem that might arrise: When trying to run a local copy when it is installed in site-packages/
sys.path.append(os.path.realpath(os.path.expanduser(os.path.dirname(os.path.abspath(__file__))+os.sep+"..")))
from neatseq_flow.PLC_main import NeatSeqFlow

# Parse arguments:
parser = argparse.ArgumentParser(description="""
This program creates a set of scripts to perform a workflow.

The samples are defined in the --sample_file, the workflow itself in the --param_file.
""",
                                 epilog="""
Author: Menachem Sklarz, NIBN
""")
parser.add_argument("-s", "--sample_file", help="Location of sample file, in classic or tabular format")
parser.add_argument("-p", "--param_file", help="Location of parameter file. Can be a comma-separated list - all will "
                                               "be used as one. Alternatively, -p can be passed many times with "
                                               "different param files", action="append")
parser.add_argument("-g", "--mapping", help="Location of grouping file. A tab-separated table describing the samples "
                                             "and their proeprties.", action="append")
parser.add_argument("-d", "--home_dir", help="Location of workflow. Default is currect directory", default=os.getcwd())
parser.add_argument("-m", "--message", help="A message describing the workflow", default="")
parser.add_argument("-r", "--runid", help="Don't create new run ID. Use this one.", default="")
# parser.add_argument("-c","--convert2yaml", help="Convert parameter file to yaml format?", action='store_true')
parser.add_argument("-l", "--clean", help="Remove old workflow directories except for 'data'", action='store_true')
parser.add_argument("--clean-all", help="Remove all old workflow directories", action='store_true')
parser.add_argument("-V", "--verbose", help="Print admonitions?", action='store_true')
parser.add_argument("-v", "--version", help="Print version and exit.", action='store_true')

args = parser.parse_args()


if args.version:
    print "NeatSeq-Flow version %s" % __version__
    print "Installation location: %s" % os.path.dirname(os.path.realpath(__file__))
    sys.exit()

    
if args.sample_file is None or args.param_file is None:
    print "Please supply sample and parameter files...\n"
    parser.print_help()
    sys.exit()

    
if args.clean:
    # if args.home_dir != os.getcwd():
    text = raw_input("Are you sure you want to delete the workflow in {home_dir}? ".format(home_dir = args.home_dir))

    if not text.lower() == "yes":
        sys.exit()
    if args.clean_all:
        text = raw_input("Are you sure you want to delete '{data}'? ".format(data=os.sep.join([args.home_dir, "data"])))
        if os.path.isdir(os.sep.join([args.home_dir, "data"])):
            if text.lower() == "yes":
                shutil.rmtree(os.sep.join([args.home_dir, "data"]))
            else:
                print "Not removing 'data'"
    for wfdir in ["backups", "logs", "objects", "scripts", "stderr", "stdout"]:
        if os.path.isdir(os.sep.join([args.home_dir, wfdir])):
            shutil.rmtree(os.sep.join([args.home_dir, wfdir]))
else:
    if args.clean_all:
        sys.exit("Please pass -l as well as --clean-all. This is a safety precaution...")
    
    
# Checking that sample_file and param_file were passed:
if args.sample_file is None or args.param_file is None:
    print "Don't forget to pass sample and parameter files with the -s and -p flags.\n", parser.print_help()

# Converting list of parameter files into comma-separated list. This is deciphered by the neatseq_flow class.
args.param_file = ",".join(args.param_file)


NeatSeqFlow(sample_file   = args.sample_file,
            param_file    = args.param_file,
            mapping_file  = args.mapping,
            home_dir      = args.home_dir,
            message       = args.message,
            runid         = args.runid,
            verbose       = args.verbose)
