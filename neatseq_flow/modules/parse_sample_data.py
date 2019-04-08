

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
        raise Exception("Issues in samples", "The sample and parameter files must not contain carriage returns. Convert newlines to UNIX style!\n")

def parse_sample_file(filename):
    """Parses a file from filename
    """
    file_conts = []

    filenames = filename.split(",")
    for filename_raw in filenames:
        # Expanding '~' and returning full path 
        filename = os.path.realpath(os.path.expanduser(filename_raw))

        if not os.path.isfile(filename):
            raise Exception("Issues in samples", "Sample file %s does not exist.\n" % filename)
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

    # This is a stub from when we supported a different sample_data format.
    return get_tabular_sample_data(filelines)


def parse_sample_control_data(Sample_Control, sample_names):
    """ Parse lines containing sample-control relationships for ChIP-seq protocols
    """
    # Check validity of lines:
    for item in Sample_Control:
        if item.split(":")[0] not in sample_names:
            raise Exception("Issues in sample",
                            "Sample '{sample}' in sample-control data is not defined.".format(sample=item.split(":")[0]))
        if item.split(":")[1] not in sample_names:
            raise Exception("Issues in sample",
                            "Control '{sample}' in sample-control data is not defined.".format(sample=item.split(":")[1]))

    # Extract and return data
    return {item.split(":")[0]:item.split(":")[1] for item in Sample_Control}

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

        sample_lines = [line[1:]
                        for line
                        in raw_data["Sample_data"]
                        if line[0]==sample]
        # Checking sample name does not have a space in it
        if re.search(pattern=" ", string=sample):
            raise Exception("Issues in samples", "Sample name should not contain a space! ('{sample}')".
                            format(sample=sample))
        # Checking all lines have at least three values:
        for line_i in range(len(sample_lines)):
            line=sample_lines[line_i]
            if len(line)<2:
                raise Exception("Issues in samples", "Sample line #{linei} for sample {sample} does not have three "
                                                     "values! ".format(linei=line_i+1,sample=sample))

        sample_data[sample] = parse_tabular_sample_data(sample_lines)
    # pp(sample_data)
    
    if "Project_data" in raw_data:
        # Checking all lines have at least two values:
        for line_i in range(len(raw_data["Project_data"])):
            line=raw_data["Project_data"][line_i]
            if len(line)<2:
                raise Exception("Issues in project data", "Line #{linei} in project data does not have two "
                                                     "values! ".format(linei=line_i+1))
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

    # Read CSV data with csv package. Store in return_results
    linedata = StringIO("\n".join(title_line)) #("\n".join([line[1] for line in title_line])))
    reader = csv.reader(linedata, dialect='excel-tab')
    try:
        # title = [row[1] for row in reader][0]  # Get first element, 2nd (index 1) column:
        title = [row for row in reader][0]
        title = title[1]   # Not doing in one line with previous so that title can be used in exception...
    except IndexError:
        raise Exception("Issues in samples", "Title line does not have a tab-separated value! ('{line}')\n".
                        format(line=title[0]))

    # Removing trailing spaces and converting whitespace to underscore
    if re.search("\s+", title):
        # print "in here"
        title = title.strip()
        title = re.sub("\s+", "_", title)
        sys.stderr.write("The title contains white spaces. Converting to underscores. (%s)\n" % title)
    return_results["Title"] = title

    # Looking for contiguous blocks beginning with #SampleID and #Type.
    # First, getting index of blank lines:
    blank_ind = [ind for (ind,param_l) in list(enumerate(filelines)) if re.match("^\s+$", param_l)]
    blank_ind.append(len(filelines))
    
    # looking for range begining with "#SampleID" till first blank line:
    # Index of header line:
    head_ind_list = [ind
                for (ind,param_l)
                in list(enumerate(filelines))
                if re.split("\s+", param_l, maxsplit=1)[0].lower() == "#sampleid"]

    # if head_ind:  # A line beginning with '#SampleID' exists.
    return_results["Sample_data"] = []
    for head_ind in head_ind_list:
        # Range of lines to keep: from header index till first blank line
        lines_range = list(range(head_ind,min([ind for ind in blank_ind if ind>head_ind])))
        # Read CSV data with csv package. Store in return_results
        linedata = StringIO("\n".join(remove_comments([filelines[i] for i in lines_range])))
        reader = csv.reader(linedata, dialect='excel-tab')
        return_results["Sample_data"].extend([row for row in reader])

    # looking for range begining with "#Type" till first blank line:
    # Index of header line:
    head_ind_list = [ind
                     for (ind,param_l)
                     in list(enumerate(filelines))
                     if re.split("\s+", param_l, maxsplit=1)[0].lower() == "#type"]

    # if head_ind:  # A line beginning with '#Type' exists.
    return_results["Project_data"] = []
    for head_ind in head_ind_list:

        # Range of lines to keep: from header index till first blank line
        lines_range = list(range(head_ind,min([ind for ind in blank_ind if ind>head_ind])))

        linedata = StringIO("\n".join(remove_comments([filelines[i] for i in lines_range])))
        reader = csv.reader(linedata, dialect='excel-tab')
        return_results["Project_data"].extend([row for row in reader])

    # print(return_results["Project_data"])
    # sys.exit()
    # Extract Sample_Control lines:
    sample_control = [line for line in filelines if re.split("\s+", line, maxsplit=1)[0] == "Sample_Control"]
    sample_control = remove_comments(sample_control)

    if sample_control and not "Sample_data" in return_results:
        raise Exception("Sample-control info defined, but sample definition is absent!")
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

        try:
            if line[0] in list(sample_x_dict.keys()):
                # If type exists, append path to list
                # sample_x_dict[line[0]].append(get_full_path(line[1]))
                sample_x_dict[line[0]].append(line[1])

            else:
                # If not, create list with path
                # sample_x_dict[line[0]] = [get_full_path(line[1])]
                sample_x_dict[line[0]] = [line[1]]
        except IndexError:
            raise Exception("Issues in samples", "Sample line does not have three values! ('{line}')\n".
                            format(line=line))

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

    return sample_x_dict

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