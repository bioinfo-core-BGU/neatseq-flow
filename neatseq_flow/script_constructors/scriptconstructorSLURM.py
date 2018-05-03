import os
import shutil
import sys
import re
import traceback
import datetime


from copy import *
from pprint import pprint as pp

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"


from scriptconstructor import *


class ScriptConstructorSLURM(ScriptConstructor):

    @classmethod
    def get_exec_script(cls, pipe_data):
        """ Not used for SGE. Returning None"""

        script = super(ScriptConstructorSLURM, cls).get_exec_script(pipe_data)

        script += """\
jobid=$(sbatch $script_path | cut -d " " -f 4)
 
locksed "s:$qsubname.*$:&\\t$jobid:" $run_index

"""
        return script

    def get_command(self):
        """ Returnn the command for executing the this script
        """
        
        script = ""

        if "slow_release" in self.params.keys():
            sys.exit("Slow release no longer supported. Use 'job_limit'")

        else:
            script += """\
sh {nsf_exec} \\
    {script_id} &\n\n""".format(script_id = self.script_id,
                                nsf_exec = self.pipe_data["exec_script"])

        return script

    # -----------------------
    # Instance methods

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
        
            
        qsub_header = """\
#!/bin/{shell}
#SBATCH --job-name {jobname}
#SBATCH -e {stderr_dir}{jobname}.e%J
#SBATCH -o {stdout_dir}{jobname}.o%J
""".format(shell      = self.shell, \
           stderr_dir = self.pipe_data["stderr_dir"],
           stdout_dir = self.pipe_data["stdout_dir"],
           jobname    = self.script_id) 
        if  self.params["qsub_params"]["queue"]:
            qsub_header +=   "#SBATCH --partition %s\n" % self.params["qsub_params"]["queue"]
        if self.dependency_jid_list:
            qsub_header += "#$ -hold_jid %s \n" % self.dependency_jid_list
            
        return qsub_header  
# ----------------------------------------------------------------------------------
# HighScriptConstructorSLURM defintion
# ----------------------------------------------------------------------------------

class HighScriptConstructorSLURM(ScriptConstructorSLURM,HighScriptConstructor):
    """
    """

    def get_depends_command(self, dependency_list):
        """
        """
        return ""
        # This is acheived by making high level scripts 'wait' for low level scripts
        #return "# scontrol bla bla bla... Find out how is done\n\n"#qalter \\\n\t-hold_jid %s \\\n\t%s\n\n" % (dependency_list, self.script_id)

    def get_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        general_header = super(HighScriptConstructorSLURM, self).get_script_header(**kwargs)

        only_low_lev_params  = ["-pe"]
        compulsory_high_lev_params = {"-V":""}

        # Create lines containing the qsub opts.
        for qsub_opt in self.params["qsub_params"]["opts"]:
            if qsub_opt in only_low_lev_params:
                continue
            general_header += "#SBATCH {key} {val}\n".format(key=qsub_opt, val=self.params["qsub_params"]["opts"][qsub_opt]) 


        # Adding 'compulsory_high_lev_params' to all high level scripts (This includes '-V'. Otherwise, if shell is bash, the SGE commands are not recognized)
        for qsub_opt in compulsory_high_lev_params:
            if qsub_opt not in self.params["qsub_params"]["opts"]:
                general_header += "#SBATCH {key} {val}\n".format(key = qsub_opt, 
                                                            val = compulsory_high_lev_params[qsub_opt]) 


        # Sometimes qsub_opts is empty and then there is an ugly empty line in the middle of the qsub definition. Removing the empty line with replace()
        return general_header + "\n\n"

    def get_command(self):
        """ Writing low level lines to high level script: job_limit loop, adding qdel line and qsub line
            spec_qsub_name is the qsub name without the run code (see caller)
        """
        
        command = super(HighScriptConstructorSLURM, self).get_command()

        # TODO: Add output from stdout and stderr

        script = """
# ---------------- Code for {script_id} ------------------
echo running {script_id}
{command}

sleep {sleep_time}

""".format(script_id = self.script_id,
           command = command,
           sleep_time=self.pipe_data["Default_wait"])

        return script

    def get_child_command(self, script_obj):
        """ Writing low level lines to high level script: job_limit loop, adding qdel line and qsub line
            spec_qsub_name is the qsub name without the run code (see caller)
        """

        job_limit = ""

        if "job_limit" in self.pipe_data.keys():
            # sys.exit("Job limit not supported yet for Local!")

            job_limit = """\
# Sleeping while jobs exceed limit
while : ; do numrun=$(egrep -c "^\w" {run_index}); maxrun=$(sed -ne "s/limit=\([0-9]*\).*/\\1/p" {limit_file}); sleeptime=$(sed -ne "s/.*sleep=\([0-9]*\).*/\\1/p" {limit_file}); [[ $numrun -ge $maxrun ]] || break; sleep $sleeptime; done
""".format(limit_file=self.pipe_data["job_limit"],
           run_index=self.pipe_data["run_index"])

        script = """
# ---------------- Code for {script_id} ------------------
{job_limit}

{child_cmd}

sleep {sleep_time}
""".format(script_id = script_obj.script_id,
           child_cmd = script_obj.get_command(),
           kill_line = script_obj.get_kill_command(),
           sleep_time=self.pipe_data["Default_wait"],
           job_limit=job_limit)
            
        return script

    def get_script_postamble(self):
        """ Local script postamble is same as general postamble with addition of sed command to mark as finished in run_index
        """
    
        # Get general postamble
        postamble = super(HighScriptConstructorSLURM, self).get_script_postamble()

        # Add sed command:
        script = """\
{postamble}

wait

# Setting script as done in run index:
# Using locksed provided in helper functions
locksed  "s:^{script_id}.*:# &\\tdone:" {run_index}

""".format(postamble=postamble,
           run_index=self.pipe_data["run_index"],
           script_id=self.script_id)

        # Write the kill command to the kill script
        try:
            self.kill_obj.write_kill_cmd(self)
        except AttributeError:
            pass

        return script
                                             
