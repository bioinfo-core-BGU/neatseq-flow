

""" Functions for reading and parsing pipeline sample files
"""

__author__ = "Menachem Sklarz"
__version__ = "1.6.0"


import os, sys
from urllib.parse import urlparse

import csv 
from io import StringIO

from pprint import pprint as pp
import re

FASTQ_FILE_TPYES = ['Single', 'Forward', 'Reverse']
FASTA_FILE_TYPES = ['Nucleotide','Protein']
ALIGNMENT_FILE_TYPES = ['SAM','BAM','REFERENCE']
VARIANT_FILE_TYPES = ['VCF','G.VCF']
RECOGNIZED_FILE_TYPES = FASTQ_FILE_TPYES + FASTA_FILE_TYPES + ALIGNMENT_FILE_TYPES + VARIANT_FILE_TYPES 
GLOBAL_SAMPLE_LIST = ['Title', 'Sample', 'Single', 'Sample_Control'] + RECOGNIZED_FILE_TYPES

from  neatseq_flow.modules.global_defs import ZIPPED_EXTENSIONS, ARCHIVE_EXTENSIONS, KNOWN_FILE_EXTENSIONS


def remove_comments(filelines):
    """
    Remove all comments, commented lines and empty lines from the parameter file lines list
    filelines = list of lines read from parameter file with "readlines()"
    Used by parse_param_data as well
    """

    exceptions = ["#sampleid","#type"]
    # Remove all comments, empty lines and trailing white space:
    filelines = [line.partition("#")[0].rstrip()
                 for line
                 in filelines
                 if len(line.partition("#")[0].strip())>0 ]
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
    if lines_with_CRs:
        print("The sample and parameter files must not contain carriage returns. Convert newlines to UNIX style!\n")
        raise Exception("Issues in samples", "samples")


def parse_sample_file(filename):
    """Parses a file from filename
    """
    file_conts = []

    filenames = filename.split(",")
    for filename_raw in filenames:
        # Expanding '~' and returning full path 
        filename = os.path.realpath(os.path.expanduser(filename_raw))

        if not os.path.isfile(filename):
            sys.exit("Sample file %s does not exist.\n" % filename)
        with open(filename, encoding='utf-8') as fileh:
            file_conts += fileh.readlines()
                
    check_newlines(file_conts)
    sample_data = get_sample_data(file_conts)
    # check_sample_constancy(sample_data)  # Letting user use both zipped and unzipped files. Not recommended
    
    # pp(sample_data)
    # sys.exit()
    return sample_data
        
def get_sample_data(filelines):
    """return lines relevant to the sample data, if exist
    """
    
    sample_file_type = guess_sample_data_format(filelines)
    if (sample_file_type == "Classic"):
        sys.exit("The classic sample file format is no longer supported. Please use the tab-separated format only.")
        # return get_classic_sample_data(filelines)
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
    # Changing to lower case:
    myset = set([x.lower() for x in myset])
    recognized_file_types = set([x.lower() for x in RECOGNIZED_FILE_TYPES])
    
    # pp(set(recognized_file_types))
    # Check if one of the following words exists in the set by checking the intersection of the sets:
    if(({"title", "sample"} <= myset) & \
        (len(myset & set(recognized_file_types))>=1)):    
        # 1. Does myset contain Title and Sample?
        # 2. Does myset include at least one of the RECOGNIZED_FILE_TYPES?
        return "Classic";
    elif ({"title","#sampleid"} <= myset) or ({"title","#type"} <= myset):
        # 1. If myset contains Title and #SampleID
        return "Tabular"
    else:
        sys.exit("Unknown sample file format. Make sure you have a 'Title' line in the sample file.")
    
    

