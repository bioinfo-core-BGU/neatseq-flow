import os
import shutil
import sys
import re
import traceback
import datetime

from copy import *
from pprint import pprint as pp

__author__ = "Menachem Sklarz"
__version__ = "1.6.0"


from .scriptconstructor import *


class ScriptConstructorPBS(ScriptConstructor):

    @classmethod
    def get_helper_script(cls, pipe_data):
        """ Returns the code for the helper script
        """
        script = super(ScriptConstructorPBS, cls).get_helper_script(pipe_data)
        script = re.sub("## locksed command entry point", r"""locksed  "s:^\\($3\\).*:# \\1\\t$err_code:" $run_index""", script)
        script = re.sub("## maxvmem calc entry point", r""" maxvmem="-"; """, script)
        script = re.sub("jobid=\$\$", r""" jobid=$PBS_JOBID """, script)


        # Add job_limit function:
        if "job_limit" in pipe_data:
            script += """\
job_limit={job_limit}

wait_limit() {{
    while : ; do
        numrun=$(grep -c '\sPID\s'  $run_index);
        maxrun=$(sed -ne "s/limit=\([0-9]*\).*/\\1/p" $job_limit);
        sleeptime=$(sed -ne "s/.*sleep=\([0-9]*\).*/\\1/p" $job_limit);
        [[ $numrun -ge $maxrun ]] || break;
        sleep $sleeptime;
    done
}}
""".format(job_limit=pipe_data["job_limit"])
#        numrun=$(awk 'BEGIN {{jobsc=0}} /^\w/ {{jobsc=jobsc+1}} END {{print jobsc}}' $run_index);
        return script

    @classmethod
    def get_exec_script(cls, pipe_data):
        """ Not used for SGE. Returning None"""
        # $(echo $(basename $0) | sed 's/\.[^.]*$//')
        script     = super(ScriptConstructorPBS, cls).get_exec_script(pipe_data)
        if "qstat_path" in pipe_data["qsub_params"].keys():
            qstat_path = pipe_data["qsub_params"]["qstat_path"]
            if not qstat_path.endswith("qsub"):
                qstat_path = os.path.join(qstat_path,"qsub" )
        else:
            qstat_path = "qsub"
        script += """\
jobid=$({qsub} $script_path | cut -d " " -f 4)

locksed "s:\($qsubname\).*$:\\1\\trunning\\t$jobid:" $run_index


""".format(qsub=qstat_path)
        return script

    @classmethod
    def get_run_index_clean_script(cls, pipe_data):

        return """\
#!/bin/bash
sed -i -E -e 's/^([^#][^[[:space:]]+).*/# \\1/g' -e 's/^(# [^[[:space:]]+).*/\\1/g' {run_index}\n""".\
            format(run_index=pipe_data["run_index"])
# sed -i -e 's/^\([^#]\w\+\).*/\# \\1/g' -e 's/^\(\# \w\+\).*/\\1/g' {run_index}\n""". \

    def get_command(self):
        """ Returnn the command for executing the this script
        """
        
        script = ""

        if "slow_release" in self.params.keys():
            sys.exit("Slow release no longer supported. Use 'job_limit'")
        else:
            script += """\
bash {nsf_exec} {script_id} &\n\n""".format(script_id = self.script_id,
                                nsf_exec = self.pipe_data["exec_script"])

        return script

    # -----------------------
    # Instance methods

    def get_kill_command(self):
        """
        """
        pass
        # TODO: somehow this has to be the numeric run-0time job id!
        # return "# qdel JOB_ID \n" #{script_name}".format(script_name = self.script_id)
        
    def get_script_header(self):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """
        
        # Make a step specific subdir for stderr and stdout
        stderr_dir = os.path.join( self.pipe_data["stderr_dir"], "_".join([self.step,self.name]) ) + os.sep
        stdout_dir = os.path.join( self.pipe_data["stdout_dir"], "_".join([self.step,self.name]) ) + os.sep
        if not os.path.isdir(stderr_dir):
            os.makedirs(stderr_dir) 
        if not os.path.isdir(stdout_dir):
            os.makedirs(stdout_dir) 
        
        qsub_header = """\