# ----------------------------------------------------------------------------------
# LowScriptConstructorSLURM definition
# ----------------------------------------------------------------------------------


class LowScriptConstructorSLURM(ScriptConstructorSLURM,LowScriptConstructor):
    """
    """

    def get_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        
        general_header = super(LowScriptConstructorSLURM, self).get_script_header(**kwargs)

        only_low_lev_params  = ["-pe"]
        compulsory_high_lev_params = {"-V":""}
        # special_opts = "-N -e -o -q -hold_jid".split(" ") + only_low_lev_params

        # Create lines containing the qsub opts.
        for qsub_opt in self.params["qsub_params"]["opts"]:
            general_header += "#SBATCH {key} {val}\n".format(key=qsub_opt, val=self.params["qsub_params"]["opts"][qsub_opt]) 
            
        # if "queue" in self.params["qsub_params"]:
        #     general_header += "#SBATCH --partition %s\n" % self.params["qsub_params"]["queue"]
        # Adding node limitation to header, but only for low-level scripts
        if self.params["qsub_params"]["node"]:     # If not defined then this will be "None"
            # qsub_queue += "@%s" % self.params["qsub_params"]["node"]
            general_header += "#SBATCH --nodelist %s\n" % ",".join(self.params["qsub_params"]["node"])

        # Sometimes qsub_opts is empty and then there is an ugly empty line in the middle of the qsub definition. Removing the empty line with replace()
        return general_header + "\n\n"

    def write_script(self,
                     script,
                     dependency_jid_list,
                     stamped_files,
                     **kwargs):
        """ Assembles the scripts to writes to file
        """

        if "level" not in kwargs:
            kwargs["level"] = "low"

        super(LowScriptConstructorSLURM, self).write_script(script,
                                                        dependency_jid_list,
                                                        stamped_files,
                                                        **kwargs)

        
        self.write_command("""\

# Setting script as done in run index:
# Using locksed provided in helper functions 
locksed "s:^{script_id}.*:# &\\tdone:" {run_index}

""".format(run_index = self.pipe_data["run_index"],
           script_id = self.script_id))

# ----------------------------------------------------------------------------------
# KillScriptConstructorSLURM defintion
# ----------------------------------------------------------------------------------


class KillScriptConstructorSLURM(ScriptConstructorSLURM,KillScriptConstructor):

    @classmethod
    def get_main_preamble(cls, run_index):
        """ Return main kill-script preamble"""
        pass
        return """\
#!/bin/sh

# Kill held scripts:
touch {run_index}.killall

""".format(run_index=run_index)

    @classmethod
    def get_main_postamble(cls, run_index):
        """ Return main kill-script postamble"""

        return """\
wait

rm -rf {run_index}.killall
""".format(run_index=run_index)

    def write_kill_cmd(self, caller_script):
        """

        :return:
        """

        # Create one killing routine for all instance jobs:
        script = """\
line2kill=$(grep '^{step}_{name}' {run_index} | awk '{{print $3}}')
line2kill=(${{line2kill//,/ }})
for item1 in "${{line2kill[@]}}"; do 
    echo running "scancel $item1"
    scancel $item1 
done

""".format(run_index = self.pipe_data["run_index"],
           step=caller_script.step,
           name=caller_script.name)

        self.filehandle.write(script)


#     def __init__(self, **kwargs):
#
#         super(KillScriptConstructor, self).__init__(**kwargs)
#
#         self.script_path = "".join([self.pipe_data["scripts_dir"],
#                                     "99.kill_all",
#                                     os.sep,
#                                     "99.kill_all_{name}".format(name=self.name),
#                                     ".sh"])
#
#         self.filehandle = open(self.script_path, "w")
#
#         self.filehandle.write("""\
# #!/usr/csh
#
# touch {run_index}.killall
#
# sleep 100
#
# rm -rf {run_index}.killall""")
#
