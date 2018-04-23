

""" Functions for reading and parsing pipeline parameter files
"""

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"


import os, sys, re, yaml
from pprint import pprint as pp
import collections

######################## From here: https://gist.github.com/pypt/94d747fe5180851196eb
from yaml.constructor import ConstructorError

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def no_duplicates_constructor(loader, node, deep=False):
    """Check for duplicate keys."""

    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        value = loader.construct_object(value_node, deep=deep)
        if key in mapping:
            raise ConstructorError("while constructing a mapping", node.start_mark,
                                   "found duplicate key (%s)" % key, key_node.start_mark)
        mapping[key] = value

    return loader.construct_mapping(node, deep)

yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, no_duplicates_constructor)
########################



# from parse_sample_data import remove_comments
from neatseq_flow.modules.parse_sample_data import remove_comments, check_newlines

# # A list of words that identify global parameters:
# GLOBAL_PARAMS_LIST = ['Default_wait','Main','Qsub_opts','Qsub_q','Qsub_nodes','Qsub_path','slow_release','module_path','job_limit']
# # A list of words that identify global parameters that take multiple values (are stored as lists even when only one value exists)
# GLOBAL_PARAMS_MULTIPLE_V = ['Qsub_opts','Qsub_nodes','module_path']   
# STEP_PARAMS_MULTIPLE_V = ['script_path','base','setenv','export']   


STEP_PARAMS_SINGLE_VALUE = ['module','redirects']
SUPPORTED_EXECUTORS = ["Local","SGE","SLURM","QSUB"]
NOT_PASSABLE_EXECUTOR_PARAMS = \
    {"SGE" : "-N -e -o -q -hold_jid".split(" "), \
    "QSUB" : "-N -e -o -q -hold_jid".split(" "), \
    "SLURM" : "-e -o -hold_jid --error --output -J --job-name -p --partition -w".split(" "), \
    "Local" : ""}


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
        
    except ConstructorError, exc:
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            print "Error position: (%s:%s)" % (mark.line+1, mark.column+1)
            print mark.get_snippet()
        raise Exception("Possible duplicate value passed", "parameters")
    except yaml.YAMLError, exc:
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            print "Error position: (%s:%s)" % (mark.line+1, mark.column+1)
            print mark.get_snippet()
        
        # Comment out the following line to enable classic param file format.
        # Not recommended.
        raise Exception("Failed to read YAML file. Make sure your parameter file is a correctly formatted YAML document.", "parameters")
    except:
        raise #Exception("Unrecognised exception reading the parameter file.", "parameters")
    
    # print "YAML failed. trying classic"
    # return get_param_data(file_conts)

    
from collections import OrderedDict
    
def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)

# # usage example:
# ordered_load(stream, yaml.SafeLoader)



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
            if "redirects" in yamlname_params.keys():
                yamlname_params["redir_params"] = \
                    yamlname_params.pop("redirects")
            else: # Add empty redir_params.
                yamlname_params["redir_params"] = {}
            # When redirects keys are numbers, such as '-1' in bowtie2 mapper, the keys are stored as numbers. This is bad for testing. Converting all numeric keys to character keys:
            yamlname_params["redir_params"] = \
                {str(key):value \
                for (key,value) \
                in yamlname_params["redir_params"].items()}

            # Converting base to list if it is not one already
            if "base" in yamlname_params.keys() and not isinstance(yamlname_params["base"],list):
                yamlname_params["base"] = [yamlname_params["base"]]

            if "qsub_params" in yamlname_params:
                # # 1. Dealing with 'queue' and '-q':
                ## Has been moved to function param_data_testing_step_wise()

                # 2. Dealing with 'node'
                # Converting node to list if it is not one already
                if "node" in yamlname_params["qsub_params"]:
                    if isinstance(yamlname_params["qsub_params"]["node"],str):
                        yamlname_params["qsub_params"]["node"] = [yamlname_params["qsub_params"]["node"]]

                # 3. Moving all params which are not 'node', '-q' or 'queue', to 'opts'
                params2mv = list(set(yamlname_params["qsub_params"]) - set(["node","queue","-q"]))
                yamlname_params["qsub_params"]["opts"] = {key:(val if val!=None else '') for key,val in yamlname_params["qsub_params"].iteritems() if key in params2mv}
                for param in params2mv:
                    del yamlname_params["qsub_params"][param]
            endparams[param_dict[yamlname]["module"]][yamlname] = yamlname_params    
        return endparams
 
    filelines = remove_comments(filelines)
    
    # Convert all tabs to 4 spaces. Tabs do not work well with YAML!
    filelines = [re.sub("\t","    ",line) for line in filelines]
    
    # Read params with pyyaml package:
    # yaml_params = yaml.load("\n".join(filelines),  Loader=yaml.SafeLoader)
    # yaml_params = yaml.safe_load("\n".join(filelines))
    yaml_params = ordered_load("\n".join(filelines), yaml.SafeLoader)
    usr_step_order = yaml_params["Step_params"].keys()
    
    # If there is a Variables section, interpolate any appearance of the variables in the params
    if "Vars" in yaml_params.keys():
        
        # Prepare the bunch for variable interpolation:
        from bunch import Bunch 
        from var_interpol_defs import make_interpol_func, walk, test_vars
        
        test_vars(yaml_params["Vars"])

        variables_bunch = Bunch.fromDict({"Vars":yaml_params["Vars"]})
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


    

