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
jobid=$(qsub $script_path | cut -d " " -f 3)

echo "lock on sedlock" 
sedlock=${run_index}.sedlock
exec 200>$sedlock
flock -w 20 200 || exit 1

sed -i -e "s:$1.*$:&\\t$jobid:" $run_index

echo $qsubname "sedlock released"
"""
    

class ScriptConstructorQSUB(ScriptConstructor):

        
        
    def get_command(self):
        """ Return the command for executing the this script
        """
        
        script = ""

        if "slow_release" in self.params.keys():
            sys.exit("Slow release no longer supported. Use 'job_limit'")

        else:
            script += """\
sh {nsf_exec} \\
    {script_id} \\ 
    1>> {nsf_exec}.stdout \\
    2>> {nsf_exec}.stderr &\n\n""".format(script_id = self.script_id,
                          nsf_exec = self.pipe_data["exec_script"])


        return script

        
        
###################################################
        
        
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
        qsub_queue =   "#$ -q %s" % self.params["qsub_params"]["queue"]
        
        return "\n".join([qsub_shell,
                            qsub_name,
                            qsub_stderr,
                            qsub_stdout,
                            qsub_holdjids]).replace("\n\n","\n") 
        
        
        

        
        
        
####----------------------------------------------------------------------------------

class HighScriptConstructorQSUB(ScriptConstructorQSUB,HighScriptConstructor):
    """
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

        general_header = super(HighScriptConstructorQSUB, self).get_script_header(**kwargs)

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


        # Adding 'compulsory_high_lev_params' to all high level scripts (This includes '-V'. Otherwise, if shell is bash, the QSUB commands are not recognized)
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
        
        if "job_limit" in self.pipe_data.keys():
            sys.exit("Job limit not supported yet for Local!")


        command = super(HighScriptConstructorQSUB, self).get_command()

        

        # TODO: Add output from stdout and stderr

        script = """
# ---------------- Code for {script_id} ------------------
echo running {script_id}
{command}

sleep {sleep_time}
""".format(script_id = self.script_id,
        sleep_time = self.pipe_data["Default_wait"],
        command = command)
        
        
        return script                            
                            
                            
                            

    def get_child_command(self, script_obj):
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
# ---------------- Code for {script_id} ------------------

echo '{qdel_line}' >> {step_kill_file}
# Adding qsub command:
{child_cmd}

""".format(qdel_line = script_obj.get_kill_command(),
        script_name = script_obj.script_path,
        script_id = script_obj.script_id,
        child_cmd = script_obj.get_command(),
        step_kill_file = self.params["kill_script_path"])

        
        return script
                            
                            
                   
    def get_script_postamble(self):
                            
                            
        
    
        # Get general postamble
        postamble = super(HighScriptConstructorQSUB, self).get_script_postamble()

        
        script = """\
{postamble}

wait

# manage without!!!:  csh {scripts_dir}98.qalter_all.csh

# Setting script as done in run index:
echo "lock on sedlock" 
sedlock={run_index}.sedlock
exec 200>$sedlock
flock -w 20 200 || exit 1

sed -i -e "s:^{script_id}.*:# &:" {run_index}
echo "{script_id} sedlock released"
""".format(\
    postamble = postamble, 
    script_id = self.script_id,
    run_index = self.pipe_data["run_index"],
    scripts_dir = self.pipe_data["scripts_dir"])
        
        return script
                     
        
                            
                            
####----------------------------------------------------------------------------------
    
class LowScriptConstructorQSUB(ScriptConstructorQSUB,LowScriptConstructor):
    """
    """

    def get_script_header(self, **kwargs):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        general_header = super(LowScriptConstructorQSUB, self).get_script_header(**kwargs)

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

    def write_script(self,
                        script,
                        dependency_jid_list,
                        stamped_files, **kwargs):

        if "level" not in kwargs:
            kwargs["level"] = "low"

        super(LowScriptConstructorQSUB, self).write_script(script,
                                                        dependency_jid_list,
                                                        stamped_files,
                                                        **kwargs)

        
        self.write_command("""\

# Setting script as done in run index:
echo "lock on sedlock" 
sedlock={run_index}.sedlock
exec 200>$sedlock
flock -w 20 200 || exit 1

sed -i -e "s:^{script_id}.*:# &:" {run_index}
echo "{script_id} sedlock released"

""".format(\
    run_index = self.pipe_data["run_index"],
    script_id = self.script_id))
                
        
####----------------------------------------------------------------------------------

class KillScriptConstructorQSUB(ScriptConstructorQSUB,KillScriptConstructor):


    
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
        
        