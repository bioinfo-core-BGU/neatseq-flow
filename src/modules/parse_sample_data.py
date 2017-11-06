

""" Functions for reading and parsing pipeline sample files
"""

__author__ = "Menachem Sklarz"
__version__ = "1.1.0"


import os
import sys
from pprint import pprint as pp
import re

# execfile("parse_params.py")

RECOGNIZED_FILE_TYPES = ['Single', 'Forward', 'Reverse', 'Nucleotide','Protein', 'SAM', 'BAM', 'REFERENCE']
GLOBAL_SAMPLE_LIST = ['Title', 'Sample', 'Single', 'Sample_Control'] + RECOGNIZED_FILE_TYPES

from  modules.global_defs import ZIPPED_EXTENSIONS, ARCHIVE_EXTENSIONS, KNOWN_FILE_EXTENSIONS


def remove_comments(filelines):
    """
    Remove all comments, commented lines and empty lines from the parameter file lines list
    filelines = list of lines read from parameter file with "readlines()"
    Used by parse_param_data as well
    """
    
    # Remove all comments, empty lines and trailing white space:
    filelines = [line.partition("#")[0].rstrip() for line in filelines if len(line.partition("#")[0].strip())>0]
    # Remove all lines after "STOP_HERE"
    try:
        filelines = filelines[0:filelines.index("STOP_HERE")]
    except ValueError:
        pass
    
    return filelines

def check_newlines(filelines):
    """
    """
    # Assert that the list of lines containing "\r" charaters is empty.
    lines_with_CRs = [line for line in filelines if re.search("\r",line)]
    assert not lines_with_CRs, "The sample and parameter files must not contain carriage returns. Convert newlines to UNIX style!\n"
    
    

def parse_sample_file(filename):
    """Parses a file from filename
    """
    file_conts = []

    filenames = filename.split(",")
    for filename in filenames:
        if not os.path.isfile(filename):
            sys.exit("Sample file %s does not exist.\n" % filename)
        with open(filename) as fileh:
            file_conts += fileh.readlines()
                
    check_newlines(file_conts)
    sample_data = get_sample_data(file_conts)
    check_sample_constancy(sample_data)
    
    # pp(sample_data)
    # sys.exit()
    return sample_data
        
def get_sample_data(filelines):
    """return lines relevant to the sample data, if exist
    """
    
    sample_file_type = guess_sample_data_format(filelines)
    if (sample_file_type == "Classic"):
        return get_classic_sample_data(filelines)
    elif (sample_file_type == "Tabular"):   
        return get_tabular_sample_data(filelines)
    else:
        sys.exit("There is a problem with the sample file format. Make sure all lines begin with keywords.")
        
    

def guess_sample_data_format(filelines):
    """Guess the format of sample data. Could be tsv (preferable but not defined yet) or old pipeline format
    """
    # Remove comments:  CANCELLED. Tabular format has #SampleID as header line prefix!
    # filelines = remove_comments(filelines)
    # Get all unique first words on line (=set)
    # This can contain parameter file stuff as well, when they are merged!
    myset = {re.split("\s+", line, maxsplit=1)[0] for line in filelines}

    # sys.exit({"Title", "Sample"} <= myset)
    # pp(myset)
    # Check if one of the following words exists in the set by checking the intersection of the sets:
    if(({"Title", "Sample"} <= myset) & \
        (len(myset & set(RECOGNIZED_FILE_TYPES))>=1)):    
        # 1. Does myset contain Title and Sample?
        # 2. Does myset include at least one of {"Forward","Reverse","Single","Nucleotide","Protein"}?
        return "Classic";
    elif ({"Title","#SampleID"} <= myset):
        # 1. If myset contains Title and #SampleID
        return "Tabular"
    else:
        sys.exit("Unknown sample file type.")
    