def get_classic_sample_data(filelines):
    """
    Get sample data from filelines
    """
    
    # Helper function. Converts sample line into sample name while removing trailing spaces and converting internal spaces into underscores.
    def get_sample_name(sample_name):
        return re.sub("\s+","_",re.split("\s+", sample_name.strip(), maxsplit=1)[1])

    # Extract sample-related lines from filelines:
    filelines = get_classic_sample_data_lines(filelines)
    # Get list of tuples: (index, sample name) where "index" is the line in filelines holding the sample name line
    sample_index = [(ind,get_sample_name(line))
                    for ind,line
                    in list(enumerate(filelines))
                    if re.split("\s+", line, maxsplit=1)[0]=="Sample"]
    
    
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
    Sample_Control = [re.split("\s+", line, maxsplit=1)[1]
                      for line
                      in filelines
                      if re.split("\s+", line, maxsplit=1)[0]=="Sample_Control"]
    if Sample_Control:
        controls = parse_sample_control_data(Sample_Control,sample_names=list(sample_data.keys()))
        
    # Add a list of sample names to sample_data
    sample_data["samples"] = sorted(sample_data.keys())

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
    #===========================================================================
    # # Create dict with lists of files for each possible direction 
    # reads = {alldirect:[(filename) for (direction,filename) in \
    #                 [re.split("\s+", line, maxsplit=1) for line in lines] \
    #         if direction==alldirect] for alldirect in {"Forward","Reverse","Single"}}
    #===========================================================================
    # Create dict with lists of files for each possible direction 
    reads = {alldirect:[get_full_path(filename) for (direction,filename) in \
                    [re.split("\s+", line, maxsplit=1) for line in lines] \
            if direction==alldirect] for alldirect in {"Forward","Reverse","Single"}}
    # Remove empty lists 
    reads = {direct:files for direct,files in reads.items() if files != []}
    

    # Create dict for storing full sequences, e.g. genomes and proteins. Will be searching for 'Nucleotide' and 'Protein' keywords
    if reads:
        sample_x_data.update(reads)
    
    ## Read fasta files:
    fasta = {alldirect:[get_full_path(filename) for (direction,filename) in \
                    [re.split("\s+", line, maxsplit=1) for line in lines] \
            if direction==alldirect] for alldirect in {"Nucleotide","Protein"}}
    # Remove empty lists 
    fasta = {direct:files for direct,files in fasta.items() if files != []}
    # Put these files in a separate entry in the reads structure called "fasta"
    if fasta:
        sample_x_data.update(fasta)
    
    ## Read BAM/SAM files:
    bam_sam = {alldirect:[get_full_path(filename) for (direction,filename) in \
                    [re.split("\s+", line, maxsplit=1) for line in lines] \
            if direction==alldirect] for alldirect in ALIGNMENT_FILE_TYPES}
    # Remove empty lists 
    bam_sam = {direct:files for direct,files in bam_sam.items() if files != []}
    
    # Complain if more or less than 1 REFERENCE was passed:
    if(bam_sam):    # Do the following only if BAM/SAM files were passed:
        if "REFERENCE" not in bam_sam:
            print("No reference passed with SAM and BAM files...")
            raise Exception("Issue in sample file")
        if len(bam_sam["REFERENCE"]) > 1:
            print("You tried passing more than one REFERENCE with SAM and BAM files...")
            raise Exception("Issue in sample file")
        
        sample_x_data.update(bam_sam)
    
    ## Read vcf files:
    vcf_files = {alldirect:[get_full_path(filename) for (direction,filename) in \
                    [re.split("\s+", line, maxsplit=1) for line in lines] \
            if direction==alldirect] for alldirect in VARIANT_FILE_TYPES}
    # Remove empty lists 
    vcf_files = {direct:files for direct,files in vcf_files.items() if files != []}
    
    # Complain if more or less than 1 REFERENCE was passed:
    if(vcf_files):    # Do the following only if BAM/SAM files were passed:
        sample_x_data.update(vcf_files)

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

        for direction in list(sample_data[sample].keys()):
            # Get a list of file extensions (chars to the RHS of the last period in the filename)
            # extensions = list(set([os.path.splitext(fn)[1] for fn in sample_data[sample][type][direction]]))
            extensions = [os.path.splitext(fn)[1] for fn in sample_data[sample][direction]]
            # Convert file extension to 'zip' or 'regular', depending on the extension:
            # Keep only unique values (using set: {}) and adding to ext_types
            #{"zip" if ext in ZIPPED_EXTENSIONS else "regular" for ext in extensions}
            ext_types = ext_types | set(["zip" if ext in ZIPPED_EXTENSIONS else "regular" for ext in extensions])
        
    if len(ext_types) > 1:
        sys.exit("At the moment, you can't mix zipped and unzipped files!")

