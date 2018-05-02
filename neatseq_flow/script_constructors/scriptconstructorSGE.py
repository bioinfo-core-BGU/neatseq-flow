import os, shutil, sys, re
import traceback
import datetime


from copy import *
from pprint import pprint as pp

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"


from scriptconstructor import *


class ScriptConstructorSGE(ScriptConstructor):
    """ Class for implementing ScriptConstructor class for SGE executor
    """

    @classmethod
    def get_helper_script(cls, log_file, qstat_path):
        """ Returns the code for the helper script
        """


        script = super(ScriptConstructorSGE, cls).get_helper_script(log_file,qstat_path)

        return script

    @classmethod
    def get_exec_script(cls, pipe_data):
        """ Not used for SGE. Returning None"""

        return None

    def get_command(self):
        """ Return the command for executing this script
        """
        script = ""

        if "slow_release" in self.params.keys():
            sys.exit("Slow release no longer supported. Use 'job_limit'")
        else:
            script = """\
qsub {script_path}
""".format(script_path = self.script_path)

        return script

        
    def get_kill_command(self):
    
        return "qdel {script_name}".format(script_name = self.script_id)
        
    def get_script_header(self):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        qsub_shell = "#!/bin/%(shell)s\n#$ -S /bin/%(shell)s" % {"shell": self.shell}
        # Make hold_jids line only if there are jids (i.e. self.get_dependency_jid_list() != [])
        if self.dependency_jid_list:
            qsub_holdjids = "#$ -hold_jid %s " % self.dependency_jid_list
        else:
            qsub_holdjids = ""
        qsub_name =    "#$ -N %s " % (self.script_id)
        qsub_stderr =  "#$ -e %s" % self.pipe_data["stderr_dir"]
        qsub_stdout =  "#$ -o %s" % self.pipe_data["stdout_dir"]
        # qsub_queue =   "#$ -q %s" % self.params["qsub_params"]["queue"]

        return "\n".join([qsub_shell,
                          qsub_name,
                          qsub_stderr,
                          qsub_stdout,
                          qsub_holdjids]).replace("\n\n","\n")

        

        
        
        
####----------------------------------------------------------------------------------

class HighScriptConstructorSGE(ScriptConstructorSGE,HighScriptConstructor):
    """ A class for creating the high-level script for NeatSeq-Flow when Executor is SGE
    """

    def get_depends_command(self, dependency_list):
        """
        """
        
        return "qalter \\\n\t-hold_jid %s \\\n\t%s\n\n" % (dependency_list, self.script_id)
    # dependency_list

        
    def get_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        general_header = super(HighScriptConstructorSGE, self).get_script_header(**kwargs)

        only_low_lev_params  = ["-pe"]
        compulsory_high_lev_params = {"-V":""}
        # special_opts = "-N -e -o -q -hold_jid".split(" ") + only_low_lev_params

        qsub_queue =   "#$ -q %s" % self.params["qsub_params"]["queue"]

        # Create lines containing the qsub opts.
        qsub_opts = ""
        for qsub_opt in self.params["qsub_params"]["opts"]:
            if qsub_opt in only_low_lev_params:
                continue
            qsub_opts += "#$ {key} {val}\n".format(key=qsub_opt, val=self.params["qsub_params"]["opts"][qsub_opt]) 


        # Adding 'compulsory_high_lev_params' to all high level scripts (This includes '-V'. Otherwise, if shell is bash, the SGE commands are not recognized)
        for qsub_opt in compulsory_high_lev_params:
            if qsub_opt not in self.params["qsub_params"]["opts"]:
                qsub_opts += "#$ {key} {val}\n".format(key=qsub_opt, 
                                                val=compulsory_high_lev_params[qsub_opt]) 


        # Sometimes qsub_opts is empty and then there is an ugly empty line in the middle of the qsub definition. Removing the empty line with replace()
        return "\n".join([general_header,
                            qsub_queue,
                            qsub_opts]).replace("\n\n","\n") + "\n\n"

                            
    def get_command(self):
        """ Writing low level lines to high level script: job_limit loop, adding qdel line and qsub line
            spec_qsub_name is the qsub name without the run code (see caller)
            """

        job_limit = ""

        if "job_limit" in self.pipe_data.keys():
            job_limit = """
# Sleeping while jobs exceed limit
while : ; do numrun=$({qstat} -u $USER | wc -l ); maxrun=$(sed -ne "s/limit=\([0-9]*\).*/\\1/p" {limit_file}); sleeptime=$(sed -ne "s/.*sleep=\([0-9]*\).*/\\1/p" {limit_file}); [[ $numrun -ge $maxrun ]] || break; sleep $sleeptime; done
""".format(limit_file=self.pipe_data["job_limit"],
           qstat=self.pipe_data["qsub_params"]["qstat_path"])

        command = super(HighScriptConstructorSGE, self).get_command()

        

        # TODO: Add output from stdout and stderr

        script = """
# ---------------- Code for {script_id} ------------------
{job_limit}
echo running {script_id}
{command}

""".format(script_id = self.script_id,
           job_limit=job_limit,
           command = command)
        
        
        return script                            
                            
                            
                            

    def get_child_command(self, script_obj):
        """ Writing low level lines to high level script: job_limit loop, adding qdel line and qsub line
            spec_qsub_name is the qsub name without the run code (see caller)
        """

        job_limit = ""

        if "job_limit" in self.pipe_data.keys():
            job_limit = """
# Sleeping while jobs exceed limit
while : ; do numrun=$({qstat} -u $USER | wc -l ); maxrun=$(sed -ne "s/limit=\([0-9]*\).*/\\1/p" {limit_file}); sleeptime=$(sed -ne "s/.*sleep=\([0-9]*\).*/\\1/p" {limit_file}); [[ $numrun -ge $maxrun ]] || break; sleep $sleeptime; done
""".format(limit_file=self.pipe_data["job_limit"],
           qstat=self.pipe_data["qsub_params"]["qstat_path"])

        script = """
# ---------------- Code for {script_id} ------------------
{job_limit}
echo '{qdel_line}' >> {step_kill_file}
# Adding qsub command:
qsub {script_name}

""".format(qdel_line = script_obj.get_kill_command(),
           job_limit=job_limit,
           script_name = script_obj.script_path,
           script_id = script_obj.script_id,
           step_kill_file = self.params["kill_script_path"])

        
        return script
                            
                            
                   
    def get_script_postamble(self):
                            
                            
        
    
        # Get general postamble
        postamble = super(HighScriptConstructorSGE, self).get_script_postamble()

        script = """\
{postamble}

csh {depends_script_name}

""".format(postamble = postamble,
           run_index = self.pipe_data["run_index"],
           depends_script_name = self.pipe_data["depends_script_name"])

        return script

    def main_script_kill_commands(self, kill_script_filename_main):

        f = open(kill_script_filename_main, 'r')
        kill_file = f.read()
        f.close()

        kill_file = re.sub("# entry_point",
                           "# entry_point\n{kill_cmd}".format(kill_cmd=self.get_kill_command()),
                           kill_file)

        f = open(kill_script_filename_main, 'w')
        f.write(kill_file)
        f.close()


