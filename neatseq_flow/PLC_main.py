
""" A class defining a pipeline.

This class takes input files: samples and parameters, and creates a qsub pipeline, including dependencies
Actual work is done by calling other class types: PLCStep and PLCName
"""

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"


import os, sys, json, shutil, time, yaml, re


from copy import *
from pprint import pprint as pp
from random import randint
from datetime import datetime


from modules.parse_sample_data import parse_sample_file
from modules.parse_param_data import parse_param_file

from PLC_step import Step,AssertionExcept


class neatseq_flow:
    """Main pipeline class. Contains sample data and parameters
    """
    
    def __init__(self, sample_file, param_file, home_dir = None, message = None, runid = None, verbose = False):
        
        # Read and parse the sample and parameter files:

        sys.stdout.write("Reading files...\n")

        try:
            self.sample_data = parse_sample_file(sample_file)
        except Exception:
            
            print("An exception has occured in sample file reading. Double check!")
            raise

        try:
            self.param_data = parse_param_file(param_file)
        except Exception as raisedex:
            
            if raisedex.args[0] == "Issues in parameters":
                sys.exit()
            elif len(raisedex.args)>1:
                if raisedex.args[1] in ["Variables","parameters"]:
                    sys.exit(raisedex.args[0])
                    # raise
                else:  # Unknown
                    # sys.stderr.write("unknown exception type")
                    raise
            else:
                raise
            # sys.stderr.write("An exception has occured in parameter file reading. Double check!")
            # raise
        except:
            raise
        
        # Prepare dictionary for pipe data (in perl version: pipe_hash)
        self.pipe_data = dict()

        self.pipe_data["step_order"] = self.param_data["step_order"]
        del(self.param_data["step_order"])

        # Determine type of sample: SE, PE or mixed:
        self.determine_sample_types()

        # if home_dir is None or empty, set to cwd, else leave as is
        self.pipe_data["home_dir"] = home_dir if home_dir else os.getcwd()
        # Assert that the dir is a valid existing directory:
        assert os.path.isdir(self.pipe_data["home_dir"]), "Directory %s does not exist!\n" % self.pipe_data["home_dir"]
        self.pipe_data["home_dir"] = os.path.realpath(self.pipe_data["home_dir"])

        # Store message:
        assert message==None or isinstance(message, basestring), "Message must be text or 'None'."
        self.pipe_data["message"] = message

        # Store list of sample names in pipe_data (A patch. This is so that steps can have access to the full sample list after a user requests a step to operate on a subset of samples.)
        # See definition of PLC_step.set_sample_data()
        self.pipe_data["samples"] = self.sample_data["samples"]
        
        self.pipe_data["verbose"] = verbose

        # Making a step name index (dict of form {step_name:step_type})
        # Storing in self.name_index
        self.make_names_index()
        
        # Expanding dependencies based on "base" parameter:
        # Storing in self.depend_dict 
        self.expand_depends()

        # Create run code to identify the scripts etc.
        # Original: just random number: self.run_code = str(randint(0,1e6)) # Is always used as a string
        # Current: Date+rand num (to preserve order of pipelines)
        if runid:
            self.run_code = runid
        else:
            self.run_code = datetime.now().strftime("%Y%m%d%H%M%S") # Is always used as a string
        self.pipe_data["run_code"] = self.run_code
        if "Default_wait" in self.param_data["Global"].keys():
            self.pipe_data["Default_wait"] = self.param_data["Global"]["Default_wait"]
        if "job_limit" in self.param_data["Global"].keys():
            self.pipe_data["job_limit"] = self.param_data["Global"]["job_limit"]
        
        
        # ------------------------------
        # Define default qsub parameters
        self.pipe_data["qsub_params"] = {}
        
        self.pipe_data["qsub_params"]["queue"] = self.param_data["Global"]["Qsub_q"]    # This is required by assertion in parse_param_data()
        # if "Qsub_nodes" in self.param_data["Global"].keys():
            # self.pipe_data["qsub_params"]["node"] = ",".join(list(set(self.param_data["Global"]["Qsub_nodes"])))
        # else:
            # self.pipe_data["qsub_params"]["node"] = None
        if "Qsub_nodes" in self.param_data["Global"].keys():
            self.pipe_data["qsub_params"]["node"] = list(set(self.param_data["Global"]["Qsub_nodes"]))
        else:
            self.pipe_data["qsub_params"]["node"] = None

        # If Qsub_opts is defined by user in global params, copy into pipe_data:
        self.pipe_data["qsub_params"]["opts"] = self.param_data["Global"]["Qsub_opts"] if "Qsub_opts" in self.param_data["Global"].keys() else ""
        
        # Setting path to qstat
        if "Qsub_path" in self.param_data["Global"].keys():
            self.pipe_data["qsub_params"]["qstat_path"] = os.sep.join([self.param_data["Global"]["Qsub_path"].rstrip(os.sep),"qstat"])
        else:
            self.pipe_data["qsub_params"]["qstat_path"] = "qstat"

        # --------------------------------
        
        # --------------------------------
        # Define conda parameters
        self.define_conda_params()
        
        # Create directory structure:
        sys.stdout.write("Creating direcotry structure...\n")
        self.make_directory_structure()

        # Create log file:
        self.create_log_file()

        # Create file md5sum registration file:
        self.create_registration_file()
        
        # Backup parameter and sample files:
        self.backup_source_files(param_file, sample_file)
        
        # Create step instances:
        sys.stdout.write("Making step instances...\n")
        self.make_step_instances()
        
        # if convert2yaml:
            # # Convert to YAML
            # self.convert_data_to_YAML()
            # print "Exported sample and param data to YAML format.\nExitting...\n"
            # # sys.exit()
            # return

        # Make main script:
        self.make_main_pipeline_script()

        # Make the qdel script:
        self.create_qdel_script()
        
        # Do the actual script building:
        # Also, catching assetion exceptions raised by class build_scripts() and 
        sys.stdout.write("Building scripts...\n")
        try:
            self.build_scripts()
            
        except AssertionExcept as assertErr:
            print "An error has occured. See comment above.\nPrinting current JSON and exiting\n"
            with open(self.pipe_data["objects_dir"]+"WorkflowData.json","w") as json_fh:
                json_fh.write(self.get_json_encoding())
            # sys.exit() 
            return
            
        
        
        # Make the qalter script:
        self.create_qalter_script()
        
        # Make js graphical representation (maybe add parameter to not include this feature?)
        sys.stdout.write("Making workflow plots...\n")
        self.create_js_graphic()
        self.create_diagrammer_graphic()
        
        # Writing JSON encoding ofg pipeline:
        sys.stdout.write("Writing JSON files...\n")
        with open(self.pipe_data["objects_dir"]+"WorkflowData.json","w") as json_fh:
            json_fh.write(self.get_json_encoding())
        # Writing JSON encoding of qsub names (can be used by remote progress monitor)
        with open(self.pipe_data["objects_dir"]+"qsub_names.json","w") as json_fh:
            json_fh.write(self.get_qsub_names_json_encoding())
            
        
        
        self.create_log_plotter()
        
        sys.stderr.flush()
        sys.stdout.write("Finished successfully....\n\n")
        
    # Handlers
    def get_param_data(self):
        """ Return parameter data
        """
        return self.param_data
        
    def get_step_param_data(self):
        """ Return step-wise parameter data
        """
        return self.param_data["Step"]
        
        
    def get_steps(self):
        """ return a list of step types required 
        """
        
        return self.param_data["Step"].keys()
        
        
    def get_step_names(self):
        """ return a list of step names (=step instances)
        """
        return self.name_index.keys()
        pass
        
        
    def get_names_index(self):
        return self.name_index
        
        
    def make_names_index(self):
        """ Make a dict of the form name:steps
        """
        self.name_index = dict()
        for step in self.param_data["Step"]:
            for name in self.param_data["Step"][step].keys():
                self.name_index[name] = step
        
        return self.name_index
        
    def build_scripts(self):
        """ Run the actual script building
        """

        # For each step name (step_n), set sample_data based on the steps base(s) and then create scripts
        for step_n in self.step_list:
           
            step_name = step_n.get_step_name()
            step_step = step_n.get_step_step()

            # Find base step(s) for current step: (If does not exist return None)
            base_name_list = step_n.get_base_step_name()    

            
            # For merge, 1st step, this will be true, passing the original sample_data to the step:
            if base_name_list == None:
                step_n.set_sample_data(self.sample_data)
                step_n.set_base_step([])
            # For the others, finds the instance(s) of the base step(s) and calls set_base_step() with the list of bases:
            else:
                # Note: set_base_step() takes a list of step objects, not names. Finding them is done by the .index() method.
                step_n.set_base_step([self.step_list[self.step_list_index.index(base_name)] for base_name in base_name_list])

                
            # Do the actual script building for step_n
            step_n.create_all_scripts()
                
            
                
                
    def make_step_order(self):
        pass
        
    # def complete_depends(self):     # Complete the dependencies 
    
    def make_depends_dict(self):
        """ Creates and returns the basic depend_dict structure
            step names are keys, values are a list of the step names which are bases for the step
        """
        step_data = self.get_step_param_data()
        # Get the base list for each step.
        # self.depend_dict = {name:[step_data[self.name_index[name]][name]["base"] if self.name_index[name] != "merge" else ""] for name in self.name_index.keys() }
        self.depend_dict = {name:deepcopy(step_data[self.name_index[name]][name]["base"]) 
                                if self.name_index[name] != "merge" 
                                else [""] for name in self.name_index.keys() }
        return self.depend_dict
        
        
    def expand_depends(self):
        """ Extract base info for each step from parameters and expand the dependency info
            i.e. if base(samtools)=['Bowtie_mapper'], expand it to ['merge','Bowtie_mapper']
        """
        step_data = self.get_step_param_data()
        # Get the base list for each step.
        self.make_depends_dict()
        
        # ### Helper recursive function
        def expand_depend_list(step_name,depend_list,depend_dict):
            """ helper function. takes a list and RECURSIVELY expands it based on the dependency dict
            step_name is the name of the step on which it is executing. Used to hault the recursion on cases of loops in the DAG...
            """
            
            if depend_list==[]:
                return depend_list
            ret_list = depend_list
            if step_name in depend_list:
                sys.exit("There seems to be a cycle in the workflow design. Check dependencies of step %s" % step_name)
            for elem in depend_list:
                if (elem==""):
                    pass
                else:
                    ret_list += expand_depend_list(step_name, list(depend_dict[elem]),depend_dict)
                    
            return list(set(ret_list))
        # ######

        # Expand to include all dependencies in the list
        # This is a little bit of recursive and comprehension magic...
        local_depend_dict = {step:expand_depend_list(step, self.depend_dict[step], self.depend_dict) for step in self.depend_dict}
        # Remove empty strings ('') from the lists of dependencies:
        local_depend_dict = {step:[depend for depend in local_depend_dict[step] if depend != ""] for step in local_depend_dict}    
        self.depend_dict = local_depend_dict

        # Store dependencies in param structure:
        for step in step_data:
            for name in self.param_data["Step"][step]:
                self.param_data["Step"][step][name]["depend_list"] = self.depend_dict[name]
            
        
        return self.depend_dict 


    def sort_step_list(self):
        """ This function sorts the step list
            By default uses the list.sort function on the step list, which sorts the steps by level, i.e. all direct merge dependents first, then their dependents, etc.
            A different sorting scheme can be added here for depth-wise sorting, for instance.
        """
        
        self.step_list.sort()    # Sort by internal __lt__ and __gt__
            
    def make_step_instances(self):
        """ Makes step instances and stores them in self.step_list.
            The steps are also sorted based on their dependencies. See __lt__ and __gt__ in "Step" class definition.
        """
        # The list of steps is created using a helper function, make_step_type_instance.
        # See definition of make_step_type_instance to see how step type is determined and imported...
        self.step_list = [self.make_step_type_instance(step_n) for step_n in self.get_step_names()]

        self.sort_step_list()

        
        # Send number of step to the instances:
        # This is used for numbering the scripts in the scripts_dir
        counter = 1
        for step_n in self.step_list:
            step_n.set_step_number(counter)
            counter+=1
            
        # Create index of step names. Once their order is set, above, this new list will contain the step names in the same order
        # Is used to search the list of classes.
        self.step_list_index = [step_n.get_step_name() for step_n in self.step_list]
        
        # NOTE: Each step's base step is set in build_scripts(), because not all info exists at construction time...
        
        return self.step_list
        

        
    def make_directory_structure(self):
        """ Creating the directory structure to hold the scripts, data etc.
        """
        for directory in ["data_dir","scripts_dir","stderr_dir","stdout_dir","objects_dir","logs_dir","backups_dir"]:
            # Get only the first part of 'directory' for directory name:
            dir_name = directory.split("_")[0]
            # Concatenate the directory name to the home path:
            self.pipe_data[directory] = self.pipe_data["home_dir"] + os.sep + dir_name + os.sep
            if (os.path.isdir(self.pipe_data[directory])):
                if self.pipe_data["verbose"]:
                    sys.stderr.write("WARNING: {dirname} folder exists. Overwriting existing! (existing files will not be deleted)\n".format(dirname=dir_name))
            else:
                if self.pipe_data["verbose"]:
                    sys.stderr.write("WARNING: Creating {dir_name} directory\n".format(dir_name=dir_name))
                os.mkdir(self.pipe_data[directory])
        

    def make_main_pipeline_script(self):
        """ Create the main pipline script stored in 00.pipe.commands.csh 
        """
        
        with open(self.pipe_data["scripts_dir"] + "00.pipe.commands.csh", "w") as pipe_fh:
            # Writing header :)
            pipe_fh.write("""
\n\n
# This is the main executable script of this pipeline
# It was created on %(date)s by NeatSeq-Flow version %(version)s
# See http://neatseq-flow.readthedocs.io/en/latest/

\n\n\n""" % {"date": time.strftime("%d/%m/%Y %H:%M:%S"), "version": __version__})
            
            # For each step, write the qsub command created by get_qsub_command() method:
            for step_n in self.step_list:
                if not step_n.skip_scripts:   # Add the line only for modules that produce scripts (see del_type and move_type for examples of modules that don't...)
                    pipe_fh.write(self.get_qsub_command(step_n))

                
                
    def get_qsub_command(self,step):
        """ Get the qsub command for step to print in main pipeline script, 00....
        """
        qsub_line = ""
        qsub_line += "echo running " + step.get_step_name() + " ':\\n------------------------------'\n"
        
        # slow_release_script_loc = os.sep.join([self.pipe_data["home_dir"],"utilities","qsub_scripts","run_jobs_slowly.pl"])

        if "slow_release" in step.params.keys():
            # Define the code for slow release 
            # Define the slow_release command (common to both options of slow_release)
            qsub_line += """ 
qsub -N %(step_step)s_%(step_name)s_%(run_code)s \\
    -q %(queue)s \\
    -e %(stderr)s \\
    -o %(stdout)s \\
    %(slow_rel_params)s \\
    -f %(scripts_dir)s%(script_name)s \n""" % \
                        {"step_step"              : step.get_step_step(),
                        "step_name"               : step.get_step_name(),
                        "run_code"                : self.run_code,
                        "stderr"                  : self.pipe_data["stderr_dir"],
                        "stdout"                  : self.pipe_data["stdout_dir"],
                        "queue"                   : self.pipe_data["qsub_params"]["queue"],
                        "scripts_dir"             : self.pipe_data["scripts_dir"],
                        "script_name"             : step.get_script_name(),
                        "slow_rel_params"         : step.params["slow_release"]}

        else:
            qsub_line += "qsub %(scripts_dir)s%(script_name)s\n" % {"scripts_dir" : self.pipe_data["scripts_dir"], 
                                                                    "script_name" : step.get_script_name()}

        qsub_line += "\n\n"
        return qsub_line




    def make_step_type_instance(self,step_name):
        """ Create and return a class of the type defined in step_type
            Gets the module name from Step class, imports it, constructs the suitable subclass and returns it.
        """
        step_type   = self.name_index[step_name]
        step_params = self.get_step_param_data()[step_type][step_name]
        
        # Find the location of the step module in the file structure (see function find_step_module())
        step_module_loc = Step.find_step_module(step_type, self.param_data, self.pipe_data)  # Passing param data because it contains the optional search path...
        try:
            # Import the module:
            exec "from %s import %s as StepClass" % (step_module_loc,'Step_' + step_type)
        except ImportError:
            print "An error has occured loading module %s.\n" % step_module_loc
            print "CMD: from %s import %s as StepClass\n" % (step_module_loc,'Step_' + step_type)
            raise

        # Run constructor:
        try:
            return StepClass(step_name,   \
                             step_type,   \
                             step_params, \
                             self.pipe_data)
        except AssertionExcept as assertErr:
            print("An error has occured in step initialization (type: %s). See comment above.\n" % step_type)
            print assertErr.get_error_str()

            sys.exit()
            # raise

    def define_conda_params(self):
        """ If conda params are required, define them:
        """
        
        if "conda" in self.param_data["Global"]:
            self.pipe_data["conda"] = self.param_data["Global"]["conda"]
            if "CONDA_PREFIX" in os.environ:
                conda_module_path = os.path.join(os.environ["CONDA_PREFIX"], "lib/python2.7/site-packages/neatseq_flow_modules")
                if not os.path.isdir(conda_module_path):
                    if self.pipe_data["verbose"]:
                        sys.stderr.write("WARNING: conda default additional modules path (%s) does not exist!\n" % conda_module_path)
                else:
                    if self.pipe_data["verbose"]:
                        sys.stderr.write("ATTENTION: Adding conda default additional modules path (%s). If it is different, please add manually to 'module_path' in 'Global_params'." % conda_module_path)
                    if "module_path" in self.param_data["Global"]:
                        if conda_module_path not in self.param_data["Global"]["module_path"]:
                            self.param_data["Global"]["module_path"].append(conda_module_path)
                    else:
                        self.param_data["Global"]["module_path"] = [os.path.join(conda_module_path)]

    
        
                        
    def determine_sample_types(self):
        """ Add a "type" field to each sample with "PE", "SE" or "Mixed"
        """
        
        
        for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash
            
            # Prepare holder for type:
            self.sample_data[sample]["type"] = list()
            if "Single" in self.sample_data[sample]:
                # Only one type of file: SE
                self.sample_data[sample]["type"].append("SE")
            if "Forward" in self.sample_data[sample] and "Reverse" in self.sample_data[sample]:
                self.sample_data[sample]["type"].append("PE")
            if "Forward" in self.sample_data[sample] and "Reverse" not in self.sample_data[sample]:
                sys.exit("You have only Forward for sample %s. Can't proceed!" % sample)
            if "Reverse" in self.sample_data[sample] and "Forward" not in self.sample_data[sample]:
                sys.exit("You have only Reverse for sample %s. Can't proceed!" % sample)
            # IF fasta exists, add to types list
            if "Nucleotide" in self.sample_data[sample]:
                self.sample_data[sample]["type"].append("nucl")
            if "Protein" in self.sample_data[sample]:
                self.sample_data[sample]["type"].append("prot")
            if "BAM" in self.sample_data[sample] or "SAM" in self.sample_data[sample]:
                self.sample_data[sample]["type"].append("mapping")
            
                
    def create_qdel_script(self):
        """ This function creates the 99.qdel_all script
        """
        
        # Create name for qdel script:
        self.qdel_script_name = self.pipe_data["scripts_dir"] + "99.qdel_all.csh"
        
        # Create directory for step-wise qdel 
        stepWiseDir = "%s99.qdel_all%s" % (self.pipe_data["scripts_dir"],os.sep)
        if not os.path.isdir(stepWiseDir):
            if self.pipe_data["verbose"]:
                sys.stderr.write("Making dir 99.qdel_all directory at %s\n" % stepWiseDir)
            os.makedirs(stepWiseDir) 
        else:
            if self.pipe_data["verbose"]:
                sys.stderr.write("Dir %s exists. Will overwrite... \n" % stepWiseDir)

        
        
        with open(self.qdel_script_name, "w") as script_fh:
            # Adding preliminary stuff:
            script_fh.write("#!/bin/csh\n\n")
            script_fh.write("# Adding line to log file:\n")
            script_fh.write("date '+%%d %%b %%Y, %%H:%%M' >> %s\n" % (self.pipe_data["log_file"]))
            script_fh.write("echo '\\t\\tDeleting all jobs with 99.qdel_all.csh' >> %s\n\n\n" % (self.pipe_data["log_file"]))

            script_fh.write("# Remove high level scripts:\n# entry_point\n\n\n")
            
            # For every step, create separate qdel file with step jobs.
            # These files are populated and de-populated on the run:
            for step in self.step_list:
                # Create step-specific del script:
                step_del_script_fn = "%s99.qdel_all_%s.csh" % (stepWiseDir,step.name)
                with open(step_del_script_fn, "w") as step_del_script:
                    # Write header
                    step_del_script.write("#!/bin/csh\n\n")
                    step.set_qdel_files(step_del_script_fn, self.qdel_script_name)
                    # # For every jid, add a qdel line:
                    # for jid in step.get_jid_list():
                        # step_del_script.write("qdel %s\n" % jid)
                # Add call to step-specific qdel script to main qdel script:
                script_fh.write("csh %s\n" % step_del_script_fn)
            # Add logging:
            script_fh.write("\n\n# Adding line to log file:\n")
            script_fh.write("date '+%%d %%b %%Y, %%H:%%M' >> %s\n" % (self.pipe_data["log_file"]))
            script_fh.write("echo '\\t\\tCompleted deleting all jobs with 99.qdel_all.csh' >> %s\n\n\n" % (self.pipe_data["log_file"]))
              
    def create_qalter_script(self):
        """ This function creates the 98.qalter_all script
        """
        
        self.qalter_script_name = self.pipe_data["scripts_dir"] + "98.qalter_all.csh"

        with open(self.qalter_script_name, "w") as script_fh:
            script_fh.write("#!/bin/csh\n\n")
            for step in self.step_list:
                if step.get_depend_list():      # The step has dependencies:
                    script_fh.write("qalter \\\n\t-hold_jid %s \\\n\t%s\n\n" % (",".join(step.get_dependency_jid_list()), step.get_qsub_name()))
              
    def create_log_file(self):
        
        # Set log file name in pipe_data
        self.pipe_data["log_file"] = "".join([self.pipe_data["logs_dir"], "log_" ,  self.pipe_data["run_code"] , ".txt"])

        # Initialize log file with current datetime:
        # Only if file does not exist yet. This is to enable rerunning with the same runcode
        if not os.path.exists(self.pipe_data["log_file"]):
            with open(self.pipe_data["log_file"],"w") as logf:
                logf.write("""
Pipeline %(run_code)s logfile:
----------------

%(datetime)s:   Pipeline %(run_code)s created.

""" % \
                {"datetime" : datetime.now().strftime("%d %b %Y, %H:%M"),\
                 "run_code" : self.pipe_data["run_code"]})
            
                if(self.pipe_data["message"] != None):
                    logf.write("Message: %s\n" % self.pipe_data["message"])
                else:
                    logf.write("Message: No message passed for this pipeline\n")  # This is here to keep the number of header lines constant. The reason - R reading the log file for graphing!
    
                logf.write("""
Timestamp\tEvent\tModule\tInstance\tJob name\tLevel\tHost\tMax mem
""")

                
        # Set file name for storing list of pipeline versions:
        self.pipe_data["version_list_file"] = "".join([self.pipe_data["logs_dir"], "version_list.txt"])
        # Initialize log file with current datetime:
        # Only if file does not exist yet. This is to enable rerunning with the same runcode
        if not os.path.exists(self.pipe_data["version_list_file"]):
            with open(self.pipe_data["version_list_file"],"a") as logf:
                logf.write("%s\t%s\n" % (self.pipe_data["run_code"], self.pipe_data["message"]))


            
    def create_registration_file(self):
        """
        """
        # Set log file name in pipe_data
        self.pipe_data["registration_file"] = "".join([self.pipe_data["logs_dir"], "file_registration.txt"])
        # If file does not exist, initialize it:
        if not os.path.isfile(self.pipe_data["registration_file"]):
            with open(self.pipe_data["registration_file"],"w") as regist_f:
                regist_f.write("""# Registration of files created in this pipeline:
Date\tStep\tName\tScript\tFile\tmd5sum\n
""")
              
              

    def get_dict_encoding(self):
        """ Returns a dict representation of the pipeline.
        """
        
        ret_dict = dict()
        ret_dict["sample_data"] = self.sample_data
        ret_dict["pipe_data"] = self.pipe_data
        ret_dict["global_params"] = self.param_data["Global"]
        ret_dict["step_data"] = {step.get_step_name():step.get_dict_encoding() for step in self.step_list}
        
        return ret_dict
        
        
    def get_json_encoding(self):
        """ Convert pipeline data into JSON format
        """
        return json.dumps(self.get_dict_encoding(), sort_keys = False, indent = 4, separators=(',', ': '))
        
    def get_qsub_names_json_encoding(self):
        """ Convert qsub names dict into JSON format
        """
        
        dict_to_dump = {step.get_step_name():step.get_qsub_names_dict() for step in self.step_list}
        return json.dumps(dict_to_dump, sort_keys = False, indent = 4, separators=(',', ': '))
        
        
        
    def backup_source_files(self, param_file, sample_file):
        """
        Copies the parameter and sample files for backup in 'backups' directory
        """
        # param_file and sample_file can be a comma separated lists, so backing up all files:
        filenames = param_file.split(",")
        i = 0
        for filename in filenames:
            shutil.copyfile(filename, "%s%s_params_%d.txt" % (self.pipe_data["backups_dir"], \
                                                                self.pipe_data["run_code"], \
                                                                i))
            i += 1

        filenames = sample_file.split(",")
        i = 0
        for filename in filenames:
            shutil.copyfile(filename, "%s%s_samples_%d.txt" % (self.pipe_data["backups_dir"], \
                                                                self.pipe_data["run_code"], \
                                                                i))
            i += 1
        
        modules_bck_dir = "{bck_dir}{run_code}".format(bck_dir = self.pipe_data["backups_dir"], \
                                                       run_code = self.pipe_data["run_code"]) 
        if not os.path.exists(modules_bck_dir):
            os.mkdir(modules_bck_dir)
        
        

        
    def create_js_graphic(self):
        """ Use http://bl.ocks.org/mbostock/1153292 to make graphic of pipeline
        """
        
 
        links_part = []

        # For each step, create text encoding of connection between it and all it's base steps.
        # Print links_part to see what it looks like
        for step in self.step_list:
            if step.get_base_step_name():
                for base_step in step.get_base_step_list():
                    links_part.append("{source: \"%s(%s)\", target: \"%s(%s)\", type: \"dependency\"}" % \
                                    (base_step.get_step_name(),\
                                    base_step.get_step_step(),\
                                    step.get_step_name(),\
                                    step.get_step_step()))
        links_part = "\n,".join(links_part)

        
        html_text = """<!DOCTYPE html>
<meta charset="utf-8">
<style>

.link {
  fill: none;
  stroke: #666;
  stroke-width: 1.5px;
}

#dependency {
  fill: green;
}

.link.dependency {
  stroke: green;
}


circle {
  fill: #ccc;
  stroke: #333;
  stroke-width: 1.5px;
}

text {
  font: 10px sans-serif;
  pointer-events: none;
  text-shadow: 0 1px 0 #fff, 1px 0 0 #fff, 0 -1px 0 #fff, -1px 0 0 #fff;
}

</style>
<body>
<script src="%(d3_loc)s"></script>
<script>

var links = [
%(links_p)s  
];

var nodes = {};

// Compute the distinct nodes from the links.
links.forEach(function(link) {
  link.source = nodes[link.source] || (nodes[link.source] = {name: link.source});
  link.target = nodes[link.target] || (nodes[link.target] = {name: link.target});
});

var width = 960,
    height = 500;

var force = d3.layout.force()
    .nodes(d3.values(nodes))
    .links(links)
    .size([width, height])
    .linkDistance(60)
    .charge(-300)
    .on("tick", tick)
    .start();

var svg = d3.select("body").append("svg")
    .attr("width", width)
    .attr("height", height);

// Per-type markers, as they don't inherit styles.
svg.append("defs").selectAll("marker")
    .data(["suit", "dependency", "resolved"])
  .enter().append("marker")
    .attr("id", function(d) { return d; })
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 15)
    .attr("refY", -1.5)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
  .append("path")
    .attr("d", "M0,-5L10,0L0,5");

var path = svg.append("g").selectAll("path")
    .data(force.links())
  .enter().append("path")
    .attr("class", function(d) { return "link " + d.type; })
    .attr("marker-end", function(d) { return "url(#" + d.type + ")"; });

var circle = svg.append("g").selectAll("circle")
    .data(force.nodes())
  .enter().append("circle")
    .attr("r", 12)
    .call(force.drag);

// Change color of first circle to red (root of pipeline)
svg.select("circle").style("fill","red")

var text = svg.append("g").selectAll("text")
    .data(force.nodes())
  .enter().append("text")
    .attr("x", 8)
    .attr("y", ".31em")
    .text(function(d) { return d.name; });

// Use elliptical arc path segments to doubly-encode directionality.
function tick() {
  path.attr("d", linkArc);
  circle.attr("transform", transform);
  text.attr("transform", transform);
}

function linkArc(d) {
  var dx = d.target.x - d.source.x,
      dy = d.target.y - d.source.y,
      dr = Math.sqrt(dx * dx + dy * dy),
      dist_ratio = 0.88;
  return "M" + d.source.x + "," + d.source.y + "L" + (d.source.x + dx*dist_ratio) + "," + (d.source.y + dy*dist_ratio);
//  return "M" + d.source.x + "," + d.source.y + "L" + d.target.x + "," + d.target.y;
//  return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
}

function transform(d) {
  return "translate(" + d.x + "," + d.y + ")";
}

</script>  """ % {"links_p":links_part, "d3_loc":"https://d3js.org/d3.v3.min.js"}
        
        with open(self.pipe_data["objects_dir"]+os.sep+"WorkflowGraph.svg.html" , "w") as pipejs:
            pipejs.write(html_text)
            
            
            
            
            
    def create_log_plotter(self):
    

        with open(self.pipe_data["logs_dir"] + "log_file_plotter.R", "w") as log_plot:
            log_plot.write(""" 
library(reshape2); library(googleVis); args <- commandArgs(trailingOnly =T);log_file <- read.delim(args[1],skip = 8, he=T,stringsAsFactors = F);parsed_log_file <- dcast(data = log_file, formula = Module+Instance+Job.name~Event, value.var = "Timestamp", fun.aggregate = function(x) x[1]);parsed_log_file$Started <- as.POSIXct(parsed_log_file$Started, tz = "", format="%d/%m/%Y %H:%M:%S ");parsed_log_file$Finished <- as.POSIXct(parsed_log_file$Finished, tz = "", format="%d/%m/%Y %H:%M:%S ");parsed_log_file <- parsed_log_file[not(is.na(parsed_log_file$Finished)|is.na(parsed_log_file$Started)),];parsed_log_file <- parsed_log_file[order(parsed_log_file$Started),];color_leg <- substring(rainbow(length(unique(parsed_log_file$Module))),first = 1,last = 7);names(color_leg) <- unique(parsed_log_file$Module);plotcolors <- sprintf("[%s]",paste(paste("'",color_leg[parsed_log_file$Module],"'",sep=""),collapse = ","));Timeline <- gvisTimeline(data=parsed_log_file, rowlabel="Instance", barlabel="Job.name", start="Started", end="Finished", options=list(timeline="{groupByRowLabel:false}", backgroundColor='#ffd', height=800, width=1000, colors=plotcolors));print(x = Timeline, tag=NULL, file = sprintf("%s.html",args[1]));## https://github.com/al2na/Rmarkdown_JSviz/blob/master/googleVis.Rmd


""")

