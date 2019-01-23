import os
import shutil
import sys
import re
import traceback
import datetime

from copy import *
from pprint import pprint as pp

__author__ = "Menachem Sklarz"
__version__ = "1.5.0"


from scriptconstructor import *


class ScriptConstructorLocal(ScriptConstructor):

    @classmethod
    def get_helper_script(cls, pipe_data):
        """ Returns the code for the helper script
        """
        script = super(ScriptConstructorLocal, cls).get_helper_script(pipe_data)
        script = re.sub("## locksed command entry point", r"""locksed  "s:^\\($3\\).*:# \\1\\t$err_code:" $run_index""", script)

        # Add job_limit function:
        if "job_limit" in pipe_data:
            script += """\
job_limit={job_limit}

wait_limit() {{
    while : ; do
        # Count active (PID), child-level (merge..merge1..sample..runid) jobs
        numrun=$(grep  '\sPID\s' $run_index | grep -P ".*\.\..*\.\..*\.\." | wc -l);
        maxrun=$(sed -ne "s/limit=\([0-9]*\).*/\\1/p" $job_limit);
        sleeptime=$(sed -ne "s/.*sleep=\([0-9]*\).*/\\1/p" $job_limit);
        [[ $numrun -ge $maxrun ]] || break;
        sleep $sleeptime;
    done
}}
""".format(job_limit=pipe_data["job_limit"])
#        numrun=$(awk 'BEGIN {{jobsc=0}} /^\w/ {{jobsc=jobsc+1}} END {{print jobsc}}' $run_index);
#        numrun=$(grep -c '\sPID\s'  $run_index);


        return script

    @classmethod
    def get_exec_script(cls, pipe_data):
        """ Not used for SGE. Returning None"""

        script = super(ScriptConstructorLocal, cls).get_exec_script(pipe_data)

        # Adding PID after hold in run_index
        script = re.sub("(locksed.*hold)",r"\1\\t$$", script)

        script += """\

iscsh=$(grep "csh" <<< $script_path)
if [ -z $iscsh ]; then
    bash $script_path &
else
    csh $script_path &
fi

# gpid=$(ps -o pgid= $! | grep -o '[0-9]*')
locksed "s:\($qsubname\).*$:\\1\\tPID\\t$!:" $run_index

"""
        return script

    @classmethod
    def get_run_index_clean_script(cls, pipe_data):
            # Create run_index cleaning script
        return """\
#!/bin/bash
sed -i -E -e 's/^([^#][^[[:space:]]+).*/# \\1/g' -e 's/^(# [^[[:space:]]+).*/\\1/g' {run_index}\n""".\
                            format(run_index=pipe_data["run_index"])
# sed -i -e 's/^\([^#]\w\+\).*/\# \\1/g' -e 's/^\(\# \w\+\).*/\\1/g' {run_index}\n""".\

    def get_command(self):
        """ Returnn the command for executing the this script
        """
        
        script = ""

        if "slow_release" in self.params.keys():
            sys.exit("Slow release no longer supported. Use 'job_limit'")
        else:
            script += """\
bash {nsf_exec} {script_id} 1> {stdout} 2> {stderr} & \n\n""".\
                format(script_id = self.script_id,
                       nsf_exec = self.pipe_data["exec_script"],
                       stderr = "{dir}{id}.e".format(dir=self.pipe_data["stderr_dir"], id=self.script_id),
                       stdout = "{dir}{id}.o".format(dir=self.pipe_data["stdout_dir"], id=self.script_id))

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

        qsub_header = """#!/bin/{shell}\n""".format(shell      = self.shell)
        
        if self.master.dependency_jid_list:
            qsub_header += "#$ -hold_jid %s " % ",".join(self.master.dependency_jid_list)

            
        return qsub_header  

# ----------------------------------------------------------------------------------
# HighScriptConstructorLocal defintion
# ----------------------------------------------------------------------------------


