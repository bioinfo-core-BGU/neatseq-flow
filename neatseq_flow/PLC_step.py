
""" A class defining a step in the pipeline.

"""
import os
import shutil
import sys
import re
import importlib
import traceback
import datetime
import itertools
import json

# from script_constructors.ScriptConstructorSGE import HighScriptConstructorSGE, KillScriptConstructorSGE

from copy import *
from pprint import pprint as pp
from modules.parse_param_data import manage_conda_params

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"



class AssertionExcept(Exception):
    """A class to be raised by modules failing at assertions
    """
    def __init__(self, comment = "Unknown problem", sample = None, step = None):
        """ initializize with error comment and sample, if exists)
            step is not required. Can be set later with set_step_name()
            """
        if sample == "project_data":
            # Sometimes, sample is project_data for routines which are both for samples and for projects
            sample = None
        self.sample = sample
        self.comment = comment
        self.step = step
        
    def set_step_name(self, step_name = None):
        if not step_name:
            sys.exit("You must specify step_name when calling set_step_name()")
            
        self.step = step_name
        
    def get_error_str(self):
        
        if self.step:
            error_str = "In %s" % self.step
        else:
            error_str = ""
            
        if self.sample: # If a sample was passed. The exception is specific to a sample
            self.comment =  error_str + " (sample %s): %s" % (self.sample, self.comment)
        else:       
            self.comment = error_str + " (project scope): " + self.comment if error_str else self.comment

        return self.comment




class Step(object):
    """ A class that defines a pipeline step name (=instance).
    """
    Cwd = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------------------
# Step class methods
# ----------------------------------------------------------------------------------

    @classmethod
    def find_step_module(cls, step, param_data, pipe_data):
        """ A class method for finding the location of a module for a given step
        """

        def walkerr(err):
            """ Helper function for os.walk below. Catches errors during walking and reports on them.
            """
            print "WARNING: Error while searching for modules:"
            print err

        # Searching module paths passed by user in parameter file:
        if "module_path" in param_data["Global"]:
            for module_path_raw in param_data["Global"]["module_path"]:
                # Remove trainling '/' from dir name. For some reason that botches things up!
                module_path = module_path_raw.rstrip(os.sep)

                # Expanding '~' and returning full path 
                module_path = os.path.realpath(os.path.expanduser(module_path))
                

                # Check the dir exists:
                if not os.path.isdir(module_path):
                    sys.stderr.write("WARNING: Path %s from module_path does not exist. Skipping...\n" % module_path)
                    continue

                mod_t = step
                dir_generator = os.walk(module_path, onerror = walkerr)
                # Each .next call on this generator
                # returns a level tuple as follows:
                try:
                    level = dir_generator.next()
                    # level is a tuple with: (current dir. [list of dirs],[list of files])
                except StopIteration:
                    sys.stderr.write("WARNING: Module path {mod_path} seems to be empty! Possibly issue with "
                                     "permissions...\n".format(mod_path=module_path))
                while mod_t + ".py" not in level[2] or "__init__.py" not in level[2]:
                    # Repeat while expected filename is NOT in current dir contents (=level[2]. see above)
                    #   and while __init__.py is not in current dir (avoid finding modules in non-active dirs)
                    try:
                        level = dir_generator.next()    # Try getting another level    
                    except StopIteration:
                        # print "Step %s not found in path %s." % (mod_t,module_path)
                        break # Leave while without executing "else"
                else:
                    # Adding module_path to search path
                    if module_path not in sys.path:
                        sys.path.append(os.path.abspath(module_path))
                        # print ">>> ", sys.path
                        
                    # Backup module to backups dir:
                    shutil.copyfile(level[0] + os.sep + mod_t + ".py", \
                        "{bck_dir}{runcode}{ossep}{filename}".format(bck_dir = pipe_data["backups_dir"], \
                                                                     runcode = pipe_data["run_code"], \
                                                                     ossep = os.sep, \
                                                                     filename = mod_t + ".py"))

                    # For what this does, see below (# Build module name)...
                    retval = (level[0].split(module_path)[1].partition(os.sep)[2].replace(os.sep,".") + "." + mod_t).lstrip(".")
                    module_loc = level[0] + os.sep + mod_t + ".py"

                    return retval, module_loc


        # If not found, do the same with cls.Cwd:
        mod_t = step
        dir_generator = os.walk(cls.Cwd, onerror = walkerr)     # Each .next call on this generator returns a level tuple as follows:
        try:
            level = dir_generator.next()           # level is a tuple with: (current dir. [list of dirs],[list of files])
        except StopIteration:
            sys.stderr.write("WARNING: Module path %s seems to be empty! Possibly issue with permissions...\n" % self.Cwd)

        while(mod_t + ".py" not in level[2]):     # Repeat while expected filename is NOT in current dir contents (=level[2]. see above)
            try:
                level = dir_generator.next()    # Try getting another level    
            except StopIteration:
                sys.exit("Step %s not found in regular path or user defined paths." % mod_t)
        

        # Backup module to backups dir:
        shutil.copyfile(level[0] + os.sep + mod_t + ".py", \
                        "{bck_dir}{runcode}{ossep}{filename}".format(bck_dir = pipe_data["backups_dir"], \
                                                                     runcode = pipe_data["run_code"], \
                                                                     ossep = os.sep, \
                                                                     filename = mod_t + ".py"))

        # Build module name:
        # 1. take dir found in search
        # 2. split it by CWD and take 2nd part,  i.e. remove cwd from dir name...
        # 3. partition by os.sep to remove leading os.sep
        # 4. replace remaining os.sep's by ".".
        # 5. Add .
        # Adding 'neatseq_flow' at begginning of module location.
        retval = "neatseq_flow."+level[0].split(cls.Cwd)[1].partition(os.sep)[2].replace(os.sep,".") + "." + mod_t
        module_loc = level[0] + os.sep + mod_t + ".py"

        return retval, module_loc

    @classmethod
    def determine_sample_types(cls, sample, sample_data):
        """

        :param sample_data:
        :return: List of sample types
        """


        # Prepare holder for type:
        sample_type = list()
        # Testing fastq files:
        if "Single" in sample_data:
            # Only one type of file: SE
            sample_type.append("SE")
        if "Forward" in sample_data and "Reverse" in sample_data:
            sample_type.append("PE")
        if "Forward" in sample_data and "Reverse" not in sample_data:
            # sys.exit("You have only Forward for sample %s. Can't proceed!" % sample)
            sys.stderr.write("You have only Forward for sample %s. Converting to 'Single'!\n" % sample)
            sample_data["Single"] = sample_data["Forward"]
            del(sample_data["Forward"])
        if "Reverse" in sample_data and "Forward" not in sample_data:
            # sys.exit("You have only Reverse for sample %s. Can't proceed!" % sample)
            sys.stderr.write("You have only Reverse for sample %s. Converting to 'Single'!\n" % sample)
            sample_data["Single"] = sample_data["Reverse"]
            del (sample_data["Reverse"])
        if "fastq.S" in sample_data:
            # Only one type of file: SE
            sample_type.append("SE")
        if "fastq.F" in sample_data and "fastq.R" in sample_data:
            sample_type.append("PE")
        if "fastq.F" in sample_data and "fastq.R" not in sample_data:
            sys.exit("You have only fastq.F for sample %s. Wierd!" % sample)
        if "fastq.R" in sample_data and "fastq.F" not in sample_data:
            sys.exit("You have only fastq.R for sample %s. Weird!" % sample)
        # IF fasta exists, add to types list
        if "Nucleotide" in sample_data or "fasta.nucl" in sample_data:
            sample_type.append("nucl")
        if "Protein" in sample_data or "fasta.prot" in sample_data:
            sample_type.append("prot")

        if "BAM" in sample_data or "SAM" in sample_data:
            sample_type.append("mapping")

        return sample_type
