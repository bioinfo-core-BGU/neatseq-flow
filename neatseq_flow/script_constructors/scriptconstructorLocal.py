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
        
        script = ""


        if "slow_release" in self.params.keys():
            sys.exit("Slow release no longer supported. Use 'job_limit'")

        else:
            script += """\
sh {nsf_exec} \\
    {script_id} \\
    1> {stdout} \\
    2> {stderr} & \n\n""".format(script_id = self.script_id,
                          nsf_exec = self.pipe_data["exec_script"],
                          stderr = "{dir}{id}.e".format(dir=self.pipe_data["stderr_dir"], id=self.script_id),
                          stdout = "{dir}{id}.o".format(dir=self.pipe_data["stdout_dir"], id=self.script_id))


        return script

        
#### Methods for adding lines:
        
                
        
        
###################################################
        
        
    def get_kill_command(self):
        """
        """
        pass
        # TODO: somehow this has to be the numeric run-0time job id!
        # return "# scancel JOB_ID \n" #{script_name}".format(script_name = self.script_id)
        
    def get_script_header(self):
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


        
    def get_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        general_header = super(HighScriptConstructorLocal, self).get_script_header(**kwargs)


        return general_header + "\n\n"

    def get_command(self):
        """ Writing low level lines to high level script: job_limit loop, adding qdel line and qsub line
            spec_qsub_name is the qsub name without the run code (see caller)
        """
        
        if "job_limit" in self.pipe_data.keys():
            sys.exit("Job limit not supported yet for Local!")


        command = super(HighScriptConstructorLocal, self).get_command()

        

        # TODO: Add output from stdout and stderr

        script = """
# ---------------- Code for {script_id} ------------------
echo running {script_id}
{command}

""".format(script_id = self.script_id,
        command = command)
        
        
        return script
                            
                     
    def get_child_command(self, script_obj):
        """ Writing low level lines to high level script: job_limit loop, adding qdel line and qsub line
            spec_qsub_name is the qsub name without the run code (see caller)
        """
        
        
        script = ""

        
        if "job_limit" in self.pipe_data.keys():
            sys.exit("Job limit not supported yet for Local!")

        # TODO: Add output from stdout and stderr

        script += """
# ---------------- Code for {script_id} ------------------

{child_cmd}

""".format(script_id = script_obj.script_id,
        child_cmd = script_obj.get_command())
        
        
        return script
                            
                            
                            
                            
    def get_script_postamble(self):
        """ Local script postamble is same as general postamble with addition of sed command to mark as finished in run_index
        """
    
        # Get general postamble
        postamble = super(HighScriptConstructorLocal, self).get_script_postamble()

        # Add sed command:
        script = """\
{postamble}

# Setting script as done in run index:
sed -i -e "s:^{script_id}$:# {script_id}:" {run_index}""".format(\
    postamble = postamble, 
    run_index = self.pipe_data["run_index"],
    script_id = self.script_id)
        
        return script
                            
                            
####----------------------------------------------------------------------------------
    
class LowScriptConstructorLocal(ScriptConstructorLocal,LowScriptConstructor):
    """
    """

    def get_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        
        general_header = super(LowScriptConstructorLocal, self).get_script_header(**kwargs)


        # Sometimes qsub_opts is empty and then there is an ugly empty line in the middle of the qsub definition. Removing the empty line with replace()
        return general_header + "\n\n"

        


    def write_script(self,
                        script,
                        dependency_jid_list,
                        stamped_files, **kwargs):

        if "level" not in kwargs:
            kwargs["level"] = "low"

        super(LowScriptConstructorLocal, self).write_script(script,
                                                        dependency_jid_list,
                                                        stamped_files,
                                                        **kwargs)

        
        self.write_command("""\

# Setting script as done in run index:
sed -i -e "s:^{script_id}$:# {script_id}:" {run_index}""".format(\
    run_index = self.pipe_data["run_index"],
    script_id = self.script_id))
        
####----------------------------------------------------------------------------------

class KillScriptConstructorLocal(ScriptConstructorLocal,KillScriptConstructor):


    pass