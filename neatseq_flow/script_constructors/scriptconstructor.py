import os
import sys
import re

from ..PLC_step import AssertionExcept

from pprint import pprint as pp

__author__ = "Menachem Sklarz"
__version__ = "1.6.0"


class ScriptConstructor(object):
    """ General class for script construction and management
    """

    @classmethod
    def get_utilities_script(cls, pipe_data):

        """

        :return:
        """
#
#         # # Steps:
#         # 1. Find failed steps in log file
#         # 2. Find downstream steps in depend_file
#         # 3. Get qsub commands from main script
#         # 4. Execute the qsub command
#
#         recover_script = """
# # Recover a failed execution
# function recover_run {{
#     cat {log_file} \\
#         | awk '{{  if(NR<=9) {{next}};
#                     if($3=="Started" && $11 ~ "OK") {{jobs[$6]=$5;}}
#                     if($3=="Finished" && $11 ~ "OK") {{delete jobs[$6]}}
#                 }}
#                 END {{
#                     for (key in jobs) {{
#                         print jobs[key]
#                     }}
#
#                 }}'  \\
#         | while read step; do \\
#             echo $step; \\
#             grep $step {depend_file} | cut -f2;
#           done \\
#         | sort -u \\
#         | while read step; do \\
#             grep $step {main} | egrep -v "^#|^echo";
#           done \\
#         | sort -u \\
#         > {recover_script}
#     echo -e "\\nWritten recovery code to file {recover_script}\\n\\n"
# }}
#                 """.format(log_file=pipe_data["log_file"],
#                            depend_file=pipe_data["dependency_index"],
#                            main=pipe_data["scripts_dir"] + "00.workflow.commands.sh",
#                            recover_script=pipe_data["scripts_dir"] + "AA.Recovery_script.sh")

        return ""

    @classmethod
    def get_helper_script(cls, pipe_data):
        """ Returns the code for the helper script
            Note. The line with '## locksed command entry point' should be dealt with in inheriting classes.
            Either replace with nothing to remove (see scriptConstructorSGE) or replaced with a
            locksed command, see scriptConstructorLocal.
        """
        script = """\
#!/bin/bash

run_index={run_index}

trap_with_arg() {{
    # $1: func
    # $2: module
    # $3: instance
    # $4: instance_id
    # $5: level
    # $6: hostname
    # $7: jobid
    
    args="$1 $2 $3 $4 $5 $6 $7"
    shift 7
    for sig ; do
        trap "$args $sig" "$sig"
    done
    }}

func_trap() {{
    # $1: module
    # $2: instance
    # $3: instance_id
    # $4: level
    # $5: hostname
    # $6: jobid
    # $8: sig
    jobid=$6

    ## maxvmem calc entry point

    if [ $7 == 'ERR' ]; then err_code='ERROR'; fi
    if [ $7 == 'INT' ]; then err_code='TERMINATED'; fi
    if [ $7 == 'TERM' ]; then err_code='TERMINATED'; fi
    if [ $7 == 'SIGUSR2' ]; then err_code='TERMINATED'; fi

    if [ $jobid == 'ND' ]; then
        jobid=$$
    fi        
    
    exec 220>>{log_file}
    flock -w 4000 220
    echo -e $(date '+%d/%m/%Y %H:%M:%S')'\\tFinished\\t'$1'\\t'$2'\\t'$3'\\t'$4'\\t'$5'\\t'$6'\\t'$maxvmem'\\t[0;31m'$err_code'[m' >> {log_file}; 
    flock -u 220
    
    ## locksed command entry point
    exit 1;
}}         

log_echo() {{
    # $1: module
    # $2: instance
    # $3: instance_id
    # $4: level
    # $5: hostname
    # $6: jobid
    # $7: type (Started/Finished)
    jobid=$6

    
    if [ $7 == 'Finished' ]; then
        ## maxvmem calc entry point

    else
        maxvmem="-";
    fi

    if [ $jobid == 'ND' ]; then
        jobid=$$
    fi        


    exec 220>>{log_file}
    flock -w 4000 220
    echo -e $(date '+%d/%m/%Y %H:%M:%S')'\\t'$7'\\t'$1'\\t'$2'\\t'$3'\\t'$4'\\t'$5'\\t'$jobid'\\t'$maxvmem'\\t[0;32mOK[m' >> {log_file};
    flock -u 220
}}

locksed() {{
    # $1: program
    # $2: file
    # Setting script as done in run index:
    sedlock=${{2}}.lock
    exec 200>$sedlock
    flock -w 4000 200 || exit 1

    # echo do sed 
    sed -i -e "$1" $2

    # echo unlock
    flock -u 200
}}

""".format(log_file=pipe_data["log_file"],
           qstat_path=pipe_data["qsub_params"]["qstat_path"],
           run_index=pipe_data["run_index"])

        return script

    @classmethod
    def get_exec_script(cls, pipe_data):
        """ Returns the code for the helper script
        """

        script = """\
#!/bin/bash
qsubname=$1
script_index="{script_index}"
run_index="{run_index}"
# 1. Find script path

# Import helper functions
. {helper_funcs}

echo "Running job: " $qsubname

# Setting trap
trap_with_arg func_trap $module $instance $qsubname Queue $HOSTNAME $$ SIGUSR2 ERR INT TERM

module=$(awk 'BEGIN {{FS="[.][.]";}} {{print $1}}' <<< $qsubname)
instance=$(awk 'BEGIN {{FS="[.][.]";}} {{print $2}}' <<< $qsubname)

log_echo $module $instance $qsubname Queue $HOSTNAME $$ Started

script_path=$(awk -v qsname="$qsubname" '$0 ~ qsname".*" {{print $2}}' $script_index)

echo "Running script: " $script_path

# 2. Marking in run_index as running

locksed "s:# \($qsubname\).*:\\1\\thold:" $run_index

# 3. Getting script dependencies

hold_jids=$(grep '#$ -hold_jid' $script_path | cut -f 3 -d " ")
set -f                     # avoid globbing (expansion of *).
# Convert into array:
hold_jids=(${{hold_jids//,/ }})
# echo ${{array[*]}}

# 4. Waiting for dependencies to finish
flag=0
while [ $flag -eq 0 ]
do
    if [ -f {run_index}.killall ]; then
        echo -e $run_index ".killall file created. Stopping all waiting jobs. \\nMake sure you delete the file before re-running!"
        locksed "s:\($qsubname\).*:# \\1\\tkilled:" $run_index
        kill $$;
        exit 1;
    fi
    if [ ! -f {run_index} ]; then
        echo $run_index " file deleted. Stopping all waiting jobs"
        locksed "s:\($qsubname\).*:# \\1\\tkilled:" $run_index
        kill $$;
        exit 1;
    fi

    # Get running jobs
    running=$(grep -v "^#" $run_index)
    # running=(${{running//\\n/ }})
    running=($(echo ${{running}})) 

    # Is there overlap between 'running' and 'hold_jids'?
    overlap=0
    result=""

    for item1 in "${{hold_jids[@]}}"; do
        for item2 in "${{running[@]}}"; do
            if [[ $item1 = $item2 ]]; then
                echo "Job $item1 is running. Waiting..."
                overlap=1
            fi
        done
    done
    # echo "Overlap: $overlap"
    if (( $overlap == 0 )); then
        flag=1
    fi
#    echo -n "."
    sleep 3
done

# 5. Execute script:

""".format(script_index=pipe_data["script_index"],
           run_index=pipe_data["run_index"],
           helper_funcs=pipe_data["helper_funcs"])

        return script

