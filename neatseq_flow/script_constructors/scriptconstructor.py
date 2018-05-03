import os
import sys
import re

from ..PLC_step import AssertionExcept

# from pprint import pprint as pp

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"


class ScriptConstructor(object):
    """ General class for script construction and management
    """

    @classmethod
    def get_helper_script(cls, log_file, qstat_path):
        """ Returns the code for the helper script
            Note. The line with '## locksed command entry point' should be dealt with in inheriting classes.
            Either replace with nothing to remove (see scriptConstructorSGE) or replaced with a
            locksed command, see scriptConstructorLocal.
        """
        script = """\
#!/bin/bash
trap_with_arg() {{
    # $1: func
    # $2: module
    # $3: instance
    # $4: instance_id
    # $5: level
    # $6: run_index file
    # $7: hostname
    # $8: jobid

    args="$1 $2 $3 $4 $5 $6 $7 $8"
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
    # $5: run_index file
    # $6: hostname
    # $7: jobid
    # $8: sig

    if [ ! $6 == 'ND' ]; then
        maxvmem=$({qstat_path} -j $6 | grep maxvmem | cut -d = -f 6);
    else
        maxvmem="NA";
    fi

    if [ $7 == 'ERR' ]; then err_code='ERROR'; fi
    if [ $7 == 'INT' ]; then err_code='TERMINATED'; fi
    if [ $7 == 'TERM' ]; then err_code='TERMINATED'; fi
    if [ $7 == 'SIGUSR2' ]; then err_code='TERMINATED'; fi


    echo -e $(date '+%d/%m/%Y %H:%M:%S')'\\tFinished\\t'$1'\\t'$2'\\t'$3'\\t'$4'\\t'$5'\\t'$maxvmem'\\t[0;31m'$err_code'[m' >> {log_file}; 

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

    if [ ! $6 == 'ND' ]; then
        if [ $7 == 'Finished' ]; then
            maxvmem=$({qstat_path} -j $6 | grep maxvmem | cut -d = -f 6);
        else    
            maxvmem="-"
        fi
    else
        maxvmem="NA";
    fi


    echo -e $(date '+%d/%m/%Y %H:%M:%S')'\\t'$7'\\t'$1'\\t'$2'\\t'$3'\\t'$4'\\t'$5'\\t'$maxvmem'\\t[0;32mOK[m' >> {log_file};

}}

locksed() {{
    # $1: program
    # $2: file
    # Setting script as done in run index:
    sedlock=${{2}}.sedlock
    exec 200>$sedlock
    flock -w 4000 200 || exit 1

    echo do sed 
    sed -i -e "$1" $2

    echo unlock
    flock -u 200
}}

""".format(log_file=log_file,
           qstat_path=qstat_path)
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

echo $1

script_path=$(grep $qsubname $script_index | cut -f 2 )

echo $script_path

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
        exit 1;
    fi
    if [ ! -f {run_index} ]; then
        echo $run_index " file deleted. Stopping all waiting jobs"
        locksed "s:\($qsubname\).*:# \\1\\tkilled:" $run_index
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



        self.step = kwargs["step"]
        self.name = kwargs["name"]
        self.step_number = kwargs["number"]
        self.shell = kwargs["shell"]
        self.params = kwargs["params"]
        self.pipe_data = kwargs["pipe_data"]
        if "kill_obj" in kwargs:
            self.kill_obj = kwargs["kill_obj"]

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
        print "%s - %s - %s" % (self.step , self.name , self.shell)


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
# Import trap functions
. {helper_funcs}

# If not in SGE context, set JOB_ID to ND
if [ -z "$JOB_ID" ]; then JOB_ID="ND"; fi

# Trap various signals. SIGUSR2 is passed by qdel when -notify is passes
trap_with_arg func_trap {step} {stepname} {stepID} {level} {run_index} $HOSTNAME $JOB_ID SIGUSR2 ERR INT TERM
            """.format(step       = self.step,
                       stepname   = self.name,
                       stepID     = self.script_id,
                       helper_funcs = self.pipe_data["helper_funcs"],
                       run_index  = self.pipe_data["run_index"],
                       level      = self.level)

        else:
            script = ""
            if self.pipe_data["verbose"]:
                sys.stderr.write("shell not recognized. Not creating error trapping lines.\n")

        return script

    def get_log_lines(self, state = "Started", status = "\033[0;32mOK\033[m"):
        """ Create logging lines. Added before and after script to return start and end times
            If bash, adding at beginning of script also lines for error trapping
        """

        log_cols_dict = {"type"       : state,
                         "step"       : self.step,
                         "stepname"   : self.name,
                         "stepID"     : self.script_id,
                         "qstat_path" : self.pipe_data["qsub_params"]["qstat_path"],
                         "level"      : self.level,
                         "status"     : status,
                         "file"       : self.pipe_data["log_file"]}
        
        if self.shell == "csh":
        
            script = """