# def get_param_data(filelines):
    # """
    # Get sample data from filelines
    # """
    # # Prepare param_data to store parameters:
    # param_data = dict()

    # # Extract global parameter dict from lines:
    # param_data["Global"] = parse_global_param_data_lines(filelines)
    
    # # Extract step-wise parameter dict from lines:
    # param_data["Step"] = parse_step_param_data_lines(filelines)
    

    
    # param_data_testing(param_data)

    # # pp(param_data)
    # # sys.exit()
    # return param_data

# def get_global_param_data_lines(filelines):
    # """ Get global params from parameter lines
        # Is recognized by the words "Sample","Forward","Reverse","Single" as line prefixes
    # """
    # filelines = remove_comments(filelines)
    # # Retain lines that match GLOBAL parameter format
    # # possible_g_params_list = ['Default_wait','Main','Qsub_opts','Qsub_q','Qsub_nodes','slow_release']   # Included 'Title'. This is a sample data line... Removed...
    # # return [line for line in filelines if re.split("\s", line, maxsplit=1)[0] in possible_g_params_list]
    # return [line for line in filelines if re.split("\s", line, maxsplit=1)[0] in GLOBAL_PARAMS_LIST]
    
    
    
# def parse_global_param_data_lines(g_filelines):
    # """
    # Given lines for one sample, return a dictionary holding the data for that sample:
    # """

    # # Extract global parameter lines from filelines:
    # g_filelines = get_global_param_data_lines(g_filelines)
    # # Create dict with lists of values for each possible parameter
    # # Also splitting values by comma, to enable multiple values per line
    # # OLd:
    # # g_params = {params:[parm_val.split(",") for (spec_param,parm_val) in \
                    # # [re.split("\s+", line, maxsplit=1) for line in g_filelines] \
            # # if spec_param==params] for params in GLOBAL_PARAMS_LIST}   
    # # New:
    # g_params = {params:["" if len(spec_param_val)==1 else spec_param_val[1] for spec_param_val in \
                    # [re.split("\s+", line, maxsplit=1) for line in g_filelines] \
            # if spec_param_val[0] == params] for params in GLOBAL_PARAMS_LIST}   

    # # Convert comma separated character strings into lists
    # for param in g_params.keys():
        # # First convert lists into space delimited character strings
        # if isinstance(g_params[param],list):
            # g_params[param] = " ".join(g_params[param])
        # # Then split final string by space-padded comma or space
        # try:
            # # g_params[param] = g_params[param].split(",")
            # g_params[param] = re.split("\s*[\,\s]\s*", g_params[param])
        # except ValueError:
            # g_params[param] = ""
        # except AttributeError:
            # pass

    # # Flatten lists of lists and remove empty lists.
    # # g_params = {param:val for param,val in g_params.iteritems() if val!=[]}
    # # pp(g_params)
    # g_params = {param:(reduce(lambda x,y: " ".join([x,y]), val) if param in GLOBAL_PARAMS_MULTIPLE_V else val[0]) for param,val in g_params.iteritems() if val != ['']}

            
    # # Convert single value lists into strings
    # # g_params = {param:(val[0] if (len(val) == 1 and param not in GLOBAL_PARAMS_MULTIPLE_V) else val) 
    # g_params = {param:(val[0] if (len(val) == 1) else val) 
                    # for param,val in g_params.iteritems()}


    # # Check that Default_wait is integer. if passed:
    # if "Default_wait" in g_params.keys():
        # if isinstance(g_params["Default_wait"], (list)): # More than one values was passed
            # sys.exit("It seems like you passed two values for 'Default_wait'\n")
        # try:
            # g_params["Default_wait"] = int(g_params["Default_wait"])
        # except ValueError:
            # sys.exit("Default_wait value must be an integer")
    # else:
        # g_params["Default_wait"] = 10

    # # pp(g_params)
    # # sys.exit("Stoppping in parse_param_data")
            
    # return g_params
    
    