# ----------------------------------------------------------------
# Instance methods
# ----------------------------------------------------------------

    def __init__(self, **kwargs):#step, name, number, shell, params, pipe_data, kill_obj=None):
        """ Create a script constructor with name(i.e. 'qsub_name') and script path
        """

        if "master" not in kwargs:
            sys.exit("master must be passed in constructor")
        self.master = kwargs["master"]
            # print "Saving master"
            # print self.master.get_glob_jid_list()

        self.step = self.master.step
        self.name = self.master.name
        self.step_number = self.master.step_number
        self.shell = self.master.shell
        self.params = self.master.params
        self.pipe_data = self.master.pipe_data

        try:
            self.kill_obj = self.master.kill_script_obj
        except:
            pass

        # self.step = step
        # self.name = name
        # self.step_number = number
        # self.shell = shell
        # self.params = params
        # self.pipe_data = pipe_data
        # self.kill_obj = kill_obj

        # self.shell_ext contains the str to use as script extension for step scripts
        if self.shell == "bash":
            self.shell_ext = "sh"
        else:
            self.shell_ext = "csh"

    def __del__(self):
        """ Close filehandle when destructing class
        """
        self.filehandle.close()
    
    def __str__(self):
        print("%s - %s - %s" % (self.step , self.name , self.shell))


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

# If not in SGE context, set JOB_ID to ND
if [ -z "$JOB_ID" ]; then JOB_ID="ND"; fi

