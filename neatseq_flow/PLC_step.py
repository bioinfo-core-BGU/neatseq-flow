
""" A class defining a step in the pipeline.

"""
import os, shutil, sys, re
import traceback
import datetime


from copy import *
from pprint import pprint as pp
from matplotlib.cbook import get_sample_data

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"



class AssertionExcept(Exception):
    """A class to be raised by modules failing at assertions
    """
    def __init__(self, comment = "Unknown problem", sample = None, step = None):
        """initializize with error comment and sample, if exists)
        """
        self.sample = sample
        self.comment = comment
        self.step = step
        
    def get_error_str(self, step_name = None):
        
        if self.sample: # If a sample was passed. The exception is specific to a sample
            return "ERROR  : In %s (sample %s): %s" % (step_name, self.sample, self.comment)
        elif not step_name:
            if self.step:
                return "ERROR  : In %s: %s" % (self.step, self.comment)
            else:
                return "ERROR  : %s" % (self.comment)
        else:       
            return "ERROR  : In %s: %s" % (step_name, self.comment)
        

class Step:
    """ A class that defines a pipeline step name (=instance).
    """
    Cwd = os.path.dirname(os.path.abspath(__file__))

    @classmethod
    def find_step_module(self,step,param_data, pipe_data):
        """ A class method for finding the location of a module for a given step
        """

        def walkerr(err):
            """ Helper function for os.walk below. Catches errors during walking and reports on them.
            """
            print "WARNING: Error while searching for modules:"
            print  err

#===============================================================================
#         # This will automatically load modules installed in "conda"
#         # It adds the default path ($CONDA_PREFIX/lib/python2.7/site-packages/neatseq_flow_modules) to modules_path
#         if "conda" in pipe_data:
#             if "CONDA_PREFIX" in os.environ:
# #                print "--%s--" % os.environ["CONDA_PREFIX"]
#                 conda_module_path = os.path.join(os.environ["CONDA_PREFIX"], "lib/python2.7/site-packages/neatseq_flow_modules")
#                 sys.stderr.write("ATTENTION: Adding conda default additional modules path (%s). If it is different, please add manually to 'module_path' in 'Global_params'." % conda_module_path)
#                 if "module_path" in param_data["Global"]:
#                     if conda_module_path not in param_data["Global"]["module_path"]:
#                         param_data["Global"]["module_path"].append(conda_module_path)
#                 else:
#                     param_data["Global"]["module_path"] = [os.path.join(conda_module_path)]
#  #               print param_data["Global"]["module_path"]
#===============================================================================



            
        # Searching module paths passed by user in parameter file:
        if "module_path" in param_data["Global"]:
            for module_path_raw in param_data["Global"]["module_path"]:#.split(" "):
                # Remove trainling '/' from dir name. For some reason that botches things up!
                module_path = module_path_raw.rstrip(os.sep)

                # Expanding '~' and returning full path 
                module_path = os.path.realpath(os.path.expanduser(module_path))
                

                # Check the dir exists:
                if not os.path.isdir(module_path):
                    sys.stderr.write("WARNING: Path %s from module_path does not exist. Skipping...\n" % module_path)
                    continue

                

                    
                mod_t = step
                dir_generator = os.walk(module_path, onerror = walkerr)       # Each .next call on this generator returns a level tuple as follows:
                try:
                    level = dir_generator.next()           # level is a tuple with: (current dir. [list of dirs],[list of files])
                except StopIteration:
                    sys.stderr.write("WARNING: Module path %s seems to be empty! Possibly issue with permissions..." % module_path)
                while(mod_t + ".py" not in level[2]):     # Repeat while expected filename is NOT in current dir contents (=level[2]. see above)
                    try:
                        level = dir_generator.next()    # Try getting another level    
                    except StopIteration:
