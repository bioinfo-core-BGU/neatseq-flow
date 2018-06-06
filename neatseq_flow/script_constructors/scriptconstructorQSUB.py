# import os
# import shutil
# import sys
# import re
# import traceback
# import datetime
#
# from copy import *
# from pprint import pprint as pp

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"


from scriptconstructor import *


class ScriptConstructorQSUB(ScriptConstructor):

    @classmethod
    def get_helper_script(cls, *args):
        """ Returns the code for the helper script
        """
        script = super(ScriptConstructorQSUB, cls).get_helper_script(*args)
        script = re.sub("## locksed command entry point", r"""locksed  "s:^\\($3\\).*:# \\1\\t$err_code:" $run_index""", script)

        return script

    @classmethod
    def get_exec_script(cls, pipe_data):
        """ Not used for SGE. Returning None"""

        script = super(ScriptConstructorQSUB, cls).get_exec_script(pipe_data)

        script += """\
jobid=$(qsub $script_path | cut -d " " -f 3)

locksed "s:\($qsubname\).*$:\\1\\trunning\\t$jobid:" $run_index

"""
        return script

    def get_command(self):
        """ Return the command for executing the this script
        """
        
        script = ""

        if "slow_release" in self.params.keys():
            sys.exit("Slow release no longer supported. Use 'job_limit'")

        else:
            script += """\
bash {nsf_exec} {script_id} 1>> {nsf_exec}.stdout 2>> {nsf_exec}.stderr &\n\n""".\
                format(script_id = self.script_id,
                       nsf_exec = self.pipe_data["exec_script"])

        return script

    # -----------------------
    # Instance methods

    def get_kill_command(self):

        pass
        # TODO: Change this to work like SLURM: qdel on numbers in run_index
        # Not implemented in SLURM, yet, either...
        # return "qdel {script_name}".format(script_name = self.script_id)
        
    def get_script_header(self):
        """ Make the first few lines for the scripts
            Is called for high level, low level and wrapper scripts
        """

        qsub_shell = "#!/bin/%(shell)s\n#$ -S /bin/%(shell)s" % {"shell": self.shell}
        # Make hold_jids line only if there are jids (i.e. self.get_dependency_jid_list() != [])
        # Make hold_jids line only if there are jids (i.e. self.get_dependency_jid_list() != [])
        if self.master.dependency_jid_list:
            # Old style: Full list of jids:
            # qsub_holdjids = "#$ -hold_jid %s " % ",".join(self.master.dependency_jid_list)
            # New style: Using globs:
            qsub_holdjids = "#$ -hold_jid {hold_jid_list}".format(
                hold_jid_list=",".join(map(lambda x: '"%s"' % x, self.master.dependency_glob_jid_list)))
        else:
            qsub_holdjids = ""

        qsub_name =    "#$ -N %s " % (self.script_id)
        qsub_stderr =  "#$ -e %s" % self.pipe_data["stderr_dir"]
        qsub_stdout =  "#$ -o %s" % self.pipe_data["stdout_dir"]
        # qsub_queue =   "#$ -q %s" % self.params["qsub_params"]["queue"]

        return "\n".join([qsub_shell,
                            qsub_name,
                            qsub_stderr,
                            qsub_stdout,
                            qsub_holdjids]).replace("\n\n","\n")

# ----------------------------------------------------------------------------------
# HighScriptConstructorQSUB defintion
# ----------------------------------------------------------------------------------


