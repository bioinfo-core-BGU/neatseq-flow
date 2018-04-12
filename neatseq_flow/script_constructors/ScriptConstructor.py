import os, shutil, sys, re
import traceback
import datetime


from copy import *
from pprint import pprint as pp

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"


class ScriptConstructor(object):

    def __init__(self, step, name, number, shell, params, pipe_data):
        """ Create a script constructor with name(i.e. 'qsub_name') and script path
        """
        
        self.step = step
        self.name = name
        self.step_number = number
        self.shell = shell
        self.params = params
        self.pipe_data = pipe_data
        
        # self.qsub_name = "_".join([self.step,self.name,self.pipe_data["run_code"]])

        
        # self.shell_ext contains the str to use as script extension for step scripts
        if self.shell == "bash":
            self.shell_ext = "sh"
        else:
            self.shell_ext = "csh"

    def __del__(self):
    
        
        self.filehandle.close()
    
    def __str__(self):
        print "%s - %s - %s" % (self.step , self.name , self.shell)
        
        
    def get_command(self):
        """ Returnn the command for executing the this script
        """
        
        qsub_line = ""
        qsub_line += "echo running " + self.name + " ':\\n------------------------------'\n"
        
        # slow_release_script_loc = os.sep.join([self.pipe_data["home_dir"],"utilities","qsub_scripts","run_jobs_slowly.pl"])

        if "slow_release" in self.params.keys():
            # Define the code for slow release 
            # Define the slow_release command (common to both options of slow_release)
            qsub_line += """ 
qsub -N %(step_step)s_%(step_name)s_%(run_code)s \\
    -q %(queue)s \\
    -e %(stderr)s \\
    -o %(stdout)s \\
    %(slow_rel_params)s \\
    -f %(scripts_dir)s%(script_name)s \n""" % \
                        {"step_step"              : self.get_step_step(),
                        "step_name"               : self.get_step_name(),
                        "run_code"                : self.run_code,
                        "stderr"                  : self.pipe_data["stderr_dir"],
                        "stdout"                  : self.pipe_data["stdout_dir"],
                        "queue"                   : self.pipe_data["qsub_params"]["queue"],
                        "scripts_dir"             : self.pipe_data["scripts_dir"],
                        "script_name"             : self.script_name,
                        "slow_rel_params"         : self.params["slow_release"]}

        else:
            qsub_line += "qsub %(scripts_dir)s%(script_name)s\n" % {"scripts_dir" : self.pipe_data["scripts_dir"], 
                                                                    "script_name" : self.script_name}

        qsub_line += "\n\n"
        return qsub_line

        
#### Methods for adding lines:
    def add_header(self):
        """
        """
        pass
        
    def write_trap_line(self):
        """
        """
        pass

        if self.shell=="csh":
            self.write_warning("Error trapping not defined for csh scripts. Consider using bash instead.\n", admonition = "WARNING")

            script = ""
            
        elif self.shell == "bash":
            script = """
# Import trap functions
. {helper_funcs}

# If not in SGE context, set JOB_ID to ND
if [ -z "$JOB_ID" ]; then JOB_ID="ND"; fi

# Trap various signals. SIGUSR2 is passed by qdel when -notify is passes
trap_with_arg func_trap {step} {stepname} {stepID} {level} $HOSTNAME $JOB_ID SIGUSR2 ERR INT TERM
            """.format(step       = self.step,                        \
                       stepname   = self.name,                        \
                       stepID     = self.script_id,                                   \
                       helper_funcs = self.pipe_data["helper_funcs"], \
                       level      = self.level)

        else:
            script = ""
            self.write_warning("shell not recognized. Not creating error trapping lines.\n", admonition = "WARNING")
        # set -Eeuxo pipefail        
        self.filehandle.write(script)
                
        
    def write_log_lines(self, state = "Started", status = "\033[0;32mOK\033[m"):
        """ Create logging lines. Added before and after script to return start and end times
            If bash, adding at beginning of script also lines for error trapping
        """

        log_cols_dict = {"type"       : state,                                        \
                         "step"       : self.step,                        \
                         "stepname"   : self.name,                        \
                         "stepID"     : self.script_id,                                   \
                         "qstat_path" : self.pipe_data["qsub_params"]["qstat_path"], \
                         "level"      : self.level,                                       \
                         "status"     : status,                                      \
                         "file"       : self.pipe_data["log_file"]}
        
        if self.shell=="csh":
        
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
            self.write_warning("shell not recognized. Not creating log writing lines in scripts.\n", admonition = "WARNING")
        
        self.filehandle.write(script)