def get_classic_sample_data(filelines):
    """
    Get sample data from filelines
    """
    # Extract sample-related lines from filelines:
    filelines = get_classic_sample_data_lines(filelines)
    # Get list of tuples: (index, sample name) where "index" is the line in filelines holding the sample name line
    sample_index = [(ind,re.split("\s+", line, maxsplit=1)[1]) for ind,line in list(enumerate(filelines)) if re.split("\s+", line, maxsplit=1)[0]=="Sample"]
    
    # Get project title:
    title = get_project_title(filelines)
    
    
    # Indexes of samples in lines
    indexes = [ind for (ind,smp) in sample_index]
    # Indexes of ends of samples in lines
    indexes_end = [ind-1 for ind in indexes[1:]]
    indexes_end.extend([len(filelines)-1])
    sample_data = dict()
    for (i,j,smp) in zip(indexes,indexes_end,sample_index):
        # print "i+1: %d j: %d smp: %s" % (i+1,j,smp[1])
        # Put parse_classic_sample_data into dictionary
        sample_data[smp[1]] = parse_classic_sample_data(filelines[(i+1):(j+1)])
    

    # Get Sample_Control data for ChIP-seq samples:
    Sample_Control = [re.split("\s+", line, maxsplit=1)[1] for line in filelines if re.split("\s+", line, maxsplit=1)[0]=="Sample_Control"]
    if Sample_Control:
        controls = parse_sample_control_data(Sample_Control,sample_names=sample_data.keys())
        
    # Add a list of sample names to sample_data
    sample_data["samples"] = sample_data.keys()

    # Add project title sample_data
    sample_data["Title"] = title
    
    if Sample_Control:
        sample_data["Controls"] = controls 
    
    return sample_data
    
def parse_classic_sample_data(lines):
    """
    Given lines for one sample, return a dictionary holding the data for that sample:
    """
    sample_x_data = dict()
    # Create dict with lists of files for each possible direction 
    reads = {alldirect:[(filename) for (direction,filename) in \
                    [re.split("\s+", line, maxsplit=1) for line in lines] \
            if direction==alldirect] for alldirect in {"Forward","Reverse","Single"}}
    # Remove empty lists 
    reads = {direct:files for direct,files in reads.iteritems() if files != []}
    # Create dict for storing full sequences, e.g. genomes and proteins. Will be searching for 'Nucleotide' and 'Protein' keywords
    if reads:
        sample_x_data.update(reads)
    
    ## Read fasta files:
    fasta = {alldirect:[(filename) for (direction,filename) in \
                    [re.split("\s+", line, maxsplit=1) for line in lines] \
            if direction==alldirect] for alldirect in {"Nucleotide","Protein"}}
    # Remove empty lists 
    fasta = {direct:files for direct,files in fasta.iteritems() if files != []}
    # Put these files in a separate entry in the reads structure called "fasta"
    if fasta:
        sample_x_data.update(fasta)
    
    ## Read BAM/SAM files:
    bam_sam = {alldirect:[(filename) for (direction,filename) in \
                    [re.split("\s+", line, maxsplit=1) for line in lines] \
            if direction==alldirect] for alldirect in {"SAM","BAM","REFERENCE"}}
    # Remove empty lists 
    bam_sam = {direct:files for direct,files in bam_sam.iteritems() if files != []}
    
    # Complain if more or less than 1 REFERENCE was passed:
    if(bam_sam):    # Do the following only if BAM/SAM files were passed:
        if "REFERENCE" not in bam_sam:
            print "No reference passed with SAM and BAM files..."
            raise Exception("Issue in sample file")
        if len(bam_sam["REFERENCE"]) > 1:
            print "You tried passing more than one REFERENCE with SAM and BAM files..."
            raise Exception("Issue in sample file")
        
        # Put these files in a separate entry in the reads structure called "mapping"
        if bam_sam:
            sample_x_data.update(bam_sam)
    

    return sample_x_data
    
def get_classic_sample_data_lines(filelines):
    """ Get sample data from "Classic" sample data file, i.e. pipeline format
        Is recognized by the words "Sample","Forward","Reverse","Single" as line prefixes
    """
    filelines = remove_comments(filelines)
    return [line for line in filelines if re.split("\s+", line, maxsplit=1)[0] in GLOBAL_SAMPLE_LIST]
    
