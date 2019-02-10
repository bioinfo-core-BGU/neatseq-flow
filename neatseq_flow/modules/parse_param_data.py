

""" Functions for reading and parsing pipeline parameter files
"""

__author__ = "Menachem Sklarz"
__version__ = "1.5.0"


import os, sys, re, yaml
from pprint import pprint as pp
import collections
from collections import OrderedDict

######################## From here: https://gist.github.com/pypt/94d747fe5180851196eb
from yaml.constructor import ConstructorError
from functools import reduce

try:
    # from yaml import CLoader as Loader
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader

from neatseq_flow.modules.parse_sample_data import remove_comments, check_newlines

STEP_PARAMS_SINGLE_VALUE = ['module','redirects']

# The keys are the supported executors. The values - a str list of parameters that NeatSeq-Flow sets independently
SUPPORTED_EXECUTORS = \
    {"SGE": "-N -e -o -q -hold_jid".split(" "),
     "QSUB": "-N -e -o -q -hold_jid".split(" "),
     "SLURM": "-e -o -hold_jid --error --output -J --job-name -p --partition -w".split(" "),
     "SLURMnew": "-e -o -hold_jid --error --output -J --job-name -p --partition -w".split(" "),
     "Local": ""}

def parse_param_file(filename):
    """Parses a file from filename
    """
    file_conts = []

    filenames = filename.split(",")
    for filename_raw in filenames:
        # Expanding '~' and returning full path 
        filename = os.path.realpath(os.path.expanduser(filename_raw))

        if not os.path.isfile(filename):
            sys.exit("Parameter file %s does not exist.\n" % filename)

        with open(filename) as fileh:
            file_conts += fileh.readlines()
           
    check_newlines(file_conts)

    try:
        return get_param_data_YAML(file_conts)
        # pp(get_param_data_YAML(file_conts))
        
    except ConstructorError as exc:
        error_comm = ""
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            error_comm = "Error position: ({l}:{c})\n{snippet}".format(l=mark.line+1,
                                                                       c=mark.column+1,
                                                                       snippet=mark.get_snippet())
        raise Exception("{error}\nPossible duplicate value passed".format(error=error_comm), "parameters")
    except yaml.YAMLError as exc:
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            print("Error position: (%s:%s)" % (mark.line+1, mark.column+1))
            print(mark.get_snippet())
        
        # Comment out the following line to enable classic param file format.
        # Not recommended.
        raise Exception("Failed to read YAML file. Make sure your parameter file is a correctly formatted YAML document.", "parameters")
    except:
        raise #Exception("Unrecognised exception reading the parameter file.", "parameters")
    
    # print "YAML failed. trying classic"
    # return get_param_data(file_conts)

def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node, deep=False, upper_key=None):
        ##########
        # Detecting duplicate keys. From: https://gist.github.com/pypt/94d747fe5180851196eb
        mapping = {}

        for key_node, value_node in node.value:
            # import pdb;
            # pdb.set_trace()
            key = loader.construct_object(key_node, deep=deep)
            value = loader.construct_object(value_node, deep=deep)
            # print "key:{key}; value:{value}\n".format(key=key, value=value)
            if key in mapping and node.value:
                raise ConstructorError("while constructing a mapping", node.start_mark,
                                       "found duplicate key (%s)" % key, key_node.start_mark)
            mapping[key] = value

        ##########
        loader.flatten_mapping(node)

        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)

