#!/fastspace/bioinfo_apps/python-2.7_SL6/bin/python



""" A module for running vcftools:

Can take a VCF, gunzipped VCF or BCF file as input.

Produces an output file, as specified by the output options arguments.


Requires
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


* Input files in one of the following slots (for project scope):

    * ``sample_data["variants"]["VCF" | "gzVCF" | "BCF"]``
    
* Input files in one of the following slots (for sample scope):

    * ``sample_data[<sample>]["variants"]["VCF" | "gzVCF" | "BCF"]``
    

Output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


* Puts output files in the following slots (for project scope): 
    ``self.sample_data["variants"][<output type>]``

* Puts output files in the following slots (for sample scope): 
    ``self.sample_data[<sample>]["variants"][<output type>]``

.. Note:: 

    Output type is set by redirecting the required type, *i.e.* **one** of the following list of types.
    
    For extracting several INFO fields, set ``--get-INFO`` to a list of INFO elements to extract (instead of passing ``--get-INFO`` several times). See examples below.
    
    See the vcftools manual for details (https://vcftools.github.io/man_latest.html).
    
    ``"--freq"``, ``"--freq2"``, ``"--counts"``, ``"--counts2"``, ``"--depth"``, ``"--site-depth"``, ``"--site-mean-depth"``, ``"--geno-depth"``, ``"--hap-r2"``, ``"--geno-r2"``, ``"--geno-chisq"``, ``"--hap-r2-positions"``, ``"--geno-r2-positions"``, ``"--interchrom-hap-r2"``, ``"--interchrom-geno-r2"``, ``"--TsTv"``, ``"--TsTv-summary"``, ``"--TsTv-by-count"``, ``"--TsTv-by-qual"``, ``"--FILTER-summary"``, ``"--site-pi"``, ``"--window-pi"``, ``"--weir-fst-pop"``, ``"--het"``, ``"--hardy"``, ``"--TajimaD"``, ``"--indv-freq-burden"``, ``"--LROH"``, ``"--relatedness"``, ``"--relatedness2"``, ``"--site-quality"``, ``"--missing-indv"``, ``"--missing-site"``, ``"--SNPdensity"``, ``"--kept-sites"``, ``"--removed-sites"``, ``"--singletons"``, ``"--hist-indel-len"``, ``"--hapcount"``, ``"--mendel"``, ``"--extract-FORMAT-info"``, ``"--get-INFO"``, ``"--recode"``, ``"--recode-bcf"``, ``"--12"``, ``"--IMPUTE"``, ``"--ldhat"``, ``"--ldhat-geno"``, ``"--BEAGLE-GL"``, ``"--BEAGLE-PL"``, ``"--plink"``, ``"--plink-tped"``.




Parameters that can be set
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. csv-table:: 
    :header: "Parameter", "Values", "Comments"
    :widths: 15, 10, 10

    "scope", "project | sample", "Indicates whether to use a project or sample bowtie1 index."
    "input", "vcf | bcf | gzvcf", "Type of input to use. Default: vcf"

Lines for parameter file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    vcftools1:
        module: vcftools
        base: freebayes1
        script_path: /path/to/vcftools
        scope: project
        input: vcf
        redirects:
            --recode:

::

    vcftools1:
        module: vcftools
        base: freebayes1
        script_path: /path/to/vcftools
        scope: project
        input: vcf
        redirects:
            --extract-FORMAT-info: GT

::

    vcftools1:
        module: vcftools
        base: freebayes1
        script_path: /path/to/vcftools
        scope: project
        input: vcf
        redirects:
            --get-INFO:
                - NS
                - DB
"""

import os
import sys
from PLC_step import Step,AssertionExcept


