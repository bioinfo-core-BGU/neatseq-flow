import os, shutil, sys, re
import traceback
import datetime


from copy import *
from pprint import pprint as pp

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"


class ScriptConstructor(object):
    """ General class for script construction and management
    """
    
    def __init__(self, step, name, number, shell, params, pipe_data):
        """ Create a script constructor with name(i.e. 'qsub_name') and script path
        """
        
        self.step = step
        self.name = name
        self.step_number = number
        self.shell = shell
        self.params = params
        self.pipe_data = pipe_data
        
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
        
        

        
#### Methods for adding lines:
        
    def get_trap_line(self):
        """
        """
        

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
        return script
                
        
    def get_log_lines(self, state = "Started", status = "\033[0;32mOK\033[m"):
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
        
        script = ""
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
        
        return script
        
        

    def get_set_options_line(self, type = "set"):
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
            
        return script
            
    def get_activate_lines(self, type):
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
        
        return script
        
        
    def write_command(self, command):
    
        self.filehandle.write(command)
                
        
        
        
        
        
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
        


    
    def get_script_preamble(self, dependency_jid_list):
    
        self.dependency_jid_list = ",".join(dependency_jid_list) if dependency_jid_list else None
        
        
        
        script = "\n".join([self.get_script_header(),                                                         \
                            self.get_trap_line(), #create_trap_line(self.spec_qsub_name, level="high"),  \
                            self.get_log_lines(state = "Started"), # self.create_log_lines(self.spec_qsub_name,"Started", level="high"),  \
                            self.get_set_options_line(type = "set"),# self.create_set_options_line(self.spec_qsub_name, level="high", type="set"),  \
                            "# Calling low level scripts:\n\n"])
        
        # Write script to high-level script
        return script
        
        
        
                            
    def get_script_postamble(self):
                            
                     
        # Unsetting error trapping and flags before qalter, since qalter usually fails (because dependencies don't exist, etc.)
        script = """
sleep {sleep}

trap '' ERR

{set_line}

{log_line}
""".format(sleep = self.pipe_data["Default_wait"],
            set_line = self.get_set_options_line(type = "unset"),
            log_line = self.get_log_lines(state = "Finished"))

        
        return script

        
        
                            
                            
                            
                            
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
""" %      {"echo_cmd" : echo_cmd,             \
            "filename" : filename,             \
            "step"     : self.step, \
            "stepname" : self.name, \
            "stepID"   : self.script_id,            \
            "file"     : self.pipe_data["registration_file"]}
        
        script += "#############\n\n"
            
        return script
        
        
        
    def write_script(self,
                        script,
                        dependency_jid_list,
                        stamped_files, **kwargs):

        if "level" not in kwargs:
            kwargs["level"] = "low"
            

        script = "\n".join([   \
            self.get_script_preamble(dependency_jid_list),        \
            self.get_trap_line(),                                 \
            self.get_log_lines(state="Started"),                  \
            self.get_activate_lines(type = "activate"),           \
            self.get_set_options_line(type = "set"),              \
            # THE SCRIPT!!!!
            script,                                               \
            self.get_stamped_file_register(stamped_files),        \
            self.get_set_options_line(type = "unset"),            \
            self.get_activate_lines(type = "deactivate"),         \
            self.get_kill_line(state = "Stop"),                   \
            self.get_log_lines(state = "Finished")])

        
        self.write_command(script)


    def get_script_preamble(self, dependency_jid_list):
    
        self.dependency_jid_list = ",".join(dependency_jid_list) if dependency_jid_list else None
        
        
        
        script = "\n".join([self.get_script_header()])
        
        
        return script
        
        
        
                            
    # def get_script_postamble(self):
                            
                            
        
        # # Unsetting error trapping and flags before qalter, since qalter usually fails (because dependencies don't exist, etc.)
        # script = """

# trap '' ERR
# """
        # # self.filehandle.write(script)
        # # self.write_set_options_line(type = "unset")

        # script = "\n".join([script,
                            # self.get_set_options_line(type = "unset"),
                            # self.get_log_lines(state = "Finished")])
        
        # return script
        
        # # self.write_log_lines(state = "Finished")

                                    
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
        
        