def get_param_data_YAML(filelines):
    """ Parse YAML-formatted parameter files
    """
    def convert_param_format(param_dict):  # Gets the step part of the params dict
        yamlnames = [name for name in param_dict]
        endparams = {}
        for yamlname in yamlnames:
            if "module" not in param_dict[yamlname]:
                raise Exception("You did not supply a module name in %s\n" % yamlname, "parameters")
            if not isinstance(param_dict[yamlname]["module"], str):
                raise Exception("In %s: 'module' must be a string, not a list or anything else...\n" % yamlname, "parameters")
            if param_dict[yamlname]["module"] not in endparams:
                endparams[param_dict[yamlname]["module"]] = {}
            # Create temporary dict for instance parameters. Store permanently at end of loop iteration
            yamlname_params = param_dict[yamlname]
        
            # Converting "redirects" to "redir_params" for backwards compatibility...
            if "redirects" in list(yamlname_params.keys()):
                yamlname_params["redir_params"] = \
                    yamlname_params.pop("redirects")
            else:   # Add empty redir_params.
                yamlname_params["redir_params"] = {}
            # When redirects keys are numbers, such as '-1' in bowtie2 mapper, the keys are stored as numbers.
            # This is bad for testing. Converting all numeric keys to character keys:
            yamlname_params["redir_params"] = \
                {str(key):value \
                for (key,value) \
                in list(yamlname_params["redir_params"].items())}

            # Converting base to list if it is not one already
            if "base" in list(yamlname_params.keys()) and not isinstance(yamlname_params["base"],list):
                yamlname_params["base"] = [yamlname_params["base"]]

            if "qsub_params" in yamlname_params:
                # # 1. Dealing with 'queue' and '-q':
                ## Has been moved to function param_data_testing_step_wise()

                # 2. Dealing with 'node'
                # Converting node to list if it is not one already
                # If 'nodes' was used, convert it to 'node', i.e. accept nodes typo...
                if "nodes" in yamlname_params["qsub_params"]:
                    yamlname_params["qsub_params"]["node"] = yamlname_params["qsub_params"]["nodes"]
                    del yamlname_params["qsub_params"]["nodes"]

                if "node" in yamlname_params["qsub_params"]:
                    if isinstance(yamlname_params["qsub_params"]["node"], str):
                        yamlname_params["qsub_params"]["node"] = re.split("[\, ]*",yamlname_params["qsub_params"]["node"])
                        #[yamlname_params["qsub_params"]["node"]]

                # 3. Moving all params which are not 'node', '-q' or 'queue', to 'opts'
                params2mv = list(set(yamlname_params["qsub_params"]) - {"node", "queue", "-q"})
                yamlname_params["qsub_params"]["opts"] = {key: (val if val is not None else '')
                                                          for key, val
                                                          in yamlname_params["qsub_params"].items()
                                                          if key in params2mv}
                for param in params2mv:
                    del yamlname_params["qsub_params"][param]

                # Convert sample_list to list, or empty list if empty
            if "sample_list" in yamlname_params:
                if isinstance(yamlname_params["sample_list"], str):
                    yamlname_params["sample_list"] = re.split("[\, ]*", yamlname_params["sample_list"])
                elif isinstance(yamlname_params["sample_list"], list):
                    pass
                elif isinstance(yamlname_params["sample_list"], dict):
                    # Allowing dict for category-wise sample specification
                    pass
                else:
                    raise AssertionExcept("sample_list must be string or list!")

                # Remove empty and duplicate strings:
                if isinstance(yamlname_params["sample_list"], list):
                    yamlname_params["sample_list"] = list(set([x for x in yamlname_params["sample_list"] if x != ""]))

            endparams[param_dict[yamlname]["module"]][yamlname] = yamlname_params
        return endparams
 
    #filelines = remove_comments(filelines)
    
    # Convert all tabs to 4 spaces. Tabs do not work well with YAML!
    filelines = [re.sub("\t","    ",line) for line in filelines]
    
    # Read params with pyyaml package:
    # yaml_params = yaml.load("\n".join(filelines),  Loader=yaml.SafeLoader)
    # yaml_params = yaml.safe_load("\n".join(filelines))

    yaml_params = ordered_load("\n".join(filelines),Loader=Loader)

    # yaml.safe_dump(yaml_params)
    # sys.exit()
    usr_step_order = list(yaml_params["Step_params"].keys())
    
    # If there is a Variables section, interpolate any appearance of the variables in the params
    if "Vars" in list(yaml_params.keys()):
        
        # Prepare the bunch for variable interpolation:
        from munch import Munch
        from .var_interpol_defs import make_interpol_func, walk, test_vars
        
        test_vars(yaml_params["Vars"])

        variables_bunch = Munch.fromDict({"Vars":yaml_params["Vars"]})
        # print variables_bunch
        f_interpol = make_interpol_func(variables_bunch)

        # Actual code to run when 'Vars' exists:
        # Walk over params dict and interpolate strings:

        yaml_params = walk(yaml_params, variables_bunch, callback= f_interpol)

    param_data = dict()

    # Extract global parameter dict from lines:
    try:
        param_data["Global"] = yaml_params["Global_params"]
    except KeyError:
        raise Exception("You must include a 'Global_params' section in your parameter file!\n\n", "parameters")

    param_data["Global"] = test_and_modify_global_params(param_data["Global"])

    # Extract step-wise parameter dict from lines:
    param_data["Step"] = convert_param_format(yaml_params["Step_params"])
    # Returning original step order. Will be stored in pipe_data and used to sort scripts in 00.main script
    param_data["usr_step_order"] = usr_step_order
    
    param_data_testing(param_data)

    return param_data