#                        print "Step %s not found in path %s." % (mod_t,module_path)
                        break # Leave while without executing "else"
                else:
                    # Adding module_path to search path
                    if module_path not in sys.path:
                        sys.path.append(os.path.abspath(module_path))

                    # For what this does, see below (# Build module name)...

                    # Backup module to backups dir:
                    shutil.copyfile(level[0] + os.sep + mod_t + ".py", \
                        "{bck_dir}{runcode}{ossep}{filename}".format(bck_dir = pipe_data["backups_dir"], \
                                                                     runcode = pipe_data["run_code"], \
                                                                     ossep = os.sep, \
                                                                     filename = mod_t + ".py"))
                    retval = (level[0].split(module_path)[1].partition(os.sep)[2].replace(os.sep,".") + "." + mod_t).lstrip(".")
                    return retval


        # If not found, do the same with self.Cwd:
        mod_t = step
        dir_generator = os.walk(self.Cwd, onerror = walkerr)     # Each .next call on this generator returns a level tuple as follows:
        try:
            level = dir_generator.next()           # level is a tuple with: (current dir. [list of dirs],[list of files])
        except StopIteration:
            sys.stderr.write("WARNING: Module path %s seems to be empty! Possibly issue with permissions..." % self.Cwd)

        while(mod_t + ".py" not in level[2]):     # Repeat while expected filename is NOT in current dir contents (=level[2]. see above)
            try:
                level = dir_generator.next()    # Try getting another level    
            except StopIteration:
                sys.exit("Step %s not found in regular path or user defined paths." % mod_t)
        
        # Build module name:
        # 1. take dir found in search
        # 2. split it by CWD and take 2nd part,  i.e. remove cwd from dir name...
        # 3. partition by os.sep to remove leading os.sep
        # 4. replace remaining os.sep's by ".". 
        # 5. Add .
        
        # Backup module to backups dir:
        shutil.copyfile(level[0] + os.sep + mod_t + ".py", \
                        "{bck_dir}{runcode}{ossep}{filename}".format(bck_dir = pipe_data["backups_dir"], \
                                                                     runcode = pipe_data["run_code"], \
                                                                     ossep = os.sep, \
                                                                     filename = mod_t + ".py"))
        retval = level[0].split(self.Cwd)[1].partition(os.sep)[2].replace(os.sep,".") + "." + mod_t
        return retval
        # return level[0].split(self.Cwd)[1].partition(os.sep)[2].replace(os.sep,".") + "." + mod_t

        
    def __init__(self,name,step_type,params,pipe_data):
        """ should not be used. only specific step inits should be called. 
            Maybe a default init can be defined as well. check.
        """
        self.name = name
        self.step = step_type
        self.params = params
        self.pipe_data = pipe_data
        
        ###### Place for testing parameters:
        try:
            self.params["script_path"]
        except KeyError:
            sys.exit("You must supply a script_path parameter in %s\n" % self.name)

        self.base_dir = self.pipe_data["data_dir"] + self.step + os.sep + self.name + os.sep
        # Move to general init function:
        # Make dir for $qsub_name results
        if not os.path.isdir(self.base_dir):
            self.write_warning("Making dir for results of %s at %s \n" % (self.name,self.base_dir), admonition = "ATTENTION")
            os.makedirs(self.base_dir) 
        else:
            pass
            # TODO: Do the following only if verbose is set:
            # sys.stderr.write("Dir %s exists for results of %s \n" % (self.base_dir,self.name))

        # -----------------------------------------------------
        # Testing 'conda' parameters

        if "conda" in self.pipe_data and "conda" not in self.params: # Only global "conda" params defined:
            self.params["conda"] = self.pipe_data["conda"]
        if "conda" in self.params:
            if not self.params["conda"]:
                self.write_warning("'conda' is provided but empty. Not 'activating' for this step")
            else:  # Conda is not empty
                if "path" not in self.params["conda"] or "env" not in self.params["conda"]:
                    raise AssertionExcept("'conda' must include 'path' and 'env'", step=self.get_step_name())

                elif filter(lambda x: x not in ["path","env"],self.params["conda"].keys()):
                    self.write_warning("You provided extra 'conda' parameters. They will be ignored!")
                else:
                    pass
                
                
                if not self.params["conda"]["path"]: # == None:  # Path is empty (None or "", take from $CONDA_PREFIX
                    if "CONDA_PREFIX" in os.environ:
                        # CONDA_PREFIX is: conda_path/'envs'/env_name
                        # First split gets the env name
                        # Second split gets the conda_path and adds 'bin'
                        (t1,env) = os.path.split(os.environ["CONDA_PREFIX"])
                        self.params["conda"]["path"] = os.path.join(os.path.split(t1)[0],"bin")
                        if  not self.params["conda"]["env"]: ##==None:
                            self.params["conda"]["env"] = env
        
                    else:
                        raise AssertionExcept("'conda' 'path' is empty, but no CONDA_PREFIX is defined. Make sure you are in an active conda environment.",step=self.get_step_name())
                        
                elif not self.params["conda"]["env"]:# == None:
                    if "conda" in self.pipe_data:
                        self.params["conda"]["env"] = self.pipe_data["conda"]["env"]
                        self.write_warning("No 'env' supplied for 'conda'. Using global 'env'")
                    else: 
#                        sys.stderr.write
                        raise AssertionExcept("'conda' 'path' is defined, but no 'env' was passed in step or global parameters.", step=self.get_step_name())
        # -----------------------------------------------------
  
                                                    
        # Setting qsub options in step parameters:
        self.manage_qsub_opts()
       
        
        self.jid_list = []      # Initialize a list to store the list of jids of the current step
        
        # The following line defines A list of jids from current step that all other steps should depend on.
        # Is used to add a prelimanry step, equivalent to the "wrapping up" step that is dependent on all previous scripts
        self.preliminary_jids =[]  

        self.skip_scripts = False   # This is supposed to enable steps to avoid script building by setting to True.
                                    # See for example del_type and move_type

        # Catch exceptions of type AssertionExcept raised by the specific initiation code
        try:
            self.step_specific_init()
        except AssertionExcept as assertErr:
            print assertErr.get_error_str(self.get_step_name())
            raise
        
        
        # Create a list for filenames to register with md5sum for each script:
        self.stamped_files = list()
        # self.stamped_dirs = list()

        # Create a dictionary storing the step name and names of sub-scripts
        # Will then be queried by main to create a general dictionary which can be written to json and used for remote run monitor
        self.qsub_names_dict = dict()


                                    
    def __str__(self):
        """ Print a summary of the class: name, step and depend list
        """
        
        return "Name: %(name)s\nStep: %(step)s\nBase %(base)s\nDependencies %(depends)s" % \
                {"name"   : self.name, \
                "step"    : self.step, \
                "base"    : self.get_base_step_list, \
                "depends" : self.get_depend_list()}
        
    def write_warning(self, warning = "Unknown problem", sample = None, admonition = "WARNING"):
        """ Write a warning when doing something that might be foolish.
            If the foolishness is sample-specific, pass the sample as an argument
        """
        if self.pipe_data["verbose"]:   # At the moment not set anywhere. Maybe in the future

            if sample: # If a sample was passed. The exception is specific to a sample
                sys.stderr.write("%s: In %s (sample %s): %s\n" % (admonition, self.get_step_name(), sample, warning))
            else:
                sys.stderr.write("%s: In %s: %s\n" % (admonition, self.get_step_name(), warning))
        
        
    
    def get_depend_list(self):
        return self.params["depend_list"]
        
    def get_step_step(self):
        return self.step

    def get_step_name(self):
        return self.name
        
    def get_base_step_name(self):
        """ Return name of base step for this step.
            Used by pipeline class to send the base step class
        """
        try:
            return self.params["base"]
        except KeyError:
            return None
            
    def set_base_step(self,base_step_list):
        """ Sets the base step for the current step
            This is the class of the base step, not just the name
            NOTE: This is a bit convoluted. This shoud be set only for the low level step classes
        """
        # Check the base step is a valid Step object:
        # assert isinstance(base_step,Step) or base_step==None
        
        # base list version: Check all bases in base list are valid Step objects:
        # The map-reduce pair do the following:
        #   map - check each element in base_step (now a list...) is a legitimate Step object (returns a list of booleans for each step)
        #   all() = make sure all map comparisons are True.
        # print "base step for %s (in Step):\n------------\n" % self.name
        # print base_step_list

        # assert base_step_list == [] or all(map(lambda x: isinstance(x,Step), base_step_list)), "For some reason, step %s has an invalid base list." % self.name
        if base_step_list != [] and not all(map(lambda x: isinstance(x,Step), base_step_list)):
            raise AssertionExcept("Invalid base list\n")
        
        try:
            self.base_step_list
        except AttributeError:
            # Good. Does not exist
            self.base_step_list = base_step_list if base_step_list else None  # Set merge base_step to None and all others to base_step
            # While at it, update sample_data according to new base_step
            if self.base_step_list:  # Do the following only if base_step is not None (= there is a base step. all except merge)
                # sys.stderr.write("setting sample data for %s \n" % self.name)
                # self.set_sample_data(self.base_step_list[0].get_sample_data())
                self.set_sample_data()  # Uses self.base_step_list
                
                
        else:
            raise AssertionExcept("Somehow base_step is defined more than once", self.get_step_name())
        
    def get_base_step_list(self):
        try:
            return self.base_step_list
        except AttributeError:
            sys.exit("base_step not found in %s\n" % (self.name))
            