# Code to add to Rscript above to convert datetime values into absolute time:
# parsed_log_file$Started_numeric <- as.numeric(parsed_log_file$Started);PL_start <- min(parsed_log_file$Started_numeric);parsed_log_file$Started_numeric <- parsed_log_file$Started_numeric - PL_start;parsed_log_file$Finished_numeric <- as.numeric(parsed_log_file$Finished);parsed_log_file$Finished_numeric <- parsed_log_file$Finished_numeric - PL_start;parsed_log_file$Started_numeric <- parsed_log_file$Started_numeric * 1000; parsed_log_file$Finished_numeric <- parsed_log_file$Finished_numeric * 1000;

    def create_diagrammer_graphic(self):

        # colors = "darkgreen darkred firebrick4 forestgreen saddlebrown blue2 deepskyblue4 brown green1 gold4 salmon4 darkorchid4 olivedrab4 lightsalmon4 palevioletred4 palegreen4 orangered lightpink4 tomato3 orchid4"
        # colors = "rosybrown2 lightsteelblue darkseagreen1 gray87 navajowhite lemonchiffon bisque2 mistyrose gray95 lightcyan3 peachpuff2 lightsteelblue2 thistle2 lightyellow2 moccasin antiquewhite2 gray80"
        colors = "lightskyblue3 lightpink2 plum3 burlywood3 pink2 mediumturquoise darkseagreen palegreen3 aquamarine3 skyblue3 lightsteelblue darkkhaki lightseagreen rosybrown3"
        colors = colors.split(" ")
        color_counter = 0
        links_part = []
        footnote_part = []
        nodes_list = []
        nodes_list_step = []
        step_colors_index = dict()
        # For each step, create text encoding of connection between it and all it's base steps.
        # Print links_part to see what it looks like
        for step in self.step_list:
            # Add base_step to dict of nodes, if not yet existing
            if step.get_step_name() not in nodes_list:
                nodes_list.append(step.get_step_name())
                nodes_list_step.append(step.get_step_step())
            # Storing color for step type:
            if step.get_step_step() not in step_colors_index.keys():
                step_colors_index[step.get_step_step()] = colors[color_counter]
                color_counter = (color_counter+1) % len(colors)
                
            if step.get_base_step_name():
                for base_step in step.get_base_step_list():
                    
                    
                    # Add base_step to dict of nodes, if not yet existing
                    if base_step.get_step_name() not in nodes_list:
                        nodes_list.append(base_step.get_step_name())
                        nodes_list_step.append(base_step.get_step_step())
                    # Storing color for step type:
                    if base_step.get_step_step() not in step_colors_index.keys():
                        step_colors_index[base_step.get_step_step()] = colors[color_counter]
                        color_counter = (color_counter+1) % len(colors)

                    
                    links_part.append("%d -> %d" % (1+nodes_list.index(base_step.get_step_name()),\
                                                    1+nodes_list.index(step.get_step_name())))
                    
                    
                    
                    
        links_part = "\n".join(links_part)
        nodes_part = "\n".join(["%(node_num)d [label = '@@%(node_num)d', fillcolor = %(step_col)s]" % \
                                {"node_num" : 1+counter,  \
                                 "step_col" : step_colors_index[nodes_list_step[counter]]} \
                                    for counter,step in enumerate(nodes_list)])
        footnote_part = "\n".join(["[%d]: '%s\\\\n(%s)'" % (1+counter, step, nodes_list_step[counter]) \
                                    for counter,step in enumerate(nodes_list)])
        
        Gviz_text =  """
# Check if required packages are installed:
if(!(all(c("DiagrammeR","htmlwidgets") %%in%% installed.packages()))) {
    cat("'DiagrammeR' and 'htmlwidgets' are not installed.\nYou must install them for this script to work!\nInstall by running the following commands:\ninstall.packages('DiagrammeR')\ninstall.packages('htmlwidgets')")
}
library(DiagrammeR)
library(htmlwidgets)        
        
        
myviz <- grViz("
digraph a_nice_graph {
      
      # node definitions with substituted label text
      node [shape = egg, style = filled, fontname = Helvetica]
      %(nodes_p)s
      
      # edge definitions with the node IDs
      %(links_p)s
      }

      %(foot_p)s
      ")
      
      saveWidget(myviz,file = "%(out_file_name)s",selfcontained = F)
      
""" % { "nodes_p" : nodes_part,
        "links_p" : links_part,
        "foot_p"  : footnote_part,
        "out_file_name" : self.pipe_data["objects_dir"] + "WorkflowGraph.html"}
        
        with open(self.pipe_data["objects_dir"] + "diagrammer.R" , "w") as diagrammer:
            diagrammer.write(Gviz_text)
                
                
                