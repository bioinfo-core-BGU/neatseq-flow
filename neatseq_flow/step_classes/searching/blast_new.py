# -*- coding: UTF-8 -*-
""" 
Module ``blast``
------------------------------

:Authors: Menachem Sklarz
:Affiliation: Bioinformatics core facility
:Organization: National Institute of Biotechnology in the Negev, Ben Gurion University.

A class that defines a module for executing blast on a nucleotide or protein fasta file.
The search can be either on a sample fasta or on a project-wide fasta.
It can use the fasta as a database or as a query.
If used as a database, you must call the makeblastdb module prior to this step.

In order to cover all the possible configurations of database and query scopes, please follow the scheme described in the following table:


    
Requires:
~~~~~~~~~~~~~

* fasta files in one of the following slots for sample-wise blast:

    * ``sample_data[<sample>]["fasta.nucl"]``
    * ``sample_data[<sample>]["fasta.prot"]``

* or fasta files in one of the following slots for project-wise blast:

    * ``sample_data["fasta.nucl"]``
    * ``sample_data["fasta.prot"]``
    
* or a ``makeblastdb`` index in one of the following slots:

    * When 'scope' is set to 'project'
    
        * ``sample_data["blastdb.nucl"|"blastdb.prot"]``
        * ``sample_data["blastdb.log.nucl"|"blastdb.log.prot"]``

    * When 'scope' is set to 'sample'

        * ``sample_data[<sample>]["blastdb.nucl"|"blastdb.prot"]``
        * ``sample_data[<sample>]["blastdb.log.nucl"|"blastdb.log.prot"]``

    
    
Output:
~~~~~~~~~~~~~

* puts BLAST output files in the following slots for sample-wise blast:

    * ``sample_data[<sample>]["blast.nucl"|"blast.prot"]``
    * ``sample_data[<sample>]["blast"]``

* puts fasta output files in the following slots for project-wise blast:
    
    * ``sample_data["blast.nucl"|"blast.prot"]``
    * ``sample_data["blast"]``


Parameters that can be set        
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. csv-table:: 
    :header: "Parameter", "Values", "Comments"
    :widths: 5,10,10

    "scope", "sample|project", "Set if project-wide fasta slot should be used"
    "dbscope", "sample|project", "If scope=sample and you want to use internal fasta and database, this will tell "
    "fasta2use", "nucl|prot", "Helps the module decide which fasta file to use."
    "db2use", "nucl|prot", "Helps the module decide which database to use."
    "-query | -db", "Path to fasta or BLAST index", "The sequences to use as query, using the internal database as database, or a BLAST database index, using the internal fasta as query."

Lines for parameter file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


External query, project-wise fasta database (must be proceeded by ``makeblastdb`` module)::

    blastOnAssembl:
        module: blast
        base: mkblst1
        script_path: /path/to/bin/blastn
        fasta2use: nucl
        scope: project
        redirects:
            -evalue: '0.0001'
            -num_descriptions: '20'
            -num_threads: '40'
            -outfmt: '"6 qseqid sallseqid qlen slen qstart qend sstart send length
                evalue bitscore score pident qframe"'
            -query: /path/to/query.fasta


Sample specific fasta, external database::

    sprot:
        module: blast
        base: sample_assembl
        script_path: /path/to/blastx
        redirects:
            -db: /path/to/database/index
            -evalue: '0.0001'
            -max_target_seqs: '5'
            -num_of_proc: '20'
            -num_threads: '20'
            -outfmt: '"6 qseqid sallseqid qlen slen qstart qend sstart send length
                evalue bitscore score pident qframe"'
        scope: sample

References
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Altschul, S.F., Madden, T.L., Schäffer, A.A., Zhang, J., Zhang, Z., Miller, W. and Lipman, D.J., 1997. **Gapped BLAST and PSI-BLAST: a new generation of protein database search programs**. *Nucleic acids research*, 25(17), pp.3389-3402.

"""

import os
import sys
import re
from PLC_step import Step,AssertionExcept


__author__ = "Menachem Sklarz"
__version__ = "1.1.0"