#####################################################
    def write_set_options_line(self, type = "set"):
        """ Adds line for activating and deactivating certain bash options
        """
        
        if self.shell=="csh":
            self.write_warning("Option setting is not defined for csh. Consider using bash for your modules.\n", admonition = "WARNING")

            script = ""
            
        elif self.shell == "bash":
            if type=="set":
                script = """set -Eeuxo pipefail\n\n"""
            else:
                script = """set +Eeuxo pipefail\n\n"""
        else:
            script = ""
            self.write_warning("shell not recognized.\n", admonition = "WARNING")
            
        self.filehandle.write(script)
            
    def write_activate_lines(self, type):
        """ Function for adding activate/deactivate lines to scripts so that virtual environments can be used 
            A workflow that uses this option is the QIIME2 workflow.
        """
        
        if type not in ["activate","deactivate"]:
            sys.exit("Wrong 'type' passed to create_activate_lines")
            
        if "conda" in self.params:
            if not self.params["conda"]:  # Was provided with 'null' or empty - do not do activate overriding possible global conda defs
                
                return ""
            if "path" in self.params["conda"] and "env" in self.params["conda"]:
                activate_path = os.path.join(self.params["conda"]["path"],type)
                environ       = self.params["conda"]["env"]
            else:
                raise AssertionExcept("'conda' parameter must include 'path' and 'env'", step = self.get_step_name())
            
        else:
            return ""
            
            


        if self.shell=="csh":
            self.write_warning("Are you sure you want to use 'activate' with a 'csh' based script?")
        
        script = """
# Adding environment activation/deactivation command:
source {activate_path} {environ}

""".format(activate_path = activate_path,
             environ = environ if type == "activate" else "") 
        
        self.filehandle.write(script)
        
        
###################################################
        
    def add_del_line(self):
        """
        """
        pass
        
        
    def add_activate_lines(self):
        """
        """
        pass
        
        
    def add_set_options_line(self):
        """
        """
        pass
        
        
    def add_script(self):
        """
        """
        pass
        
        
    def add_register_files(self):
        """
        """
        pass
        
        
    def get_kill_command(self):
    
        return "qdel {script_name}".format(script_name = self.script_id)
        
    def make_script_header(self):
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
        qsub_queue =   "#$ -q %s" % self.params["qsub_params"]["queue"]
        
        return "\n".join([qsub_shell,
                            qsub_name,
                            qsub_stderr,
                            qsub_stdout,
                            qsub_holdjids]).replace("\n\n","\n") + "\n\n"
        
        
        

        
        
        
####----------------------------------------------------------------------------------

class HighScriptConstructor(ScriptConstructor):
    """
    """
    
    def __init__(self, **kwargs):
    
        super(HighScriptConstructor, self).__init__(**kwargs)

        self.script_name = "{step_number}.{step}_{name}.{shell_ext}".format(**vars(self))
        
        self.script_path = self.pipe_data["scripts_dir"] + self.script_name
        
        self.script_id   = "_".join([self.step,self.name,self.pipe_data["run_code"]])
        self.level = "high"
        
        self.filehandle = open(self.script_path, "w")
        

    def get_depends_command(self, dependency_list):
        """
        """
        
        return "qalter \\\n\t-hold_jid %s \\\n\t%s\n\n" % (dependency_list, self.script_id)
    # dependency_list

    
    def write_script_preamble(self, dependency_jid_list):
    
        self.dependency_jid_list = ",".join(dependency_jid_list) if dependency_jid_list else None
        
        # Create header with dependency_jid_list:
        qsub_header = self.make_script_header()
        script = qsub_header
        
        script = "\n".join([qsub_header,                                                         \
                            # self.create_trap_line(self.spec_qsub_name, level="high"),  \
                            # self.create_log_lines(self.spec_qsub_name,"Started", level="high"),  \
                            # self.create_set_options_line(self.spec_qsub_name, level="high", type="set"),  \
                            "# Calling low level scripts:\n\n"])
        
        # Write script to high-level script
        # with open(self.high_level_script_name, "w") as script_fh:
        self.filehandle.write(script)
        
    def make_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        general_header = super(HighScriptConstructor, self).make_script_header(**kwargs)

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


    def write_child_command(self, script_path, script_id, qdel_line):
        """ Writing low level lines to high level script: job_limit loop, adding qdel line and qsub line
            spec_qsub_name is the qsub name without the run code (see caller)
        """
        
        
        script = ""

        
        if "job_limit" in self.pipe_data.keys():
           
            script += """
# Sleeping while jobs exceed limit
perl -e 'use Env qw(USER); open(my $fh, "<", "%(limit_file)s"); ($l,$s) = <$fh>=~/limit=(\d+) sleep=(\d+)/; close($fh); while (scalar split("\\n",qx(%(qstat)s -u $USER)) > $l) {sleep $s; open(my $fh, "<", "%(limit_file)s"); ($l,$s) = <$fh>=~/limit=(\d+) sleep=(\d+)/} print 0; exit 0'

""" % {"limit_file" : self.pipe_data["job_limit"],\
            "qstat" : self.pipe_data["qsub_params"]["qstat_path"]}

            