def parse_sample_control_data(Sample_Control, sample_names):
    """ Parse lines containing sample-control relationships for ChIP-seq protocols
    """
    # Check validity of lines:
    for item in Sample_Control:
        assert item.split(":")[0] in sample_names, "%s in sample-control data is not defined as a sample\n" % item.split(":")[0]
        assert item.split(":")[1] in sample_names, "%s in sample-control data is not defined as a sample\n" % item.split(":")[1]
        
    # Extract and return data
    return {item.split(":")[0]:item.split(":")[1] for item in Sample_Control}


    

def check_file_name(filename):
    """ Check wether a filename is legitimate
        The exact tests will be defined and updated periodically...
    """
    
    pass
    

def check_sample_constancy(sample_data):
    """ Checks that all sample files are either zipped or unzipped.
        Uses file extensions for determination. 
        zipped file extensions are stored in global param ZIPPED_EXTENSIONS
    """
    
    # For each file type in each sample, get a list of extension types:
    ext_types = set()
    for sample in sample_data["samples"]:      # Getting list of samples out of samples_hash
        # for type in sample_data[sample].keys():
            # if type in ["type"]:
                # continue
            # for direction in sample_data[sample][type].keys():
                # # Get a list of file extensions (chars to the RHS of the last period in the filename)
                # extensions = list(set([os.path.splitext(fn)[1] for fn in sample_data[sample][type][direction]]))
                # # Convert file extension to 'zip' or 'regular', depending on the extension:
                # # Keep only unique values (using set: {}) and adding to ext_types
                # ext_types = ext_types | {"zip" if ext in ZIPPED_EXTENSIONS else "regular" for ext in extensions}
        for direction in sample_data[sample].keys():
            # Get a list of file extensions (chars to the RHS of the last period in the filename)
            # extensions = list(set([os.path.splitext(fn)[1] for fn in sample_data[sample][type][direction]]))
            extensions = map(lambda fn: os.path.splitext(fn)[1], sample_data[sample][direction])
            # Convert file extension to 'zip' or 'regular', depending on the extension:
            # Keep only unique values (using set: {}) and adding to ext_types
            ext_types = ext_types | set(map(lambda ext: "zip" if ext in ZIPPED_EXTENSIONS else "regular", extensions)) #{"zip" if ext in ZIPPED_EXTENSIONS else "regular" for ext in extensions}
        
    if len(ext_types) > 1:
        sys.exit("At the moment, you can't mix zipped and unzipped files!")
        
        
        
def get_tabular_sample_data(filelines):
    """
    Get sample data from filelines
    """
    # Extract sample-related lines from filelines:
    filelines = get_tabular_sample_data_lines(filelines)
    

    title = get_project_title(filelines)


    sample_lines = [line for line in filelines if re.split("\s+", line, maxsplit=1)[0] not in ["Title","Sample_Control"]]

    # sys.exit(sample_lines)
    
    sample_names = set([re.split("\s+", line, maxsplit=1)[0] for line in sample_lines])

    sample_data = dict()
    
    for sample in sample_names:
        # Parse lines for a single sample.
        # Get the lines that have the sample name in first column and extract data from them with parse_tabular_sample_data()
        sample_data[sample] = parse_tabular_sample_data([line for line in sample_lines if re.split("\s+", line, maxsplit=1)[0]==sample])
    # pp(sample_data)
    
    
    # Get Sample_Control data for ChIP-seq samples:
    Sample_Control = [re.split("\s+", line, maxsplit=1)[1] for line in filelines if re.split("\s+", line, maxsplit=1)[0]=="Sample_Control"]
    if Sample_Control:
        controls = parse_sample_control_data(Sample_Control,sample_names=sample_data.keys())
        
    # pp(sample_data)
    # sys.exit()
    
    # Add a list of sample names to sample_data
    sample_data["samples"] = sample_data.keys()

    # Add project title sample_data
    sample_data["Title"] = title
    
    if Sample_Control:
        sample_data["Controls"] = controls 
    
    return sample_data
    
    
    
    
    
