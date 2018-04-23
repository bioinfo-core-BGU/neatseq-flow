import os, shutil, sys, re
import traceback
import datetime


from copy import *
from pprint import pprint as pp

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"


from scriptconstructor import *

def get_script_exec_line():
    """ Return script to add to script execution function """
    

    return """\
jobid=$(sbatch $script_path | cut -d " " -f 4)

echo $qsubname " lock on sedlock" 
sedlock=${run_index}.sedlock
exec 200>$sedlock
flock -w 50 200 || exit 1

sed -i -e "s:$1.*$:&\\t$jobid:" $run_index

echo $qsubname "sedlock released"

"""


class ScriptConstructorSLURM(ScriptConstructor):

        
        
    def get_command(self):
        """ Returnn the command for executing the this script
        """
        
        script = ""
        
        # slow_release_script_loc = os.sep.join([self.pipe_data["home_dir"],"utilities","qsub_scripts","run_jobs_slowly.pl"])

        if "slow_release" in self.params.keys():
            sys.exit("Slow release no longer supported. Use 'job_limit'")

        else:
            script += """\
sh {nsf_exec} \\
    {script_id} &\n\n""".format(script_id = self.script_id,
                          nsf_exec = self.pipe_data["exec_script"])


        return script

        
#### Methods for adding lines:
        
        
        
    def get_kill_command(self):
    
        # TODO: somehow this has to be the numeric run-0time job id!
        return "# scancel JOB_ID \n" #{script_name}".format(script_name = self.script_id)
        
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
      

        
        
        
####----------------------------------------------------------------------------------

class HighScriptConstructorSLURM(ScriptConstructorSLURM,HighScriptConstructor):
    """
    """
    
        

    def get_depends_command(self, dependency_list):
        """
        """
        
        return "# scontrol bla bla bla... Find out how is done\n\n"#qalter \\\n\t-hold_jid %s \\\n\t%s\n\n" % (dependency_list, self.script_id)


        
    def get_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        general_header = super(HighScriptConstructorSLURM, self).get_script_header(**kwargs)

        only_low_lev_params  = ["-pe"]
        compulsory_high_lev_params = {"-V":""}

        # if "queue" in self.params["qsub_params"]:
        #     general_header +=   "#SBATCH --partition %s" % self.params["qsub_params"]["queue"]

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
        
        if "job_limit" in self.pipe_data.keys():
            sys.exit("Job limit not supported yet for Local!")


        command = super(HighScriptConstructorSLURM, self).get_command()

        

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
            sys.exit("Job limit not supported yet for SLURM!")

        script += """
# ---------------- Code for {script_id} ------------------
{kill_line}

{child_cmd}

""".format(script_id = script_obj.script_id,
        child_cmd = script_obj.get_command(),
        kill_line = script_obj.get_kill_command())
            
            
        
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

echo "{script_id} lock on sedlock" 
sedlock={run_index}.sedlock
exec 200>$sedlock
flock -w 50 200 || exit 1

sed -i -e "s:^{script_id}.*:# &:" {run_index}

echo "{script_id} sedlock released"
""".format(\
    postamble = postamble, 
    run_index = self.pipe_data["run_index"],
    script_id = self.script_id)
        
        return script
                                             
####----------------------------------------------------------------------------------
    
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
                        stamped_files, **kwargs):

        if "level" not in kwargs:
            kwargs["level"] = "low"

        super(LowScriptConstructorSLURM, self).write_script(script,
                                                        dependency_jid_list,
                                                        stamped_files,
                                                        **kwargs)

        
        self.write_command("""\

# Setting script as done in run index:
echo "{script_id} lock on sedlock" 
sedlock={run_index}.sedlock
exec 200>$sedlock
flock -w 50 200 || exit 1

sed -i -e "s:^{script_id}.*:# &:" {run_index}

echo "{script_id} sedlock released"
""".format(\
    run_index = self.pipe_data["run_index"],
    script_id = self.script_id))
        
        
####----------------------------------------------------------------------------------

class KillScriptConstructorSLURM(ScriptConstructorSLURM,KillScriptConstructor):


    
    def __init__(self, **kwargs):
    
        super(KillScriptConstructor, self).__init__(**kwargs)
        
        
        self.script_path = \
            "".join([self.pipe_data["scripts_dir"], \
                     "99.kill_all", \
                     os.sep, \
                     "99.kill_all_{name}".format(name=self.name), \
                     ".csh"])


        self.filehandle = open(self.script_path, "w")

        self.filehandle.write("""\
#!/usr/csh

touch {run_index}.killall

sleep 100

rm -rf {run_index}.killall""")
        
        