# Trap various signals. SIGUSR2 is passed by qdel when -notify is passes
trap_with_arg func_trap {step} {stepname} {stepID} {level} $HOSTNAME $JOB_ID SIGUSR2 ERR INT TERM
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



    def get_set_options_line(self, type = "set"):
        """ Adds line for activating and deactivating certain bash options
        """
        
        if self.shell=="csh":
            if self.pipe_data["verbose"]:
                sys.stderr.write("Option setting is not defined for csh. Consider using bash for your modules.\n")

            script = ""
            
        elif self.shell == "bash":
            if type=="set":
                script = """set -Eeuxo pipefail\n\n"""
            else:
                script = """set +Eeuxo pipefail\n\n"""
        else:
            script = ""
            if self.pipe_data["verbose"]:
                sys.stderr.write("shell not recognized.\n")
            
        return script
            
    def get_activate_lines(self, type):
        """ Function for adding activate/deactivate lines to scripts so that virtual environments can be used 
            A workflow that uses this option is the QIIME2 workflow.
        """
        
        if type not in ["activate", "deactivate"]:
            sys.exit("Wrong 'type' passed to create_activate_lines")
            
        if "conda" in self.params:
            # Was provided with 'null' or empty - do not do activate overriding possible global conda defs
            if not self.params["conda"]:
                
                return ""
            if "path" in self.params["conda"] and "env" in self.params["conda"]:
                activate_path = os.path.join(self.params["conda"]["path"],type)
                environ       = self.params["conda"]["env"]
            else:
                raise AssertionExcept("'conda' parameter must include 'path' and 'env'", step = self.name)
            
        else:
            return ""

        if self.shell=="csh":
            if self.pipe_data["verbose"]:
                sys.stderr.write("Are you sure you want to use 'activate' with a 'csh' based script?.\n")
        
        script = """
# Adding environment activation/deactivation command (trys activating the environment 10 times):

while [[ $lc -lt 10 ]]; do if source {activate_path} {environ}; then break; else sleep 2; lc=$(( $lc+1 )); fi; done;
[[ $lc < 10 ]]

""".format(activate_path = activate_path,
             environ = environ if type == "activate" else "") 
        
        return script
        
    def get_rm_intermediate_line(self):
        """

        :return:
        """
        return("rm -rf {dir}*\n".format(dir=self.master.base_dir))

    def write_command(self, command):
    
        self.filehandle.write(command)
                

# ----------------------------------------------------------------------------------
# HighScriptConstructor defintion
# ----------------------------------------------------------------------------------


class HighScriptConstructor(ScriptConstructor):
    """
    """
    
    def __init__(self, **kwargs):

        super(HighScriptConstructor, self).__init__(**kwargs)

        self.script_name = "{step_number}.{step}_{name}.{shell_ext}".format(**vars(self))

        self.script_path = self.pipe_data["scripts_dir"] + self.script_name

        self.script_id = self.master.spec_script_name
        self.script_id = self.master.jid_name_sep.join([self.script_id, self.pipe_data["run_code"]])
        self.level = "high"
        
        self.filehandle = open(self.script_path, "w")

    def main_script_kill_commands(self, kill_script_filename_main):
        """
        Inserts main-script killing lines into main killing script.
        Override to do something (see SGE)
        :return:
        """

        pass

    def get_script_preamble(self):   #dependency_jid_list
    
        # self.dependency_jid_list = ",".join(dependency_jid_list) if dependency_jid_list else None

        script = "\n".join([self.get_script_header(),
                            self.get_trap_line(),
                            self.get_log_lines(state = "Started"),
                            self.get_set_options_line(type = "set"),
                            "# Calling low level scripts:\n\n"])

        # Write script to high-level script
        return script

    def get_script_postamble(self):
        """ Returns part of script following main part
        """

        # Unsetting error trapping and flags before qalter, since qalter usually fails
        # (because dependencies don't exist, etc.)
        script = """
sleep {sleep}

trap '' ERR

{set_line}

{log_line}
""".format(sleep = self.pipe_data["Default_wait"],
           set_line = self.get_set_options_line(type = "unset"),
           log_line = self.get_log_lines(state = "Finished"))

        return script

    def close_script(self):
        """ Adds the closing lines to the script
        """
        self.write_command(self.get_script_postamble())

    def get_depends_command(self):
        """
        """

        return ""


# ----------------------------------------------------------------------------------
# LowScriptConstructor defintion
# ----------------------------------------------------------------------------------


