import os, shutil, sys, re
import traceback
import datetime


from copy import *
from pprint import pprint as pp

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"


class ScriptConstructorSGE(ScriptConstructor):

    def __init__(self, name, path):
        """ Create a script constructor with name(i.e. 'qsub_name') and script path
        """
        
        pass
        
    
    
#### Methods for adding lines:
    def add_header(self):
        """
        """
        pass
        
    def add_trap_line(self):
        """
        """
        pass
        
        
    def add_log_line(self):
        """
        """
        pass
        
        
    def add_del_line(self):
        """
        """
        pass
        
        
    def add_activate_lines(self):
        """
        """
        pass
        
        
    def add_set_options_line(self):
        """
        """
        pass
        
        
    def add_script(self):
        """
        """
        pass
        
        
    def add_register_files(self):
        """
        """
        pass
        
        
    
class HighScriptConstructor(ScriptConstructor):
    """
    """
    
    pass
    
class LowScriptConstructor(ScriptConstructor):
    """
    """
    
    pass
    
    
    # def make_sbatch_header(self, jid_list, script_lev = "low"):
        # """ Make the first few lines for the scripts
            # Is called for high level, low level and wrapper scripts
        # """
        
        # only_low_lev_params  = "-n --ntasks -c --cpus-per-task".split(" ")
        # compulsory_high_lev_params = {"--export":"ALL"}
        # # special_opts = "-J --job-name -e -o -q -hold_jid".split(" ") + only_low_lev_params
        
        # # qsub_shell = "#!/bin/%(shell)s\n#$ -S /bin/%(shell)s" % {"shell": self.shell}
        # qsub_shell = "#!/bin/%(shell)s"  % {"shell": self.shell}  # I haven't discovered how to change the default SBATCH shell...
        
        # # Make hold_jids line only if there are jids (i.e. self.get_dependency_jid_list() != [])
        # if jid_list:
            # qsub_holdjids = "#$ -hold_jid %s " % jid_list
        # else:
            # qsub_holdjids = ""
        # qsub_name =    "#SBATCH --job-name %s " % (self.spec_qsub_name)
        # qsub_stderr =  "#SBATCH -e {stderr_dir}{name}.e%J".format(stderr_dir=self.pipe_data["stderr_dir"],name=self.spec_qsub_name)
        # qsub_stdout =  "#SBATCH -o {stdout_dir}{name}.o%J".format(stdout_dir=self.pipe_data["stdout_dir"],name=self.spec_qsub_name) 
        # qsub_queue =   "#SBATCH --partition %s" % self.params["qsub_params"]["queue"]

        # # Create lines containing the qsub opts.
        # qsub_opts = ""
        # for qsub_opt in self.params["qsub_params"]["opts"]:
            # if qsub_opt in only_low_lev_params and script_lev=="high":
                # continue
            # qsub_opts += "#SBATCH {key} {val}\n".format(key=qsub_opt, val=self.params["qsub_params"]["opts"][qsub_opt]) 
            
        
        # # Adding 'compulsory_high_lev_params' to all high level scripts (This includes '-V'. Otherwise, if shell is bash, the SGE commands are not recognized)
        # if script_lev == "high":
            # for qsub_opt in compulsory_high_lev_params:
                # if qsub_opt not in self.params["qsub_params"]["opts"]:
                    # qsub_opts += "#$ {key} {val}\n".format(key=qsub_opt, 
                                                    # val=compulsory_high_lev_params[qsub_opt]) 


        # # Adding node limitation to header, but only for low-level scripts
        # if script_lev == "low":
            # if self.params["qsub_params"]["node"]:     # If not defined then this will be "None"
                # # qsub_queue += "@%s" % self.params["qsub_params"]["node"]
                # qsub_queue = "#SBATCH --nodelist %s" % ",".join(self.params["qsub_params"]["node"])

        # # Sometimes qsub_opts is empty and then there is an ugly empty line in the middle of the qsub definition. Removing the empty line with replace()
        # return "\n".join([qsub_shell,
                            # qsub_queue,
                            # qsub_opts,
                            # qsub_name,
                            # qsub_stderr,
                            # qsub_stdout,
                            # qsub_holdjids]).replace("\n\n","\n") + "\n\n"



    # def make_local_header(self, jid_list, script_lev = "low"):
        # """ Make the first few lines for the scripts
            # Is called for high level, low level and wrapper scripts
        # """
        

        # qsub_shell = "#!/bin/%(shell)s"  % {"shell": self.shell}  # I haven't discovered how to change the default SBATCH shell...
        
        # # Make hold_jids line only if there are jids (i.e. self.get_dependency_jid_list() != [])
        # if jid_list:
            # qsub_holdjids = "#$ -hold_jid %s " % jid_list
        # else:
            # qsub_holdjids = ""

        
        # # Sometimes qsub_opts is empty and then there is an ugly empty line in the middle of the qsub definition. Removing the empty line with replace()
        # return "\n".join([qsub_shell,
                            # qsub_holdjids]).replace("\n\n","\n") + "\n\n"
        
