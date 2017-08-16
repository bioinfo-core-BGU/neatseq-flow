""" A class defining a pipeline.

This class takes input files: samples and parameters, and creates a qsub pipeline, including dependencies
Actual work is done by calling other class types: PLCStep and PLCName
"""
import os
import sys
import re
from PLC_step import Step,AssertionExcept

from  modules.global_defs import ZIPPED_EXTENSIONS, ARCHIVE_EXTENSIONS, KNOWN_FILE_EXTENSIONS



__author__ = "Menachem Sklarz"
__version__ = "1.0.1"

# A dict for conversion of types of sample data to positions in fasta structure:
fasta_types_dict = {"Nucleotide":"nucl","Protein":"prot"}

class Step_add_trinity_tags(Step):
    """ A module for adding \1 and \2 tags to sequences for analysis by Trinity:
        requires:
            fastq files in one of the following slots:
                sample_data[<sample>]["fastq"]["readF"|"readR"|"readS"]
            
        output:
            puts fastq output files in the following slots:
                self.sample_data[<sample>]["fastq"]["readF"|"readR"|"readS"]
            
    """
    
    def step_specific_init(self):
        self.shell = "csh"      # Can be set to "bash" by inheriting instances
        self.file_tag = "trin_tags.fq"
        
    def step_sample_initiation(self):
        """ A place to do initiation stages following setting of sample_data
        """
        
        
        pass


    def create_spec_wrapping_up_script(self):
        """ Add stuff to check and agglomerate the output data
        """
        
        pass
      
    def build_scripts(self):
        
        
        # Each iteration must define the following class variables:
            # spec_script_name
            # script
        for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash
            # Adding tags to Forward and Reverse files only
            for direction in ["Forward","Reverse","Single"]:
                file_slot = "reads" + direction[0]  # file_slot is "readsF", "readsR" and "readS" for "Forward", "Reverse" and "Single" resepctively
                if (file_slot in self.sample_data[sample]["fastq"].keys()):
                    self.script = ""
                    direction_tag = direction[0] # Get first letter in direction
                    # Name of specific script:
                    self.spec_script_name = "_".join([self.step,self.name,sample,direction_tag]) 
                    
                    # This line should be left before every new script. It sees to local issues.
                    # Use the dir it returns as the base_dir for this step.
                    use_dir = self.local_start(self.base_dir)

                    
                    baseFN = os.path.basename(self.sample_data[sample]["fastq"][file_slot])
                    # TODO: Remove ".fq" in middle of file name
                    # Setting filenames before adding output arguments to script
                    fq_fn = ".".join([baseFN, self.file_tag])  #The filename containing the end result. Used both 
                    
                    
                    
                    # self.script += self.get_script_const()
                    ""
                    self.script += "awk '{ if (NR%%4==1) { gsub(\" \",\"_\"); print $0\"%(tag)s\" } else { print } }' \\\n\t" % {"tag" : {"R":"/2","F":"/1","S":""}[direction[0]]}
                    self.script += "%s \\\n\t" % self.sample_data[sample]["fastq"][file_slot]
                    self.script += "> %s\n\n" % (use_dir + fq_fn)

                    
                    # Move all files from temporary local dir to permanent base_dir
                    self.local_finish(use_dir,self.base_dir)       # Sees to copying local files to final destination (and other stuff)

                    
                    # Store file in active file for sample:
                    self.sample_data[sample]["fastq"][file_slot] = (self.base_dir + fq_fn)
                    self.stamp_file(self.sample_data[sample]["fastq"][file_slot])
                    
                    self.create_low_level_script()
        