# def get_step_param_data_lines(filelines):
    # """ Get sample data from "Classic" sample data file, i.e. pipeline format
        # Is recognized by the words "Sample","Forward","Reverse","Single" as line prefixes
    # """
    
    
    # filelines = remove_comments(filelines)
    # # Retain lines that have a ":" in the first part o the line (before the first whitespace)
    # return [line for line in filelines if re.split("\s", line, maxsplit=1)[0].partition(":")[1] == ":"]

# def parse_step_param_data_lines(sw_filelines):
    # """
    # Given lines for one sample, return a dictionary holding the data for that sample:
    # """
    # # Extract step-wise parameter lines from filelines:
    # sw_filelines = get_step_param_data_lines(sw_filelines)

    # # Change approach:
    # # Comprehend sw_params_lines in 3 levels: step, name and vaues

    # sw_lines_steps = [re.split("\:", line, maxsplit=1) for line in sw_filelines]
    # # A set of all step types (i.e. first part of line till first ":")
    # all_steps = {step_n[0] for step_n in sw_lines_steps}
    
    # # For each step type, run parse_step_parameters() on the lines belonging to that step type
    # #    and create {"step_type":"param_dict"} pairs
    # return {step_n:parse_step_parameters(step_n,[lines for step_n2,lines in sw_lines_steps if step_n2==step_n]) for step_n in all_steps}
    
    

# def parse_step_parameters(step_name,step_lines):
    # """ Get a list of all step lines. May include more than one name. 
        # Returns a dict with names as keys and parameter dicts as values.
    # """
    # # Split all lines into keys (left of the first space) and values (right of the 1st space):
    # sw_step_lines = [re.split("\s+", line, maxsplit=1) for line in step_lines]

    # # Find positions of lines containing name definitions:
    # names_inds = [ind for (ind,param_l) in list(enumerate(sw_step_lines)) if param_l[0] == "name"]
    # # Make sure instance names are unique: (i.e. length of name list is same as length of name set)

    # if (len([sw_step_lines[ind][1] for ind in names_inds]) != len({sw_step_lines[ind][1] for ind in names_inds})):
        # # get step names
        # names = [sw_step_lines[ind][1] for ind in names_inds]
        # # get names with more than on definition
        # name_nums = [name for name in set(names) if len(filter(lambda x: x == name, names)) > 1]
        # sys.exit("There seem to be two instances of %s with the same name: %s\n" % (step_name, ", ".join(name_nums)))
    # # Create dict with name as key and parameter dict as value: 
    # return {sw_step_lines[i][1]:parse_name_parameters(sw_step_lines[(i+1):j]) for (i,j) in zip(names_inds,[ind for ind in names_inds[1:]+[len(sw_step_lines)]])}

    