class LowScriptConstructor(ScriptConstructor):
    """
    """
    
    def __init__(self,  **kwargs):

        super(LowScriptConstructor, self).__init__(**kwargs)
        
        self.script_id = self.master.spec_script_name

        self.scripts_dir = \
            "{scripts_dir}{number}.{step}_{name}{sep}".format(scripts_dir=self.pipe_data["scripts_dir"],
                                                              number = self.step_number,
                                                              step = self.step,
                                                              name = self.name,
                                                              sep = os.sep)

        self.script_path = \
            "{scripts_dir}{number}.{id}.{ext}".format(scripts_dir = self.scripts_dir,
                                                      number = self.step_number,
                                                      id = "_".join(self.script_id.split(self.master.jid_name_sep)),
                                                      ext = self.shell_ext)


        self.script_id = self.master.jid_name_sep.join([self.script_id, self.pipe_data["run_code"]])
        self.level = "low"
        self.filehandle = open(self.script_path, "w")

    def get_kill_line(self, state = "Start"):
        """ Add and remove qdel lines from qdel file.
            type can be "Start" or "Stop"
        """

        kill_cmd = self.get_kill_command()
        
        if not kill_cmd:
            return ""
            # kill_cmd = "## NO KILL COMMAND DEFINED ##"
        if state == "Start":
            script = """\
# Adding kill command to kill commands file.
exec 230>>{qdel_file}
flock -w 4000 230
echo '{kill_cmd}' >> {qdel_file}
flock -u 230\n""".format(kill_cmd = kill_cmd, qdel_file = self.script_path)
        elif state == "Stop":
            script = """\
# Removing kill command from kill commands file.
exec 230>>{qdel_file}
flock -w 4000 230
sed -i -c -e 's:^{kill_cmd}$:#&:' {qdel_file} 
flock -u 230\n""".format(kill_cmd = re.escape(kill_cmd), 
                                qdel_file = self.params["kill_script_path"])
        else:
            raise AssertionExcept("Bad type value in add_qdel_lines()", step = self.name)
            
        return script

    def get_stamped_file_register(self):
        """
        """
        
        if not self.master.stamped_files:
            return ""

        script = "######\n# Registering files with md5sum:\n"

        # Bash needs the -e flag to render \t as tabs.
        if self.shell=="csh":
            echo_cmd = "echo"
        elif self.shell=="bash":
            echo_cmd = "echo -e"
        else:
            pass

        for filename in self.master.stamped_files:
            script += """
if [ -e {filename} ]; then {echo_cmd} `date '+%%d/%%m/%%Y %%H:%%M:%%S'` '\\t{step}\\t{stepname}\\t{stepID}\\t' `md5sum {filename}` >> {file}; fi
""".format(echo_cmd=echo_cmd,
            filename=filename,
            step=self.step,
            stepname=self.name,
            stepID=self.script_id,
            file=self.pipe_data["registration_file"])
        
        script += "#############\n\n"
            
        return script

    def test_executed(self, state="Start"):
        """
        If 'rerun' is set to 'no' in params, test for existance of stamped files:
        Adds test for existance of stamped files.  If all exist, skip the script
        :return:
        """

        if not self.master.stamped_files:
            return ""

        if "keep_previous" not in self.params:
            return ""

        if state=="Start":
            script = "if [[ -e "
            script += " && \\\n\t-e ".join(self.master.stamped_files)
            script += " ]]; then \n" \
                      "    echo Skipping because output files exist >&2\n" \
                      "else\n\n\n"
            return script
            # for filename in self.master.stamped_files:
            #     script += "-e {filename} && \\".format(filename=filename)
        else:
            return "fi\n"


    def write_script(self):
        # ,
        #              script,
        #              dependency_jid_list,
        #              stamped_files,
        #              **kwargs):
        """ Assembles the scripts to writes to file
        """

        script = "\n".join([
            self.get_script_preamble(),  #dependency_jid_list
            self.get_trap_line(),
            self.get_log_lines(state="Started"),
            self.get_activate_lines(type = "activate"),
            self.get_set_options_line(type = "set"),
            self.test_executed(state="Start"),
            # THE SCRIPT!!!!
            self.master.script,
            self.test_executed(state="Stop"),
            self.get_stamped_file_register(),
            self.get_set_options_line(type = "unset"),
            # self.get_activate_lines(type = "deactivate"),
            self.get_kill_line(state = "Stop"),
            self.get_log_lines(state = "Finished")])

        self.write_command(script)

    def get_script_preamble(self):   #dependency_jid_list
    
        # self.dependency_jid_list = ",".join(dependency_jid_list) if dependency_jid_list else None

        script = "\n".join([self.get_script_header()])

        return script
        
        
# ----------------------------------------------------------------------------------
# KillScriptConstructor defintion
# ----------------------------------------------------------------------------------


class KillScriptConstructor(ScriptConstructor):

    @classmethod
    def get_main_preamble(cls, *args):
        """ Return main kill-script preamble"""

        return """\
#!/bin/bash
"""

    @classmethod
    def get_main_postamble(cls, *args):
        """ Return main kill-script postamble"""

        return """\
"""

    def __init__(self, **kwargs):

        super(KillScriptConstructor, self).__init__(**kwargs)
        
        self.script_id = self.name + "_killscript"

        self.script_path = \
            "".join([self.pipe_data["scripts_dir"],
                     "99.kill_all",
                     os.sep,
                     "99.kill_all_{name}".format(name=self.name),
                     ".sh"])

        self.filehandle = open(self.script_path, "w")

        self.filehandle.write("#!/bin/bash\n\n")