#!/bin/{shell}
#PBS -N {jobname}
#PBS -e {stderr_dir}{jobname}.e%J
#PBS -o {stdout_dir}{jobname}.o%J
""".format(shell      = self.shell, \
           stderr_dir = stderr_dir,
           stdout_dir = stdout_dir,
           jobname    = self.script_id) 
        if  self.params["qsub_params"]["queue"]:
            qsub_header +=   "#PBS -q %s\n" % self.params["qsub_params"]["queue"]
        if self.master.dependency_jid_list:
            qsub_header += "#$ -hold_jid {hjids}\n".format(hjids=",".join(self.master.dependency_jid_list))

        return qsub_header

    def get_log_lines(self, state="Started", status="\033[0;32mOK\033[m"):
        """ Create logging lines. Added before and after script to return start and end times
            If bash, adding at beginning of script also lines for error trapping
        """

        log_cols_dict = {"type": state,
                         "step": self.step,
                         "stepname": self.name,
                         "stepID": self.script_id,
                         "qstat_path": self.pipe_data["qsub_params"]["qstat_path"],
                         "level": self.level,
                         "status": status,
                         "file": self.pipe_data["log_file"]}

        if self.shell == "csh":

            script = """
if ($?JOB_ID) then 
    # Adding line to log file:  Date    Step    Host
    echo `date '+%%d/%%m/%%Y %%H:%%M:%%S'`'\\t%(type)s\\t%(step)s\\t%(stepname)s\\t%(stepID)s\\t%(level)s\\t'$HOSTNAME'\\t'`%(qstat_path)s -j $PBS_JOBID | grep maxvmem | cut -d = -f 6`'\\t%(status)s' >> %(file)s
else
    echo `date '+%%d/%%m/%%Y %%H:%%M:%%S'`'\\t%(type)s\\t%(step)s\\t%(stepname)s\\t%(stepID)s\\t%(level)s\\t'$HOSTNAME'\\t$$\\t-\\t%(status)s' >> %(file)s
endif
####
""" % log_cols_dict

        elif self.shell == "bash":

            script = """
# Adding line to log file
log_echo {step} {stepname} {stepID} {level} $HOSTNAME $JOB_ID {type}

""".format(**log_cols_dict)

        else:
            script = ""

            if self.pipe_data["verbose"]:
                sys.stderr.write("shell not recognized. Not creating log writing lines in scripts.\n")

        return script


# ----------------------------------------------------------------------------------
# HighScriptConstructorPBS defintion
# ----------------------------------------------------------------------------------

class HighScriptConstructorPBS(ScriptConstructorPBS,HighScriptConstructor):
    """
    """

    def get_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        general_header = super(HighScriptConstructorPBS, self).get_script_header(**kwargs)

        only_low_lev_params  = ["-l"]
        compulsory_high_lev_params = {}

        # Create lines containing the qsub opts.
        for qsub_opt in self.params["qsub_params"]["opts"]:
            if qsub_opt in only_low_lev_params:
                continue
            general_header += "#PBS {key} {val}\n".format(key=qsub_opt, val=self.params["qsub_params"]["opts"][qsub_opt]) 


        # Adding 'compulsory_high_lev_params' to all high level scripts (This includes '-V'. Otherwise, if shell is bash, the SGE commands are not recognized)
        for qsub_opt in compulsory_high_lev_params:
            if qsub_opt not in self.params["qsub_params"]["opts"]:
                general_header += "#PBS {key} {val}\n".format(key = qsub_opt, 
                                                            val = compulsory_high_lev_params[qsub_opt]) 


        # Sometimes qsub_opts is empty and then there is an ugly empty line in the middle of the qsub definition. Removing the empty line with replace()
        return general_header + "\n\n"

    def get_command(self):
        """ Writing low level lines to high level script: job_limit loop, adding qdel line and qsub line
            spec_qsub_name is the qsub name without the run code (see caller)
        """
        
        command = super(HighScriptConstructorPBS, self).get_command()

        job_limit = ""

        if "job_limit" in self.pipe_data.keys():
            job_limit = """\
# Sleeping while jobs exceed limit
wait_limit
        """
        # TODO: Add output from stdout and stderr

        script = """