## Comprison methods
    
    def __lt__(self,other):
        """ A step is _lt_ than 'other' if it is in 'other's list of dependencies or if it has a shorter dependency list.
            Is used by the sort function to sort the steps in a correct running order
            A side effect is that parallel branches are sorted top-down rather than branch-wise.
            You can redefine the 'sort' method in Pipeline class to change this behaviour.
        """
        if self.name in other.get_depend_list():
            return True
        if other.name in self.get_depend_list():
            return False
        if len(self.get_depend_list()) < len(other.get_depend_list()):
            return True
        if len(self.get_depend_list()) > len(other.get_depend_list()):
            return False
        if self.get_step_name() < other.get_step_name():
            return True
        if self.get_step_name() > other.get_step_name():
            return False
        return NotImplemented 
        
    def __gt__(self,other):
        """ See doc string for __lt__
        """
        if self.name in other.get_depend_list():
            return False
        if other.name in self.get_depend_list():
            return True
        if len(self.get_depend_list()) > len(other.get_depend_list()):
            return True
        if len(self.get_depend_list()) < len(other.get_depend_list()):
            return False
        if self.get_step_name() > other.get_step_name():
            return True
        if self.get_step_name() < other.get_step_name():
            return False
        return NotImplemented 
        
        
    def set_step_number(self,step_number):
        """ Sets the number of the step in the step list. 
            Is used in naming the scripts, so that they can be sorted with 'll'
        """
        assert isinstance(step_number, int)
        self.step_number = "{:0>2}".format(step_number)
        # If number is added/updated, the script name must be initialized/updated
        self.set_script_name()
        
        
    def set_script_name(self):
        """ Defines the name of the step script (level 2. Appears in qsub command in 00.pipe.commands.csh )
        """
        self.script_name = "{!s}.{!s}_{!s}.{!s}".format(self.step_number,self.step,self.name,"csh" if self.shell=="csh" else "sh")
        return self.script_name

    def get_script_name(self):
        return self.script_name
        

    def get_sample_data(self):
        return self.sample_data
        
    def get_base_sample_data(self):
        """ Get base_sample_data
        """
        return self.base_sample_data
        
    def sample_data_merge(self, sample_data, other_sample_data, other_step_name):
        """ Merge a different sample_data dict into this step's sample_data
            Used for cyclic sungrebe - basing a step on more than one base.
        """
        # new_smpdt = deepcopy(smpdt)

        for k, v in other_sample_data.iteritems():
            # print smpdt
            # print "\n\n"
            if (k in sample_data):
                if (isinstance(sample_data[k], dict) 
                    and isinstance(other_sample_data[k], dict)):
                    sample_data[k] = self.sample_data_merge(sample_data[k], other_sample_data[k], other_step_name)
                else:
                    # Do nothing, but check not discarding values from other_sample_data
                    if (sample_data[k] != other_sample_data[k]):
                        self.write_warning("There is a difference from %s in key %s\n" % (other_step_name, k))
            else:
                sample_data[k] = deepcopy(other_sample_data[k])
        
        return sample_data
        
    
    def set_sample_data(self, sample_data = None):
        """ Sets the sample_data. 
            This cannot be done in constructor because it depends on the output from previous steps.
            Uses self.base_step_list
        """


        # Preparing dict to store sample_data of bases:
        # This is not usually used but might be handy when you need more than one bam, for instance (see below)

        if sample_data != None:     # When passing sample_data (i.e. for merge)
            # Copying sample_data. Just '=' would create a kind of reference
            self.sample_data = deepcopy(sample_data)
            self.base_sample_data = dict()  
        else:   # Extract sample_data from base steps:
            self.sample_data = dict()

            for base_step in self.base_step_list:
                # Merge sample_data from all base steps.
                # Function sample_data_merge uses deepcopy as well
                self.sample_data = self.sample_data_merge(self.get_sample_data(),
                                                          base_step.get_sample_data(),
                                                          base_step.get_step_name())


            # Storing sample_data from base_step in base_sample_data dict:
            # This might be used when more than one copy of sample_data is required, for instance
            #   one might need two bam files.
            self.base_sample_data = dict()

            for base_step in self.base_step_list:
                # Update current base_sample_data to include base's base_sample_data
                # This effectively merges bases base_sample_data into this step's base_sample_data
                self.base_sample_data.update(base_step.get_base_sample_data())
                # Add the base sample_data to this step's base_sample_data:
                self.base_sample_data[base_step.get_step_name()] = deepcopy(base_step.get_sample_data())

        # Limit operation to sample_list only
        if "sample_list" in self.params:
            if self.params["sample_list"] == "all_samples":
                self.sample_data["samples"] = self.pipe_data["samples"]
            else:
                self.sample_data["samples"] = re.split("[, ]+", self.params["sample_list"])
            
            # print(self.sample_data["samples"])
            # sys.exit()
            # self.sample_data[samples]
            
        # Trying running step specific sample initiation script:
        try:
            self.step_sample_initiation()
        except AttributeError:
            pass    # It dosen't have to be defined.
        except AssertionExcept as assertErr: 
            # An error was raised during specific sample initiation
            print assertErr.get_error_str(self.get_step_name())
            raise


            

    def get_qsub_name(self):
        """ Return the jid id of the current step
        """
        self.spec_qsub_name = "_".join([self.step,self.name,self.pipe_data["run_code"]])
        return self.spec_qsub_name
        
    def set_spec_script_name(self,sample=None):
        """ Sets the current spec_script_name to a regular name, i.e.:
                sample level: "_".join([self.step,self.name,sample])
                project level: "_".join([self.step,self.name,self.sample_data["Title"]])
            In the build_scripts function, run:
                sample level: self.set_spec_script_name(sample)
                project level: self.set_spec_script_name()
            If using a different level of paralleization, see e.g. VCFtools, 
                you can set your own self.spec_script_name.
                
        """
        
        if sample:
            self.spec_script_name = "_".join([self.step,self.name,sample])
        else:
            self.spec_script_name = "_".join([self.step,self.name,self.sample_data["Title"]])

        return self.spec_script_name
        
        
        
    def add_jid_to_jid_list(self):
        """ Adds a jid for a sub process (e.g. a sample-specific script) to the jid list of the current step
        """
        
        self.jid_list.append(self.spec_qsub_name)
        
        
    def get_jid_list(self):
        """ Return list of jids
            To be used by pipeline for creating the delete function (99.del...)
        """
        
        return self.jid_list
        
    def get_dependency_jid_list(self):
        """ Returns the list of jids of all base steps
            Recursion. beware!
        """
        
        depend_jid_list = []
        
        if self.base_step_list:
            for base_step in self.base_step_list:
                depend_jid_list += (base_step.get_jid_list() + base_step.get_dependency_jid_list())

        return depend_jid_list
        
        
    def create_low_level_script(self):
        """ Create the low (i.e. 3rd) level scripts, which are the scripts that actually do the work
            The actual part of the script is produced by the particular step class.
            This function is responsible for the generic part: opening the file and writing the qsub parameters and the script
        """
        # Name of specific qsub command:
        self.spec_qsub_name = self.spec_script_name
        # Adding path to spec_script_name: 
        self.spec_script_name = os.path.join(self.step_scripts_dir, \
                                             ".".join([self.step_number,self.spec_script_name,"csh" if self.shell=="csh" else "sh"])) 
        self.spec_qsub_name = "_".join([self.spec_qsub_name,self.pipe_data["run_code"]])

        
        self.add_jid_to_jid_list()  # Adds spec_qsub_name to jid_list
        
        # Add qsub headers to the script:
            # Decide wether to use csh or bash
            # determine queue and nodes
            # User-defined qsub opts
            # Dependencies: DONE: use self.get_dependency_jid_list()
        
        # DONE. Update list of jids for this step (maybe different function)
        # Add jid to list of jids in pipe_data for process deletion script. TO BE DONE IN PIPELINE, NOT HERE! USE get_jid_list() METHOD FOR THIS! 
        
        # Print script to level 3 script file
        
        # Get dependency jid list and add prelimanry jids if exist 
            # (if not, is an empty list and will not affect the outcome)
        dependency_jid_list = self.get_dependency_jid_list() + self.preliminary_jids  
        
        # Create header with dependency_jid_list:
        qsub_header = self.make_qsub_header(jid_list = ",".join(dependency_jid_list) if dependency_jid_list else None)
        
        # Without logging:
        # self.script = qsub_header + self.script
        # With logging:
        self.script = "\n".join([qsub_header,                                                       \
                                self.create_log_lines(self.spec_qsub_name,"Started", level="low"),  \
                                self.add_qdel_line(type="Start"),                                   \
                                self.create_activate_lines(type = "activate"),                      \
                                self.script,                                                        \
                                self.register_files(self.spec_qsub_name),                           \
                                self.create_activate_lines(type = "deactivate"),                    \
                                self.add_qdel_line(type="Stop"),                                    \
                                self.create_log_lines(self.spec_qsub_name,"Finished", level="low")])
        


        # sys.stdout.write(self.spec_script_name + "\n")
        with open(self.spec_script_name, "w") as script_fh:
            script_fh.write(self.script)
