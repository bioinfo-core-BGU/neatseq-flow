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


class ScriptConstructorLocal(ScriptConstructor):

    @classmethod
    def get_helper_script(cls, pipe_data):
        """ Returns the code for the helper script
        """
        script = super(ScriptConstructorLocal, cls).get_helper_script(pipe_data)
        script = re.sub("## locksed command entry point", r"""locksed  "s:^\\($3\\).*:# \\1\\t$err_code:" $run_index""",
                        script)
        script = re.sub("## maxvmem calc entry point", 'maxvmem="-";', script)

        # Add job_limit function:
        if "job_limit" in pipe_data:
            script += """\
    job_limit={job_limit}
    holdlimit=$(nproc)
    holdlimit=$( echo "0.5*$holdlimit/1" | bc )

    wait_limit() {{
        while : ; do
            # Count hold jobs
            numhold=$(grep -v "^#" $run_index | grep -P ".*\.\..*\.\..*\.\." | grep -w -c "hold") || true;
            maxrun=$(sed -ne "s/limit=\([0-9]*\).*/\\1/p" $job_limit);
            sleeptime=$(sed -ne "s/.*sleep=\([0-9]*\).*/\\1/p" $job_limit);
            [[ $numhold -ge $holdlimit ]] || break;
            # Count active (PID) jobs
            numrun=$(grep -v "^#" $run_index | grep -w -c "PID") || true;
            [[ $numrun -ge $maxrun ]] || [[ $numhold -ge $holdlimit ]] || break;
            sleep $sleeptime;
        done
    }}
    """.format(job_limit=pipe_data["job_limit"])
        #        numrun=$(awk 'BEGIN {{jobsc=0}} /^\w/ {{jobsc=jobsc+1}} END {{print jobsc}}' $run_index);
        #        numrun=$(grep -c '\sPID\s'  $run_index);
        else:
            pipe_data["job_limit"]=''
            script += """\

    sleeptime={sleeptime}
    holdlimit=$(nproc)
    holdlimit=$( echo "0.5*$holdlimit/1" | bc )
    
    wait_limit() {{
        while : ; do
            # Count hold jobs
            numhold=$(grep -v "^#" $run_index | grep -P ".*\.\..*\.\..*\.\." | grep -w -c "hold" ) || true;
            [[ $numhold -ge $holdlimit ]] || break;
            sleep $sleeptime;
        done
    }}
    """.format(sleeptime=pipe_data["Default_wait"])
    
        path = shutil.which("bc")
        if path:
            script = re.sub(" bc ", " " + path + " ", script)
        else:
            sys.exit("You need to have the 'bc' program installed")
    
    
    
        return script

    @classmethod
    def get_exec_script(cls, pipe_data):
        """ Not used for SGE. Returning None"""

        script = super(ScriptConstructorLocal, cls).get_exec_script(pipe_data)

        # Adding PID after hold in run_index
        script = re.sub("(locksed.*hold)", r"\1\\t$$", script)
        
        script = re.sub("(# local )", r"", script)
        
        script += """\

# iscsh=$(grep "csh" <<< $script_path)
# if [ -z $iscsh ]; then
    # bash $script_path &
# else
    # csh $script_path &
# fi

# # gpid=$(ps -o pgid= $! | grep -o '[0-9]*')
# locksed "s:\($qsubname\).*$:\\1\\tPID\\t$!\\t$pe:" $run_index

runlock $qsubname $run_index $script_path $pe

"""
        path = shutil.which("bc")
        if path:
            script = re.sub(" bc "," " + path + " ", script)
        else:
            sys.exit("You need to have the 'bc' program installed")
    
        return script

    @classmethod
    def get_utilities_script(cls, pipe_data):

        util_script = super(ScriptConstructorLocal, cls).get_utilities_script(pipe_data)

        # # Steps:
        # - Join the following two files:
        #   1. Lines to execute from main script:
        #     a. Find failed steps in log file
        #     b. Find downstream steps in depend_file
        #     c. Extract lines from main script
        #     d. Sort (by script ID)
        #   2. Step order file, sorted alphabetically by step name
        # - Sort by script number (column 9 in joined file)
        # - Reform the commands
        # - write to recover_script

        recover_script = """
# Recover a failed execution
function recover_run {{
    echo "echo 'Recovering previous run...\\n'" > {recover_script}
    join -1 3 -2 2 \\
        <(cat {log_file} \\
            | awk '{{  if(NR<=9) {{next}};
                        if($3=="Started" && $11 ~ "OK") {{jobs[$6]=$5;}}
                        if($3=="Finished" && $11 ~ "OK") {{delete jobs[$6]}}
                    }}
                    END {{
                        for (key in jobs) {{
                            print jobs[key]
                        }}
    
                    }}'  \\
            | while read step; do \\
                echo $step; \\
                grep $step {depend_file} | cut -f2;
              done \\
            | sort -u \\
            | while read step; do \\
                grep $step {main} | egrep -v "^#|^echo";
              done \\
            | sort -u) \\
        <(sort -k 2b,2 {step_order}) \\
        | sort -k 9b,9 \\
        | awk 'BEGIN{{OFS=" "}} {{print $2,$3,$1,$4,$5,$6,$7,$8; print "\\n"}}' \\
        >> {recover_script}
    echo -e "\\nWritten recovery code to file {recover_script}\\n\\n" 

}}
                """.format(log_file=pipe_data["log_file"],
                           depend_file=pipe_data["dependency_index"],
                           main=pipe_data["scripts_dir"] + "00.workflow.commands.sh",
                           step_order=pipe_data["step_order"],
                           recover_script=pipe_data["scripts_dir"] + "AA.Recovery_script.sh")

        return util_script + recover_script



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
        # Make a step specific subdir for stderr and stdout
        stderr_dir = os.path.join( self.pipe_data["stderr_dir"], "_".join([self.step,self.name]) ) + os.sep
        stdout_dir = os.path.join( self.pipe_data["stdout_dir"], "_".join([self.step,self.name]) ) + os.sep
        if not os.path.isdir(stderr_dir):
            os.makedirs(stderr_dir) 
        if not os.path.isdir(stdout_dir):
            os.makedirs(stdout_dir)         
        script = ""

        if "slow_release" in list(self.params.keys()):
            sys.exit("Slow release no longer supported. Use 'job_limit'")
        else:
            script += """\
bash {nsf_exec} {script_id} 1> {stdout} 2> {stderr} & \n\n""".\
                format(script_id = self.script_id,
                       nsf_exec = self.pipe_data["exec_script"],
                       stderr = "{dir}{id}.e".format(dir=stderr_dir, id=self.script_id),
                       stdout = "{dir}{id}.o".format(dir=stdout_dir, id=self.script_id))

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
echo `date '+%%d/%%m/%%Y %%H:%%M:%%S'`'\\t%(type)s\\t%(step)s\\t%(stepname)s\\t%(stepID)s\\t%(level)s\\t'$HOSTNAME'\\t$$\\t-\\t%(status)s' >> %(file)s
####
""" % log_cols_dict

        elif self.shell == "bash":

            script = """