if ($?JOB_ID) then 
	# Adding line to log file:  Date    Step    Host
	echo `date '+%%d/%%m/%%Y %%H:%%M:%%S'`'\\t%(type)s\\t%(step)s\\t%(stepname)s\\t%(stepID)s\\t%(level)s\\t'$HOSTNAME'\\t'`%(qstat_path)s -j $JOB_ID | grep maxvmem | cut -d = -f 6`'\\t%(status)s' >> %(file)s
else
	echo `date '+%%d/%%m/%%Y %%H:%%M:%%S'`'\\t%(type)s\\t%(step)s\\t%(stepname)s\\t%(stepID)s\\t%(level)s\\t'$HOSTNAME'\\t-\\t%(status)s' >> %(file)s
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
# Adding environment activation/deactivation command:
source {activate_path} {environ}

""".format(activate_path = activate_path,
             environ = environ if type == "activate" else "") 
        
        return script
        
        
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
        
        self.script_id = "_".join([self.step,self.name, self.pipe_data["run_code"]])
        self.level = "high"
        
        self.filehandle = open(self.script_path, "w")

    def main_script_kill_commands(self, kill_script_filename_main):
        """
        Inserts main-script killing lines into main killing script.
        Override to do something (see SGE)
        :return:
        """

        pass


    def get_script_preamble(self, dependency_jid_list):
    
        self.dependency_jid_list = ",".join(dependency_jid_list) if dependency_jid_list else None

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


# ----------------------------------------------------------------------------------
# LowScriptConstructor defintion
# ----------------------------------------------------------------------------------


class LowScriptConstructor(ScriptConstructor):
    """
    """
    
    def __init__(self, id, **kwargs):

        super(LowScriptConstructor, self).__init__(**kwargs)
        
        self.script_id = id
        
        self.scripts_dir = \
            "{scripts_dir}{number}.{step}_{name}{sep}".format(scripts_dir=self.pipe_data["scripts_dir"],
                                                              number = self.step_number,
                                                              step = self.step,
                                                              name = self.name,
                                                              sep = os.sep)

        self.script_path = \
            "{scripts_dir}{number}.{id}.{ext}".format(scripts_dir = self.scripts_dir,
                                                    number = self.step_number,
                                                    id = self.script_id,
                                                    ext = self.shell_ext)

        self.script_id = "_".join([self.script_id, self.pipe_data["run_code"]])
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
echo '{kill_cmd}' >> {qdel_file}\n""".format(kill_cmd = kill_cmd, qdel_file = self.script_path)
        elif state == "Stop":
            script = """\
# Removing kill command from kill commands file.
sed -i -e 's:^{kill_cmd}$:#&:' {qdel_file}\n""".format(kill_cmd = re.escape(kill_cmd), 
                                qdel_file = self.script_path)
        else:
            raise AssertionExcept("Bad type value in add_qdel_lines()", step = self.name)
            
        return script

    def get_stamped_file_register(self,stamped_files):
        """
        """
        
        if not stamped_files:
            return ""

        script = "######\n# Registering files with md5sum:\n"

        # Bash needs the -e flag to render \t as tabs.
        if self.shell=="csh":
            echo_cmd = "echo"
        elif self.shell=="bash":
            echo_cmd = "echo -e"
        else:
            pass

        for filename in stamped_files:
            script += """
%(echo_cmd)s `date '+%%d/%%m/%%Y %%H:%%M:%%S'` '\\t%(step)s\\t%(stepname)s\\t%(stepID)s\\t' `md5sum %(filename)s` >> %(file)s
""" %      {"echo_cmd" : echo_cmd,
            "filename" : filename,
            "step"     : self.step,
            "stepname" : self.name,
            "stepID"   : self.script_id,
            "file"     : self.pipe_data["registration_file"]}
        
        script += "#############\n\n"
            
        return script
        
    def write_script(self,
                     script,
                     dependency_jid_list,
                     stamped_files,
                     **kwargs):
        """ Assembles the scripts to writes to file
        """

        if "level" not in kwargs:
            kwargs["level"] = "low"

        script = "\n".join([
            self.get_script_preamble(dependency_jid_list),
            self.get_trap_line(),
            self.get_log_lines(state="Started"),
            self.get_activate_lines(type = "activate"),
            self.get_set_options_line(type = "set"),
            # THE SCRIPT!!!!
            script,
            self.get_stamped_file_register(stamped_files),
            self.get_set_options_line(type = "unset"),
            self.get_activate_lines(type = "deactivate"),
            self.get_kill_line(state = "Stop"),
            self.get_log_lines(state = "Finished")])

        
        self.write_command(script)


    def get_script_preamble(self, dependency_jid_list):
    
        self.dependency_jid_list = ",".join(dependency_jid_list) if dependency_jid_list else None

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
#!/bin/sh
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