def get_tabular_sample_data_lines(filelines):
    """ Get sample data from "Tabular" sample data lines
        Will keep one line beginning with "Title" and all consecutive lines from "#SampleID" till first blank line
        
        The reason for this is that the user should have the option of embedding the sample file in the parameter file. This way, all line except the title and the consecutive sample lines will be discarded
    """

    # filelines = remove_comments(filelines)
    title_line = [line for line in filelines if re.split("\s+", line, maxsplit=1)[0] == "Title"]
    
    # Check there is only one title line (title is a list of length 1)
    
    ## looking for range begining with "#SampleID" till first blank line:
    # Index of blank lines :
    blank_ind = [ind for (ind,param_l) in list(enumerate(filelines)) if re.match("^\s+$", param_l)]
    blank_ind.append(len(filelines))

    # Index of header line:
    head_ind =  [ind for (ind,param_l) in list(enumerate(filelines)) if re.split("\s+", param_l, maxsplit=1)[0] == "#SampleID"]
    # Range of lines to keep: from header index till first blank line
    lines_range = range(head_ind[0],min([ind for ind in blank_ind if ind>head_ind[0]]))

    # Extract Sample_Control lines:
    sample_control = [line for line in filelines if re.split("\s+", line, maxsplit=1)[0] == "Sample_Control"]

    # Keep title line and actual table:
    filelines = title_line + [filelines[i] for i in lines_range] + sample_control

    filelines = remove_comments(filelines)

    return filelines
    
def parse_tabular_sample_data(sample_lines):
    """
    """
    # pp(sample_lines)
    
    sample_x_dict = dict()
    
    for line in sample_lines:
        line_data = re.split("\s+", line)
        
        if line_data[1] in ["Forward", "Reverse","Single", "Nucleotide", "Protein", "SAM", "BAM", "REFERENCE"]:   
            if line_data[1] in sample_x_dict.keys():
                if line_data[1] == "REFERENCE":
                    sys.exit("Only one REFERENCE permitted per sample")
                # If type exists, append path to list
                sample_x_dict[line_data[1]].append(line_data[2])
            else:
                # If not, create list with path
                sample_x_dict[line_data[1]] = [line_data[2]]

        else:
            sys.exit("Unrecognised file type in line %s" % line)

        # if line_data[1] in ["Forward", "Reverse","Single"]:   # fastq files
            # # Initialize a "fastq" slot if does not exist
            # if "fastq" not in sample_x_dict.keys():
                # sample_x_dict["fastq"] = dict()
            # if line_data[1] in sample_x_dict["fastq"]:
                # # If type exists, append path to list
                # sample_x_dict["fastq"][line_data[1]].append(line_data[2])
            # else:
                # # If not, create list with path
                # sample_x_dict["fastq"][line_data[1]] = [line_data[2]]
        
        # elif line_data[1] in ["Nucleotide", "Protein"]:   # fasta files
            # if "fasta" not in sample_x_dict.keys():
                # sample_x_dict["fasta"] = dict()
            # if line_data[1] in sample_x_dict["fasta"]:
                # # If type exists, append path to list
                # sample_x_dict["fasta"][line_data[1]].append(line_data[2])
            # else:
                # # If not, create list with path
                # sample_x_dict["fasta"][line_data[1]] = [line_data[2]]
        # # Experimental: Getting SAM or BAM files:
        # elif line_data[1] in ["SAM", "BAM"]:   # fasta files
            # if "fastq" not in sample_x_dict.keys():
                # sample_x_dict["fastq"] = dict()
            # if "mapping" not in sample_x_dict["fastq"].keys():
                # sample_x_dict["fastq"]["mapping"] = dict()
            # if line_data[1] in sample_x_dict["fastq"]["mapping"]:
                # # If type exists, append path to list
                # sample_x_dict["fastq"]["mapping"][line_data[1]].append(line_data[2])
            # else:
                # # If not, create list with path
                # sample_x_dict["fastq"]["mapping"][line_data[1]] = [line_data[2]]
        # else:
            # sys.exit("Unrecognised file type in line %s" % line)

    return(sample_x_dict)
    
def get_project_title(filelines):
    """ Extract the project title from the file lines
    """
    
    # Get lines with titles:
    title = [re.split("\s+", line, maxsplit=1)[1] for line in filelines if re.split("\s+", line, maxsplit=1)[0]=="Title"]
    if title==[]:
        sys.exit("The sample file does not contain a 'Title' line!\n")
    if len(title) > 1:
        sys.stderr.write("The sample file contains more than one 'Title' line! USING THE FIRST ONE (%s)\n" % title[0])
    return title[0]