def param_data_testing(param_data):
    """ Check for various errors that might occur in the param data.
        These can indicate problems in the paramater file
    """
    
    # If errors in global or step params, raise a special exception which is caugth by PLC_main
    if not param_data_testing_global(param_data["Global"]) or not param_data_testing_step_wise(param_data["Step"]):
        raise Exception("Issues in parameters", "parameters")


def param_data_testing_global(param_data):

    issue_warning = ""
    # # If one of parameter values is a list, create warning - multiple definitions of a param
    # for param in param_data.keys():
        # if isinstance(param_data[param],list):
            # issue_warning += "Duplicate values for param %s\n" % param

    # The following 'Executors' do NOT require a queue to be passed:
    no_queue_required = "SLURM Local".split(" ")
    # No default queue is defined:
    if "Qsub_q" not in list(param_data.keys()):
        if param_data["Executor"] in no_queue_required:# and "Qsub_q" not in param_data.keys():
            param_data["Qsub_q"] = ""
        else:
            issue_warning += "You must supply a default queue name with 'Qsub_q'\n"
    else:
        if isinstance(param_data["Qsub_q"],list):
            issue_warning += "Duplicate values for 'Qsub_q'\n"

    if param_data["Executor"] not in SUPPORTED_EXECUTORS:
        issue_warning += "Executor %s not defined.\n" % param_data["Executor"]

    if "Qsub_opts" in list(param_data.keys()):
        # Checking no automatically set qsub parameters are defined by user
        if any([x in param_data["Qsub_opts"] for x in NOT_PASSABLE_EXECUTOR_PARAMS]):
            issue_warning += "Automatically set qsub parameters defined (one of %s)\n" % (", ".join(NOT_PASSABLE_EXECUTOR_PARAMS))

    if issue_warning=="":
        return True
    else:
        sys.stderr.write("Issues in Global parameters:\n%s\n" % issue_warning)
        return False
        
        