#######            
        # Append the qsub command to the 2nd level script:
        # script_name = self.pipe_data["scripts_dir"] + ".".join([self.step_number,"_".join([self.step,self.name]),self.shell]) 
        script += """
# ---------------- Code for {spec_qsub} ------------------
{qdel_line}
# Adding qsub command:
qsub {script_name}

""".format(qdel_line = qdel_line,
        script_name = script_path,
        spec_qsub = script_id)

        
        self.filehandle.write(script)
                            
                            
    def write_script_postamble(self):
                            
                            
        
        # Unsetting error trapping and flags before qalter, since qalter usually fails (because dependencies don't exist, etc.)
        script = """
sleep {sleep}

trap '' ERR
"""
        self.filehandle.write(script)
        self.write_set_options_line(type = "unset")

        script = """
csh {scripts_dir}98.qalter_all.csh
"""
        self.filehandle.write(script)
        self.write_log_lines(state = "Finished")

                            
                            
                            
                            
                            
                            
                            
####----------------------------------------------------------------------------------
    
class LowScriptConstructor(ScriptConstructor):
    """
    """
    
    def __init__(self, id, **kwargs):
    
        
        super(LowScriptConstructor, self).__init__(**kwargs)
        
        self.script_id = id #kwargs["id"]
        self.scripts_dir = \
            "{scripts_dir}{number}.{step}_{name}{sep}".format(scripts_dir=self.pipe_data["scripts_dir"], \
                                                                number = self.step_number, \
                                                                step = self.step, \
                                                                name = self.name, \
                                                                sep = os.sep)

        self.script_path = \
            "{scripts_dir}{number}.{id}.{ext}".format(scripts_dir = self.scripts_dir, \
                                                    number = self.step_number, \
                                                    id = self.script_id, \
                                                    ext = self.shell_ext)

        self.script_id = "_".join([self.script_id, self.pipe_data["run_code"]])
        self.level = "low"
        self.filehandle = open(self.script_path, "w")

        
    def write_script_preamble(self, dependency_jid_list):
    
        self.dependency_jid_list = ",".join(dependency_jid_list) if dependency_jid_list else None
        
        # Create header with dependency_jid_list:
        qsub_header = self.make_script_header()
        
        script = "\n".join([qsub_header,                                                         \
                            # self.create_trap_line(self.spec_qsub_name, level="high"),  \
                            # self.create_log_lines(self.spec_qsub_name,"Started", level="high"),  \
                            # self.create_set_options_line(self.spec_qsub_name, level="high", type="set"),  \
                            "# Low level script goes here:\n\n"])
        
        # Write script to high-level script
        
        self.filehandle.write(script)
        
    def make_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        general_header = super(LowScriptConstructor, self).make_script_header(**kwargs)

        only_low_lev_params  = ["-pe"]
        compulsory_high_lev_params = {"-V":""}
        # special_opts = "-N -e -o -q -hold_jid".split(" ") + only_low_lev_params


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

    def write_command(self, command):
    
        self.filehandle.write(command)
        
    def write_kill_line(self, state = "Start"):
        """ Add and remove qdel lines from qdel file.
            type can be "Start" or "Stop"
        """
        

        kill_cmd = self.get_kill_command() #"qdel {script_name}".format(script_name = self.spec_qsub_name)
        
        if state == "Start":
            script = "# Adding qdel command to qdel file.\necho '{kill_cmd}' >> {qdel_file}\n".format(kill_cmd = kill_cmd, qdel_file = self.script_path)
        elif state == "Stop":
            script = "# Removing qdel command from qdel file.\nsed -i -e 's:^{kill_cmd}$:#&:' {qdel_file}\n".format(kill_cmd = re.escape(kill_cmd), 
                                qdel_file = self.script_path)
        else:
            raise AssertionExcept("Bad type value in add_qdel_lines()", step = self.name)
            
        self.filehandle.write(script)

    def write_stamped_file_register(self,stamped_files):
        """
        """
        
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
""" %      {"echo_cmd" : echo_cmd,             \
            "filename" : filename,             \
            "step"     : self.step, \
            "stepname" : self.name, \
            "stepID"   : self.script_id,            \
            "file"     : self.pipe_data["registration_file"]}
        
        script += "#############\n\n"
            
        self.filehandle.write(script)
        
        
        
    def write_script(self,
                        script,
                        dependency_jid_list,
                        stamped_files, **kwargs):

        if "level" not in kwargs:
            kwargs["level"] = "low"

        self.write_script_preamble(dependency_jid_list)

        self.write_trap_line()
        self.write_log_lines(state="Started")
        
        self.write_activate_lines(type = "activate")
        self.write_set_options_line(type = "set")
        
        self.write_command(script)
        
        
        if stamped_files:
            self.write_stamped_file_register(stamped_files)
            
        self.write_set_options_line(type = "unset")
        self.write_activate_lines(type = "deactivate")
        self.write_kill_line(state = "Stop")
        self.write_log_lines(state = "Finished")
        
####----------------------------------------------------------------------------------

class KillScriptConstructor(ScriptConstructor):

    def __init__(self, **kwargs):
    
        super(KillScriptConstructor, self).__init__(**kwargs)
        
        
        self.script_path = \
            "".join([self.pipe_data["scripts_dir"], \
                     "99.kill_all", \
                     os.sep, \
                     "99.kill_all_{name}".format(name=self.name), \
                     ".csh"])


        self.filehandle = open(self.script_path, "w")

        self.filehandle.write("#!/usr/csh\n\n")
        
        