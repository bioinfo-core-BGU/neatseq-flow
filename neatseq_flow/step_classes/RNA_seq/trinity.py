# -*- coding: UTF-8 -*-
""" 
``trinity`` :sup:`*`
-----------------------------------------------------------------
:Authors: Menachem Sklarz
:Affiliation: Bioinformatics core facility
:Organization: National Institute of Biotechnology in the Negev, Ben Gurion University.

A class that defines a module for RNA_seq assembly using the `Trinity assembler`_.


.. Attention:: This module was tested on release 2.5.x. It should also work with 2.4.x 
    
    For old versions of Trinity, you might need to use ``trinity_old`` module.
    
    The main difference between the modules is that ``trinity`` creates an output directory with the word `trinity` in it as required by the newer release of Trinity.
    
    In order to run on the cluster, you need to install `HpcGridRunner`_.     
    
.. _Trinity assembler: https://github.com/trinityrnaseq/trinityrnaseq/wiki
.. _HpcGridRunner: http://hpcgridrunner.github.io/


Requires
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    * ``fastq`` files in at least one of the following slots:
        
        * ``sample_data[<sample>]["fastq.F"]``
        * ``sample_data[<sample>]["fastq.R"]``
        * ``sample_data[<sample>]["fastq.S"]``
        
* ``bam`` file for Genome Guided assembly in:
        
        * ``sample_data["bam"]``
        * ``sample_data[<sample>]["bam"]``
Output:
~~~~~~~~~~~~~

    * puts ``fasta`` output files in the following slots:
        
        * for sample-wise assembly:
        
            * ``sample_data[<sample>]["fasta.nucl"]``
            * ``sample_data[<sample>]["Trinity.contigs"]``
        
        * for project-wise assembly:
        
            * ``sample_data["fasta.nucl"]``
            * ``sample_data["Trinity.contigs"]``

                
Parameters that can be set        
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. csv-table:: 
    :header: "Parameter", "Values", "Comments"

    "scope", "sample|project", "Set if project-wide fasta slot should be used"
    "skip_gene_to_trans_map", "", "Set to skip construction of the transcript map. You can use a dedicated module, ``Trinity_gene_to_trans_map``. Both put the map in the same slot (gene_trans_map)"
    "get_Trinity_gene_to_trans_map", "", "Path to get_Trinity_gene_to_trans_map.pl. If not passed, will try guessing from Trinity path"
    "TrinityStats", "", "block with 'path:' set to `TrinityStats.pl` executable"
    "genome_guided", "", "Use if you have a project level BAM file with reads mapped to a reference genome and it is coordinate sorted"
    "Group_by", "Name of the Column in the grouping file to use for grouping", "Only works in project scope: Will create a sample file for Trinity"
    
Lines for parameter file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    trinity1:
        module:                 trinity
        base:                   trin_tags1
        script_path:            {Vars.paths.Trinity}
        qsub_params:
            node:               sge213
            -pe:                shared 20
        redirects:
            --grid_exec:        "{Vars.paths.hpc_cmds_GridRunner} --grid_conf {Vars.paths.SGE_Trinity_conf} -c" 
            --grid_node_CPU:    40 
            --grid_node_max_memory: 80G 
            --max_memory:        80G 
            --seqType:          fq
            --min_kmer_cov:     2
            --full_cleanup:
        TrinityStats:
            path:           {Vars.paths.TrinityStats}

References
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Grabherr, M.G., Haas, B.J., Yassour, M., Levin, J.Z., Thompson, D.A., Amit, I., Adiconis, X., Fan, L., Raychowdhury, R., Zeng, Q. and Chen, Z., 2011. **Trinity: reconstructing a full-length transcriptome without a genome from RNA-Seq data**. *Nature biotechnology*, 29(7), p.644.

"""



import os
import sys
import re
from neatseq_flow.PLC_step import Step,AssertionExcept


__author__ = "Menachem Sklarz"
__version__ = "1.6.0"