__author__ = "Menachem Sklarz"
__version__ = "0.2.0"
class Step_vcftools(Step):

   
    
    def step_specific_init(self):
        self.shell = "bash"      # Can be set to "bash" by inheriting instances
        # self.file_tag = "Bowtie_mapper"
        if "scope" not in self.params:
            raise AssertionExcept("You must supply a 'scope' parameter!")
        elif self.params["scope"] not in ["project","sample"]:
            raise AssertionExcept("'scope' must be 'sample' or 'project' (case sensitive)!")
                    
        if "input" not in self.params:
            self.write_warning("No 'input' parameter passed. Looking for VCF")
            self.params["input"] = "vcf"
        elif self.params["input"] not in ["vcf","bcf","gzvcf"]:
            raise AssertionExcept("'input' must be 'vcf', 'bcf' or 'gzvcf' (case sensitive)!")
        # Check that 'redirects' contains only one of the following options:
        if "redir_params" not in self.params:
            raise AssertionExcept("You must supply an output type in 'redirects'")
            
        # Checking the length of the intersection of redirects params and the possible list of output types:
        # If 0 - none passed. Use 'recode' as default
        # If >1 - error. two passed.
        # If 1 - OK.
        num_of_output_types = len(set(self.params["redir_params"]) & set(["--recode", "--recode-bcf", "--012", "--IMPUTE", "--ldhat", "--ldhat-geno", "--BEAGLE-GL", "--BEAGLE-PL", "--plink", "--plink-tped", "--chrom-map", "--freq", "--freq2", "--counts", "--counts2", "--depth", "--site-depth", "--site-mean-depth", "--geno-depth", "--hap-r2", "--geno-r2", "--geno-chisq", "--hap-r2-positions", "--geno-r2-positions", "--interchrom-hap-r2", "--interchrom-geno-r2", "--TsTv", "--TsTv-summary", "--TsTv-by-count", "--TsTv-by-qual", "--FILTER-summary", "--site-pi", "--window-pi", "--weir-fst-pop", "--het", "--hardy", "--TajimaD", "--indv-freq-burden", "--LROH", "--relatedness", "--relatedness2", "--site-quality", "--missing-indv", "--missing-site", "--SNPdensity", "--kept-sites", "--removed-sites", "--singletons", "--hist-indel-len", "--hapcount", "--mendel", "--extract-FORMAT-info", "--get-INFO"]))
        if num_of_output_types == 0:
            self.params["redir_params"]["--recode"] = None
            self.write_warning("No output type passed. Using '--recode' by default")
        elif num_of_output_types != 1:
            raise AssertionExcept("More than one output type passed")
        else:
            pass
        
    def step_sample_initiation(self):
        """ A place to do initiation stages following setting of sample_data
        """

            
        if self.params["scope"] == "sample":
            for sample in self.sample_data["samples"]:
                if self.params["input"] == "vcf":
                    try:
                        self.sample_data[sample]["variants"]["VCF"]
                    except KeyError:
                        raise AssertionExcept("Sample does not have a VCF variants file." , sample)
                elif self.params["input"] == "bcf":
                    try:
                        self.sample_data[sample]["variants"]["BCF"]
                    except KeyError:
                        raise AssertionExcept("Sample does not have a BCF variants file." , sample)
                else:
                    try:
                        self.sample_data[sample]["variants"]["gzVCF"]
                    except KeyError:
                        raise AssertionExcept("Sample does not have a gzVCF variants file." , sample)
        else:  # Scope == project
            if self.params["input"] == "vcf":
                try:
                    self.sample_data["variants"]["VCF"]
                except KeyError:
                    raise AssertionExcept("Sample does not have a VCF variants file." , sample)
            elif self.params["input"] == "bcf":
                try:
                    self.sample_data["variants"]["BCF"]
                except KeyError:
                    raise AssertionExcept("Sample does not have a BCF variants file." , sample)
            else:
                try:
                    self.sample_data["variants"]["gzVCF"]
                except KeyError:
                    raise AssertionExcept("Sample does not have a gzVCF variants file." , sample)

            
        
    def create_spec_wrapping_up_script(self):
        """ Add stuff to check and agglomerate the output data
        """
        pass
        
    
    def build_scripts(self):
        """ This is the actual script building function
            Most, if not all, editing should be done here 
            HOWEVER, DON'T FORGET TO CHANGE THE CLASS NAME AND THE FILENAME!
        """
        
        
        # Each iteration must define the following class variables:
            # self.spec_script_name
            # self.script

        # Name of specific script:
        
        if self.params["scope"] == "sample":
            for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash

                # Make a dir for the current sample:
                sample_dir = self.make_folder_for_sample(sample)

                # Name of specific script:
                self.spec_script_name = "_".join([self.step,self.name,sample])
                self.script = ""
                
                # This line should be left before every new script. It sees to local issues.
                # Use the dir it returns as the base_dir for this step.
                use_dir = self.local_start(sample_dir)


                if self.params["input"] == "vcf":
                    input_file = self.sample_data[sample]["variants"]["VCF"]
                elif self.params["input"] == "bcf":
                    input_file = self.sample_data[sample]["variants"]["BCF"]
                else:
                    input_file = self.sample_data[sample]["variants"]["gzVCF"]
                
                output_prefix = (use_dir + self.get_step_name() + sample)
                    
                # Get constant part of script:
                self.script += self.get_script_const()
                # Reference file:
                self.script += "--{flag} {file} \\\n\t".format(flag = self.params["input"], file = input_file)
                self.script += "--out %s \\\n\t" % output_prefix

                
                if "--recode" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["VCF"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "recode.vcf") 
                    self.stamp_file(self.sample_data[sample]["variants"]["VCF"])
                if "--recode-bcf" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["BCF"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "recode.bcf") 
                    self.stamp_file(self.sample_data[sample]["variants"]["BCF"])
                if "--012" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["012"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "012") 
                    self.sample_data[sample]["variants"]["012_indv"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "012.indv") 
                    self.sample_data[sample]["variants"]["012_pos"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "012.pos") 
                    self.stamp_file(self.sample_data[sample]["variants"]["012"])
                    self.stamp_file(self.sample_data[sample]["variants"]["012_indv"])
                    self.stamp_file(self.sample_data[sample]["variants"]["012_pos"])
                if "--IMPUTE" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["impute.hap"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "impute.hap") 
                    self.sample_data[sample]["variants"]["impute.hap.legend"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "impute.hap.legend") 
                    self.sample_data[sample]["variants"]["impute.hap.indv"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "impute.hap.indv") 
                    self.stamp_file(self.sample_data[sample]["variants"]["impute.hap"])
                    self.stamp_file(self.sample_data[sample]["variants"]["impute.hap.legend"])
                    self.stamp_file(self.sample_data[sample]["variants"]["impute.hap.indv"])
                if "--ldhat" in self.params["redir_params"] or "--ldhat-geno" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["ldhat.sites"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "ldhat.sites") 
                    self.sample_data[sample]["variants"]["ldhat.locs"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "ldhat.locs") 
                    self.stamp_file(self.sample_data[sample]["variants"]["ldhat.sites"])
                    self.stamp_file(self.sample_data[sample]["variants"]["ldhat.locs"])
                if "--BEAGLE-GL" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["BEAGLE.GL"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "BEAGLE.GL") 
                    self.stamp_file(self.sample_data[sample]["variants"]["BEAGLE.GL"])
                if "--BEAGLE-PL" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["BEAGLE.PL"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "BEAGLE.PL") 
                    self.stamp_file(self.sample_data[sample]["variants"]["BEAGLE.PL"])
                if "--plink" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["ped"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "ped") 
                    self.sample_data[sample]["variants"]["map"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "map") 
                    self.stamp_file(self.sample_data[sample]["variants"]["ped"])
                    self.stamp_file(self.sample_data[sample]["variants"]["map"])
                if "--plink-tped" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["tped"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "tped") 
                    self.sample_data[sample]["variants"]["tfam"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "tfam") 
                    self.stamp_file(self.sample_data[sample]["variants"]["tped"])
                    self.stamp_file(self.sample_data[sample]["variants"]["tfam"])
                if "--freq" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["freq"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "frq") 
                    self.stamp_file(self.sample_data[sample]["variants"]["freq"])

                if "--freq2" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["freq2"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "frq") 
                    self.stamp_file(self.sample_data[sample]["variants"]["freq2"])

                if "--counts" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["counts"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "frq.count") 
                    self.stamp_file(self.sample_data[sample]["variants"]["counts"])

                if "--counts2" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["counts2"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "frq.count") 
                    self.stamp_file(self.sample_data[sample]["variants"]["counts2"])

                if "--depth" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["depth"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "idepth") 
                    self.stamp_file(self.sample_data[sample]["variants"]["depth"])

                if "--site-depth" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["site-depth"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "ldepth") 
                    self.stamp_file(self.sample_data[sample]["variants"]["site-depth"])

                if "--site-mean-depth" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["site-mean-depth"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "ldepth.mean") 
                    self.stamp_file(self.sample_data[sample]["variants"]["site-mean-depth"])

                if "--geno-depth" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["geno-depth"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "gdepth") 
                    self.stamp_file(self.sample_data[sample]["variants"]["geno-depth"])

                if "--hap-r2" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["hap-r2"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "hap.ld") 
                    self.stamp_file(self.sample_data[sample]["variants"]["hap-r2"])

                if "--geno-r2" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["geno-r2"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "geno.ld") 
                    self.stamp_file(self.sample_data[sample]["variants"]["geno-r2"])

                if "--geno-chisq" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["geno-chisq"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "geno.chisq") 
                    self.stamp_file(self.sample_data[sample]["variants"]["geno-chisq"])

                if "--hap-r2-positions" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["hap-r2-positions"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "list.hap.ld") 
                    self.stamp_file(self.sample_data[sample]["variants"]["hap-r2-positions"])

                if "--geno-r2-positions" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["geno-r2-positions"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "list.geno.ld") 
                    self.stamp_file(self.sample_data[sample]["variants"]["geno-r2-positions"])

                if "--interchrom-hap-r2" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["interchrom-hap-r2"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "interchrom.hap.ld") 
                    self.stamp_file(self.sample_data[sample]["variants"]["interchrom-hap-r2"])

                if "--interchrom-geno-r2" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["interchrom-geno-r2"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "interchrom.geno.ld") 
                    self.stamp_file(self.sample_data[sample]["variants"]["interchrom-geno-r2"])

                if "--TsTv" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["TsTv"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "TsTv") 
                    self.stamp_file(self.sample_data[sample]["variants"]["TsTv"])

                if "--TsTv-summary" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["TsTv-summary"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "TsTv.summary") 
                    self.stamp_file(self.sample_data[sample]["variants"]["TsTv-summary"])

                if "--TsTv-by-count" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["TsTv-by-count"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "TsTv.count") 
                    self.stamp_file(self.sample_data[sample]["variants"]["TsTv-by-count"])

                if "--TsTv-by-qual" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["TsTv-by-qual"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "TsTv.qual") 
                    self.stamp_file(self.sample_data[sample]["variants"]["TsTv-by-qual"])

                if "--FILTER-summary" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["FILTER-summary"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "FILTER.summary") 
                    self.stamp_file(self.sample_data[sample]["variants"]["FILTER-summary"])

                if "--site-pi" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["site-pi"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "sites.pi") 
                    self.stamp_file(self.sample_data[sample]["variants"]["site-pi"])

                if "--window-pi" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["window-pi"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "windowed.pi") 
                    self.stamp_file(self.sample_data[sample]["variants"]["window-pi"])

                if "--weir-fst-pop" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["weir-fst-pop"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "weir.fst") 
                    self.stamp_file(self.sample_data[sample]["variants"]["weir-fst-pop"])

                if "--het" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["het"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "het") 
                    self.stamp_file(self.sample_data[sample]["variants"]["het"])

                if "--hardy" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["hardy"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "hwe") 
                    self.stamp_file(self.sample_data[sample]["variants"]["hardy"])

                if "--TajimaD" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["TajimaD"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "Tajima.D") 
                    self.stamp_file(self.sample_data[sample]["variants"]["TajimaD"])

                if "--indv-freq-burden" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["indv-freq-burden"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "ifreqburden") 
                    self.stamp_file(self.sample_data[sample]["variants"]["indv-freq-burden"])

                if "--LROH" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["LROH"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "LROH") 
                    self.stamp_file(self.sample_data[sample]["variants"]["LROH"])

                if "--relatedness" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["relatedness"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "relatedness") 
                    self.stamp_file(self.sample_data[sample]["variants"]["relatedness"])

                if "--relatedness2" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["relatedness2"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "relatedness2") 
                    self.stamp_file(self.sample_data[sample]["variants"]["relatedness2"])

                if "--site-quality" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["site-quality"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "lqual") 
                    self.stamp_file(self.sample_data[sample]["variants"]["site-quality"])

                if "--missing-indv" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["missing-indv"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "imiss") 
                    self.stamp_file(self.sample_data[sample]["variants"]["missing-indv"])

                if "--missing-site" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["missing-site"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "lmiss") 
                    self.stamp_file(self.sample_data[sample]["variants"]["missing-site"])

                if "--SNPdensity" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["SNPdensity"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "snpden") 
                    self.stamp_file(self.sample_data[sample]["variants"]["SNPdensity"])

                if "--kept-sites" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["kept-sites"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "kept.sites") 
                    self.stamp_file(self.sample_data[sample]["variants"]["kept-sites"])

                if "--removed-sites" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["removed-sites"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "removed.sites") 
                    self.stamp_file(self.sample_data[sample]["variants"]["removed-sites"])

                if "--singletons" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["singletons"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "singletons") 
                    self.stamp_file(self.sample_data[sample]["variants"]["singletons"])

                if "--hist-indel-len" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["hist-indel-len"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "indel.hist") 
                    self.stamp_file(self.sample_data[sample]["variants"]["hist-indel-len"])

                if "--hapcount" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["hapcount"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "hapcount") 
                    self.stamp_file(self.sample_data[sample]["variants"]["hapcount"])

                if "--mendel" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["mendel"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "mendel") 
                    self.stamp_file(self.sample_data[sample]["variants"]["mendel"])

                if "--extract-FORMAT-info" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["extract-FORMAT-info"] = \
                        "{prefix}.{info}.{suffix}".format(prefix = output_prefix, \
                                                          info = self.params["redir_params"]["--extract-FORMAT-info"],\
                                                          suffix = "FORMAT") 
                    self.stamp_file(self.sample_data[sample]["variants"]["extract-FORMAT-info"])

                if "--get-INFO" in self.params["redir_params"]:
                    self.sample_data[sample]["variants"]["get-INFO"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "INFO") 
                    self.stamp_file(self.sample_data[sample]["variants"]["get-INFO"])



            
                # Move all files from temporary local dir to permanent base_dir
                self.local_finish(use_dir,self.base_dir)       # Sees to copying local files to final destination (and other stuff)
                
                self.create_low_level_script()
                                     
        else:
            self.spec_script_name = "_".join([self.step,self.name,self.sample_data["Title"]])
            self.script = ""
            
            
            # This line should be left before every new script. It sees to local issues.
            # Use the dir it returns as the base_dir for this step.
            use_dir = self.local_start(self.base_dir)

            if self.params["input"] == "vcf":
                input_file = self.sample_data["variants"]["VCF"]
            elif self.params["input"] == "bcf":
                input_file = self.sample_data["variants"]["BCF"]
            else:
                input_file = self.sample_data["variants"]["gzVCF"]
            
            output_prefix = (use_dir + self.sample_data["Title"])
                
            # Get constant part of script:
            self.script += self.get_script_const()
            # Reference file:
            self.script += "--{flag} {file} \\\n\t".format(flag = self.params["input"], file = input_file)
            self.script += "--out %s \\\n\t" % output_prefix

            
            if "--recode" in self.params["redir_params"]:
                self.sample_data["variants"]["VCF"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "recode.vcf") 
                self.stamp_file(self.sample_data["variants"]["VCF"])
            if "--recode-bcf" in self.params["redir_params"]:
                self.sample_data["variants"]["BCF"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "recode.bcf") 
                self.stamp_file(self.sample_data["variants"]["BCF"])
            if "--012" in self.params["redir_params"]:
                self.sample_data["variants"]["012"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "012") 
                self.sample_data["variants"]["012_indv"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "012.indv") 
                self.sample_data["variants"]["012_pos"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "012.pos") 
                self.stamp_file(self.sample_data["variants"]["012"])
                self.stamp_file(self.sample_data["variants"]["012_indv"])
                self.stamp_file(self.sample_data["variants"]["012_pos"])
            if "--IMPUTE" in self.params["redir_params"]:
                self.sample_data["variants"]["impute.hap"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "impute.hap") 
                self.sample_data["variants"]["impute.hap.legend"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "impute.hap.legend") 
                self.sample_data["variants"]["impute.hap.indv"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "impute.hap.indv") 
                self.stamp_file(self.sample_data["variants"]["impute.hap"])
                self.stamp_file(self.sample_data["variants"]["impute.hap.legend"])
                self.stamp_file(self.sample_data["variants"]["impute.hap.indv"])
            if "--ldhat" in self.params["redir_params"] or "--ldhat-geno" in self.params["redir_params"]:
                self.sample_data["variants"]["ldhat.sites"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "ldhat.sites") 
                self.sample_data["variants"]["ldhat.locs"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "ldhat.locs") 
                self.stamp_file(self.sample_data["variants"]["ldhat.sites"])
                self.stamp_file(self.sample_data["variants"]["ldhat.locs"])
            if "--BEAGLE-GL" in self.params["redir_params"]:
                self.sample_data["variants"]["BEAGLE.GL"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "BEAGLE.GL") 
                self.stamp_file(self.sample_data["variants"]["BEAGLE.GL"])
            if "--BEAGLE-PL" in self.params["redir_params"]:
                self.sample_data["variants"]["BEAGLE.PL"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "BEAGLE.PL") 
                self.stamp_file(self.sample_data["variants"]["BEAGLE.PL"])
            if "--plink" in self.params["redir_params"]:
                self.sample_data["variants"]["ped"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "ped") 
                self.sample_data["variants"]["map"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "map") 
                self.stamp_file(self.sample_data["variants"]["ped"])
                self.stamp_file(self.sample_data["variants"]["map"])
            if "--plink-tped" in self.params["redir_params"]:
                self.sample_data["variants"]["tped"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "tped") 
                self.sample_data["variants"]["tfam"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "tfam") 
                self.stamp_file(self.sample_data["variants"]["tped"])
                self.stamp_file(self.sample_data["variants"]["tfam"])
            if "--freq" in self.params["redir_params"]:
                self.sample_data["variants"]["freq"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "frq") 
                self.stamp_file(self.sample_data["variants"]["freq"])

            if "--freq2" in self.params["redir_params"]:
                self.sample_data["variants"]["freq2"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "frq") 
                self.stamp_file(self.sample_data["variants"]["freq2"])

            if "--counts" in self.params["redir_params"]:
                self.sample_data["variants"]["counts"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "frq.count") 
                self.stamp_file(self.sample_data["variants"]["counts"])

            if "--counts2" in self.params["redir_params"]:
                self.sample_data["variants"]["counts2"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "frq.count") 
                self.stamp_file(self.sample_data["variants"]["counts2"])

            if "--depth" in self.params["redir_params"]:
                self.sample_data["variants"]["depth"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "idepth") 
                self.stamp_file(self.sample_data["variants"]["depth"])

            if "--site-depth" in self.params["redir_params"]:
                self.sample_data["variants"]["site-depth"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "ldepth") 
                self.stamp_file(self.sample_data["variants"]["site-depth"])

            if "--site-mean-depth" in self.params["redir_params"]:
                self.sample_data["variants"]["site-mean-depth"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "ldepth.mean") 
                self.stamp_file(self.sample_data["variants"]["site-mean-depth"])

            if "--geno-depth" in self.params["redir_params"]:
                self.sample_data["variants"]["geno-depth"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "gdepth") 
                self.stamp_file(self.sample_data["variants"]["geno-depth"])

            if "--hap-r2" in self.params["redir_params"]:
                self.sample_data["variants"]["hap-r2"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "hap.ld") 
                self.stamp_file(self.sample_data["variants"]["hap-r2"])

            if "--geno-r2" in self.params["redir_params"]:
                self.sample_data["variants"]["geno-r2"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "geno.ld") 
                self.stamp_file(self.sample_data["variants"]["geno-r2"])

            if "--geno-chisq" in self.params["redir_params"]:
                self.sample_data["variants"]["geno-chisq"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "geno.chisq") 
                self.stamp_file(self.sample_data["variants"]["geno-chisq"])

            if "--hap-r2-positions" in self.params["redir_params"]:
                self.sample_data["variants"]["hap-r2-positions"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "list.hap.ld") 
                self.stamp_file(self.sample_data["variants"]["hap-r2-positions"])

            if "--geno-r2-positions" in self.params["redir_params"]:
                self.sample_data["variants"]["geno-r2-positions"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "list.geno.ld") 
                self.stamp_file(self.sample_data["variants"]["geno-r2-positions"])

            if "--interchrom-hap-r2" in self.params["redir_params"]:
                self.sample_data["variants"]["interchrom-hap-r2"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "interchrom.hap.ld") 
                self.stamp_file(self.sample_data["variants"]["interchrom-hap-r2"])

            if "--interchrom-geno-r2" in self.params["redir_params"]:
                self.sample_data["variants"]["interchrom-geno-r2"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "interchrom.geno.ld") 
                self.stamp_file(self.sample_data["variants"]["interchrom-geno-r2"])

            if "--TsTv" in self.params["redir_params"]:
                self.sample_data["variants"]["TsTv"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "TsTv") 
                self.stamp_file(self.sample_data["variants"]["TsTv"])

            if "--TsTv-summary" in self.params["redir_params"]:
                self.sample_data["variants"]["TsTv-summary"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "TsTv.summary") 
                self.stamp_file(self.sample_data["variants"]["TsTv-summary"])

            if "--TsTv-by-count" in self.params["redir_params"]:
                self.sample_data["variants"]["TsTv-by-count"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "TsTv.count") 
                self.stamp_file(self.sample_data["variants"]["TsTv-by-count"])

            if "--TsTv-by-qual" in self.params["redir_params"]:
                self.sample_data["variants"]["TsTv-by-qual"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "TsTv.qual") 
                self.stamp_file(self.sample_data["variants"]["TsTv-by-qual"])

            if "--FILTER-summary" in self.params["redir_params"]:
                self.sample_data["variants"]["FILTER-summary"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "FILTER.summary") 
                self.stamp_file(self.sample_data["variants"]["FILTER-summary"])

            if "--site-pi" in self.params["redir_params"]:
                self.sample_data["variants"]["site-pi"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "sites.pi") 
                self.stamp_file(self.sample_data["variants"]["site-pi"])

            if "--window-pi" in self.params["redir_params"]:
                self.sample_data["variants"]["window-pi"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "windowed.pi") 
                self.stamp_file(self.sample_data["variants"]["window-pi"])

            if "--weir-fst-pop" in self.params["redir_params"]:
                self.sample_data["variants"]["weir-fst-pop"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "weir.fst") 
                self.stamp_file(self.sample_data["variants"]["weir-fst-pop"])

            if "--het" in self.params["redir_params"]:
                self.sample_data["variants"]["het"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "het") 
                self.stamp_file(self.sample_data["variants"]["het"])

            if "--hardy" in self.params["redir_params"]:
                self.sample_data["variants"]["hardy"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "hwe") 
                self.stamp_file(self.sample_data["variants"]["hardy"])

            if "--TajimaD" in self.params["redir_params"]:
                self.sample_data["variants"]["TajimaD"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "Tajima.D") 
                self.stamp_file(self.sample_data["variants"]["TajimaD"])

            if "--indv-freq-burden" in self.params["redir_params"]:
                self.sample_data["variants"]["indv-freq-burden"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "ifreqburden") 
                self.stamp_file(self.sample_data["variants"]["indv-freq-burden"])

            if "--LROH" in self.params["redir_params"]:
                self.sample_data["variants"]["LROH"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "LROH") 
                self.stamp_file(self.sample_data["variants"]["LROH"])

            if "--relatedness" in self.params["redir_params"]:
                self.sample_data["variants"]["relatedness"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "relatedness") 
                self.stamp_file(self.sample_data["variants"]["relatedness"])

            if "--relatedness2" in self.params["redir_params"]:
                self.sample_data["variants"]["relatedness2"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "relatedness2") 
                self.stamp_file(self.sample_data["variants"]["relatedness2"])

            if "--site-quality" in self.params["redir_params"]:
                self.sample_data["variants"]["site-quality"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "lqual") 
                self.stamp_file(self.sample_data["variants"]["site-quality"])

            if "--missing-indv" in self.params["redir_params"]:
                self.sample_data["variants"]["missing-indv"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "imiss") 
                self.stamp_file(self.sample_data["variants"]["missing-indv"])

            if "--missing-site" in self.params["redir_params"]:
                self.sample_data["variants"]["missing-site"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "lmiss") 
                self.stamp_file(self.sample_data["variants"]["missing-site"])

            if "--SNPdensity" in self.params["redir_params"]:
                self.sample_data["variants"]["SNPdensity"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "snpden") 
                self.stamp_file(self.sample_data["variants"]["SNPdensity"])

            if "--kept-sites" in self.params["redir_params"]:
                self.sample_data["variants"]["kept-sites"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "kept.sites") 
                self.stamp_file(self.sample_data["variants"]["kept-sites"])

            if "--removed-sites" in self.params["redir_params"]:
                self.sample_data["variants"]["removed-sites"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "removed.sites") 
                self.stamp_file(self.sample_data["variants"]["removed-sites"])

            if "--singletons" in self.params["redir_params"]:
                self.sample_data["variants"]["singletons"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "singletons") 
                self.stamp_file(self.sample_data["variants"]["singletons"])

            if "--hist-indel-len" in self.params["redir_params"]:
                self.sample_data["variants"]["hist-indel-len"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "indel.hist") 
                self.stamp_file(self.sample_data["variants"]["hist-indel-len"])

            if "--hapcount" in self.params["redir_params"]:
                self.sample_data["variants"]["hapcount"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "hapcount") 
                self.stamp_file(self.sample_data["variants"]["hapcount"])

            if "--mendel" in self.params["redir_params"]:
                self.sample_data["variants"]["mendel"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "mendel") 
                self.stamp_file(self.sample_data["variants"]["mendel"])

            if "--extract-FORMAT-info" in self.params["redir_params"]:
                self.sample_data["variants"]["extract-FORMAT-info"] = \
                    "{prefix}.{info}.{suffix}".format(prefix = output_prefix, \
                                                      info = self.params["redir_params"]["--extract-FORMAT-info"],\
                                                      suffix = "FORMAT") 
                self.stamp_file(self.sample_data["variants"]["extract-FORMAT-info"])

            if "--get-INFO" in self.params["redir_params"]:
                self.sample_data["variants"]["get-INFO"] = "{prefix}.{suffix}".format(prefix = output_prefix, suffix = "INFO") 
                self.stamp_file(self.sample_data["variants"]["get-INFO"])



        
            # Move all files from temporary local dir to permanent base_dir
            self.local_finish(use_dir,self.base_dir)       # Sees to copying local files to final destination (and other stuff)
            
            self.create_low_level_script()
                                