######
        
        if "job_limit" in self.pipe_data.keys():
           
            job_limit = """
# Sleeping while jobs exceed limit
perl -e 'use Env qw(USER); open(my $fh, "<", "%(limit_file)s"); ($l,$s) = <$fh>=~/limit=(\d+) sleep=(\d+)/; close($fh); while (scalar split("\\n",qx(%(qstat)s -u $USER)) > $l) {sleep $s; open(my $fh, "<", "%(limit_file)s"); ($l,$s) = <$fh>=~/limit=(\d+) sleep=(\d+)/} print 0; exit 0'

""" % {"limit_file" : self.pipe_data["job_limit"],\
            "qstat" : self.pipe_data["qsub_params"]["qstat_path"]}

            
            # Append the qsub command to the 2nd level script:
            with open(self.high_level_script_name, "a") as script_fh:
                script_fh.write(job_limit + "\n\n")        

#######            
        # Append the qsub command to the 2nd level script:
        # script_name = self.pipe_data["scripts_dir"] + ".".join([self.step_number,"_".join([self.step,self.name]),self.shell]) 
        with open(self.high_level_script_name, "a") as script_fh:
            script_fh.write("qsub " + self.spec_script_name + "\n\n")        
        
        # Adding to qsub_names_dict:
        self.qsub_names_dict["low_qsubs"].append(self.spec_qsub_name)
        
    def create_scripts_dir(self):
        """ Create a dir for storing the step scripts.
        """
        # Set script dir name:
        self.step_scripts_dir = self.pipe_data["scripts_dir"] + ".".join([self.step_number,"_".join([self.step,self.name])]) + os.sep
        # Create, if not existing 
        if not os.path.isdir(self.step_scripts_dir):
            self.write_warning("Making dir (%s) at %s \n" % (self.name,self.step_scripts_dir), admonition = "ATTENTION")
            os.makedirs(self.step_scripts_dir) 
        else:
            self.write_warning("Dir %s exists (step %s) \n" % (self.step_scripts_dir,self.name), admonition = "ATTENTION")

            
    def create_high_level_script(self):
        """ Create the high (i.e. 2nd) level scripts, which are the scripts that run the 3rd level scripts for the step
        """
        
        # Set script name for high level script:
        self.high_level_script_name = self.pipe_data["scripts_dir"] + ".".join([self.step_number,"_".join([self.step,self.name]),"csh" if self.shell=="csh" else "sh"]) 
        

        
        self.spec_qsub_name = self.get_qsub_name()   #"_".join([self.step,self.name,self.pipe_data["run_code"]])

        # Get dependency jid list and add prelimanry jids if exist 
            # (if not, is an empty list and will not affect the outcome)
        dependency_jid_list = self.get_dependency_jid_list() + self.preliminary_jids  
        
        # Create header with dependency_jid_list:
        qsub_header = self.make_qsub_header(jid_list   = ",".join(dependency_jid_list) if dependency_jid_list else None,\
                                            script_lev = "high")
        script = qsub_header

        # script += "# Adding line to log file:\n"
        # script += "set Date1 = `date '+%d/%m/%Y %H:%M:%S'`\n"
        # script += "echo $Date1 '\\tStarted step %s' >> %s\n\n\n" % (self.name, self.pipe_data["log_file"])
        
        # Storing name of high level script (only used for correct logging at "Finshed" step)
        self.high_spec_qsub_name = self.spec_qsub_name
        # Adding high-level jid to jid_list
        self.add_jid_to_jid_list()
        
        script = script + self.create_log_lines(self.high_spec_qsub_name, "Started", level = "high")
        
        with open(self.high_level_script_name, "w") as script_fh:
            script_fh.write(script)        
        
        # The actual qsub commands must be written in the create_low_level_script() function because they are step_name dependent!
            
        # Adding to qsub_names_dict:
        self.qsub_names_dict["step"] = self.get_step_step()
        self.qsub_names_dict["high_qsub"] = self.high_spec_qsub_name
        self.qsub_names_dict["low_qsubs"] = list()
        
            
    def close_high_level_script(self):
        """ Add lines at the end of the high level script:
        """

        script = "sleep %d\n\ncsh %s98.qalter_all.csh\n\n" % (self.pipe_data["Default_wait"], self.pipe_data["scripts_dir"])

        script = script + self.create_log_lines(self.high_spec_qsub_name, "Finished", level="high")
        
        with open(self.high_level_script_name, "a") as script_fh:
            script_fh.write(script)        

     
    def create_preliminary_script(self):
        """ Create a script that will run before all other low level scripts commence

        """

        #----- Define actual script here
        # Adding line to remove temporary folder:

        # Creating script. If 'create_spec_preliminary_script' is not defined or returns nothing, return from here without doing anything
        self.script = ""
        try:
            self.create_spec_preliminary_script()
        except AttributeError:
            return 

        if not self.script.strip():                 # If script is empty, do not create a wrapper function
            return 
        
        self.spec_qsub_name = "_".join([self.step,self.name,"preliminary"])

        self.spec_script_name = os.path.join(self.step_scripts_dir, \
                                             ".".join([self.step_number,self.spec_qsub_name,"csh" if self.shell=="csh" else "sh"])) 

                                             
        self.spec_qsub_name = "_".join([self.spec_qsub_name,self.pipe_data["run_code"]])
        
            
        # Get dependency jid list and add preliminary jids if exist (if not, is an empty list and will not affect the outcome)
        #    Also, add all jids of current step, as this script is to run only after all previous steps have completed.
        dependency_jid_list = self.get_dependency_jid_list() + self.get_jid_list()
        
        # Create header with dependency_jid_list:
        qsub_header = self.make_qsub_header(jid_list = ",".join(dependency_jid_list) if dependency_jid_list else None)
            
        # Orignal line: 
        # self.script = qsub_header +  self.script
        # New, with host reporting and time logging:
        self.script = "\n".join([qsub_header,                                                   \
                        self.create_log_lines(self.spec_qsub_name, "Started", level="prelim"),  \
                        self.create_activate_lines(type = "activate"),                          \
                        self.script,                                                            \
                        self.register_files(self.spec_qsub_name),                               \
                        self.create_activate_lines(type = "deactivate"),                        \
                        self.create_log_lines(self.spec_qsub_name, "Finished", level="prelim")])

                                

        with open(self.spec_script_name, "w") as script_fh:
            script_fh.write(self.script)
            
        # Append the qsub command to the 2nd level script:
        # script_name = self.pipe_data["scripts_dir"] + ".".join([self.step_number,"_".join([self.step,self.name]),self.shell]) 
        with open(self.high_level_script_name, "a") as script_fh:
            script_fh.write("qsub " + self.spec_script_name + "\n\n")        
            
        # This is here because I want to use jid_list to make wrapping_up script dependent on this step's main low-level scripts
        # Explantion: get_jid_list() was used above (line 'qsub_header...') to make the wrapping_up script dependent on the other scripts created by the step
        #    Now that that is done, the following line adds this step to the jid_list, so that subsequent steps are dependent on the wrapping up script as well. (I hope this makes it clear...)
        self.add_jid_to_jid_list()

        # Add the preliminary jid to the list of preliminary jids.  
        self.preliminary_jids.append(self.spec_qsub_name)

        # Adding to qsub_names_dict:
        self.qsub_names_dict["low_qsubs"].append(self.spec_qsub_name)

        
    def create_wrapping_up_script(self):
        """ Create a script that will run once all other low level scripts terminate
            Ideal place for putting testing and agglomeration procedures.
        """
        
        # Creating script. If 'create_spec_preliminary_script' is not defined or returns nothing, return from here without doing anything
        self.script = ""
        try:
            self.create_spec_wrapping_up_script()
        except AttributeError:
            return 

        if not self.script.strip():                 # If script is empty, do not create a wrapper function
            return 


        self.spec_qsub_name = "_".join([self.step,self.name,"wrapping_up"])

        self.spec_script_name = os.path.join(self.step_scripts_dir, \
                                             ".".join([self.step_number,self.spec_qsub_name,"csh" if self.shell=="csh" else "sh"])) 

        self.spec_qsub_name = "_".join([self.spec_qsub_name,self.pipe_data["run_code"]])
        
        #----- Define actual script here
        # Adding line to remove temporary folder:
        
            
        # Get dependency jid list and add prelimanry jids if exist (if not, is an empty list and will not affect the outcome)
        #    Also, add all jids of current step, as this script is to run only after all previous steps have completed.
        dependency_jid_list = self.get_dependency_jid_list() + self.preliminary_jids + self.get_jid_list()
        
        # Create header with dependency_jid_list:
        qsub_header = self.make_qsub_header(jid_list = ",".join(dependency_jid_list) if dependency_jid_list else None)
            
        # Orignal line: 
        # self.script = qsub_header +  self.script
        # New, with host reporting and time logging:
        self.script = "\n".join([qsub_header,                                                       \
                        self.create_log_lines(self.spec_qsub_name, "Started", level="wrapping"),    \
                        self.create_activate_lines(type = "activate"),                              \
                        self.script,                                                                \
                        self.register_files(self.spec_qsub_name),                                   \
                        self.create_activate_lines(type = "deactivate"),                            \
                        self.create_log_lines(self.spec_qsub_name, "Finished", level="wrapping")])


        with open(self.spec_script_name, "w") as script_fh:
            script_fh.write(self.script)
            
        # Append the qsub command to the 2nd level script:
        # script_name = self.pipe_data["scripts_dir"] + ".".join([self.step_number,"_".join([self.step,self.name]),self.shell]) 
        with open(self.high_level_script_name, "a") as script_fh:
            script_fh.write("qsub " + self.spec_script_name + "\n\n")        
            
        # This is here because I want to use jid_list to make wrapping_up script dependent on this step's main low-level scripts
        # Explantion: get_jid_list() was used above (line 'qsub_header...') to make the wrapping_up script dependent on the other scripts created by the step
        #    Now that that is done, the following line adds this step to the jid_list, so that subsequent steps are dependent on the wrapping up script as well. (I hope this makes it clear...)
        self.add_jid_to_jid_list()

        # Adding to qsub_names_dict:
        self.qsub_names_dict["low_qsubs"].append(self.spec_qsub_name)


            
    def create_all_scripts(self):
        """ Contains code to be done after build_scripts()
        """

        if not self.skip_scripts:
            try:
                
                # Create dir for storing step scripts:
                self.create_scripts_dir()
                
                # Create high (iu.e. 2nd) level script for the qsub commands
                self.create_high_level_script()

                # Add a preliminary script if it is defined in the step specific module
                self.create_preliminary_script()

                # Create actual scripts: NOTE: This function is defined in the individual step files!
                self.build_scripts()

                # Add a wrapping up script if it is defined in the step specific module
                self.create_wrapping_up_script()
                
                # Add closing lines to the high level script
                self.close_high_level_script()

            except AssertionExcept as assertErr:
                print assertErr.get_error_str(self.get_step_name())
                raise
    
        if "stop_and_show" in self.params:
            print "project slots:\n-------------"
            pp(self.sample_data.keys())
            print "sample slots:\n-------------"
            # all_sample_keys = list()
            # all_sample_keys = all_sample_keys.append(map(lambda x: self.sample_data[x].keys(), self.sample_data["samples"]))
            pp(self.sample_data[self.sample_data["samples"][0]].keys())
            # print all_sample_keys
            sys.exit("Showed. Now stopping. To continue, remove the 'stop_and_show' tage from %s" % self.get_step_name())
            
        
    def make_qsub_header(self, jid_list, script_lev = "low"):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """
        
        
        qsub_shell = "#!/bin/%(shell)s\n#$ -S /bin/%(shell)s" % {"shell": "csh" if self.shell=="csh" else "bash"}
        # Make hold_jids line only if there are jids (i.e. self.get_dependency_jid_list() != [])
        if jid_list:
            qsub_holdjids = "#$ -hold_jid %s " % jid_list
        else:
            qsub_holdjids = ""
        qsub_name =    "#$ -N %s " % (self.spec_qsub_name)
        qsub_stderr =  "#$ -e %s" % self.pipe_data["stderr_dir"]
        qsub_stdout =  "#$ -o %s" % self.pipe_data["stdout_dir"]
        # qsub_opts = "#$ " + " ".join(self.pipe_data["Qsub_opts"])
        qsub_queue =   "#$ -q %s" % self.params["qsub_params"]["queue"]
        # If there are values in Qsub_opts, add them to the qsub parameter lines:
        qsub_opts = ""
        
        
        if self.params["qsub_params"]["opts"]:
            qsub_opts += "#$ %s" % self.params["qsub_params"]["opts"]
        for qsub_opt in (set(self.params["qsub_params"].keys()) - set(["qstat_path","node","queue","opts","-pe","-q"])):       # For all qsub_params except node, queue and (global) opts which get special treatment:
            qsub_opts += "\n#$ %s %s" % (qsub_opt,self.params["qsub_params"][qsub_opt] if self.params["qsub_params"][qsub_opt]!=None else "")
        # Adding "-V" to all high level scripts (otherwise, if shell is bash, the SGE commands are not recognized)
        if "-V" not in self.params["qsub_params"].keys() and script_lev == "high":
            qsub_opts += "\n#$ -V"

        if script_lev == "low":
            
            if self.params["qsub_params"]["node"]:     # If not defined then this will be "None"
                
                
                # Perform two joins:
                #   1. For each node, join it to the queue name with '@' (e.g. 'bio.q@sge100')
                #   2. Comma-join all nodes to one list (e.g. 'bio.q@sge100,bio.q@sge102')
                qsub_queue = ",".join(["@".join([self.params["qsub_params"]["queue"],item]) for item in self.params["qsub_params"]["node"]])
                
                # qsub_queue += "@%s" % self.params["qsub_params"]["node"]
                qsub_queue = "#$ -q %s" % qsub_queue
            if "-pe" in self.params["qsub_params"].keys():     # If not defined then this will be "None"
                # Add newline if qsub_opts exists:
                if qsub_opts:
                    qsub_opts += "\n"
                qsub_opts += "#$ -pe %s" % self.params["qsub_params"]["-pe"]
            
        # Sometimes qsub_opts is empty and then there is an ugly empty line in the middle of the qsub definition
        # The following if-else is ugly, but solves the problem
        if qsub_opts.strip():
            return "\n".join([qsub_shell,qsub_queue,qsub_opts,qsub_name,qsub_stderr,qsub_stdout,qsub_holdjids]) + "\n\n"
        else:
            return "\n".join([qsub_shell,qsub_queue,qsub_name,qsub_stderr,qsub_stdout,qsub_holdjids]) + "\n\n"

    def set_qdel_file(self, qdel_filename):
        """ Called by PLC_main to store the qdel filename for the step.
        """
        
        self.qdel_filename = qdel_filename
        
        
    def add_qdel_line(self, type = "Start"):
        """ Add and remove qdel lines from qdel file.
            type can be "Start" or "Stop"
        """
        
        qdel_cmd = "qdel {script_name}".format(script_name = self.spec_script_name)
        
        if type == "Start":
            return "# Adding qdel command to qdel file.\necho '{qdel_cmd}' >> {qdel_file}\n\n".format(qdel_cmd = qdel_cmd, qdel_file = self.qdel_filename)
        elif type == "Stop":
            return "# Removing qdel command from qdel file.\nsed -i -e 's:^{qdel_cmd}$:#&:' {qdel_file}\n\n".format(qdel_cmd = re.escape(qdel_cmd), qdel_file = self.qdel_filename)
        else:
            raise AssertionExcept("Bad type value in qdd_qdel_lines")
                                           
    def create_log_lines(self, qsub_name, type = "Started", level = "high"):
        """ Create logging lines. Added before and after script to return start and end times
        """

        log_cols_dict = {"type"        : type,                                        \
        "step"       : self.get_step_step(),                        \
        "stepname"   : self.get_step_name(),                        \
        "stepID"     : qsub_name,                                   \
        "qstat_path" : self.pipe_data["qsub_params"]["qstat_path"], \
        "level"      : level, \
        "file"       : self.pipe_data["log_file"]}
        
        if self.shell=="csh":
        
            script = """