class HighScriptConstructorLocal(ScriptConstructorLocal,HighScriptConstructor):
    """
    """


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
        
        command = super(HighScriptConstructorLocal, self).get_command()

        job_limit = ""

        if "job_limit" in self.pipe_data.keys():
            job_limit = """\
# Sleeping while jobs exceed limit
wait_limit
        """
                # .format(limit_file=self.pipe_data["job_limit"],
                #    run_index=self.pipe_data["run_index"])

        # TODO: Add output from stdout and stderr

        script = """
# ---------------- Code for {script_id} ------------------
{job_limit}
echo running {script_id}
{command}

sleep {sleep_time}

""".format(script_id=self.script_id,
           command=command,
           job_limit=job_limit,
           sleep_time=self.pipe_data["Default_wait"])

        return script

    def get_child_command(self, script_obj):
        """ Writing low level lines to high level script: job_limit loop, adding qdel line and qsub line
            spec_qsub_name is the qsub name without the run code (see caller)
        """

        job_limit = ""

        if "job_limit" in self.pipe_data.keys():
            job_limit = """\
# Sleeping while jobs exceed limit
wait_limit
"""#.format(limit_file=self.pipe_data["job_limit"],
    #       run_index=self.pipe_data["run_index"])

# """while : ; do numrun=$(egrep -c "^\w" {run_index}); maxrun=$(sed -ne "s/limit=\([0-9]*\).*/\\1/p" {limit_file}); sleeptime=$(sed -ne "s/.*sleep=\([0-9]*\).*/\\1/p" {limit_file}); [[ $numrun -ge $maxrun ]] || break; sleep $sleeptime; done"""
        script = """
# ---------------- Code for {script_id} ------------------
{job_limit}

{child_cmd}

sleep {sleep_time}
""".format(script_id=script_obj.script_id,
           child_cmd=script_obj.get_command(),
           sleep_time=self.pipe_data["Default_wait"],
           job_limit=job_limit)

        return script

    def get_script_postamble(self):
        """ Local script postamble is same as general postamble with addition of sed command to mark as finished in run_index
        """

        # Write the kill command to the kill script
        try:
            self.kill_obj.write_kill_cmd(self)
        except AttributeError:
            pass

        # Get general postamble
        postamble = super(HighScriptConstructorLocal, self).get_script_postamble()

        script = """\
{postamble}

wait 

# Setting script as done in run index:
# Using locksed provided in helper functions
locksed  "s:^\({script_id}\).*:# \\1\\tdone:" {run_index}

""".format(\
            postamble=postamble,
            run_index=self.pipe_data["run_index"],
            script_id=self.script_id)
        
        return script

# ----------------------------------------------------------------------------------
# LowScriptConstructorLocal defintion
# ----------------------------------------------------------------------------------


class LowScriptConstructorLocal(ScriptConstructorLocal, LowScriptConstructor):
    """
    """

    def get_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        
        general_header = super(LowScriptConstructorLocal, self).get_script_header(**kwargs)

        return general_header + "\n\n"

    def write_script(self):
        # ,
        #              script,
        #              dependency_jid_list,
        #              stamped_files,
        #              **kwargs):
        """ Assembles the scripts to writes to file
        """

        # if "level" not in kwargs:
        #     kwargs["level"] = "low"

        super(LowScriptConstructorLocal, self).write_script()
        # script,
        #                                                 dependency_jid_list,
        #                                                 stamped_files,
        #                                                 **kwargs)

        self.write_command("""\

# Setting script as done in run index:
# Using locksed provided in helper functions
locksed  "s:^\({script_id}\).*:# \\1\\tdone:" {run_index}

""".format(run_index=self.pipe_data["run_index"],
           script_id=self.script_id))

# ----------------------------------------------------------------------------------
# KillScriptConstructorLocal defintion
# ----------------------------------------------------------------------------------


class KillScriptConstructorLocal(ScriptConstructorLocal, KillScriptConstructor):

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

        # Create one killing routine for all instance jobs:
        script = """\
line2kill=$(grep '^{step}{sep}{name}' {run_index} | awk '{{print $3}}')
line2kill=(${{line2kill//,/ }})
for item1 in "${{line2kill[@]}}"; do 
    echo running "kill -- -$(ps -o pgid= $item1 | grep -o '[0-9]'*)"
    kill -- -$(ps -o pgid= $item1 | grep -o '[0-9]'*)
done

""".format(run_index = self.pipe_data["run_index"],
           step=caller_script.step,
           name=caller_script.name,
           sep=caller_script.master.jid_name_sep)

        self.filehandle.write(script)