# ----------------------------------------------------------------------------------
# Step instance methods
# ----------------------------------------------------------------------------------

    def __init__(self, name, step_type, params, pipe_data, module_path, caller):
        """ should not be used. only specific step inits should be called. 
            Maybe a default init can be defined as well. check.
        """
        self.name = name
        self.step = step_type
        self.params = params
        self.pipe_data = pipe_data

        self.path = module_path

        # Storing reference to main pipeline object:
        self.main_pl_obj = caller

        # The following will be used to separate elements in the jid names.
        # If you change this, you have to change it in scriptconstructor, in the lines
        # beginning with module= and instance=, according to awk regular expression definitions!
        self.jid_name_sep = ".."


        self.use_provenance = True
        # -----------------------------
        # Place for testing parameters:
        try:
            self.params["script_path"]
        except KeyError:
            sys.exit("You must supply a script_path parameter in %s\n" % self.name)

        self.base_dir = os.sep.join([self.pipe_data["data_dir"], self.step, self.name, ''])
        # Move to general init function:
        # Make dir for $qsub_name results
        if not os.path.isdir(self.base_dir):
            self.write_warning("Making dir for results of %s at %s \n" % (self.name,self.base_dir), admonition = "ATTENTION")
            os.makedirs(self.base_dir) 
        else:
            pass
            # TODO: Do the following only if verbose is set:
            # sys.stderr.write("Dir %s exists for results of %s \n" % (self.base_dir,self.name))

        # Testing 'conda' parameters
        self.manage_conda_opts()
                                                    
        # Setting qsub options in step parameters:
        self.manage_qsub_opts()
       
        self.jid_list = []        # Initialize a list to store the list of jids of the current step
        self.glob_jid_list = []   # An experimental feature to enable shorter depend lists

        # The following line defines A list of jids from current step that all other steps should depend on.
        # Is used to add a prelimanry step, equivalent to the "wrapping up" step that is dependent on all previous
        # scripts
        self.preliminary_jids = []

        # self.skip_scripts determines whether scripts will be created. 
        # Defaults to False, unless SKIP is defined in parameters.
        # This is supposed:
        # A. to enable steps to avoid script building by setting to True.
        #    See for example del_type, move_type (now generalized in manage_types)
        #    In this case, set skip_scripts to True in step_specific_init(). skip_step_sample_initiation
        #    will be set to False by default.
        # B. To enable skipping a step while leaving the flow scheme intact (i.e. a step is like a channel for
        #    types without actually doing anything. Same as commenting it out but saves resetting bases...)
        #    In this case, both skip_scripts and skip_step_sample_initiation are set to True, because some of the
        #    modifications to sample_data are performed in self.step_sample_initiation().
        #    In the step_specific_init() function no changes to sample_data are possible because it is not set yet
        #    at that stage!
        if "SKIP" in self.params:
            self.skip_scripts = True
            self.skip_step_sample_initiation = True
            # This is so that modifications to sample_data requested in
            # step_sample_initiation() will not be performed if SKIP is set.
        else:
            self.skip_scripts = False   
            self.skip_step_sample_initiation = False
            
        # Catch exceptions of type AssertionExcept raised by the specific initiation code
        try:
            self.step_specific_init()
        except AssertionExcept as assertErr:
            print "step_specific_init"
            assertErr.set_step_name(self.get_step_name())
            # print assertErr.get_error_str()
            raise assertErr 

        # self.shell_ext contains the str to use as script extension for step scripts
        if self.shell == "bash":
            self.shell_ext = "sh"
        else:
            self.shell_ext = "csh"

        # Check that auto_redirs do not exist in parameter redirects list:
        try:
            auto_redirs = list(set(self.params["redir_params"].keys()) & set(self.auto_redirs))
            if auto_redirs:
                raise AssertionExcept("""\
Please do not pass the following redirected parameters: 
{parameters}
They are set automatically or module is not defined to use them""".format(parameters=", ".join(auto_redirs)))

        except AttributeError:  # Ignore if auto_redirs not defined for module. It is highly recommended to do so...
            pass
        except KeyError as keyerr:
            if keyerr.args[0]=="redir_params":
                self.write_warning("No 'redirects' defined.")
                pass
            else:
                raise keyerr
        except Exception as expt:
            raise expt
        
        # Create a list for filenames to register with md5sum for each script:
        self.stamped_files = list()
        # self.stamped_dirs = list()

        # Create a dictionary storing the step name and names of sub-scripts
        # Will then be queried by main to create a general dictionary which can be written to json and
        # used for remote run monitor
        self.qsub_names_dict = dict()

        # # Add job_limit to params
        # # This way, job_limit can be passed globally or by step...
        # # Problematic because job_limit is treated at the class level in scriptconstructor...
        # if "job_limit" in self.pipe_data:
        #     self.params["job_limit"] = self.pipe_data["job_limit"]
                                    
    def __str__(self):
        """ Print a summary of the class: name, step and depend list
        """
        
        return """
Name:         {name}
Step:         {module}
Base:         {base}
Dependencies: {depends}""".format(name=self.name,
                                  module=self.step,
                                  base=[step.get_step_name()
                                        for step
                                        in self.get_base_step_list()] if self.get_base_step_list() else None,
                                  depends=self.get_depend_list())
        
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

        if base_step_list != [] and not all(map(lambda x: isinstance(x,Step), base_step_list)):
            raise AssertionExcept("Invalid base list\n", step = self.get_step_name())
        
        try:
            self.base_step_list
        except AttributeError:
            # Good. Does not exist
            # Set merge base_step to None and all others to base_step
            # While at it, update sample_data according to new base_step
            self.base_step_list = base_step_list if base_step_list else None
            # Do the following only if base_step is not None (= there is a base step. all except merge)
            if self.base_step_list:
                # sys.stderr.write("setting sample data for %s \n" % self.name)
                # self.set_sample_data(self.base_step_list[0].get_sample_data())
                self.set_sample_data()  # Uses self.base_step_list
        else:
            raise AssertionExcept("Somehow base_step is defined more than once", self.get_step_name())
        
    def get_base_step_list(self):
        try:
            return self.base_step_list
        except AttributeError:
            return []
            # sys.exit("base_step not found in %s\n" % (self.name))
            