class Step_blast_new(Step):
    
    
    def step_specific_init(self):
        """ Called on intiation
            Good place for parameter testing.
            Wrong place for sample data testing
        """
        self.shell = "csh"      # Can be set to "bash" by inheriting instances
        self.file_tag = ".blast.out"

        # Check that either -db or -query (not both) are set in redir_params:
        if "-db" not in self.params["redir_params"]:
            raise AssertionExcept("You must supply a '-db' redirects parameter\n")
        if "-query" not in self.params["redir_params"]:
            raise AssertionExcept("You must supply a '-query' redirects parameter\n")
        
            

    def step_sample_initiation(self):
        """ A place to do initiation stages following setting of sample_data
        """
        
        if self.params["redir_params"]["-db"] in ["sample","project"]:
            if "dbtype" not in self.params:
                raise AssertionExcept("No 'dbtype' passed. Please specify the db type to use.")
            elif self.params["dbtype"] not in ["prot","nucl"]:
                raise AssertionExcept("'dbtype' must be either 'prot' or 'nucl'.")
            else:
                pass
        if self.params["redir_params"]["-query"] in ["sample","project"]:
            if "querytype" not in self.params:
                raise AssertionExcept("No 'querytype' passed. Please specify the query type to use.")
            elif self.params["querytype"] not in ["prot","nucl"]:
                raise AssertionExcept("'querytype' must be either 'prot' or 'nucl'.")
            else:
                pass

        if self.params["redir_params"]["-query"] not in ["sample","project"] and self.params["redir_params"]["-db"] not in ["sample","project"]:
            raise AssertionExcept("At least one of -query and -db must be 'sample' or 'project'. You can't pass two paths.")

        if self.params["redir_params"]["-query"] == "sample" or self.params["redir_params"]["-db"] == "sample":
            self.params["scope"] = "sample"
        else:
            self.params["scope"] = "project"

                # else:
                # if self.params["redir_params"]["-db"] == "sample":
                    # if ("blastdb." + self.params["dbtype"]) not in self.sample_data
        
        if "scope" in self.params:
          
            if self.params["scope"]=="project":
                self.step_sample_initiation_byproject()
            elif self.params["scope"]=="sample":
                self.step_sample_initiation_bysample()
            else:
                raise AssertionExcept("'scope' must be either 'sample' or 'project'")
        else:
            raise AssertionExcept("No 'scope' specified.")
        
        
    def step_sample_initiation_bysample(self):
        """ A place to do initiation stages following setting of sample_data
            This set of tests is performed for sample-level BLAST
        """
        
            
        for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash
            # if not "blast" in self.sample_data[sample].keys():
                # self.sample_data[sample]["blast"] = dict()

            if self.params["redir_params"]["-query"] == "sample":
                if "fasta." + self.params["querytype"] not in self.sample_data[sample]:
                    raise AssertionExcept("No fasta of type %s in sample" % self.params["querytype"], sample)
            if self.params["redir_params"]["-query"] == "project":
                if "fasta." + self.params["querytype"] not in self.sample_data:
                    raise AssertionExcept("No fasta of type %s in project" % self.params["querytype"])
            if self.params["redir_params"]["-db"] == "sample":
                if "blastdb." + self.params["dbtype"] not in self.sample_data[sample]:
                    raise AssertionExcept("No blastdb of type %s in sample. Did you run makeblastdb module with sample scope?" % self.params["dbtype"], sample)            
            if self.params["redir_params"]["-db"] == "project":
                if "blastdb." + self.params["dbtype"] not in self.sample_data:
                    raise AssertionExcept("No blastdb of type %s in project. Did you run makeblastdb module with project scope?" % self.params["dbtype"])
            
            # # Decide on locations of -db and -query
            # if "-query" in self.params["redir_params"].keys():
                # if not "blastdb" in self.sample_data[sample]:
                    # raise AssertionExcept("For sample-as-DB BLAST, you need to first run makeblastdb.\n\tIf the query is a project fasta, set parameter 'scope' to 'project'\n", sample)
                
            # # Decide which fasta to use in blast:
            # # This has holes. If some of the samples have only nucl and some only prot, it will not fail...
            # if "fasta2use" not in self.params.keys():
                # # # "fasta" is not defined for the sample:
                # # if not "fasta" in self.sample_data[sample].keys():
                    # # raise AssertionExcept("No 'fasta' defined.\nIf the query is a project fasta, set parameter 'scope' to 'project'\n",sample)       
                # # Both nucl and prot exist:
                # if "fasta.nucl" in self.sample_data[sample] and "fasta.prot" in self.sample_data[sample]:
                    # raise AssertionExcept("There are both nucl and prot fasta files. You must supply a fasta2use param\n",sample)
                # # Neither nucl nor prot exist:
                # if "fasta.nucl" not in self.sample_data[sample] and "fasta.prot" not in self.sample_data[sample]:
                    # raise AssertionExcept("There are neither nucl nor prot fasta files.\nIf the query is a project fasta, set parameter 'scope' to 'project'\n",sample)
                
                
                # if "fasta.nucl" in self.sample_data[sample].keys():
                    # self.params["fasta2use"] = "nucl"
                # elif "fasta.prot" in self.sample_data[sample].keys():
                    # self.params["fasta2use"] = "prot"
                # else:
                    # ""
                    
            # # if "fasta2use" in self.params.keys():
            # self.fasta2use = self.params["fasta2use"]
            # if not "fasta." + self.fasta2use in self.sample_data[sample]:
                # raise AssertionExcept("The type you passed in fasta2use ('%s') does not exist.\nIf the query is a project fasta, set parameter 'scope' to 'project'\n" % self.params["fasta2use"], sample)

        # pass

    def step_sample_initiation_byproject(self):
        """ A place to do initiation stages following setting of sample_data
            This set of tests is performed for project-level BLAST
        """
        

        if self.params["redir_params"]["-query"] == "project":
            if "fasta." + self.params["querytype"] not in self.sample_data:
                raise AssertionExcept("No fasta of type %s in project" % self.params["querytype"])
        if self.params["redir_params"]["-db"] == "project":
            if "blastdb." + self.params["dbtype"] not in self.sample_data:
                raise AssertionExcept("No blastdb of type %s in project. Did you run makeblastdb module with project scope?" % self.params["dbtype"])
                   
        # if not "blast" in self.sample_data.keys():
            # self.sample_data["blast"] = dict()

        # if not "fasta" in self.sample_data.keys():
            # raise AssertionExcept("You need a 'fasta' file defined to run BLAST.\n\tIf the 'fasta' files are per sample, remove the 'projectBLAST' parameter.\n")
            
            
        # Decide on locations of -db and -query
        # if "-query" in self.params["redir_params"].keys():
            # if not "blastdb" in self.sample_data:
                # raise AssertionExcept("For project-as-DB BLAST, you need to first run makeblastdb.\n")
            
        # # Decide which fasta to use in blast:
        # # This has holes. If some of the samples have only nucl and some only prot, it will not fail...
        # if "fasta2use" not in self.params.keys():
            # # If both nucl and prot exist:
            # if "fasta.nucl" in self.sample_data and "fasta.prot" in self.sample_data:
                # raise AssertionExcept("There are both 'nucl' and 'prot' fasta files. You must supply a fasta2use param\n")       
            # # If neither nucl or prot exist:
            # if "fasta.nucl" not in self.sample_data and "fasta.prot" not in self.sample_data:
                # raise AssertionExcept("There are neither 'nucl' and 'prot' fasta files defined\n")      

            # if "fasta.nucl" in self.sample_data.keys():
                # self.params["fasta2use"] = "nucl"
            # elif "fasta.prot" in self.sample_data.keys():
                # self.params["fasta2use"] = "prot"
            # else:
                # pass # Should'nt get here because of assertions above. Included elif "prot" for clarity
                
        # # if "fasta2use" in self.params.keys():
        # self.fasta2use = self.params["fasta2use"]
        # if not ("fasta." + self.fasta2use) in self.sample_data:
            # raise AssertionExcept("The type you passed in 'fasta2use' ('%s') does not exist for the project.\n\tIf the 'fasta' files are per sample, remove the 'projectBLAST' parameter.\n" % self.params["fasta2use"])

        # # pass
        
    def create_spec_wrapping_up_script(self):
        """ Add stuff to check and agglomerate the output data
        """

        

          
        if self.params["scope"]=="project":
            pass
        elif self.params["scope"]=="sample":
            self.make_sample_file_index()   # see definition below
        
        

    
    def build_scripts(self):
        """ This is the actual script building function
            
        """
        

          
        if self.params["scope"]=="project":
            self.build_scripts_byproject()
        elif self.params["scope"]=="sample":
            self.build_scripts_bysample()
        else:
            raise AssertionExcept("'scope' must be either 'sample' or 'project'")
                
        

    def build_scripts_bysample(self):
        """ Script building function for sample-level BLAST
            
        """
   
        
        # Each iteration must define the following class variables:
            # spec_script_name
            # script
        for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash
            
            # Name of specific script:
            self.spec_script_name = "_".join([self.step,self.name,sample])
            self.script = ""

            # Make a dir for the current sample:
            sample_dir = self.make_folder_for_sample(sample)
            
            # This line should be left before every new script. It sees to local issues.
            # Use the dir it returns as the base_dir for this step.
            use_dir = self.local_start(sample_dir)
                
                
            # Define output filename 
            output_filename = "".join([use_dir , sample , self.file_tag])

            self.script += self.get_script_const()

            # Adding -db :
            if self.params["redir_params"]["-db"] == "project":
                if "dbtype" in self.params:
                    try:
                        self.script += "-db %s \\\n\t" % self.sample_data["blastdb." + self.params["dbtype"]]
                    except KeyError:
                        raise AssertionExcept("No blastdb of type %s exists" % self.params["dbtype"])
                else:
                    self.script += "-db %s \\\n\t" % self.sample_data["blastdb"]
            elif self.params["redir_params"]["-db"] == "sample":
                if "dbtype" in self.params:
                    try:
                        self.script += "-db %s \\\n\t" % self.sample_data[sample]["blastdb." + self.params["dbtype"]]
                    except KeyError:
                        raise AssertionExcept("No blastdb of type %s exists" % self.params["dbtype"], sample)
                else:
                    self.script += "-db %s \\\n\t" % self.sample_data[sample]["blastdb"]
            else: # Path
                self.script += "-db %s \\\n\t" % self.params["redir_params"]["-db"]
                    
            # Adding -query :
            if self.params["redir_params"]["-query"] == "project":
                if "querytype" in self.params:
                    try:
                        self.script += "-query %s \\\n\t" % self.sample_data["fasta." + self.params["querytype"]]
                    except KeyError:
                        raise AssertionExcept("No fasta of type %s exists" % self.params["querytype"])
                else:
                    raise AssertionExcept("You must specify querytype")
            elif self.params["redir_params"]["-query"] == "sample":
                if "querytype" in self.params:
                    try:
                        self.script += "-query %s \\\n\t" % self.sample_data[sample]["fasta." + self.params["querytype"]]
                    except KeyError:
                        raise AssertionExcept("No blastdb of type %s exists" % self.params["querytype"], sample)
                else:
                    raise AssertionExcept("You must specify querytype", sample)
            else: # Path
                self.script += "-query %s \\\n\t" % self.params["redir_params"]["-query"]
                
            self.script += "-out %s\n\n" % output_filename
            
            # Store BLAST result file:
            self.sample_data[sample]["blast"] = (sample_dir + os.path.basename(output_filename))
            self.stamp_file(self.sample_data[sample]["blast"])
            
            # Wrapping up function. Leave these lines at the end of every iteration:
            self.local_finish(use_dir,sample_dir)       # Sees to copying local files to final destination (and other stuff)
            
            
            self.create_low_level_script()
                    
    def build_scripts_byproject(self):
        """ Script building function for project-level BLAST

        """


        
        
        # Each iteration must define the following class variables:
        # spec_script_name
        # script
        
        # Name of specific script:
        self.spec_script_name = "_".join([self.step,self.name,self.sample_data["Title"]])
        self.script = ""

        
        # This line should be left before every new script. It sees to local issues.
        # Use the dir it returns as the base_dir for this step.
        use_dir = self.local_start(self.base_dir)
                
                
        # Define output filename 
        output_filename = "".join([use_dir , self.sample_data["Title"] , self.file_tag])

        self.script += self.get_script_const()
        # Adding -db :
        if self.params["redir_params"]["-db"] == "project":
            if "dbtype" in self.params:
                try:
                    self.script += "-db %s \\\n\t" % self.sample_data["blastdb." + self.params["dbtype"]]
                except KeyError:
                    raise AssertionExcept("No blastdb of type %s exists" % self.params["dbtype"])
            else:
                self.script += "-db %s \\\n\t" % self.sample_data["blastdb"]
        else: # Path
            self.script += "-db %s \\\n\t" % self.params["redir_params"]["-db"]
                
        # Adding -query :
        if self.params["redir_params"]["-query"] == "project":
            if "querytype" in self.params:
                try:
                    self.script += "-query %s \\\n\t" % self.sample_data["fasta." + self.params["querytype"]]
                except KeyError:
                    raise AssertionExcept("No fasta of type %s exists" % self.params["querytype"])
            else:
                raise AssertionExcept("You must specify querytype")
        else: # Path
            self.script += "-query %s \\\n\t" % self.params["redir_params"]["-query"]
            
        self.script += "-out %s\n\n" % output_filename
            
        # Store BLAST result file:
        self.sample_data["blast"] = (self.base_dir + os.path.basename(output_filename))
        self.stamp_file(self.sample_data["blast"])

        # Wrapping up function. Leave these lines at the end of every iteration:
        self.local_finish(use_dir,self.base_dir)       # Sees to copying local files to final destination (and other stuff)
                  
        
        self.create_low_level_script()
                

                    
    def make_sample_file_index(self):
        """ Make file containing samples and target file names.
            This can be used by scripts called by create_spec_wrapping_up_script() to summarize the BLAST outputs.
        """
        
        with open(self.base_dir + "BLAST_files_index.txt", "w") as index_fh:
            index_fh.write("Sample\tBLAST_report\n")
            for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash
                index_fh.write("%s\t%s\n" % (sample,self.sample_data[sample]["blast." + self.fasta2use]))
                
        self.sample_data["BLAST_files_index"] = self.base_dir + "BLAST_files_index.txt"
        
  
        