def param_data_testing_step_wise(param_data):

    issue_warning = ""
    issue_count = 1
    # List of all step names:

    names = reduce(lambda x, y: x+y, [list(param_data[step].keys()) for step in list(param_data.keys())])

    if len(set([nam for nam in names if names.count(nam) > 1])) > 0:
        
        issue_warning += "%s. Duplicate values for the following step names: %s.\n" % (issue_count,",".join(set([nam for nam in names if names.count(nam) > 1])))
        issue_count += 1
        
    # If one of parameter values is a list, create warning - multiple definitions of a param
    for step in list(param_data.keys()):
        for name in list(param_data[step].keys()):
            for param in list(param_data[step][name].keys()):
                # Checking that no parameter except "base" is a list:
                # if param not in STEP_PARAMS_MULTIPLE_V and isinstance(param_data[step][name][param],list):
                if param in STEP_PARAMS_SINGLE_VALUE and isinstance(param_data[step][name][param],list):
                    issue_warning += "%s. Duplicate values for param %s in step %s (name %s)\n" % (issue_count,param,step,name)
                    issue_count += 1
                if param == "qsub_params":
                    # Check that 'queue' and '-q' are strings and are not both specified
                    if all([x in param_data[step][name][param] for x in ["queue","-q"]]):
                        issue_warning += "%s. Both '-q' and 'queue' defined in step %s (name %s)\n" % (issue_count,step,name)
                    if "queue" in param_data[step][name][param]:
                        if not isinstance(param_data[step][name][param]["queue"],str):
                            issue_warning += "%s. 'queue' must be string in step %s (name %s)\n" % (issue_count,step,name)
                    if "-q" in param_data[step][name][param]:
                        if not isinstance(param_data[step][name][param]["-q"],str):
                            issue_warning += "%s. '-q' must be string in step %s (name %s)\n" % (issue_count,step,name)
                        # Moving '-q' to 'queue'
                        param_data[step][name][param]['queue'] = param_data[step][name][param]['-q']
                        # Delete '-q'
                        del param_data[step][name][param]['-q']

                    if "nodes" in param_data[step][name][param]:
                        param_data[step][name][param]["node"] = param_data[step][name][param]["nodes"]
                        del param_data[step][name][param]["nodes"]
                    if "node" in param_data[step][name][param]:
                        if not isinstance(param_data[step][name][param]["node"],list):
                            print(name)
                            print(param_data[step][name][param]["node"])
                            issue_warning += "%s. 'node' must be a string or a list in step %s (name %s)\n" % (issue_count,step,name)
                    # Checking no automatically set qsub parameters are defined by user
                    if any([x in param_data[step][name][param]["opts"] for x in NOT_PASSABLE_EXECUTOR_PARAMS]):
                        issue_warning += "{issuenum}. Automatically set qsub parameters defined (one of {params}) " \
                                         "in step {step} (name {name})\n".format(issuenum=issue_count,
                                                                                 step=step,name=name,
                                                                                 params=", ".join(NOT_PASSABLE_EXECUTOR_PARAMS))

    # Test that all steps have base steps and that the base steps are defined
    for step in list(param_data.keys()):
        if step=="merge":
            next
        else:
            for name in list(param_data[step].keys()):
                if "base" not in list(param_data[step][name].keys()):
                    issue_warning += "%s. No base defined for step %s\n" % (issue_count,name)
                    issue_count += 1
                else:
                    # For each base in the list of bases, check it exists in step names
                    for base in param_data[step][name]["base"]:
                        if base not in names:
                            issue_warning += "%s. Base %s in step %s is not defined\n" % (issue_count,base,name)
                            issue_count += 1

            
    if issue_warning=="":
        return True
    else:
        sys.stderr.write("Issues in step-wise parameters:\n%s\n" % issue_warning)
        return False
        
        