# Adding line to log file
log_echo {step} {stepname} {stepID} {level} $HOSTNAME $$ {type}

""".format(**log_cols_dict)

        else:
            script = ""

            if self.pipe_data["verbose"]:
                sys.stderr.write("shell not recognized. Not creating log writing lines in scripts.\n")

        return script



    def get_trap_line(self):
        """
        """

        if self.shell=="csh":
            # Trap lines not defined for csh shell
            # This will happen for new module creators. Not exiting nicely...
            script = ""
            if self.pipe_data["verbose"]:
                sys.stderr.write("Error trapping not defined for csh scripts. Consider using bash instead.\n")

        elif self.shell == "bash":
            script = """
# Import helper functions
. {helper_funcs}

# Trap various signals. SIGUSR2 is passed by qdel when -notify is passes
trap_with_arg func_trap {step} {stepname} {stepID} {level} $HOSTNAME $$ SIGUSR2 ERR INT TERM
            """.format(step       = self.step,
                       stepname   = self.name,
                       stepID     = self.script_id,
                       helper_funcs = self.pipe_data["helper_funcs"],
                       level      = self.level)

        else:
            script = ""
            if self.pipe_data["verbose"]:
                sys.stderr.write("shell not recognized. Not creating error trapping lines.\n")

        return script



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

        if "job_limit" in list(self.pipe_data.keys()):
            job_limit = """\
# Sleeping while jobs exceed limit
# wait_limit
        """

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

        if "job_limit" in list(self.pipe_data.keys()):
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
        
        qsub_opt = '-pe'
        if qsub_opt in self.params["qsub_params"]["opts"]:
            general_header += "\n#$ {key} {val}\n".format(key=qsub_opt, val=self.params["qsub_params"]["opts"][qsub_opt]) 
        else:
            general_header += "\n#$ {key} {val}\n".format(key=qsub_opt, val='1') 
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

#         # Create one killing routine for all instance jobs:
#         script = """\
# line2kill=$(grep '^{step}{sep}{name}' {run_index} | awk '{{print $3}}')
# line2kill=(${{line2kill//,/ }})
# for item1 in "${{line2kill[@]}}"; do
#     echo running "kill -- -$(ps -o pgid= $item1 | grep -o '[0-9]'*)"
#     kill -- -$(ps -o pgid= $item1 | grep -o '[0-9]'*)
# done
#
# """.format(run_index = self.pipe_data["run_index"],
#            step=caller_script.step,
#            name=caller_script.name,
#            sep=caller_script.master.jid_name_sep)
#
#         self.filehandle.write(script)


        # Create one killing routine for all instance jobs:
        script = """\

# 1. Find lines for step instance
# 2. Keep only lines containing hold or PID
# 3. Keep 3rd column - the pid
# 4. Create kill commands on pgids
# 5. Uniqify - several commands will have same pgid!
# 6. Execute commands
grep '^{step}{sep}{name}' {run_index} \\
    | sed -En '/\\t(PID|hold)\\t/p' \\
    | cut -f3 \\
    | while read item1; do
        echo $(ps -o pgid= $item1 | grep -o '[0-9]'*)
        done \
    | sort -u \
    | xargs -I {{}} sh -c "kill -- -{{}}"

""".format(run_index = self.pipe_data["run_index"],
           step=caller_script.step,
           name=caller_script.name,
           sep=caller_script.master.jid_name_sep)

        self.filehandle.write(script)




