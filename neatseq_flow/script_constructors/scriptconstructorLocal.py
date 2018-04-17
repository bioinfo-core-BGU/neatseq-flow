import os, shutil, sys, re
import traceback
import datetime


from copy import *
from pprint import pprint as pp

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"


from scriptconstructor import *


class ScriptConstructorLocal(ScriptConstructor):

        
        
    def get_command(self):
        """ Returnn the command for executing the this script
        """
        
        qsub_line = ""
        qsub_line += "echo running " + self.name + " ':\\n------------------------------'\n"
        
        # slow_release_script_loc = os.sep.join([self.pipe_data["home_dir"],"utilities","qsub_scripts","run_jobs_slowly.pl"])

        if "slow_release" in self.params.keys():
            sys.exit("Slow release no longer supported. Use 'job_limit'")

        else:
            qsub_line += "{nsf_exec} {scripts_dir}{script_name}\n".format(scripts_dir = self.pipe_data["scripts_dir"], 
                                                                        script_name = self.script_name,
                                                                        nsf_exec = self.pipe_data["exec_script"])

        qsub_line += "\n\n"
        return qsub_line

        
#### Methods for adding lines:
        
                
        
        
###################################################
        
        
    def get_kill_command(self):
        """
        """
        pass
        # TODO: somehow this has to be the numeric run-0time job id!
        # return "# scancel JOB_ID \n" #{script_name}".format(script_name = self.script_id)
        
    def make_script_header(self):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

            
        qsub_header = """#!/bin/{shell}\n""".format(shell      = self.shell)
        
        if self.dependency_jid_list:
            qsub_header += "#$ -hold_jid %s " % self.dependency_jid_list
            
        return qsub_header  
        
        
        

        
        
        
####----------------------------------------------------------------------------------

class HighScriptConstructorLocal(ScriptConstructorLocal,HighScriptConstructor):
    """
    """
    
        

    def get_depends_command(self, dependency_list):
        """
        """
        
        return ""  # scontrol bla bla bla... Find out how is done\n\n"#qalter \\\n\t-hold_jid %s \\\n\t%s\n\n" % (dependency_list, self.script_id)


        
    def make_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        general_header = super(HighScriptConstructorLocal, self).make_script_header(**kwargs)


        return general_header + "\n\n"


    def write_child_command(self, script_obj):
        """ Writing low level lines to high level script: job_limit loop, adding qdel line and qsub line
            spec_qsub_name is the qsub name without the run code (see caller)
        """
        
        
        script = ""

        
        if "job_limit" in self.pipe_data.keys():
            sys.exit("Job limit not supported yet for Local!")

        # TODO: Add output from stdout and stderr
        script += """
# ---------------- Code for {script_id} ------------------

{nsf_exec} {script_id}

""".format(script_id = script_obj.script_id,
        nsf_exec = self.pipe_data["exec_script"])
        
        
        self.filehandle.write(script)
                            
                            
                            
                            
####----------------------------------------------------------------------------------
    
class LowScriptConstructorLocal(ScriptConstructorLocal,LowScriptConstructor):
    """
    """

    def make_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        
        general_header = super(LowScriptConstructorLocal, self).make_script_header(**kwargs)


        # Sometimes qsub_opts is empty and then there is an ugly empty line in the middle of the qsub definition. Removing the empty line with replace()
        return general_header + "\n\n"

        
        
####----------------------------------------------------------------------------------

class KillScriptConstructorLocal(ScriptConstructorLocal,KillScriptConstructor):


    pass