def get_tabular_sample_data(filelines):
    """
    Get sample data from filelines
    """
    # Extract sample-related data from filelines:
    # Returns a dict with keys: "Title", "Sample_data" and/or "Project_data" and possibly "ChIP_data"
    raw_data = get_tabular_sample_data_lines(filelines)
    sample_data = dict()

    if "Sample_data" in raw_data:
        sample_names = set([fileline[0] for fileline in raw_data["Sample_data"]])
    else:
        sample_names = []
    
    # Add a list of sample names to sample_data
    sample_data["samples"] = sorted(sample_names)  

    # pp(raw_data["Sample_data"])     
    for sample in sample_names:
        # Parse lines for a single sample.
        # Get the lines that have the sample name in first column and extract data from them
        # with parse_tabular_sample_data()
        # Note: Sample name is removed from element 0 (line[1:]) so that function
        # parse_tabular_sample_data() can be used for project wide table, too.
        sample_data[sample] = parse_tabular_sample_data([line[1:]
                                                         for line
                                                         in raw_data["Sample_data"]
                                                         if line[0]==sample])
    # pp(sample_data)
    
    if "Project_data" in raw_data:
        sample_data["project_data"] = parse_tabular_project_data(raw_data["Project_data"])
    else:
        # Create an empty project_data slot in case an instance needs it before it has been created
        sample_data["project_data"] = dict()
        
    # Get Sample_Control data for ChIP-seq samples:
    if "ChIP_data" in raw_data:
        sample_data["Controls"] = parse_sample_control_data(raw_data["ChIP_data"],sample_names=list(sample_data.keys()))
        
    # Add project title sample_data
    sample_data["Title"] = raw_data["Title"]
    

    return sample_data
    
def get_tabular_sample_data_lines(filelines):
    """ Get sample data from "Tabular" sample data lines
        Will keep one line beginning with "Title" and all consecutive lines from "#SampleID" till first blank line
        
        The reason for this is that the user should have the option of embedding the sample file in the parameter file.
        This way, all line except the title and the consecutive sample lines will be discarded
    """

    return_results = {}
    
    # filelines = remove_comments(filelines)
    title_line = remove_comments([line for line in filelines if re.split("\s+", line, maxsplit=1)[0] == "Title"])
    
    # Check there is only one title line (title is a list of length 1)
    if len(title_line)>1:   
        sys.stdout.write("More than 1 Title line defined. Using first: %s\n" % title_line[0])
    
    # pp(title_line)
    # Read CSV data with csv package. Store in return_results
    linedata = StringIO("\n".join(title_line)) #("\n".join([line[1] for line in title_line])))
    reader = csv.reader(linedata, dialect='excel-tab')
    return_results["Title"] = [row[1] for row in reader][0]  # Get first element, 2nd (index 1) column:

    
    # Looking for contiguous blocks beginning with #SampleID and #Type.
    # First, getting index of blank lines:
    blank_ind = [ind for (ind,param_l) in list(enumerate(filelines)) if re.match("^\s+$", param_l)]
    blank_ind.append(len(filelines))
    
    # looking for range begining with "#SampleID" till first blank line:
    # Index of header line:
    head_ind = [ind
                for (ind,param_l)
                in list(enumerate(filelines))
                if re.split("\s+", param_l, maxsplit=1)[0].lower() == "#sampleid"]
    if head_ind:  # A line beginning with '#SampleID' exists.

        # Range of lines to keep: from header index till first blank line
        lines_range = list(range(head_ind[0],min([ind for ind in blank_ind if ind>head_ind[0]])))

        # Read CSV data with csv package. Store in return_results
        linedata = StringIO("\n".join(remove_comments([filelines[i] for i in lines_range])))
        reader = csv.reader(linedata, dialect='excel-tab')
        return_results["Sample_data"] = [row for row in reader]

    # looking for range begining with "#Type" till first blank line:
    # Index of header line:
    head_ind =  [ind for (ind,param_l) in list(enumerate(filelines)) if re.split("\s+", param_l, maxsplit=1)[0].lower() == "#type"]
    
    if head_ind:  # A line beginning with '#Type' exists.
    
        # Range of lines to keep: from header index till first blank line
        lines_range = list(range(head_ind[0],min([ind for ind in blank_ind if ind>head_ind[0]])))

        linedata = StringIO("\n".join(remove_comments([filelines[i] for i in lines_range])))
        reader = csv.reader(linedata, dialect='excel-tab')
        return_results["Project_data"] = [row for row in reader]


    # Extract Sample_Control lines:
    sample_control = [line for line in filelines if re.split("\s+", line, maxsplit=1)[0] == "Sample_Control"]
    sample_control = remove_comments(sample_control)

    if sample_control and not "Sample_data" in return_results:
        sys.exit("Sample-control info defined, but sample definition is absent!")
    if sample_control:  # ChIP-seq data exists:
        linedata = StringIO("\n".join(sample_control))
        reader = csv.reader(linedata, dialect='excel-tab')
        return_results["ChIP_data"] = [row[1] for row in reader]

    return return_results
    
