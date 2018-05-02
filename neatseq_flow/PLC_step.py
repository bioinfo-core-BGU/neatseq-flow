
""" A class defining a step in the pipeline.

"""
import os, shutil, sys, re, importlib
import traceback
import datetime

# from script_constructors.ScriptConstructorSGE import HighScriptConstructorSGE, KillScriptConstructorSGE

from copy import *
from pprint import pprint as pp

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"



class AssertionExcept(Exception):
    """A class to be raised by modules failing at assertions
    """
    def __init__(self, comment = "Unknown problem", sample = None, step = None):
        """ initializize with error comment and sample, if exists)
            step is not required. Can be set later with set_step_name()
            """
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
            self.comment = error_str + ": " + self.comment if error_str else self.comment
        
        return self.comment




class Step:
    """ A class that defines a pipeline step name (=instance).
    """
    Cwd = os.path.dirname(os.path.abspath(__file__))

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
                    sys.stderr.write("WARNING: Module path %s seems to be empty! Possibly issue with permissions..." % \
                                     module_path)
                while mod_t + ".py" not in level[2]:
                    # Repeat while expected filename is NOT in current dir contents (=level[2]. see above)
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
            sys.stderr.write("WARNING: Module path %s seems to be empty! Possibly issue with permissions..." % self.Cwd)

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


        
                
        
        
        
        
        
        
        
        
        
        
        
        
    def __init__(self,name,step_type,params,pipe_data,module_path):
        """ should not be used. only specific step inits should be called. 
            Maybe a default init can be defined as well. check.
        """
        self.name = name
        self.step = step_type
        self.params = params
        self.pipe_data = pipe_data
        
        self.path = module_path
        
        ###### Place for testing parameters:
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
       
        
        self.jid_list = []      # Initialize a list to store the list of jids of the current step
        
        # The following line defines A list of jids from current step that all other steps should depend on.
        # Is used to add a prelimanry step, equivalent to the "wrapping up" step that is dependent on all previous scripts
        self.preliminary_jids =[]  

        # self.skip_scripts determines whether scripts will be created. 
        # Defaults to False, unless SKIP is defined in parameters.
        # This is supposed:
        # A. to enable steps to avoid script building by setting to True.
        #    See for example del_type, move_type (now generalized in manage_types)
        #    In this case, set skip_scripts to True in step_specific_init(). skip_step_sample_initiation will be set to False by default.
        # B. To enable skipping a step while leaving the flow scheme intact (i.e. a step is like a channel for types without actually doing anything. Same as commenting it out but saves resetting bases...)
        #    In this case, both skip_scripts and skip_step_sample_initiation are set to True, because some of the modifications to sample_data are performed in self.step_sample_initiation(). 
        #    In the step_specific_init() function no changes to sample_data are possible because it is not set yet at that stage!
        if "SKIP" in self.params:
            self.skip_scripts = True
            self.skip_step_sample_initiation = True   # This is so that modifications to sample_data requested in step_sample_initiation() will not be performed if SKIP is set.
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
                raise AssertionExcept("Please do not pass the following redirected parameters. They are set automatically or module is not defined to use them. %s" % ", ".join(auto_redirs))
        except AttributeError:  # Ignore if auto_redirs not defined for module. It is highly recommended to do so...
            pass
        except KeyError as keyerr:
            if keyerr.args[0]=="redir_params":
                self.write_warning("No 'redirects' defined.")
                pass
            else:
                raise keyerr
        except:
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
        
        return """
Name:         {name}
Step:         {module}
Base:         {base}
Dependencies: {depends}""".format(name = self.name, 
                                module = self.step, 
                                base   = [step.get_step_name() for step in self.get_base_step_list()] if self.get_base_step_list() else None, 
                                depends = self.get_depend_list())
        
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
            raise AssertionExcept("Invalid base list\n", step = self.get_step_name())
        
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
        self.kill_script_obj = getScriptConstructorClass(step = self.get_step_step(), \
                                                name = self.get_step_name(), \
                                                number = self.step_number, \
                                                shell = self.shell,
                                                params = self.params,
                                                pipe_data = self.pipe_data)
        # Store path to kill script in params:
        self.params["kill_script_path"] = self.kill_script_obj.script_path

        getScriptConstructorClass = self.import_ScriptConstructor(level="high")

        ## Create main script class
        self.main_script_obj = getScriptConstructorClass(step = self.get_step_step(),
                                                         name = self.get_step_name(),
                                                         number = self.step_number,
                                                         shell = self.shell,
                                                         kill_obj=self.kill_script_obj,
                                                         params = self.params,
                                                         pipe_data = self.pipe_data)

        
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
        
        dependency_list = ",".join(self.get_dependency_jid_list())
        return self.main_script_obj.get_depends_command(dependency_list)
        
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
        if "exclude_sample_list" in self.params:
            if not isinstance(self.params["exclude_sample_list"] , list):
                self.params["exclude_sample_list"] = re.split("[, ]+", self.params["exclude_sample_list"])
            if set(self.params["exclude_sample_list"])-set(self.pipe_data["samples"]):
                raise AssertionExcept("'sample_list' includes samples not defined in sample data!", step=self.get_step_name())
            self.params["sample_list"] = list(set(self.pipe_data["samples"]) - set(self.params["exclude_sample_list"]))

        if "sample_list" in self.params:
            if self.params["sample_list"] == "all_samples":
                self.sample_data["samples"] = self.pipe_data["samples"]
            else:
                if not isinstance(self.params["sample_list"] , list):
                    self.params["sample_list"] = re.split("[, ]+", self.params["sample_list"])
                if set(self.params["sample_list"])-set(self.pipe_data["samples"]):
                    raise AssertionExcept("'sample_list' includes samples not defined in sample data!", step=self.get_step_name())
                self.sample_data["samples"] = self.params["sample_list"]



        # Trying running step specific sample initiation script:
        try:
            if not self.skip_step_sample_initiation:
                self.step_sample_initiation()
        except AttributeError:
            pass    # It dosen't have to be defined.
        except AssertionExcept as assertErr: 
            assertErr.set_step_name(self.get_step_name())
            raise assertErr


    def get_main_command(self):
        """ Return the command to put in the main workflow script to run the main step script.
        """

        return self.main_script_obj.get_command()

        
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
        
        
    def import_ScriptConstructor(self, level): #modname, classname):
        """Returns a class of "classname" from module "modname". 
        """

        level = level.lower().capitalize()
        modname = "neatseq_flow.script_constructors.scriptconstructor{executor}".format(executor=self.pipe_data["Executor"])
        classname = "{level}ScriptConstructor{executor}".format(level=level, executor=self.pipe_data["Executor"] )  #SGE"
        return getattr(importlib.import_module(modname), classname)

        
    def create_low_level_script(self):
        """ Create the low (i.e. 3rd) level scripts, which are the scripts that actually do the work
            The actual part of the script is produced by the particular step class.
            This function is responsible for the generic part: opening the file and writing the qsub parameters and the script
        """
        getChildClass = self.import_ScriptConstructor(level="low")
        # Create ScriptConstructor for low level script.
        self.child_script_obj = \
            getChildClass(step = self.get_step_step(),
                          name = self.get_step_name(),
                          number = self.step_number,
                          shell = self.shell,
                          params = self.params,
                          kill_obj=self.kill_script_obj,
                          pipe_data = self.pipe_data,
                          # This is set by the module build_scripts() function:
                          id = self.spec_script_name)

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
        dependency_jid_list = self.get_dependency_jid_list() 
        # Add prelimanry jids if exist (if not, is an empty list and will not affect the outcome)
        # Adding at the head of the list. That's why is done in two steps - just to make it clearer.
        dependency_jid_list = self.preliminary_jids + dependency_jid_list
        
        # Request low-level script construction from LowScriptConstructor:
        self.child_script_obj.write_script(script = self.script, 
                                            dependency_jid_list = dependency_jid_list,
                                            stamped_files = self.stamped_files)
        
        
        
        # Clear stamped files list
        self.stamped_files = list()

        # Add child command execution lines to main script:
        self.main_script_obj.write_command(self.main_script_obj.get_child_command(self.child_script_obj))
        # qdel_line = self.child_script_obj.get_kill_command(),\
                                                # script_path = self.child_script_obj.script_path,\
                                                # script_id = self.child_script_obj.script_id)

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
        
        # TODO: Send to be done in ScriptConstructors!
        # -------------------------------------
        # Add qdel command to main qdel script:
        self.main_script_obj.main_script_kill_commands(self.kill_script_filename_main)
        # main_script_obj.main_script_kill_commands() should enter main script killing commands into main file
        # at '# entry point'. This is done so so that steps are killed in reverse order.
        # f = open(self.kill_script_filename_main,'r')
        # kill_file = f.read()
        # f.close()
        #
        # kill_file = re.sub("# entry_point", "# entry_point\n{kill_cmd}".format(kill_cmd=self.main_script_obj.get_kill_command()),kill_file)
        #
        # f = open(self.kill_script_filename_main,'w')
        # f.write(kill_file)
        # f.close()
        # -------------------------------------
        
        
        dependency_jid_list = self.get_dependency_jid_list()# + self.preliminary_jids  
        
        # Write main script preamble:
        self.main_script_obj.write_command(self.main_script_obj.get_script_preamble(dependency_jid_list))
        
        
        # The actual qsub commands must be written in the create_low_level_script() function because they are step_name dependent!
            
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
        # Creating script. If 'create_spec_preliminary_script' is not defined or returns nothing, return from here without doing anything
        self.script = ""
        try:
            self.create_spec_preliminary_script()
        except AttributeError:
            return 

        if not self.script.strip():                 # If script is empty, do not create a wrapper function
            return 
        
        # self.spec_qsub_name = "_".join([self.step,self.name,"preliminary"])
        getChildClass = self.import_ScriptConstructor(level="low")
        # Create ScriptConstructor for low level script.
        self.prelim_script_obj = \
            getChildClass(step = self.get_step_step(),
                          name = self.get_step_name(),
                          number = self.step_number,
                          shell = self.shell,
                          params = self.params,
                          kill_obj=self.kill_script_obj,
                          pipe_data = self.pipe_data,
                          id = "_".join([self.step,self.name,"preliminary"]))

        # Get dependency jid list and add preliminary jids if exist
        # (if not, is an empty list and will not affect the outcome)
        #    Also, add all jids of current step, as this script is to run only after all previous steps have completed.
        dependency_jid_list = self.get_dependency_jid_list()

        self.prelim_script_obj.write_script(script = self.script,
                                            dependency_jid_list = dependency_jid_list,
                                            stamped_files = self.stamped_files)
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

        self.spec_qsub_name = "_".join([self.step,self.name,"wrapping_up"])

        getChildClass = self.import_ScriptConstructor(level="low")

        # Create ScriptConstructor for low level script.
        self.wrap_script_obj = \
            getChildClass(step = self.get_step_step(),
                          name = self.get_step_name(),
                          number = self.step_number,
                          shell = self.shell,
                          params = self.params,
                          kill_obj=self.kill_script_obj,
                          pipe_data = self.pipe_data,
                          id = self.spec_qsub_name)

        # Get dependency jid list and add preliminary jids if exist
        # (if not, is an empty list and will not affect the outcome)
        #    Also, add all jids of current step, as this script is to run only after all previous steps have completed.
        dependency_jid_list = self.preliminary_jids + self.get_jid_list() + self.get_dependency_jid_list()
        
        # Removing parent name from wrapping_up dependencies
        dependency_jid_list.remove(self.main_script_obj.script_id)
        self.wrap_script_obj.write_script(script = self.script, 
                                          dependency_jid_list = dependency_jid_list,
                                          stamped_files = self.stamped_files)
        # Clear stamped files list
        self.stamped_files = list()
        
        self.main_script_obj.write_command(self.main_script_obj.get_child_command(self.wrap_script_obj))
        # qdel_line = self.wrap_script_obj.get_kill_command(),\
                                        # script_path = self.wrap_script_obj.script_path,\
                                        # script_id = self.wrap_script_obj.script_id)


        # This is here because I want to use jid_list to make wrapping_up script dependent on this step's main low-level scripts
        # Explantion: get_jid_list() was used above (line 'qsub_header...') to make the wrapping_up script dependent on the other scripts created by the step
        #    Now that that is done, the following line adds this step to the jid_list, so that subsequent steps are dependent on the wrapping up script as well. (I hope this makes it clear...)
        self.add_jid_to_jid_list(self.wrap_script_obj.script_id)

        # Adding to qsub_names_dict:
        self.qsub_names_dict["low_qsubs"].append(self.spec_qsub_name)
        
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

    
        if "stop_and_show" in self.params:
            print "project slots:\n-------------"
            pp(self.sample_data.keys())
            
            if self.sample_data["samples"]:  # Sample list may be empty if only project data was passed!
                print "sample slots:\n-------------"
                pp(self.sample_data[self.sample_data["samples"][0]].keys())

            sys.exit("Showed. Now stopping. To continue, remove the 'stop_and_show' tag from %s" % self.get_step_name())
            

        
        
    def get_kill_script_name(self):
        """"""
        
        return self.kill_script_obj.script_path
    
    def set_kill_files(self, kill_script_filename_main):
        """ Called by PLC_main to store the qdel filename for the step.
        """
        
        self.kill_script_filename_main = kill_script_filename_main  # Project global qdel filename
        
        
        
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
            # ret_dict["base_sample_data"] = self.get_base_sample_data()
        except AttributeError:
            ret_dict["sample_data"] = None
            # ret_dict["base_sample_data"] = None
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
                
                
                if not self.params["conda"]["path"]: # == None:  # Path is empty (None or "", take from $CONDA_PREFIX
                    # 1. If CONDA_BASE defined, use it
                    # 2. If CONDA_PREFIX defined, compute CONDA_BASE from `conda info --root`
                    # 3. Fail
                    if "CONDA_BASE" in os.environ:
                        self.params["conda"]["path"] = os.environ["CONDA_BASE"]
                        if "env" not in self.params["conda"] or not self.params["conda"]["env"]: ##==None:
                            raise AssertionExcept("'conda: path' is empty, taking from CONDA_BASE. Failed because no 'env' was passed. When using CONDA_BASE, you must supply an environment name with 'conda: env'",step=self.get_step_name())

                    else:
                        raise AssertionExcept("""'conda' 'path' is empty, but no CONDA_BASE is defined. 
Make sure you are in an active conda environment, and that you executed the following command:
> {start_col}export CONDA_BASE=$(conda info --root){end_col}
""".format(start_col='\033[93m',end_col='\033[0m'),step = self.get_step_name())
                
                    
                    
                if "env" not in self.params["conda"] or not self.params["conda"]["env"]:# == None:
                    # if self.pipe_data["conda"]["env"]:
                        # self.write_warning("'env' is empty. Using global 'env'")
                    try:
                        self.params["conda"]["env"] = self.pipe_data["conda"]["env"]
                    except KeyError:
                        raise AssertionExcept("You must supply an 'env' in conda params.", step=self.get_step_name())
                    else:
                        self.write_warning("'env' is empty. Using global 'env'")
                    # re_env = re.search("envs/(\S+)", self.params["conda"]["path"])
                    # try:
                        # self.params["conda"]["env"] = re_env.group(1)
                    # except:
                        # raise AssertionExcept("Bad conda env path. Make sure it ends with 'envs/ENV_NAME'", step=self.get_step_name())
                
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
                    
        # Return the unique list of such params, after excluding the ones that are true for all modules: base, module, script_path, etc.
        return list(set(step_params)-set(["redir_params","qsub_params","base", "module", "sample_list", "exclude_sample_list", "script_path"]))