# ---------------- Code for {script_id} ------------------
echo running {script_id}
{job_limit}
{command}

sleep {sleep_time}

""".format(script_id = self.script_id,
           command = command,
           job_limit=job_limit,
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
wait_limit
"""#.format(limit_file=self.pipe_data["job_limit"],
    #       run_index=self.pipe_data["run_index"])

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
        postamble = super(HighScriptConstructorPBS, self).get_script_postamble()

        # Add sed command:
        script = """\
{postamble}

wait

# Setting script as done in run index:
# Using locksed provided in helper functions
locksed  "s:^\({script_id}\).*:# \\1\\tdone:" {run_index}

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
# LowScriptConstructorPBS definition
# ----------------------------------------------------------------------------------


class LowScriptConstructorPBS(ScriptConstructorPBS,LowScriptConstructor):
    """
    """

    def get_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        general_header = super(LowScriptConstructorPBS, self).get_script_header(**kwargs)

        only_low_lev_params  = ["-l"]
        compulsory_high_lev_params = {"-V":""}
        # special_opts = "-N -e -o -q -hold_jid".split(" ") + only_low_lev_params

        # Create lines containing the qsub opts.
        for qsub_opt in self.params["qsub_params"]["opts"]:
            general_header += "#PBS  {key} {val}\n".format(key=qsub_opt, val=self.params["qsub_params"]["opts"][qsub_opt]) 
            
        # if "queue" in self.params["qsub_params"]:
        #     general_header += "#SBATCH --partition %s\n" % self.params["qsub_params"]["queue"]
        # Adding node limitation to header, but only for low-level scripts
        # if self.params["qsub_params"]["node"]:     # If not defined then this will be "None"
            # # qsub_queue += "@%s" % self.params["qsub_params"]["node"]
            # general_header += "#PBS -l nodes=%s\n" % ":".join(self.params["qsub_params"]["node"])

        # Sometimes qsub_opts is empty and then there is an ugly empty line in the middle of the qsub definition. Removing the empty line with replace()
        return general_header + "\n\n"

    def write_script(self):
                     # script,
                     # dependency_jid_list,
                     # stamped_files,
                     # **kwargs):
        """ Assembles the scripts to writes to file
        """

        # if "level" not in kwargs:
        #     kwargs["level"] = "low"

        super(LowScriptConstructorPBS, self).write_script()
    # script,
    #                                                     dependency_jid_list,
    #                                                     stamped_files,
    #                                                     **kwargs)

        
        self.write_command("""\

# Setting script as done in run index:
# Using locksed provided in helper functions
locksed  "s:^\({script_id}\).*:# \\1\\tdone:" {run_index}

""".format(run_index = self.pipe_data["run_index"],
           script_id = self.script_id))

# ----------------------------------------------------------------------------------
# KillScriptConstructorPBS defintion
# ----------------------------------------------------------------------------------


class KillScriptConstructorPBS(ScriptConstructorPBS,KillScriptConstructor):

    @classmethod
    def get_main_preamble(cls, run_index):
        """ Return main kill-script preamble"""
        pass
        return """\
#!/bin/bash

# Kill held scripts:
touch {run_index}.killall
echo "Waiting for {run_index}.killall to take effect..."
sleep 10

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
        if "qstat_path" in self.pipe_data["qsub_params"].keys():
            qstat_path = self.pipe_data["qsub_params"]["qstat_path"]
            if not qstat_path.endswith("qsub"):
                qstat_path = os.path.join(qstat_path,"qdel" )
            else:
                qstat_path = os.path.join(qstat_path.strip("qsub"),"qdel" )
        else:
            qstat_path = "qdel"
        # Create one killing routine for all instance jobs:
        script = """\
line2kill=$(grep '^{step}{sep}{name}' {run_index} | awk '{{print $3}}')
line2kill=(${{line2kill//,/ }})
for item1 in "${{line2kill[@]}}"; do 
    echo running "{qdel} $item1"
    {qdel} $item1 
done

""".format(run_index = self.pipe_data["run_index"],
           step=caller_script.step,
           name=caller_script.name,
           qdel=qstat_path,
           sep=caller_script.master.jid_name_sep)

        self.filehandle.write(script)