def test_and_modify_global_params(global_params):
    
    # Setting default Executor to SGE:
    if "Executor" not in global_params:
        global_params["Executor"] = "SGE"
    # Testing executor is one of defined types:
    if global_params["Executor"] not in list(SUPPORTED_EXECUTORS.keys()):
        print("Executor {executor} is not one of " \
              "the defined executors: {executor_list}".format(executor=global_params["Executor"],
                                                              executor_list=", ".join(list(SUPPORTED_EXECUTORS.keys()))))
        raise Exception("Issues in parameters", "parameters")

    # # This should not be done this way, but couldn't think of a better way.
    # # Setting global SUPPORTED_EXECUTORS according to value of Executor
    global NOT_PASSABLE_EXECUTOR_PARAMS
    NOT_PASSABLE_EXECUTOR_PARAMS = SUPPORTED_EXECUTORS[global_params["Executor"]]
    
    # Convert Qsub_opts into a list of options (split by ' -' with look-ahead...)
    if "Qsub_opts" in global_params:
        if isinstance(global_params["Qsub_opts"], str):
            global_params["Qsub_opts"] = dict((re.split("\s+",elem,1)+[""])[0:2]
                                              for elem
                                              in re.split("\s+(?=-)",global_params["Qsub_opts"]))
            # global_params["Qsub_opts"] = re.split(" (?=-)",global_params["Qsub_opts"])
        elif isinstance(global_params["Qsub_opts"], list):
            global_params["Qsub_opts"] = dict((re.split("\s+",elem,1)+[""])[0:2]
                                              for elem
                                              in global_params["Qsub_opts"])
        # If defined as a dict, change all 'None' values to empty strings
        elif isinstance(global_params["Qsub_opts"], dict):
            global_params["Qsub_opts"] = {key:(val if val!=None else "")
                                          for key,val
                                          in global_params["Qsub_opts"].items()}
        else:
            sys.exit("'Qsub_opts' in undefined format.")
           
    # Converting single module_path into single element list
    if "module_path" in global_params:
        if isinstance(global_params["module_path"],str):
            global_params["module_path"] = [global_params["module_path"]]
        elif isinstance(global_params["module_path"], list):
            pass    # OK
        else:
            raise Exception("Unrecognised 'module_path' format. 'module_path' in 'Global_params' "
                            "must be a single path or a list. \n", "parameters")

        bad_paths = [x for x in global_params["module_path"] if not os.path.isdir(x)]
        good_paths = [x for x in global_params["module_path"] if os.path.isdir(x)]
        if bad_paths:
            sys.stderr.write("WARNING: The following module paths do not exist and will be "
                             "removed from search path: {badpaths}\n".format(badpaths=", ".join(bad_paths)))
            global_params["module_path"] = good_paths
        
    # Converting single Qsub_nodes into single element list
    if "Qsub_nodes" in global_params:
        if isinstance(global_params["Qsub_nodes"],str):
            # Convert to list by splitting by comma.
            # Remove extra spaces from around node names, if these exist (e.g. 'node1, node2')
            global_params["Qsub_nodes"] = re.split("[\, ]*",global_params["Qsub_nodes"])
                # [node.strip() for node in global_params["Qsub_nodes"].split(",")]
        elif isinstance(global_params["Qsub_nodes"], list):
            pass      # OK
        else:
            raise Exception("Unrecognised 'Qsub_nodes' format. 'Qsub_nodes' in 'Global_params' "
                            "must be a single path or a list. \n", "parameters")
    # Checking conda params are sensible:
    if "conda" in global_params:
        # print global_params["conda"]
        global_params["conda"] = manage_conda_params(global_params["conda"])
        # print global_params["conda"]

        # sys.exit()
        # if "path" not in global_params["conda"]:   # or "env" not in global_params["conda"]:
        #     raise Exception("When using 'conda', you must supply a 'path' to the environment to use.\n"
        #                     "Leave 'path:' empty if you want it to be taken from $CONDA_PREFIX\n", "parameters")
        # if global_params["conda"]["path"] is None:  # Path is empty, take from $CONDA_PREFIX
        #     if "CONDA_PREFIX" in os.environ:
        #         global_params["conda"]["path"] = os.environ["CONDA_PREFIX"]
        #
        #     else:
        #         raise Exception("'conda' 'path' is empty, but no CONDA_PREFIX is defined. "
        #                         "Make sure you are in an active conda environment.")
        #
        # if "env" not in global_params["conda"]:
        #     if global_params["conda"]["env"] is None:
        #         try:
        #             global_params["conda"]["env"] = os.environ['CONDA_DEFAULT_ENV']
        #         except KeyError:
        #             raise Exception("When using 'conda', you must supply an 'env' containing the "
        #                             "name of the environment to use, or run NeatSeq-Flow from inside an active "
        #                             "CONDA environment.\n", "parameters")
        #
    return global_params

def manage_conda_params(conda_params):
    """

    :param conda_params:
    :return:
    """

    if "path" not in conda_params or "env" not in conda_params:
        raise Exception("You must supply both 'path' and 'env' in conda block. Leave them empty if you want them to "
                        "be guessed from the current environment","parameters")

    if not conda_params["path"] or not conda_params["env"]:
        if "CONDA_PREFIX" not in os.environ:
            raise Exception(
                "If one of conda 'path' and 'env' are empty, you need to have an active environment, with "
                "$CONDA_PREFIX defined", "parameters")

    if not conda_params["path"]:
        if "CONDA_BASE" in os.environ:
            conda_params["path"] = os.environ["CONDA_BASE"]
        else:
            raise Exception("""'conda' 'path' is empty, but no CONDA_BASE is defined. 
Make sure you are in an active conda environment, and that you executed the following command:
> {start_col}export CONDA_BASE=$(conda info --root){end_col}
""".format(start_col='\033[93m',end_col='\033[0m'), "parameters")

    if not conda_params["env"]:
        if "CONDA_DEFAULT_ENV" in os.environ:
            conda_params["env"] = os.environ['CONDA_DEFAULT_ENV']
        else:
            raise Exception("'conda' 'env' is empty, but there is no active environment. Please activate "
                            "the environment and try again. Alternatively, set the CONDA_DEFAULT_ENV environment "
                            "variable to the name of the conda environment to use", "parameters")
    return conda_params