class Step_trinity(Step):
    
    def step_specific_init(self):
        self.shell = "bash"      # Can be set to "bash" by inheriting instances
        self.file_tag = ".Trinity.fasta"
        
        
    def step_sample_initiation(self):
        """ A place to do initiation stages following setting of sample_data
            Here you should do testing for dependency output. These will NOT exist at initiation of this instance. They are set only following sample_data updating
        """
        
        if "genome_guided" in list(self.params.keys()):
            if "Group_by" not in list(self.params.keys()):
                if "scope" in self.params:
                    if self.params["scope"]=="project":
                        if "bam" not in list(self.sample_data["project_data"].keys()):
                            raise AssertionExcept("You do not have a project level bam file to use with genome_guided")
                    elif self.params["scope"]=="sample":
                        for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash
                            if 'bam' not in list(self.sample_data[sample].keys()):
                                raise AssertionExcept("You do not have a sample level bam file to use with genome_guided\n",sample)
                    else:
                        raise AssertionExcept("'scope' must be either 'sample' or 'project'")
                else:
                    raise AssertionExcept("No 'scope' specified.")
                if "--genome_guided_max_intron" not in list(self.params["redir_params"].keys()):
                    raise AssertionExcept("When using genome_guided option you must include the '--genome_guided_max_intron' option within the redirects")
            else:
                raise AssertionExcept("You can not use both options : 'genome_guided' and 'Group_by' together")
        else:
        # Assert that all samples have reads files:
            for sample in self.sample_data["samples"]:    
                if not {"fastq.F", "fastq.R", "fastq.S"} & set(self.sample_data[sample].keys()):
                    raise AssertionExcept("No read files\n",sample)
                
            if "scope" in self.params:
              
                if self.params["scope"]=="project":
                    pass

                elif self.params["scope"]=="sample":
                    
                    for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash
                        pass
                else:
                    raise AssertionExcept("'scope' must be either 'sample' or 'project'")
            else:
                raise AssertionExcept("No 'scope' specified.")
                
        if "Group_by" in list(self.params.keys()):
            if "scope" in self.params:
                if self.params["scope"]=="project":
                    for sample in self.sample_data["samples"]:    
                        if not {"..grouping.."} & set(self.sample_data[sample].keys()):
                            raise AssertionExcept("Grouping information is missing: add a project level 'grouping_file' file type to your samples file \n",sample)
                        else:
                            if self.params["Group_by"] not in list(self.sample_data[sample]["..grouping.."].keys()): 
                                raise AssertionExcept("No {COL} Column in the grouping/mapping file \n".format(COL=self.params["Group_by"]),sample)
                else:
                    raise AssertionExcept("You can only use 'Group_by' in project scope")
                    
        ##########################
        pass
    
    def create_spec_preliminary_script(self):
        """ Add script to run BEFORE all other steps
        """
        self.Samples_Data = "Samples_Data.txt"
        if "Group_by" in list(self.params.keys()):
            self.Group_Dic = {}
            for sample in self.sample_data["samples"]:
                Group=self.sample_data[sample]["..grouping.."][self.params["Group_by"]]
                if Group not in list(self.Group_Dic.keys()):
                    self.Group_Dic[Group] = {}
                if sample not in list(self.Group_Dic[Group].keys()):
                    self.Group_Dic[Group][sample] = ''
            
            self.script = ''
            for Group in list(self.Group_Dic.keys()):
                self.Samples_Data_dir = self.make_folder_for_sample("Samples_Data_"+Group)
                # This line should be left before every new script. It sees to local issues.
                # Use the dir it returns as the base_dir for this step.
                use_dir = self.local_start(self.Samples_Data_dir)
                #initiating new script 
                self.script += "cd %s\n\n" % use_dir
                self.script += "echo -n ""  > {File}\n\n".format(File=self.Samples_Data)
                
                Num = 0
                for sample in list(self.Group_Dic[Group].keys()):
                    self.Group_Dic[Group][sample] = os.path.join(self.Samples_Data_dir,self.Samples_Data)
                    if "fastq.S" in self.sample_data[sample]:
                        Num +=1
                        self.script += "echo -e '{Group}\\t{Group}_rep{Num}\\t{FW}\\t{RV} >> {File}\n".format(Group = Group,
                                                                                                           Num   = Num,
                                                                                                           FW    = self.sample_data[sample]["fastq.S"],
                                                                                                           RV    = '',
                                                                                                           File  = self.Samples_Data )
                    elif  {"fastq.F", "fastq.R"} & set(self.sample_data[sample].keys()):
                        Num +=1
                        self.script += "echo -e '{Group}\\t{Group}_rep{Num}\\t{FW}\\t{RV}' >> {File}\n".format(Group = Group,
                                                                                                           Num   = Num,
                                                                                                           FW    = self.sample_data[sample]["fastq.F"],
                                                                                                           RV    = self.sample_data[sample]["fastq.R"],
                                                                                                           File  = self.Samples_Data )
                self.script += "\n\n"
                self.local_finish(use_dir,self.Samples_Data_dir) 
        pass
    
    def create_spec_wrapping_up_script(self):
        """ Add stuff to check and agglomerate the output data
        """
        
        pass

    def build_scripts(self):
    
        if self.params["scope"] == "project":
            if "Group_by" in list(self.params.keys()):
                sample_list = list(self.Group_Dic.keys())
                self.stash_sample_list(sample_list)
                # Creating data container for subsamples:
                for sample in self.sample_data["samples"]:
                    self.sample_data[sample] = dict()
            else:
                sample_list = ["project_data"]
                # self.build_scripts_project()
        elif self.params["scope"] == "sample":
            sample_list = self.sample_data["samples"]
            # self.build_scripts_sample()
        else:
            raise AssertionExcept("'scope' must be either 'sample' or 'project'")

        for sample in sample_list:  # Getting list of samples out of samples_hash

            # Name of specific script:
            self.spec_script_name = self.set_spec_script_name(sample)
            self.script = ""
            
            if '--grid_exec' in list(self.params["redir_params"].keys()):
                if ("recover" in list(self.params.keys())) or ("finish" in list(self.params.keys())):
                    self.base_step_to_use = self.get_base_step_list()[0]
                    sample_dir = self.base_step_to_use.make_folder_for_sample(sample)
                else:
                    # Make a dir for the current sample:
                    sample_dir = self.make_folder_for_sample(sample)
            else:
                # Make a dir for the current sample:
                sample_dir = self.make_folder_for_sample(sample)

            # This line should be left before every new script. It sees to local issues.
            # Use the dir it returns as the base_dir for this step.
            use_dir = self.local_start(sample_dir)

            # Adding 'trinity' to output dir:
            # "output directory must contain the word 'trinity' as a safety precaution, given that auto-deletion can take place."
        
            output_basename = "{title}_trinity".format(title=sample
                                                                if sample != "project_data"
                                                                else self.sample_data["Title"])

            self.script += self.get_script_const()
            self.script += "--output %s \\\n\t" % os.path.join(use_dir, output_basename)

            if "genome_guided" in list(self.params.keys()):
                self.script += "--genome_guided_bam %s \\\n\t" % self.sample_data[sample]['bam']
            else:
                if "Group_by" in list(self.params.keys()):
                    self.script += "--samples_file %s \\\n\t" % self.Group_Dic[sample][list(self.Group_Dic[sample].keys())[0]]
                else:
                    forward = list()  # List of all forward files
                    reverse = list()  # List of all reverse files
                    single = list()  # List of all single files
                
                    if sample=="project_data":
                        # Loop over samples and concatenate read files to $forward and $reverse respectively
                        # add cheack if paiered or single !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        for sample_k in self.sample_data["samples"]:  # Getting list of samples out of samples_hash
                            # If both F and R reads exist, adding them to forward and reverse
                            # Assuming upstream input testing to check that if there are F reads then there are also R reads.
                            if "fastq.F" in self.sample_data[sample_k]:
                                forward.append(self.sample_data[sample_k]["fastq.F"])
                            if "fastq.R" in self.sample_data[sample_k]:
                                reverse.append(self.sample_data[sample_k]["fastq.R"])
                            if "fastq.S" in self.sample_data[sample_k]:
                                single.append(self.sample_data[sample_k]["fastq.S"])

                        # Concatenate all filenames separated by commas:
                        single = ",".join(single) if (len(single) > 0) else None
                        forward = ",".join(forward) if (len(forward) > 0) else None
                        reverse = ",".join(reverse) if (len(reverse) > 0) else None

                    else:
                        if "fastq.F" in self.sample_data[sample]:
                            forward = self.sample_data[sample]["fastq.F"]
                        if "fastq.R" in self.sample_data[sample]:
                            reverse = self.sample_data[sample]["fastq.R"]
                        if "fastq.S" in self.sample_data[sample]:
                            single = self.sample_data[sample]["fastq.S"]

                    # Adding single reads to end of left (=forward) reads
                    if single and forward:
                        forward = ",".join([forward, single])

               
                    if forward and reverse:
                        self.script += "--left %s \\\n\t" % forward
                        self.script += "--right %s \\\n\t" % reverse
                    elif forward:
                        self.script += "--single %s \\\n\t" % forward
                    elif reverse:
                        self.script += "--single %s \\\n\t" % reverse
                    elif single:
                        self.script += "--single %s \\\n\t" % single
                    else:
                        raise AssertionExcept("Weird. No reads...")

            
            if '--grid_exec' in list(self.params["redir_params"].keys()):
                if "genome_guided" in list(self.params.keys()):
                    base_grid_cmd = "trinity_GG.cmds"
                else:
                    base_grid_cmd = "recursive_trinity.cmds"
                if "qsub_params" in list(self.params.keys()):
                    if "-V" not in list(self.params["qsub_params"].keys()):
                        self.params["qsub_params"]["-V"]=None
                else:
                    self.params["qsub_params"] = {}
                    self.params["qsub_params"]["-V"]=None
                temp_script = self.script
                if "recover" in list(self.params.keys()):
                    self.script = ''
                    self.script += self.get_setenv_part()
                    self.script += '\n\n'
                    self.script += "cd  %s \n\n" % os.path.join(use_dir, output_basename)
                    
                    self.script += "{grid_cmd} {cmd_file} \n\n\n".format(grid_cmd = self.params["redir_params"]["--grid_exec"].strip('"').strip("'"),
                                                                         cmd_file = os.path.join(use_dir, output_basename,base_grid_cmd + ".hpc-cache_success.__failures")) 
                elif "finish" in list(self.params.keys()):
                    # self.script += temp_script
                    # If there is an extra "\\\n\t" at the end of the script, remove it.
                    self.script += "--FORCE \\\n\n"
                    self.script = self.script.rstrip("\\\n\t") + "\n\n"
                    self.script += 'rm -rf {tempdir}\n'.format(tempdir= os.path.join(use_dir, output_basename,"farmit.J*"))
                    self.script += 'rm -f  {tempdir}\n'.format(tempdir= os.path.join(use_dir, output_basename,"*.sh.e*"))
                    self.script += 'rm -f  {tempdir}\n'.format(tempdir= os.path.join(use_dir, output_basename,"*.sh.o*"))
                else:
                    self.script += "--no_distributed_trinity_exec \\\n\n"
                    
                    self.script += "cd  %s \n\n" % os.path.join(use_dir, output_basename)
                    
                    self.script += "{grid_cmd} {cmd_file} \n\n\n".format(grid_cmd = self.params["redir_params"]["--grid_exec"].strip('"').strip("'"),
                                                                         cmd_file = os.path.join(use_dir, output_basename,base_grid_cmd)) 
                
                
                
                
            # If there is an extra "\\\n\t" at the end of the script, remove it.
            self.script = self.script.rstrip("\\\n\t") + "\n\n"
            
            if "TrinityStats" in self.params:
                self.script += """  
{TrinityStats} \\
    {fasta} \\
    > {fasta_stats}
""".format(TrinityStats=self.params["TrinityStats"]["path"],
           fasta=use_dir + ".".join([output_basename, "Trinity.fasta"]),
           fasta_stats=use_dir + ".".join([output_basename, "Trinity.fasta.stats"]),)
           
                self.sample_data[sample]["trinity.stats"] = ".".join([sample_dir, output_basename, "Trinity.fasta.stats"])

            # Store results to fasta and assembly slots:
            transcriptome = os.path.join(output_basename, "Trinity.fasta")
            if "genome_guided" in list(self.params.keys()):
                transcriptome = os.path.join(output_basename, "Trinity-GG.fasta")
            else:
                transcriptome = ".".join([output_basename, "Trinity.fasta"])
            
            self.sample_data[sample]["fasta.nucl"] = os.path.join(sample_dir, transcriptome)
            self.sample_data[sample][self.get_step_step() + ".contigs"] = self.sample_data[sample]["fasta.nucl"]

            self.stamp_file(self.sample_data[sample]["fasta.nucl"])

            # Created automatically by trinity:
            self.sample_data[sample]["gene_trans_map"] = "{contigs}.gene_trans_map".format(contigs=os.path.join(sample_dir, transcriptome))
            self.stamp_file(self.sample_data[sample]["gene_trans_map"])

            self.local_finish(use_dir, sample_dir)
            self.create_low_level_script()