if ($?JOB_ID) then 
    # Adding line to log file:  Date    Step    Host
    echo `date '+%%d/%%m/%%Y %%H:%%M:%%S'`'\\t%(type)s\\t%(step)s\\t%(stepname)s\\t%(stepID)s\\t%(level)s\\t'$HOSTNAME'\\t'`%(qstat_path)s -j $JOB_ID | grep maxvmem | cut -d = -f 6` >> %(file)s
endif
####\n\n
""" % log_cols_dict
        
        elif self.shell == "bash":
            script = """
if [ ! -z "$JOB_ID" ]; then
    # Adding line to log file:  Date    Step    Host
    echo -e $(date '+%%d/%%m/%%Y %%H:%%M:%%S')'\\t%(type)s\\t%(step)s\\t%(stepname)s\\t%(stepID)s\\t%(level)s\\t'$HOSTNAME'\\t'$(%(qstat_path)s -j $JOB_ID | grep maxvmem | cut -d = -f 6) >> %(file)s
fi
####\n\n
""" % log_cols_dict

        else:
            script = ""
            self.write_warning("shell not recognized. Not creating log writing lines in scripts.\n", admonition = "WARNING")
        
        return script
        
    def create_activate_lines(self, type):
        """ Function for adding activate/deactivate lines to scripts so that virtual environments can be used 
            A workflow that uses this option is the QIIME2 workflow.
        """
        
        if type not in ["activate","deactivate"]:
            sys.exit("Wrong 'type' passed to create_activate_lines")
            
        if "conda" in self.params:
            if not self.params["conda"]:  # Was provided with 'null' or empty - do not do activate overriding possible global conda defs
                
                return ""
            if "path" in self.params["conda"] and "env" in self.params["conda"]:
                activate_path = os.path.join(self.params["conda"]["path"],type)
                environ       = self.params["conda"]["env"]
            else:
                raise AssertionExcept("'conda' parameter must include 'path' and 'env'")
            
        #=======================================================================
        # elif "conda" in self.pipe_data:
        #     activate_path  = os.path.join(self.pipe_data["conda"]["path"],type)
        #     environ        = self.pipe_data["conda"]["env"]
        #=======================================================================
        else:
            return ""
            
            


        if self.shell=="csh":
            self.write_warning("Are you sure you want to use 'activate' with a 'csh' based script?")
        
        script = """