def parse_tabular_sample_data(sample_lines):
    """ Gets list of lists of file info: [type,path,...]
        The ... are ignored. 
    """
    sample_x_dict = dict()

    for line in sample_lines:
        # line_data = re.split("\s+", line)

        # print line_data[1]
        if line[0] in list(sample_x_dict.keys()):
            # If type exists, append path to list
            # sample_x_dict[line[0]].append(get_full_path(line[1]))
            sample_x_dict[line[0]].append(line[1])

        else:
            # If not, create list with path
            # sample_x_dict[line[0]] = [get_full_path(line[1])]
            sample_x_dict[line[0]] = [line[1]]

    # pp(sample_x_dict)
    # sys.exit()

    return(sample_x_dict)

def parse_tabular_project_data(proj_lines):
    """ Gets list of lists of file info: [type,path,...]
        The ... are ignored.
    """
    sample_x_dict = dict()

    for line in proj_lines:
        # line_data = re.split("\s+", line)

        # print line_data[1]
        if line[0] in list(sample_x_dict.keys()):
            # If type exists, append path to list
            # sample_x_dict[line[0]].append(get_full_path(line[1]))
            sample_x_dict[line[0]].append(line[1])

        else:
            # If not, create list with path
            # sample_x_dict[line[0]] = [get_full_path(line[1])]
            sample_x_dict[line[0]] = [line[1]]

    # pp(sample_x_dict)
    # sys.exit()

    return sample_x_dict

def get_project_title(filelines):
    """ Extract the project title from the file lines
    """
    
    # Get lines with titles:
    title = [re.split("\s+", line, maxsplit=1)[1] for line in filelines if re.split("\s+", line, maxsplit=1)[0]=="Title"]
    if title==[]:
        sys.exit("The sample file does not contain a 'Title' line!\n")
    if len(title) > 1:
        sys.stderr.write("The sample file contains more than one 'Title' line! USING THE FIRST ONE (%s)\n" % title[0])

    # Removing trailing spaces and converting whitespace to underscore
    if re.search("\s+", title[0]):
        # print "in here"
        title[0] = title[0].strip()
        title[0] = re.sub("\s+", "_", title[0])
        sys.stderr.write("The title contains white spaces. Converting to underscores. (%s)\n" % title[0])
  
    return title[0]
    
    
    
def get_full_path(path):
    """ Creates a full path from the given path. This is done in one of two ways:
        1. If it is a URL, IDENTIFIED BY THE PROTOCOL (or scheme): leave it unchanged
        2. Otherwise: use expanduser and abspath on the path IF IT IS NOT ABSOLUTE ALREADY
    """
    
    url = urlparse(path)
    if not url.scheme:   # Regular path
        if not os.path.isabs(path):
            return os.path.abspath(os.path.expanduser(path)) 
    return path


def parse_grouping_file(grouping_file):
    """
    Converts a tab-separated grouping (or mapping) file into a ditcionary format which can then be merged
    into sample_data
    :param grouping_file: A path to the grouping file
    :return: mapping_data in by-sample dictionary format
    """
    grouping_file = os.path.realpath(os.path.expanduser(grouping_file))

    if not os.path.isfile(grouping_file):
        # sys.exit("Grouping file {file} does not exist.\n".format(file=grouping_file))
        raise Exception("Issues in grouping", "Grouping file {file} does not exist.Unidentified extension in source\n".format(file=grouping_file))

    with open(grouping_file, encoding='utf-8') as csvfile:
        file_conts = csvfile.readlines()

    # Convert SampleID at line start to lower case
    file_conts = [re.sub("^#sampleid", "#sampleid", line, flags=re.IGNORECASE)
                  if line.lower().startswith("#sampleid")
                  else line
                  for line
                  in file_conts]

    # Remove all comments, empty lines and trailing white space:
    filelines = [line.partition("#")[0].rstrip()
                 if not line.lower().startswith("#sampleid")
                 else "#" + line.split("#")[1].strip()
                 for line
                 in file_conts
                 if len(line.partition("#")[0].strip()) > 0 or
                 line.lower().startswith("#sampleid")]

    # Read lines as dictionary
    reader = csv.DictReader(filelines, dialect='excel-tab')
    grouping_rows = [row for row in reader]

    # Convert to sample-wise dict
    # e.g:
    # {'Sample1': {'Group1': 'grpa', 'Group2': 'ga'},
    # 'Sample2': {'Group1': 'grpa', 'Group2': 'gb'},
    # 'Sample3': {'Group1': 'grpb', 'Group2': 'gb'}}
    mapping_data = dict()
    for row in grouping_rows:
        if row["#sampleid"] not in mapping_data:
            mapping_data[row["#sampleid"]] = dict()
        for category in list(set(row.keys()) - {"#sampleid"}):
            mapping_data[row["#sampleid"]][category] = row[category]

    return mapping_data