# def parse_name_parameters(sw_name_lines):
    # """ Get parameter lines for a single step name and return a dict with the parameters.
        # Special attention is given to redir parameters and to qsub parameters
    # """
    
    # # Get only redir_params (begin with "_")
    # try:
        # redir_params = {param_n:[(param_pair[1] if len(param_pair)==2 else None) for param_pair in sw_name_lines if param_pair[0]==param_n] \
                            # for param_n in {param_nv[0] for param_nv in sw_name_lines}\
                        # if param_n[0]=="_"}
    # except IndexError:
        # raise Exception("Check that all lines have a step name and a param name!\n", "parameters")
        
        
    # # Remove singleton lists and empty lists (shouldnt exist)
    # redir_params = {param[1:]:(val[0] if len(val) == 1 else val) for param,val in redir_params.iteritems() if val != []}
    
    
    # # Get step-wise qsub_opts parameters
    # qsub_params = {param_n:[(param_pair[1] if len(param_pair)==2 else None) for param_pair in sw_name_lines if param_pair[0]==param_n]\
                        # for param_n in {param_nv[0] for param_nv in sw_name_lines}\
                    # if re.match("^qsub_opts_",param_n)}
    # # Remove singleton lists and empty lists (shouldnt exist)
    # qsub_params = {re.sub("^qsub_opts_","",param):(val[0] if len(val) == 1 else val) for param,val in qsub_params.iteritems() if val != []}

    # other_params = {param_n:[(param_pair[1] if len(param_pair)==2 else None) for param_pair in sw_name_lines if param_pair[0]==param_n] for param_n in {param_nv[0] for param_nv in sw_name_lines} if (param_n[0]!="_" and not re.match("^qsub_opts_",param_n))}
    # other_params = {param:(val[0] if len(val) == 1 else val) for param,val in other_params.iteritems() if val != []}
    # other_params["redir_params"] = redir_params
    # other_params["qsub_params"] = qsub_params

    # # Convert "base" parameter into a list by splitting by comma. 
    # # At the same time, make sure a "base" exists.
    # if "base" in other_params.keys():
        # other_params["base"] = other_params["base"].split(",")


    # # pp(other_params)
    # return other_params
    
    
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
    no_queue_required = "SLURM".split(" ")
    # No default queue is defined:
    if "Qsub_q" not in param_data.keys():
        if param_data["Executor"] in no_queue_required:# and "Qsub_q" not in param_data.keys():
            param_data["Qsub_q"] = ""
        else:
            issue_warning += "You must supply a default queue name with 'Qsub_q'\n"
    else:
        if isinstance(param_data["Qsub_q"],list):
            issue_warning += "Duplicate values for 'Qsub_q'\n"

    if param_data["Executor"] not in SUPPORTED_EXECUTORS:
        issue_warning += "Executor %s not defined.\n" % param_data["Executor"]
    if "Qsub_opts" in param_data.keys():
        # Checking no automatically set qsub parameters are defined by user
        if any(map(lambda x: x in param_data["Qsub_opts"],NOT_PASSABLE_EXECUTOR_PARAMS_EXECUTOR)):
            issue_warning += "Automatically set qsub parameters defined (one of %s)\n" % (", ".join(NOT_PASSABLE_EXECUTOR_PARAMS_EXECUTOR))

    if issue_warning=="":
        return True
    else:
        sys.stderr.write("Issues in Global parameters:\n%s\n" % issue_warning)
        return False
        
        