# ----------------------------------------------------------------------------------
# LowScriptConstructorSGE definition
# ----------------------------------------------------------------------------------


class LowScriptConstructorSGE(ScriptConstructorSGE,LowScriptConstructor):
    """
    """

    def get_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        general_header = super(LowScriptConstructorSGE, self).get_script_header(**kwargs)

        only_low_lev_params  = ["-pe"]
        compulsory_high_lev_params = {"-V":""}

        # Create lines containing the qsub opts.
        qsub_opts = ""
        for qsub_opt in self.params["qsub_params"]["opts"]:
            qsub_opts += "#$ {key} {val}\n".format(key=qsub_opt, val=self.params["qsub_params"]["opts"][qsub_opt]) 

        qsub_queue =   "#$ -q %s" % self.params["qsub_params"]["queue"]
        # Adding node limitation to header, but only for low-level scripts
        if self.params["qsub_params"]["node"]:     # If not defined then this will be "None"
            # Perform two joins:
            #   1. For each node, join it to the queue name with '@' (e.g. 'bio.q@sge100')
            #   2. Comma-join all nodes to one list (e.g. 'bio.q@sge100,bio.q@sge102')
            qsub_queue = ",".join(["@".join([self.params["qsub_params"]["queue"],item]) for item in self.params["qsub_params"]["node"]])
            # qsub_queue += "@%s" % self.params["qsub_params"]["node"]
            qsub_queue = "#$ -q %s" % qsub_queue

        # Sometimes qsub_opts is empty and then there is an ugly empty line in the middle of the qsub definition. Removing the empty line with replace()
        return "\n".join([general_header,
                            qsub_queue,
                            qsub_opts]).replace("\n\n","\n") + "\n\n"

# ----------------------------------------------------------------------------------
# KillScriptConstructorSGE definition
# ----------------------------------------------------------------------------------


class KillScriptConstructorSGE(ScriptConstructorSGE,KillScriptConstructor):

    @classmethod
    def get_main_preamble(cls):
        """ Return main kill-script preamble"""
        pass
        return """\
#!/bin/sh

# Remove high level scripts:
# entry_point

"""

    @classmethod
    def get_main_postamble(cls):
        """ Return main kill-script postamble"""

        return ""

    pass