# Adding environment activation/deactivation command:
source {activate_path} {environ}

""".format(activate_path = activate_path,
             environ = environ if type == "activate" else "") 
        
        return script
        
    def make_folder_for_sample(self, sample):
        """ Creates a folder for sample in this step's results folder
        """
        
        sample_folder = self.base_dir + sample + os.sep
        if not os.path.isdir(sample_folder):
            self.write_warning("Making dir at %s \n" % sample_folder, admonition = "ATTENTION")
            os.makedirs(sample_folder) 
        else:
            # if "verbose" in self.params:   # At the moment not set anywhere. Maybe in the future
            self.write_warning("Dir %s exists\n" % sample_folder, admonition = "WARNING")
    
        return sample_folder
        
        
    def get_redir_parameters_script(self):
        """ Returns a piece of script containing the redirect parameters
        """
        
        redir_param_script = ""
        if "redir_params" in self.params:
            for key in self.params["redir_params"].keys():
                # The following permits the user to pass two values for the same redirected parameter:
                if isinstance(self.params["redir_params"][key],list):
                    self.write_warning("Passed %s twice as redirected parameter!" % key)
                    for keyval in self.params["redir_params"][key]:
                        redir_param_script += "%s %s \\\n\t" % (key,keyval if self.params["redir_params"][key]!=None else "")
                else:
                    redir_param_script += "%s %s \\\n\t" % (key,self.params["redir_params"][key] if self.params["redir_params"][key]!=None else "")

        return redir_param_script

    def get_setenv_part(self):
        """ Returns a piece of code with "env", "setenv" and "export"
        """
        script_const = ""
        # Add "env" line, if it exists:
        # New version
        if "setenv" in self.params.keys():         # Add optional environmental variables.
            if not isinstance(self.params["setenv"], list):
                self.params["setenv"] = [self.params["setenv"]]
            for setenv in self.params["setenv"]:         # Add optional environmental variables.
                if self.shell=="csh":
                    script_const += "setenv %s \n" % setenv
                elif self.shell=="bash":
                    script_const += "export %s \n" % setenv

                    
            script_const += "\n\n"
                
        # Old version (kept for backwards compatibility. Not recommended):
        if "env" in self.params.keys():         # Add optional environmental variables.
            script_const += "env %s \\\n\t" % self.params["env"]
        return script_const


        
    def get_script_env_path(self):
        """ Returns a piece of code with "env" and "script_path"
        """
        script_const = self.get_setenv_part()
        # Add "env" line, if it exists:
        # New version

        # Add "script_path" line - it must exist
        script_const += "%s \\\n\t" % self.params["script_path"]

        return script_const
        
    def get_script_const(self):
        """ Returns a piece of script containing the env, script_path and redirect parameters lines
            These are the same in most steps. Can be used whereever suitable
        """

        # Add 'env' 
        script_const = self.get_script_env_path()

        # Add redir_params:
        script_const += self.get_redir_parameters_script()

        return script_const
        

    def manage_qsub_opts(self):
        """ Add default qsub options to step params 
            If '-q' is passed, is equivalent to passing "queue"
            If both are passed, print a comment and use 'queue'
        """
        
        
        try:
            self.params["qsub_params"]
        except KeyError:
            self.params["qsub_params"] = self.pipe_data["qsub_params"]
        else:
            # 'queue' can be set with 'qsub_opts_queue' and with 'qsub_opts_-q'. Dealing with it here:
            if "-q" in self.params["qsub_params"].keys():
                if "queue" in self.params["qsub_params"].keys():
                    sys.stdout.write("In %s:\tGot both '-q' and 'queue' params for qsub. Using 'queue'\n" % self.get_step_name())
                else:
                    self.params["qsub_params"]["queue"] = self.params["qsub_params"]["-q"]
                del self.params["qsub_params"]["-q"]
                
            # For each opt in default AND NOT IN step-specific qsub params
            for default_q_opt in [qsub_opt for qsub_opt in self.pipe_data["qsub_params"].keys() if not qsub_opt in self.params["qsub_params"].keys()]:
                # print "---->"+default_q_opt
                self.params["qsub_params"][default_q_opt] = self.pipe_data["qsub_params"][default_q_opt]
            
            # Require a queue to be defined globally or locally:
            assert "queue" in self.params["qsub_params"].keys(), "In %s:\tNo 'queue' defined for qsub\n" % self.get_step_name()


    def local_start(self,base_dir):
        """ Adds code to self.script to enable steps to temporarily write to a local disk before moving to final shared destination
            This can be useful when a lot of IO to the shared disk is detrimental
        """
        # If "local" is set, will do all IO to local folder and then copy everything to self.base_dir
        if "local" in self.params.keys():
            assert self.params["local"], "In step %s: You must supply a local destination when requesting 'local' in parameters" % self.name
            local_dir = "".join([os.sep,                                                        \
                                self.params["local"].strip(os.sep),                             \
                                os.sep,                                                         \
                                "_".join([self.spec_script_name,self.pipe_data["run_code"]]),   \
                                os.sep])
            self.script += "# Adding lines for local execution:\n" 
            self.script += "mkdir -p %s \n\n" % local_dir
            return local_dir 
        else:
            return base_dir
            
            
    def local_finish(self,use_dir,base_dir):
        """
        """
        if "local" in self.params.keys():
            self.script += "# Adding lines moving local execution to final destination:\n" 
            self.script += " ".join(["cp -prf ", use_dir + "*", base_dir,"\n\n"])
            self.script += "".join(["rm -rf ", use_dir,"\n\n"])

            

    def get_dict_encoding(self):
        """ Returns a dict containing all the step information
            Used for JSON serialization and storage in MongoDB
        """
        
        ret_dict = dict()
        try:
            ret_dict["sample_data"] = self.get_sample_data()
            ret_dict["base_sample_data"] = self.get_base_sample_data()
        except AttributeError:
            ret_dict["sample_data"] = None
            ret_dict["base_sample_data"] = None
        ret_dict["param_data"]  = self.params
        
        
        return ret_dict
        
        
        
    def return_formatted_message(self, comment, sample=None):
        """ Returns a formatted comment 
        
        """
        
        # Here one can add a dependency on a 'verbose' parameter somehow...
        if sample:
            return "Step %s: In sample %s, %s\n" % (self.name, sample, comment)
        else:
            return "Step %s: %s\n" % (self.name, comment)
            
            
            
            
    def stamp_file(self, filename):
        """ Register a file for stamping with md5sum
        """
        
        self.stamped_files.append(filename)
        
        
    def register_stamped_files(self,qsub_name):
        """
        """
        
        script = "######\n# Registering files with md5sum:\n"

        # Bash needs the -e flag to render \t as tabs.
        if self.shell=="csh":
            echo_cmd = "echo"
        elif self.shell=="bash":
            echo_cmd = "echo -e"
        else:
            pass

        for filename in self.stamped_files:
            script += """