def param_data_testing_step_wise(param_data):

    issue_warning = ""
    issue_count = 1
    # List of all step names:
    names = reduce(lambda x, y: x+y, [param_data[step].keys() for step in param_data.keys()])

    if len(set([nam for nam in names if names.count(nam) > 1])) > 0:
        
        issue_warning += "%s. Duplicate values for the following step names: %s.\n" % (issue_count,",".join(set([nam for nam in names if names.count(nam) > 1])))
        issue_count += 1
    
    
    # If one of parameter values is a list, create warning - multiple definitions of a param
    for step in param_data.keys():
        for name in param_data[step].keys():
            for param in param_data[step][name].keys():
                # Checking that no parameter except "base" is a list:
                # if param not in STEP_PARAMS_MULTIPLE_V and isinstance(param_data[step][name][param],list):
                if param in STEP_PARAMS_SINGLE_VALUE and isinstance(param_data[step][name][param],list):
                    issue_warning += "%s. Duplicate values for param %s in step %s (name %s)\n" % (issue_count,param,step,name)
                    issue_count += 1
                if param == "qsub_params":
                    # Check that 'queue' and '-q' are strings and are not both specified
                    if all(map(lambda x: x in param_data[step][name][param],["queue","-q"])):
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
                        
                    if "node" in param_data[step][name][param]:
                        if not isinstance(param_data[step][name][param]["node"],list):
                            issue_warning += "%s. 'node' must be a string or a list in step %s (name %s)\n" % (issue_count,step,name)
                    # Checking no automatically set qsub parameters are defined by user
                    if any(map(lambda x: x in param_data[step][name][param]["opts"],NOT_PASSABLE_EXECUTOR_PARAMS_EXECUTOR)):
                        issue_warning += "%s. Automatically set qsub parameters defined (one of %s) in step %s (name %s)\n" % (issue_count,", ".join(NOT_PASSABLE_EXECUTOR_PARAMS_EXECUTOR),step,name)


            
            
    # Test that all steps have base steps and that the base steps are defined
    for step in param_data.keys():
        if step=="merge":
            next
        else:
            for name in param_data[step].keys():
                if "base" not in param_data[step][name].keys():
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
        
    # This should not be done this way, but couldn't think of a better way.
    # Setting global NOT_PASSABLE_EXECUTOR_PARAMS according to value of Executor
    global NOT_PASSABLE_EXECUTOR_PARAMS_EXECUTOR
    NOT_PASSABLE_EXECUTOR_PARAMS_EXECUTOR = NOT_PASSABLE_EXECUTOR_PARAMS[global_params["Executor"]]
    
    # Convert Qsub_opts into a list of options (split by ' -' with look-ahead...)
    if "Qsub_opts" in global_params:
        if isinstance(global_params["Qsub_opts"], str):
            global_params["Qsub_opts"] = dict((re.split("\s+",elem,1)+[""])[0:2] for elem in re.split("\s+(?=-)",global_params["Qsub_opts"]))
            # global_params["Qsub_opts"] = re.split(" (?=-)",global_params["Qsub_opts"])
        elif isinstance(global_params["Qsub_opts"], list):
            global_params["Qsub_opts"] = dict((re.split("\s+",elem,1)+[""])[0:2] for elem in global_params["Qsub_opts"])
        # If defined as a dict, change all 'None' values to empty strings
        elif isinstance(global_params["Qsub_opts"], dict):
            global_params["Qsub_opts"] = {key:(val if val!=None else "") for key,val in global_params["Qsub_opts"].iteritems()}
        else:
            sys.exit("'Qsub_opts' in undefined format.")
       
    
    # Converting single module_path into single element list
    if "module_path" in global_params:
        if isinstance(global_params["module_path"],str):
            global_params["module_path"] = [global_params["module_path"]]
        elif isinstance(global_params["module_path"],list):
            pass # OK
        else:
            raise Exception("Unrecognised 'module_path' format. 'module_path' in 'Global_params' must be a single path or a list. \n", "parameters")

        bad_paths = filter(lambda x: not os.path.isdir(x) , global_params["module_path"])
        good_paths = filter(lambda x: os.path.isdir(x) , global_params["module_path"])
        if bad_paths:
            sys.stderr.write("WARNING: The following module paths do not exist and will be removed from search path: {badpaths}\n".format(badpaths=", ".join(bad_paths)))
            global_params["module_path"] = good_paths
        
    # Converting single Qsub_nodes into single element list
    if "Qsub_nodes" in global_params:
        if isinstance(global_params["Qsub_nodes"],str):
            # Convert to list by splitting by comma.
            # Remove extra spaces from around node names, if these exist (e.g. 'node1 , node2')
            global_params["Qsub_nodes"] = [node.strip() for node in global_params["Qsub_nodes"].split(",")]
        elif isinstance(global_params["Qsub_nodes"],list):
            pass # OK
        else:
            raise Exception("Unrecognised 'Qsub_nodes' format. 'Qsub_nodes' in 'Global_params' must be a single path or a list. \n", "parameters")
    # Checking conda params are sensible:
    if "conda" in global_params:
        if "path" not in global_params["conda"]:# or "env" not in global_params["conda"]:
            raise Exception("When using 'conda', you must supply a 'path' to the environment to use.\nLeave 'path:' empty if you want it to be taken from $CONDA_PREFIX\n","parameters")
        if global_params["conda"]["path"] == None:  # Path is empty, take from $CONDA_PREFIX
            if "CONDA_PREFIX" in os.environ:
                global_params["conda"]["path"] = os.environ["CONDA_PREFIX"]
                # Parsing the path is done in the _init_ of PLC_step
                # CONDA_PREFIX is: conda_path/'envs'/env_name
                # First split gets the env name
                # Second split gets the conda_path and adds 'bin'
                # (t1,env) = os.path.split(os.environ["CONDA_PREFIX"])
                # global_params["conda"]["path"] = os.path.join(os.path.split(t1)[0],"bin")
                # if  global_params["conda"]["env"]==None:
                #     global_params["conda"]["env"] = env

            else:
                raise Exception("'conda' 'path' is empty, but no CONDA_PREFIX is defined. Make sure you are in an active conda environment.")
                
        if "env" not in global_params["conda"] or global_params["conda"]["env"] == None:
            raise Exception("When using 'conda', you must supply an 'env' containing the name of the environment to use.\n","parameters")
        
    return global_params
        