class HighScriptConstructorQSUB(ScriptConstructorQSUB,HighScriptConstructor):
    """
    """

    def get_depends_command(self):
        """
        """

        # Old method:
        # return "qalter \\\n\t-hold_jid %s \\\n\t%s\n\n" % (dependency_list, self.script_id)
        # New methods wirh glob:

        return "qalter \\\n\t-hold_jid {glob_jid_list} \\\n\t{script_id}\n\n".format(
            # Comma separated list of double-quote enclosed glob jids:
            glob_jid_list=",".join(map(lambda x: '"%s"' % x, self.master.dependency_glob_jid_list)),
            script_id=self.script_id)

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

        # Adding 'compulsory_high_lev_params' to all high level scripts
        # (This includes '-V'. Otherwise, if shell is bash, the QSUB commands are not recognized)
        for qsub_opt in compulsory_high_lev_params:
            if qsub_opt not in self.params["qsub_params"]["opts"]:
                qsub_opts += "#$ {key} {val}\n".format(key=qsub_opt, 
                                                val=compulsory_high_lev_params[qsub_opt]) 

        # Sometimes qsub_opts is empty and then there is an ugly empty line in the middle of the qsub definition.
        # Removing the empty line with replace()
        return "\n".join([general_header,
                            qsub_queue,
                            qsub_opts]).replace("\n\n","\n") + "\n\n"

    def get_command(self):
        """ Writing low level lines to high level script: job_limit loop, adding qdel line and qsub line
            spec_qsub_name is the qsub name without the run code (see caller)
            """
        
        # if "job_limit" in self.pipe_data.keys():
        #     sys.exit("Job limit not supported yet for Local!")

        command = super(HighScriptConstructorQSUB, self).get_command()

        # TODO: Add output from stdout and stderr

        script = """
# ---------------- Code for {script_id} ------------------
echo running {script_id}
{command}

sleep {sleep_time}
""".format(script_id=self.script_id,
           sleep_time=self.pipe_data["Default_wait"],
           command=command)

        return script

    def get_child_command(self, script_obj):
        """ Writing low level lines to high level script: job_limit loop, adding qdel line and qsub line
            spec_qsub_name is the qsub name without the run code (see caller)
        """

        job_limit = ""

        if "job_limit" in self.pipe_data.keys():
            job_limit = """\
# Sleeping while jobs exceed limit
while : ; do numrun=$(egrep -c "^\w" {run_index}); maxrun=$(sed -ne "s/limit=\([0-9]*\).*/\\1/p" {limit_file}); sleeptime=$(sed -ne "s/.*sleep=\([0-9]*\).*/\\1/p" {limit_file}); [[ $numrun -ge $maxrun ]] || break; sleep $sleeptime; done
""".format(limit_file=self.pipe_data["job_limit"],
           run_index=self.pipe_data["run_index"])

        script = """
# ---------------- Code for {script_id} ------------------
{job_limit}
# Adding qsub command:
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

        # Get general postamble
        postamble = super(HighScriptConstructorQSUB, self).get_script_postamble()

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
# LowScriptConstructorQSUB defintion
# ----------------------------------------------------------------------------------


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

        super(LowScriptConstructorQSUB, self).write_script()
        # script,
        #                                                 dependency_jid_list,
        #                                                 stamped_files,
        #                                                 **kwargs)

        self.write_command("""\

# Setting script as done in run index:
# Using locksed provided in helper functions
locksed  "s:^\({script_id}\).*:# \\1\\tdone:" {run_index}

""".format(run_index = self.pipe_data["run_index"],
           script_id = self.script_id))

# ----------------------------------------------------------------------------------
# KillScriptConstructorQSUB defintion
# ----------------------------------------------------------------------------------


class KillScriptConstructorQSUB(ScriptConstructorQSUB,KillScriptConstructor):

    @classmethod
    def get_main_preamble(cls, run_index):
        """ Return main kill-script preamble"""
        pass
        return """\
#!/bin/bash

# Kill held scripts:
touch {run_index}.killall

""".format(run_index=run_index)

    @classmethod
    def get_main_postamble(cls, run_index):
        """ Return main kill-script postamble"""

        return """\
wait
sleep 10 

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
    echo running "qdel $item1"
    qdel $item1
done

""".format(run_index=self.pipe_data["run_index"],
           step=caller_script.step,
           name=caller_script.name)

        self.filehandle.write(script)

