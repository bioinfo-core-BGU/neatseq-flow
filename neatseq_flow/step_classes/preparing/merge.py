

""" A module for merging <and unzipping> fastqc and fasta files

Requires
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* fastq files in one of the following slots:

    * ``sample_data[<sample>]["fastq"]["Forward"]``
    * ``sample_data[<sample>]["fastq"]["Reverse"]``
    * ``sample_data[<sample>]["fastq"]["Single"]``

* or fasta files in one of the following slots:

    * ``sample_data[<sample>]["fasta"]["Nucleotide"]``
    * ``sample_data[<sample>]["fasta"]["Protein"]``
    
Output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* puts fastq output files in the following slots:

    * ``sample_data[<sample>]["fastq"]["readF"|"readR"|"readS"]``
        
* puts fasta output files in the following slots:
    
    * ``sample_data[<sample>]["fasta"]["nucl"|"prot"]``

.. note:: In the *merge* parameters, set the *script_path* parameter according to the type of raw files you've got. 
    e.g., if they are gzipped, it should be ``gzip -cd``, etc.

.. note:: If you want to do something more complex with the combined files, you can use the ``pipe`` parameter to send extra commands to be piped on the files after the main command.

    e.g.: You can get files from a remote location by setting ``script_path`` to ``curl`` and ``pipe`` to ``gzip -cd``. This will download the files with curl, unzip them and concatenate them into the target file.  In the sample file, specify remote URLs instead of local pathes.
    
Parameters that can be set
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. csv-table:: 
    :header: "Parameter", "Values", "Comments"
    :widths: 15, 10, 10

    "pipe", "", "Additional commands to be piped on the files before writing to file."

Lines for parameter file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    merge1:
        module: merge
        script_path: gzip -cd

::

    merge1:
        module: merge
        script_path: curl
        pipe:  gzip -cd
        
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
sam_bam_dict     = {"SAM":"sam", "BAM":"bam"}

class Step_merge(Step):
    
    def step_specific_init(self):
        self.shell = "csh"      # Can be set to "bash" by inheriting instances
        self.file_tag = "merge"
        
        
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
            # General comment: If there is a parallel routine for each direction (forward, reverse), add this loop	
            if "fastq" in self.sample_data[sample].keys():
                for direction in ["Forward","Reverse","Single"]:
                    if (direction in self.sample_data[sample]["fastq"].keys()):
                        self.script = ""
                        direction_tag = direction[0] # Get first letter in direction
                        # Name of specific script:
                        self.spec_script_name = "_".join([self.step,self.name,sample,direction_tag]) 
                        
                        # This line should be left before every new script. It sees to local issues.
                        # Use the dir it returns as the base_dir for this step.
                        use_dir = self.local_start(self.base_dir)

                        
                        # Get all unique extensions of files in direction:
                        extensions = list(set([os.path.splitext(fn)[1] for fn in self.sample_data[sample]["fastq"][direction]]))

                        
                        # Find file extension of first input file and remove extra period at the begining of extension (note the [1:] at the end.):
                        extension = os.path.splitext(self.sample_data[sample]["fastq"][direction][0])[1][1:]
                        # Remove zip extension:
                        if "."+extension in ZIPPED_EXTENSIONS:
                            # Get last extension before the '.gz', and remove the leading period (note the [1:] at the end.)
                            extension = os.path.splitext(os.path.splitext(self.sample_data[sample]["fastq"][direction][0])[0])[1][1:]
                        if "."+extension not in KNOWN_FILE_EXTENSIONS:
                            raise AssertionExcept("One of the files has a really weird extension (%s). Make sure this is not a mistake, or update KNOWN_FILE_EXTENSIONS or ZIPPED_EXTENSIONS in global_def.py\n" % extension, sample)
                            # raise AssertionExcept("One of the files in sample %s has a really weird extension (%s). Make sure this is not a mistake, or update KNOWN_FILE_EXTENSIONS or ZIPPED_EXTENSIONS in global_def.py\n" % (sample, extension))
                        
                        fq_fn = ".".join([sample, direction_tag,self.file_tag,extension])          #The filename containing the end result. Used both in script and to set reads in $sample_params

                        
                        self.script += self.params["script_path"] + " \\\n\t"
                        # The following line concatenates all the files in the direction separated by a " "
                        self.script += " ".join(self.sample_data[sample]["fastq"][direction]) 
                        self.script += " \\\n\t"
                        if "pipe" in self.params:
                            self.script += "| {pipe} \\\n\t".format(pipe = self.params["pipe"])
                        self.script += "> %s%s \n\n"  % (use_dir, fq_fn)
    
                        # Move all files from temporary local dir to permanent base_dir
                        self.local_finish(use_dir,self.base_dir)       # Sees to copying local files to final destination (and other stuff)

                        
                        # Store file in active file for sample:
                        self.sample_data[sample]["fastq"]["reads" + direction_tag] = self.base_dir + fq_fn
                        
                        self.stamp_file(self.sample_data[sample]["fastq"]["reads" + direction_tag])
                        
                        
                        self.create_low_level_script()
            
            # Merging files in "fasta" dict in sample_data (genomes etc.)
            if "fasta" in self.sample_data[sample].keys():
                for direction in self.sample_data[sample]["fasta"].keys():
                    self.script = ""
                    direction_tag = fasta_types_dict[direction]
                    
                    # Name of specific script:
                    self.spec_script_name = "_".join([self.step,self.name,sample,direction_tag]) 
                    
                    # This line should be left before every new script. It sees to local issues.
                    # Use the dir it returns as the base_dir for this step.
                    use_dir = self.local_start(self.base_dir)


                    # Get all unique extensions of files in direction:
                    extensions = list(set([os.path.splitext(fn)[1] for fn in self.sample_data[sample]["fasta"][direction]]))
                    
                    # Find file extension of first input file and remove extra period at the begining of extension (note the [1:] at the end.):
                    extension = os.path.splitext(self.sample_data[sample]["fasta"][direction][0])[1][1:]
                    # Remove zip extension:
                    if "."+extension in ZIPPED_EXTENSIONS:
                        # Get last extension before the '.gz', and remove the leading period (note the [1:] at the end.)
                        extension = os.path.splitext(os.path.splitext(self.sample_data[sample]["fasta"][direction][0])[0])[1][1:]
                    if "."+extension not in KNOWN_FILE_EXTENSIONS:
                        raise AssertionExcept("One of the files in sample has a really weird extension (%s). \n\tMake sure this is not a mistake, or update KNOWN_FILE_EXTENSIONS\n" % extension, sample)
                    

                    fq_fn = ".".join([sample, direction_tag,self.file_tag,extension])          #The filename containing the end result. Used both in script and to set reads in $sample_params

                    # You have to add "use existing" functionality
                    self.script += self.params["script_path"] + " \\\n\t"
                    # The following line concatenates all the files in the direction separated by a " "
                    self.script += " ".join(self.sample_data[sample]["fasta"][direction]) 
                    self.script += " \\\n\t"
                    if "pipe" in self.params:
                        self.script += "| {pipe} \\\n\t".format(pipe = self.params["pipe"])
                    self.script += "> %s%s \n\n"  % (use_dir, fq_fn)

                    
                    # # Store file in active file for sample:
                    self.sample_data[sample]["fasta"][direction_tag] = self.base_dir + fq_fn
          
                    self.stamp_file(self.sample_data[sample]["fasta"][direction_tag])

                                        
                    # Move all files from temporary local dir to permanent base_dir
                    self.local_finish(use_dir,self.base_dir)       # Sees to copying local files to final destination (and other stuff)

                    self.create_low_level_script()

            if "mapping" in self.sample_data[sample].keys():
                for direction in self.sample_data[sample]["mapping"].keys():
                    # Do not attempt merging the single reference permitted:
                    if direction == "REFERENCE":
                        continue
                        
                    self.script = ""
                    direction_tag = sam_bam_dict[direction]
                    
                    # Name of specific script:
                    self.spec_script_name = "_".join([self.step,self.name,sample,direction_tag]) 
                    
                    # This line should be left before every new script. It sees to local issues.
                    # Use the dir it returns as the base_dir for this step.
                    use_dir = self.local_start(self.base_dir)


                    # Get all unique extensions of files in direction:
                    extensions = list(set([os.path.splitext(fn)[1] for fn in self.sample_data[sample]["mapping"][direction]]))
                    
                    # Find file extension of first input file and remove extra period at the begining of extension (note the [1:] at the end.):
                    extension = os.path.splitext(self.sample_data[sample]["mapping"][direction][0])[1][1:]
                    # Remove zip extension:
                    if "."+extension in ZIPPED_EXTENSIONS:
                        # Get last extension before the '.gz', and remove the leading period (note the [1:] at the end.)
                        extension = os.path.splitext(os.path.splitext(self.sample_data[sample]["fasta"][direction][0])[0])[1][1:]
                    if "."+extension not in KNOWN_FILE_EXTENSIONS:
                        raise AssertionExcept("One of the files in sample has a really weird extension (%s). \n\tMake sure this is not a mistake, or update KNOWN_FILE_EXTENSIONS\n" % extension, sample)
                    

                    fq_fn = ".".join([sample, direction_tag,self.file_tag,extension])          #The filename containing the end result. Used both in script and to set reads in $sample_params

                    # You have to add "use existing" functionality
                    self.script += self.params["script_path"] + " \\\n\t"
                    # The following line concatenates all the files in the direction separated by a " "
                    self.script += " ".join(self.sample_data[sample]["mapping"][direction]) 
                    self.script += " \\\n\t"
                    if "pipe" in self.params:
                        self.script += "| {pipe} \\\n\t".format(pipe = self.params["pipe"])
                    self.script += " > %s%s \n\n"  % (use_dir, fq_fn)

                    
                    # # Store file in active file for sample:
                    if "fastq" not in self.sample_data[sample].keys():
                        self.sample_data[sample]["fastq"] = dict()
                    if "mapping" not in self.sample_data[sample]["fastq"].keys():
                        self.sample_data[sample]["fastq"]["mapping"] = dict()
                    self.sample_data[sample]["fastq"]["mapping"][direction_tag] = self.base_dir + fq_fn
                    self.sample_data[sample]["fastq"]["mapping"]["reference"] = self.sample_data[sample]["mapping"]["REFERENCE"]
          
                    self.stamp_file(self.sample_data[sample]["fastq"]["mapping"][direction_tag])


                                        
                    # Move all files from temporary local dir to permanent base_dir
                    self.local_finish(use_dir,self.base_dir)       # Sees to copying local files to final destination (and other stuff)

                    self.create_low_level_script()
                    
                    