## Comprison methods
    
    def __lt__(self,other):
        """ A step is _lt_ than 'other' if it is in 'other's list of dependencies or if it has a shorter dependency list.
            Is used by the sort function to sort the steps in a correct running order
            A side effect is that parallel branches are sorted top-down rather than branch-wise.
            You can redefine the 'sort' method in Pipeline class to change this behaviour.
        """
        #print self.pipe_data["step_order"]
        if self.name in other.get_depend_list():
            return True
        if other.name in self.get_depend_list():
            return False
        #=======================================================================
        # print "in __lt__: other index %s (%s)\nself index %s (%s)\n" % (self.pipe_data["step_order"].index(other.name), other.name, self.pipe_data["step_order"].index(self.name),self.name)
        # # Returning order by order in param file:
        # if self.pipe_data["step_order"].index(other.name) > self.pipe_data["step_order"].index(self.name):
        #     return True
        # if self.pipe_data["step_order"].index(other.name) < self.pipe_data["step_order"].index(self.name):
        #     return False
        #=======================================================================
         
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
        #=======================================================================
        # # Returning order by order in param file:
        # print "in __gt__: other index %s (%s)\nself index %s (%s)\n" % (self.pipe_data["step_order"].index(other.name), other.name, self.pipe_data["step_order"].index(self.name),self.name)
        # if self.pipe_data["step_order"].index(other.name) > self.pipe_data["step_order"].index(self.name):
        #     return False
        # if self.pipe_data["step_order"].index(other.name) < self.pipe_data["step_order"].index(self.name):
        #     return True
        #=======================================================================

        if len(self.get_depend_list()) > len(other.get_depend_list()):
            return True
        if len(self.get_depend_list()) < len(other.get_depend_list()):
            return False
        if self.get_step_name() > other.get_step_name():
            return True
        if self.get_step_name() < other.get_step_name():
            return False
        return NotImplemented 
        
        
    def finalize_contruction(self):
        """ Put all stuff that needs to be done after init, sorting and number setting.
            Called for each step in main.
        """
        

        ## Create kill script class
        # Done before high level script so that high level knows about the 'kill_script_path' in params
        getScriptConstructorClass = self.import_ScriptConstructor(level="kill")
        self.kill_script_obj = getScriptConstructorClass(master = self)

        # Store path to kill script in params:
        self.params["kill_script_path"] = self.kill_script_obj.script_path

        getScriptConstructorClass = self.import_ScriptConstructor(level="high")

        ## Create main script class
        # First, setting spec_script_name:
        self.spec_script_name = self.jid_name_sep.join([self.step,self.name])
        # Then, creating high-level script:
        self.main_script_obj = getScriptConstructorClass(master=self)

        
    def cleanup(self):
        """ Here go things to be done just before termination of NeatSeq-Flow 
        """

        self.main_script_obj.__del__()
        self.kill_script_obj.__del__()
        
        # import pdb; pdb.set_trace()
    def get_high_depends_command(self):
        """ Get dependency command from high script object
            This will be qalter in qsub
        """

        # dependency_list = ",".join(self.get_dependency_jid_list())
        if self.skip_scripts:
            return ""

        return self.main_script_obj.get_depends_command()

    def set_step_number(self,step_number):
        """ Sets the number of the step in the step list. 
            Is used in naming the scripts, so that they can be sorted with 'll'
        """
        assert isinstance(step_number, int)
        self.step_number = "{:0>2}".format(step_number)

    def get_script_name(self):
        return self.main_script_obj.script_name

    def get_sample_data(self):
        return self.sample_data
        
    def get_base_sample_data(self):
        """ Get base_sample_data
        """
        # print [step.get_step_name()
        #        for step
        #        in self.get_base_step_list()] if self.get_base_step_list() else None
        # print self.get_step_name(), " new: ", {stepname:self.main_pl_obj.global_sample_data[stepname]
        #        for stepname
        #        in self.get_depend_list()}
        # print self.get_step_name(), " old: ", self.base_sample_data

        # return self.base_sample_data
        return {stepname:self.main_pl_obj.global_sample_data[stepname]
               for stepname
               in self.get_depend_list()}

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
                    # For list of active samples, merge the lists:
                    if k == "samples":
                        sample_data[k] = list(set(sample_data[k]) | set(other_sample_data[k]))

                    # Do nothing, but check not discarding values from other_sample_data
                    if sample_data[k] != other_sample_data[k]:
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

        if sample_data is not None:     # When passing sample_data (i.e. for merge)
            # Copying sample_data. Just '=' would create a kind of reference
            self.sample_data = deepcopy(sample_data)
            # # Also starting a new provenance dictionary
            if self.use_provenance:
                self.create_provenance()
                self.sample_data_original = deepcopy(self.sample_data)
        else:   # Extract sample_data from base steps:
            self.sample_data = dict()
            if self.use_provenance:
                self.provenance = dict()
            for base_step in self.base_step_list:
                # Merge sample_data from all base steps.
                # Function sample_data_merge uses deepcopy as well
                self.sample_data = self.sample_data_merge(self.get_sample_data(),
                                                          base_step.get_sample_data(),
                                                          base_step.get_step_name())

                if self.use_provenance:
                    self.provenance = self.sample_data_merge(self.get_provenance(),
                                                             base_step.get_provenance(),
                                                             base_step.get_step_name())
                    self.sample_data_original = deepcopy(self.sample_data)


        # This part is experimental and not 100% complete. Changes will probably occur in the future.
        # 1. Convert "exclude_sample_list" to "sample_list":
        if "exclude_sample_list" in self.params:
            if not isinstance(self.params["exclude_sample_list"] , list):
                self.params["exclude_sample_list"] = re.split("[, ]+", self.params["exclude_sample_list"])
            if set(self.params["exclude_sample_list"])-set(self.pipe_data["samples"]):
                raise AssertionExcept("'exclude_sample_list' includes samples not defined in sample data!",
                                      step=self.get_step_name())
            self.params["sample_list"] = list(set(self.pipe_data["samples"]) - set(self.params["exclude_sample_list"]))
        # 2. Deal with 'sample_list' option:
        if "sample_list" in self.params:
            # 2a. For 'all_samples', pop the last sample list from stash 'sample_data_history'
            if self.params["sample_list"] == "all_samples":
                raise AssertionExcept("'all_samples' is no longer supported as valsue for 'sample_list'."
                                      "Use a secondary base to import old samples")
            # 2b. For sample list, stash the new sample list
            elif isinstance(self.params["sample_list"], list):
                if list(set(self.params["sample_list"]) - set(self.pipe_data["samples"])):
                    raise AssertionExcept("'sample_list' includes samples not defined in sample data! ({bad})".
                                          format(bad=", ".join(set(self.params["sample_list"]) -
                                                               set(self.pipe_data["samples"]))),
                                          step=self.get_step_name())
                self.stash_sample_list(self.params["sample_list"])
            else:   # It's a dict!
                self.stash_sample_list(self.get_sample_list_by_category(self.params["sample_list"]))

        # Trying running step specific sample initiation script:
        try:
            if not self.skip_step_sample_initiation:
                self.step_sample_initiation()
        except AttributeError:
            pass    # It dosen't have to be defined.
        except AssertionExcept as assertErr: 
            assertErr.set_step_name(self.get_step_name())
            raise assertErr

        # # self.create_provenance()
        # print self.get_step_name()
        # pp(self.sample_data)
        # pp(self.provenance)
        # sys.exit()


    def stash_sample_list(self, sample_list):
        """ Call this function to change the sample_list and put current sample list in history.
            Following the call to the function, you should be able to manipulate the sample list in such a way that it
            is recoverable from sample_data_history
            Note: AN EXPERIMENTAL FEATURE STILL
        """

        # try:
        #     self.sample_data["sample_data_history"]["prev_sample_lists"].append(self.sample_data["samples"])
        # except KeyError:
        #     # container for unused sample data:
        #     self.sample_data["sample_data_history"] = dict()
        #     # Container for magazine of sample lists:
        #     self.sample_data["sample_data_history"]["prev_sample_lists"] = list()
        #     self.sample_data["sample_data_history"]["prev_sample_lists"].append(self.sample_data["samples"])

        # # Create new sample list:
        # if isinstance(sample_list,str):
        #     sample_list = [sample_list]
        # elif isinstance(sample_list,list):
        #     pass
        # else:
        #     raise AssertionExcept("sample_list must be string or list in stash_sample_list()")

        # Removing unused sample slots from sample_data
        old_samples = list(set(self.sample_data["samples"]) - set(sample_list))
        for sample in old_samples:
            self.sample_data.pop(sample)

        self.sample_data["samples"] = sample_list  #self.params["sample_list"]

    def recover_sample_list(self,base=None):
        """ Call this function to recover the most recent sample list from history.
            Note: AN EXPERIMENTAL FEATURE STILL
            If sample_data_history does not exist, will throw a KeyError exception. You have to catch it!
        """
        sys.exit("recover_sample_list is no longer used")
        if base is None:
            # try:
            self.sample_data["samples"] = self.sample_data["sample_data_history"]["prev_sample_lists"].pop()
            # except KeyError:
            #     raise AssertionExcept("'sample_list' set to 'all_samples' before sample subset selected",
            #                           step=self.get_step_name())
        else:  # Recover sample list from base
            if base not in self.get_depend_list():
                raise AssertionExcept("Base {base} undefined.".format(base=base))
            self.sample_data["samples"] = self.base_sample_data[base]["sample"]

    def get_main_command(self):
        """ Return the command to put in the main workflow script to run the main step script.
        """

        return self.main_script_obj.get_command()

    def set_spec_script_name(self, sample="project_data"):
        """ Sets the current spec_script_name to a regular name, i.e.:
                sample level: self.jid_name_sep.join([self.step,self.name,sample])
                project level: self.jid_name_sep.join([self.step,self.name,self.sample_data["Title"]])
            In the build_scripts function, run:
                sample level: self.set_spec_script_name(sample)
                project level: self.set_spec_script_name()
            If using a different level of paralleization, see e.g. VCFtools, 
                you can set your own self.spec_script_name.
                
        """
        
        if sample != "project_data":
            self.spec_script_name = self.jid_name_sep.join([self.step,self.name,sample])
        else:
            self.spec_script_name = self.jid_name_sep.join([self.step, self.name, self.sample_data["Title"]])

        return self.spec_script_name


    def set_sample_name(self, sample):
        """
        Returns a sample name. If sample is "project_data", returns the project title. Otherwise, bounces sample back.
        :param sample:
        :return: A sample name
        """

        return sample if sample != "project_data" else self.sample_data["Title"]

    def add_jid_to_jid_list(self, script_id):
        """ Adds a jid for a sub process (e.g. a sample-specific script) to the jid list of the current step
        """
        
        self.jid_list.append(script_id)
        
        
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

    def get_glob_jid_list(self):
        """ Return list of jids
            To be used by pipeline for creating the delete function (99.del...)
        """

        return self.glob_jid_list

    def get_glob_name(self):

        return "{step}{sep}{name}{sep}*{runid}".format(step=self.get_step_step(),
                                                       name=self.get_step_name(),
                                                       sep=self.jid_name_sep,
                                                       runid=self.pipe_data["run_code"])

    def get_dependency_glob_jid_list(self):
        """ Returns the list of jids of all base steps
            Recursion. beware!
        """

        glob_depend_jid_list = []

        if self.base_step_list:
            for base_step in self.base_step_list:
                glob_depend_jid_list += (base_step.get_glob_jid_list() + base_step.get_dependency_glob_jid_list())

        return list(set(glob_depend_jid_list))

    def import_ScriptConstructor(self, level): #modname, classname):
        """Returns a class of "classname" from module "modname". 
        """

        level = level.lower().capitalize()
        modname = "neatseq_flow.script_constructors.scriptconstructor{executor}".format(executor=self.pipe_data["Executor"])
        classname = "{level}ScriptConstructor{executor}".format(level=level, executor=self.pipe_data["Executor"])  #SGE"
        return getattr(importlib.import_module(modname), classname)

        
    def create_low_level_script(self):
        """ Create the low (i.e. 3rd) level scripts, which are the scripts that actually do the work
            The actual part of the script is produced by the particular step class.
            This function is responsible for the generic part: opening the file and writing the qsub parameters and the script
        """
        getChildClass = self.import_ScriptConstructor(level="low")
        # Create ScriptConstructor for low level script.
        self.child_script_obj = getChildClass(master=self)

        # Adds script_id to jid_list
        self.add_jid_to_jid_list(self.child_script_obj.script_id)  
        
        # Add qsub headers to the script:
            # Decide wether to use csh or bash
            # determine queue and nodes
            # User-defined qsub opts
            # Dependencies: DONE: use self.get_dependency_jid_list()
        
        # DONE. Update list of jids for this step (maybe different function)
        # Add jid to list of jids in pipe_data for process deletion script. TO BE DONE IN PIPELINE, NOT HERE! USE get_jid_list() METHOD FOR THIS! 
        
        # Get dependency jid list 
        self.dependency_jid_list = self.get_dependency_jid_list()
        # Add prelimanry jids if exist (if not, is an empty list and will not affect the outcome)
        # Adding at the head of the list. That's why is done in two steps - just to make it clearer.
        self.dependency_jid_list = self.preliminary_jids + self.dependency_jid_list
        self.dependency_glob_jid_list = self.preliminary_jids + self.get_dependency_glob_jid_list()

        # Request low-level script construction from LowScriptConstructor:
        self.child_script_obj.write_script()

        # Clear stamped files list
        self.stamped_files = list()

        # Add child command execution lines to main script:
        self.main_script_obj.write_command(self.main_script_obj.get_child_command(self.child_script_obj))

        # Adding to qsub_names_dict:
        self.qsub_names_dict["low_qsubs"].append(self.child_script_obj.script_id)

        # Adding job name and path to script and run indices
        self.add_job_script_run_indices(self.child_script_obj)
        
        self.child_script_obj.__del__()

    def add_job_script_run_indices(self, script_obj):
        """ Add current script to script_index and run_index files
        """
        with open(self.pipe_data["script_index"], "a") as script_fh:
            script_fh.write("{qsub_name}\t{script_name}\n".format(qsub_name   = script_obj.script_id,
                                                                  script_name = script_obj.script_path))
        with open(self.pipe_data["run_index"], "a") as script_fh:
            if script_obj.level == "high":
                script_fh.write("\n----\n")
            script_fh.write("# {qsub_name}\n".format(qsub_name   = script_obj.script_id))
        
        
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
        # Is done in HighScriptConstructor construction.
        
        # Adding high-level jid to jid_list
        self.add_jid_to_jid_list(self.main_script_obj.script_id)
        self.glob_jid_list.append(self.get_glob_name())
        # "{step}_{name}*".format(step=self.get_step_step(),
        #                                                   name=self.get_step_name()))

        self.spec_script_name = self.jid_name_sep.join([self.step,self.name])

        # Add qdel command to main qdel script:
        self.main_script_obj.main_script_kill_commands(self.kill_script_filename_main)

        self.dependency_jid_list = self.get_dependency_jid_list()   # + self.preliminary_jids
        self.dependency_glob_jid_list = self.get_dependency_glob_jid_list()

        # Write main script preamble:
        self.main_script_obj.write_command(self.main_script_obj.get_script_preamble())

        # The actual qsub commands must be written in the create_low_level_script() function because they are
        # step_name dependent!
            
        # Adding to qsub_names_dict:
        self.qsub_names_dict["step"] = self.get_step_step()
        self.qsub_names_dict["high_qsub"] = self.main_script_obj.script_id
        self.qsub_names_dict["low_qsubs"] = list()

        # Adding qsub_name and script path to script_index and run_index
        self.add_job_script_run_indices(self.main_script_obj)

    def close_high_level_script(self):
        """ Create the high (i.e. 2nd) level scripts, which are the scripts that run the 3rd level scripts for the step
        """

        # self.main_script_obj.write_command(self.main_script_obj.get_script_postamble())
        self.main_script_obj.close_script()

    def create_preliminary_script(self):
        """ Create a script that will run before all other low level scripts commence

        """
        # Creating script. If 'create_spec_preliminary_script' is not defined or returns nothing,
        # return from here without doing anything
        self.script = ""
        try:
            self.create_spec_preliminary_script()
        except AttributeError:
            return 

        if not self.script.strip():                 # If script is empty, do not create a wrapper function
            return

        self.spec_script_name = self.jid_name_sep.join([self.step, self.name, "preliminary"])

        getChildClass = self.import_ScriptConstructor(level="low")
        # Create ScriptConstructor for low level script.
        self.prelim_script_obj = \
            getChildClass(master=self)

        # Get dependency jid list and add preliminary jids if exist
        # (if not, is an empty list and will not affect the outcome)
        self.dependency_jid_list = self.get_dependency_jid_list()
        self.dependency_glob_jid_list = self.get_dependency_glob_jid_list()

        self.prelim_script_obj.write_script()

        # Clear stamped files list
        self.stamped_files = list()
                
        self.main_script_obj.write_command(self.main_script_obj.get_child_command(self.prelim_script_obj))

        # This is here because I want to use jid_list to make wrapping_up script dependent on this step's
        # main low-level scripts
        # Explantion: get_jid_list() was used above (line 'qsub_header...') to make the wrapping_up script dependent
        # on the other scripts created by the step. Now that that is done, the following line adds this step to the
        # jid_list, so that subsequent steps are dependent on the wrapping up script as well.
        # (I hope this makes it clear...)
        self.add_jid_to_jid_list(self.prelim_script_obj.script_id)

        # Add the preliminary jid to the list of preliminary jids.  
        self.preliminary_jids.append(self.prelim_script_obj.script_id)

        # Adding to qsub_names_dict:
        self.qsub_names_dict["low_qsubs"].append(self.prelim_script_obj.script_id)

        # Adding job name and path to script and run indices
        self.add_job_script_run_indices(self.prelim_script_obj)

        self.prelim_script_obj.__del__()
        
    def create_wrapping_up_script(self):
        """ Create a script that will run once all other low level scripts terminate
            Ideal place for putting testing and agglomeration procedures.
        """

        # Creating script. If 'create_spec_wrapping_up_script' is not defined or returns nothing,
        # return from here without doing anything
        self.script = ""
        try:
            self.create_spec_wrapping_up_script()
        except AttributeError:
            return 

        if not self.script.strip():                 # If script is empty, do not create a wrapper function
            return 

        self.spec_script_name = self.jid_name_sep.join([self.step,self.name,"wrapping_up"])

        getChildClass = self.import_ScriptConstructor(level="low")

        # Create ScriptConstructor for low level script.
        self.wrap_script_obj = getChildClass(master=self)

        # Get dependency jid list and add preliminary jids if exist
        # (if not, is an empty list and will not affect the outcome)
        #    Also, add all jids of current step, as this script is to run only after all previous steps have completed.
        self.dependency_jid_list = self.preliminary_jids + self.get_jid_list() + self.get_dependency_jid_list()
        self.dependency_glob_jid_list = self.preliminary_jids + \
                                        self.get_glob_jid_list() + \
                                        self.get_dependency_glob_jid_list()
        # Removing parent name from wrapping_up dependencies
        self.dependency_jid_list.remove(self.main_script_obj.script_id)

        # sys.exit(self.spec_qsub_name)
        self.wrap_script_obj.write_script()

        # Clear stamped files list
        self.stamped_files = list()
        
        self.main_script_obj.write_command(self.main_script_obj.get_child_command(self.wrap_script_obj))

        # This is here because I want to use jid_list to make wrapping_up script dependent on this step's
        # main low-level scripts
        # Explantion: get_jid_list() was used above (line 'qsub_header...') to make the wrapping_up script dependent
        # on the other scripts created by the step. Now that that is done, the following line adds this step to the
        # jid_list, so that subsequent steps are dependent on the wrapping up script as well.
        # (I hope this makes it clear...)
        self.add_jid_to_jid_list(self.wrap_script_obj.script_id)

        # Adding to qsub_names_dict:
        self.qsub_names_dict["low_qsubs"].append(self.wrap_script_obj.script_id)

        # Adding job name and path to script and run indices
        self.add_job_script_run_indices(self.wrap_script_obj)
        self.wrap_script_obj.__del__()

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
                # self.main_script_obj.get_script_postamble()
                self.close_high_level_script()

            except AssertionExcept as assertErr:
                # print assertErr.get_error_str(self.get_step_name())
                # raise
                # print assertErr.get_error_str(self.get_step_name())
                # raise AssertionExcept(assertErr.get_error_str(),step=self.get_step_name())

                assertErr.set_step_name(self.get_step_name())
                raise assertErr
        # Add sample_data to collection of sample_data dicts in main class:
        self.main_pl_obj.global_sample_data[self.get_step_name()] = deepcopy(self.sample_data)
        # Updating provenance data:
        if self.use_provenance:
            self.update_provenance()

        if "stop_and_show" in self.params:
            print self.get_stop_and_show_message()
            raise AssertionExcept("Showed. Now stopping. "
                                  "To continue, remove the 'stop_and_show' tag from %s" % self.get_step_name())

    def get_stop_and_show_message(self):

        message = """\
Project: {title}
--------------""".format(title=self.sample_data["Title"])

        if "project_data" in self.sample_data:  # If no project data exists, skip this
            if self.use_provenance:
                # Creating string of project data including provenance
                try:
                    project_slots_text = "\n".join(["- {key} ({prov})".
                                                   format(key=key,
                                                          prov="->".join(self.provenance["project_data"][key]))
                                                    for key
                                                    in self.sample_data["project_data"].keys()])
                except KeyError:
                    # print "~~~~~~~~~~~~~~~~ %s ~~~~~" % self.get_step_name()
                    # print self.sample_data["project_data"].keys()
                    # print self.provenance["project_data"].keys()
                    # print "~~~~~~~~~~~~~~~~~~~~~"
                    raise AssertionExcept("Weird error!")

            else:
                # Creating string of project data not including provenance
                project_slots_text = "\n".join(["- " + key
                                                for key
                                                in self.sample_data["project_data"].keys()])


            message = message + """
Project slots:
--------------
{project_slots}
""".format(project_slots=project_slots_text)

        if self.sample_data["samples"]:  # Sample list may be empty if only project data was passed!
            if self.use_provenance:
                all_samples = set(self.provenance.keys()) - {"project_data"}
                uniq_prov_list = list(set([json.dumps(self.provenance[sample], sort_keys=True)
                                           for sample
                                           in all_samples]))
                prov_dict = {sample: json.dumps(self.provenance[sample], sort_keys=True)
                             for sample
                             in all_samples}
                uniq_sample_lists = [[sample
                                         for sample
                                         in prov_dict.keys()
                                         if prov_dict[sample] == prov]
                                  for prov
                                  in uniq_prov_list]
                # Creating string of (first) sample data including provenance
                # Create slot data for each group of samples:
                # 1. uniq_sample_lists is a list of sample lists, each list having the same provenance
                # 2. For each of the lists in uniq_sample_lists, print the list of samples and a formatted version of the provenance
                sample_slots_text = "\n\n".join(["Samples: {samples}\nSlots:\n{slots}".
                                                # format(samples=", ".join(sorted(value) if len(value)<2 else sorted(value[0:1])+["..."]),   #
                                                format(samples=", ".join(sorted(value)),  #
                                                       slots="\n".join(["- {key} ({prov})".
                                                                       format(key=key,
                                                                              prov="->".join(self.provenance[value[0]][key]))
                                                                        for key
                                                                        in self.provenance[value[0]]]))
                                                 for value
                                                 in uniq_sample_lists])
            else:
                # Creating string of (first) sample data not including provenance
                sample_slots_text = "\n".join("- "+key
                                              for key
                                              in self.sample_data[self.sample_data["samples"][0]].keys())

            message = message + """
Samples:
-------------
{sample_list}

Sample slots:
-------------
{sample_slots}
""".format(sample_list=", ".join(self.sample_data["samples"]),
           sample_slots=sample_slots_text)

        return message


    def get_kill_script_name(self):
        """"""
        
        return self.kill_script_obj.script_path
    
    def set_kill_files(self, kill_script_filename_main):
        """ Called by PLC_main to store the qdel filename for the step.
        """
        
        self.kill_script_filename_main = kill_script_filename_main  # Project global qdel filename

    def make_folder_for_sample(self, sample="project_data"):
        """ Creates a folder for sample in this step's results folder
            If sample="project_data", will return the base dir for the step instance
        """

        if sample == "project_data":
            return self.base_dir

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
        # This is so that keys can be separated from values by '=', e.g.
        # See PICARD
        # Can be set: 1. in module init. 2. in params. 3. defaults to ' '
        if not hasattr(self,"arg_separator"):
            self.arg_separator = " "
        # print self.params
        if "arg_separator" in self.params:
            self.arg_separator = self.params["arg_separator"]

        redir_param_script = ""
        if "redir_params" in self.params:
            for key in self.params["redir_params"].keys():
                # The following permits the user to pass two values for the same redirected parameter:
                if isinstance(self.params["redir_params"][key],list):
                    self.write_warning("Passed %s twice as redirected parameter!" % key)
                    for keyval in self.params["redir_params"][key]:
                        redir_param_script += "{key}{sep}{val} \\\n\t".\
                            format(key=key,
                                   val=keyval if keyval is not None else "",
                                   sep=self.arg_separator)
                else:
                    redir_param_script += "{key}{sep}{val} \\\n\t".\
                            format(key=key,
                                   val=self.params["redir_params"][key]
                                       if self.params["redir_params"][key] is not None
                                       else "",
                                   sep=self.arg_separator)

        return redir_param_script

    def get_setenv_part(self):
        """ Returns a piece of code with "env", "setenv" and "export"
        """
        script_const = ""
        # Add "env" line, if it exists:
        # New version

        if "precode" in self.params.keys():         # Add optional code
            script_const += "%s \n" % self.params["precode"]

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
        if not isinstance(self.params["script_path"],str):
            raise AssertionExcept("'script_path' is not a string!")
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
        
        # print "=> ",self.get_step_name()
        try:
            self.params["qsub_params"]
        except KeyError:
            self.params["qsub_params"] = self.pipe_data["qsub_params"]
        else:
                

            # Updating step 'qsub_params' with global 'qsub_params', but with step params taking precedence!
            # 'opts' needs special attention. Needs to be 'updated' independently.
            # 1. deepcopy global qsub params
            # 2. Update with step qsub_params
            # 3. Replace 'opts' with global opts updated with local opts.
            qsub_params = deepcopy(self.pipe_data["qsub_params"])
            qsub_params.update(self.params["qsub_params"])
            qsub_opts = deepcopy(self.pipe_data["qsub_params"]["opts"])
            qsub_opts.update(self.params["qsub_params"]["opts"])
            self.params["qsub_params"] = qsub_params
            self.params["qsub_params"]["opts"] = qsub_opts
            # All steps will have an 'opts' dictionary, at least an empty one...
            


    def local_start(self,base_dir):
        """ Adds code to self.script to enable steps to temporarily write to a local disk before moving to final shared destination
            This can be useful when a lot of IO to the shared disk is detrimental
        """
        # If "local" is set, will do all IO to local folder and then copy everything to self.base_dir
        if "local" in self.params.keys():
            assert self.params["local"], "In step %s: You must supply a local destination when requesting 'local' in parameters" % self.name
            local_dir = "".join([os.sep,
                                self.params["local"].strip(os.sep),
                                os.sep,
                                "_".join(["_".join(self.spec_script_name.split(self.jid_name_sep)), # Convert '..' into "_":
                                          self.pipe_data["run_code"]]),
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
            Used for JSON serialization
        """
        
        ret_dict = dict()
        try:
            ret_dict["sample_data"] = self.get_sample_data()
            # ret_dict["base_sample_data"] = self.get_base_sample_data()
        except AttributeError:
            ret_dict["sample_data"] = None
            # ret_dict["base_sample_data"] = None
        ret_dict["param_data"] = self.params

        # keys_not_to_encode = ["prev_sample_lists"]
        # for key in keys_not_to_encode:
        #     ret_dict["sample_data"].pop(key)
        #
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
{echo_cmd} `date '+%%d/%%m/%%Y %%H:%%M:%%S'` '\\t{step}\\t{stepname}\\t{stepID}\\t' `md5sum {filename}` >> {file}
""".format(echo_cmd=echo_cmd,
           filename=filename,
           step= self.get_step_step(),
           stepname=self.get_step_name(),
           stepID=qsub_name,
           file=self.pipe_data["registration_file"])
        
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
    
        
    def manage_conda_opts(self):
        if "conda" in self.pipe_data and "conda" not in self.params: # Only global "conda" params defined:
            self.params["conda"] = copy(self.pipe_data["conda"])
        if "conda" in self.params:
            if not self.params["conda"]:
                self.write_warning("'conda' is provided but empty. Not 'activating' for this step")
                
            else:  # Conda is not empty
                if "conda" in self.pipe_data:
                    # If different from global, fill in data from global
                    t1 = deepcopy(self.pipe_data["conda"])
                    t1.update(self.params["conda"])
                    self.params["conda"] = deepcopy(t1)
                          
                # Warn if extra parameters passed in conda params
                if filter(lambda x: x not in ["path","env"],self.params["conda"].keys()):
                    self.write_warning("You provided extra 'conda' parameters. They will be ignored!")
                
                # print self.params["conda"]
                self.params["conda"] = manage_conda_params(self.params["conda"])
                # print self.params["conda"]
                # sys.exit()

                # Add bin at end of path
                self.params["conda"]["path"] = os.path.join(self.params["conda"]["path"],"bin")    

                
    def get_step_modifiers(self):
        """ A class method for finding the location of a module for a given step
        """
        
        step_params = []
        
        # find all places in module file (stored in self.path) where a parameter is 
        # referenced in self.params. These are 'modifiers' that the user can modify, 
        # and that the module deals with specifically, beyond those passed with redir_params.
        with open(self.path,"r") as modfh:
            for line in modfh:
                param = re.search('self.params\[\"(.*?)\"\]', line)
                if param:
                    step_params.append(param.group(1))
                    
        # Return the unique list of such params, after excluding the ones that are true for all modules:
        # base, module, script_path, etc.
        return list(set(step_params)-set(["redir_params","qsub_params","base", "module",
                                          "sample_list", "exclude_sample_list", "script_path"]))

    def get_category_levels(self, category):
        """

        :param: category
        :return: List of levels in category
        """
        try:
            return list({self.sample_data[sample]["grouping"][category]
                         for sample
                         in self.sample_data["samples"]})
        except KeyError:
            pp(self.sample_data)
            raise AssertionExcept("Category {cat} not defined for all samples".format(cat=category))

    def get_samples_in_category_level(self, category, cat_level):

        return [sample
                for sample
                in self.sample_data["samples"]
                if self.sample_data[sample]["grouping"][category] == cat_level]


    def create_group_slots(self, category):
        """
        Combines samples types into category groups
        :return:
        """

        cat_levels = self.get_category_levels(category)
        # print cat_levels
        for cat_lev in cat_levels:
            # Creating slot for level data:
            if cat_lev not in self.sample_data:
                self.sample_data[cat_lev] = dict()



    def update_provenance(self):
        """
        Creates and updates a self.sample_data shadow dict with the formation history of each slot
        :return:
        """

        # Samples added in current step
        for sample in [sample
                       for sample
                       in self.sample_data["samples"]
                       if sample not in self.sample_data_original["samples"]]:
            # print "sample -->", sample
            all_keys = list()
            if sample in self.provenance:
                all_keys = itertools.chain(all_keys,self.provenance[sample].keys())
            else:
                self.provenance[sample] = dict()
            if sample in self.sample_data:
                all_keys = itertools.chain(all_keys,self.sample_data[sample].keys())
            for key in all_keys:
                self.provenance[sample][key] = [">"+self.get_step_name()]
        # Samples removed in current step
        for sample in [sample
                       for sample
                       in self.sample_data_original["samples"]
                       if sample not in self.sample_data["samples"]]:
            # print "sample -->", sample
            all_keys = list()
            if sample in self.provenance:
                all_keys = itertools.chain(all_keys,self.provenance[sample].keys())
            if sample in self.sample_data:
                all_keys = itertools.chain(all_keys,self.sample_data_original[sample].keys())
            for key in all_keys:
                self.provenance[sample][key].append(self.get_step_name()+"|")

        # Get samples that were not added or removed, + project_data:
        sample_and_proj_list = list(set(self.sample_data["samples"]) &
                                    set(self.sample_data_original["samples"]) |
                                    set(["project_data"]))
        # # sample_and_proj_list.append("project_data")
        # print "--------- %s ---------------------" % self.get_step_name()
        # print sample_and_proj_list
        # print "P> ",self.provenance["project_data"].keys()
        # print "S> ",self.sample_data["project_data"].keys()
        # print "O> ",self.sample_data_original["project_data"].keys()
        # print "------------------------------"

        for sample in sample_and_proj_list:
            all_keys = list()
            if sample in self.provenance:
                all_keys = itertools.chain(all_keys,self.provenance[sample].keys())
            if sample in self.sample_data:
                all_keys = itertools.chain(all_keys,self.sample_data[sample].keys())
            if sample in self.sample_data_original:
                all_keys = itertools.chain(all_keys,self.sample_data_original[sample].keys())
            # Gey unique keys!
            all_keys = list(set(all_keys))

            for key in all_keys:
                if key in self.sample_data[sample] and key in self.sample_data_original[sample]:
                    if self.sample_data[sample][key] != self.sample_data_original[sample][key]:
                        self.provenance[sample][key].append(self.get_step_name())
                elif key in self.sample_data[sample]: # And not in original!
                    self.provenance[sample][key] = [">"+self.get_step_name()]
                elif key in self.sample_data_original[sample]:  # And not in current!
                    self.provenance[sample][key].append(self.get_step_name()+"|")
                else:
                    pass

    def create_provenance(self):
        """
        Create a provenance dict based on sample_da
        :return:
        """

        self.provenance = dict()
        sample_and_proj_list = deepcopy(self.sample_data["samples"])
        sample_and_proj_list.append("project_data")
        for sample in sample_and_proj_list:
            self.provenance[sample] = {key:[">"+self.get_step_name()] for key in self.sample_data[sample]}

    def get_provenance(self):
        return self.provenance

    def get_step_tag(self):
        """ Returns the step tag, if one was defined"""

        if "tag" in self.params:
            if isinstance(self.params["tag"], list):
                raise AssertionExcept("Duplicate tagts defined. At the moment, only one tag permitted per step")
                # return self.params["tag"]
            elif self.params["tag"] is None:  # This is to stop an instance from inheriting tag
                return [False]
            else:
                return [self.params["tag"]]
        # If tag is defined in one of bases, use it (first found, first use. In future, enable lists of tags...
        elif self.get_base_step_list() is not None and \
                any(["tag" in base_step.params
                     for base_step
                     in self.get_base_step_list()]):  # One of bases has a tag:
            for base_step in self.get_base_step_list():
                if "tag" in base_step.params:
                    self.params["tag"] = base_step.params["tag"]
                    return [self.params["tag"]]
        else:
            return [False]

    def get_sample_list_by_category(self, sample_dict):

        if "category" not in sample_dict:
            raise AssertionExcept("You must include a 'category' in sample_list, if passing a dict!")

        if type(sample_dict["category"]) not in [str, int]:
            raise AssertionExcept("Category must be a single value, not a list etc.")

        # Check all samples have grouping data
        bad_samples = [sample
                       for sample
                       in self.sample_data["samples"]
                       if "grouping" not in self.sample_data[sample]]
        if bad_samples:
            raise AssertionExcept("For some reason, sample '{smp}' does not have "
                                  "grouping data".format(smp=", ".join(bad_samples)))
        # Check category is in all samples
        bad_samples = [sample
                       for sample
                       in self.sample_data["samples"]
                       if sample_dict["category"] not in self.sample_data[sample]["grouping"]]
        if bad_samples:
            raise AssertionExcept(
                "Sample '{smp}' does not have '{cat}' category".format(smp=", ".join(bad_samples),
                                                                       cat=sample_dict["category"]))

        if type(sample_dict["levels"]) not in [str,list]:
            raise AssertionExcept("In sample_list, level must be a string or a list of strings.")
        # Check all levels exist in category
        if not all(
                map(lambda level: level in self.get_category_levels(sample_dict["category"]), sample_dict["levels"])):
            bad_levels = ", ".join([level for level in sample_dict["levels"] if
                                    level not in self.get_category_levels(sample_dict["category"])])
            raise AssertionExcept("Level '{lev}' is not defined for "
                                  "category '{cat}'".format(lev=bad_levels,
                                                            cat=sample_dict["category"]))
        # Create new sample list:
        samples = list()
        for level in sample_dict["levels"]:
            samples.extend(self.get_samples_in_category_level(sample_dict["category"], level))

        return samples