%(echo_cmd)s `date '+%%d/%%m/%%Y %%H:%%M:%%S'` '\\t%(step)s\\t%(stepname)s\\t%(stepID)s\\t' `md5sum %(filename)s` >> %(file)s
""" %      {"echo_cmd" : echo_cmd,             \
            "filename" : filename,             \
            "step"     : self.get_step_step(), \
            "stepname" : self.get_step_name(), \
            "stepID"   : qsub_name,            \
            "file"     : self.pipe_data["registration_file"]}
        
        script += "#############\n\n"
            
        return script
        
        
        
        
    def register_files(self, qsub_name):
        """
        """
        
        script = ""
        if self.stamped_files:
            script += self.register_stamped_files(qsub_name)
            
        # if self.stamped_dirs:
            # script += self.register_files_in_dir(qsub_name)
            
        self.stamped_files = list()
        # self.stamped_dirs  = list()

        return script
        
        
        
    def declare_file(self, filename, slot):
        """ Declare a file for inserting into sample_data and creating md5 signature
        """
        
                 
        # Store file in active file for sample:
        slot = filename

        self.stamp_file(filename)

        
    def get_qsub_names_dict(self):
    
        return self.qsub_names_dict
    
    
    
    #===========================================================================
    # def create_sample_file(self):
    #     """ Creates a sample file based on the current version of get_sample_data
    #     """
    #     
    #     with open(self.base_dir+'sample_file.nsfs', 'w') as smp_f:
    #         smp_f.write("Title\t{title}\n\n".format(title=self.sample_data["Title"]))
    #         for sample in self.sample_data["samples"]:
    #             for direction in self.params["sample_file"]:
    #===========================================================================
            
                                       
                                       
                                       
                                       