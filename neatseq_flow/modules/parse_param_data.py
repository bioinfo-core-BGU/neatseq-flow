

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

# A list of words that identify global parameters:
GLOBAL_PARAMS_LIST = ['Default_wait','Main','Qsub_opts','Qsub_q','Qsub_nodes','Qsub_path','slow_release','module_path','job_limit']
# A list of words that identify global parameters that take multiple values (are stored as lists even when only one value exists)
GLOBAL_PARAMS_MULTIPLE_V = ['Qsub_opts','Qsub_nodes','module_path']   
STEP_PARAMS_MULTIPLE_V = ['base','setenv','export']   
STEP_PARAMS_SINGLE_VALUE = ['script_path','module','redirects']

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
    
    print "YAML failed. trying classic"
    return get_param_data(file_conts)

    
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
            endparams[param_dict[yamlname]["module"]][yamlname] = param_dict[yamlname]
        
            # Converting "redirects" to "redir_params" for backwards compatibility...
            if "redirects" in endparams[param_dict[yamlname]["module"]][yamlname].keys():
                endparams[param_dict[yamlname]["module"]][yamlname]["redir_params"] = \
                    endparams[param_dict[yamlname]["module"]][yamlname].pop("redirects")
            else: # Add empty redir_params.
                endparams[param_dict[yamlname]["module"]][yamlname]["redir_params"] = {}

            # Converting base to list if it is not one already
            if "base" in endparams[param_dict[yamlname]["module"]][yamlname].keys() and not isinstance(endparams[param_dict[yamlname]["module"]][yamlname]["base"],list):
                endparams[param_dict[yamlname]["module"]][yamlname]["base"] = [endparams[param_dict[yamlname]["module"]][yamlname]["base"]]

            if "qsub_params" in endparams[param_dict[yamlname]["module"]][yamlname]:
                if "queue" in endparams[param_dict[yamlname]["module"]][yamlname]["qsub_params"]:
                    if not isinstance(endparams[param_dict[yamlname]["module"]][yamlname]["qsub_params"]["queue"], str):
                        raise Exception("queue must be a string, not a list or other.", "parameters")
                if "-q" in endparams[param_dict[yamlname]["module"]][yamlname]["qsub_params"]:
                    if not isinstance(endparams[param_dict[yamlname]["module"]][yamlname]["qsub_params"]["-q"], str):
                        raise Exception("queue must be a string, not a list or other.", "parameters")
                    
                # Converting node to list if it is not one already
                if "node" in endparams[param_dict[yamlname]["module"]][yamlname]["qsub_params"]:
                    if isinstance(endparams[param_dict[yamlname]["module"]][yamlname]["qsub_params"]["node"],str):
                        endparams[param_dict[yamlname]["module"]][yamlname]["qsub_params"]["node"] = [endparams[param_dict[yamlname]["module"]][yamlname]["qsub_params"]["node"]]
                    elif isinstance(endparams[param_dict[yamlname]["module"]][yamlname]["qsub_params"]["node"],list):
                        pass
                    else:
                        raise Exception("In %s: Node can be either string or list\n" % yamlname, "parameters")
            
        return endparams
 
    filelines = remove_comments(filelines)
    
    # Convert all tabs to 4 spaces. Tabs do not work well with YAML!
    filelines = [re.sub("\t","    ",line) for line in filelines]
    
    # Read params with pyyaml package:
    # yaml_params = yaml.load("\n".join(filelines),  Loader=yaml.SafeLoader)
    # yaml_params = yaml.safe_load("\n".join(filelines))
    yaml_params = ordered_load("\n".join(filelines), yaml.SafeLoader)
    step_order = yaml_params["Step_params"].keys()
    
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
        
    
    
    
    # Converting single module_path into single element list
    if "module_path" in param_data["Global"]:
        if isinstance(param_data["Global"]["module_path"],str):
            param_data["Global"]["module_path"] = [param_data["Global"]["module_path"]]
        elif isinstance(param_data["Global"]["module_path"],list):
            pass # OK
        else:
            raise Exception("Unrecognised 'module_path' format. 'module_path' in 'Global_params' must be a single path or a list. \n", "parameters")
        # Check existence of the paths:
        #=======================================================================
        # for module_path_raw in param_data["Global"]["module_path"]:#.split(" "):
        #     module_path = module_path_raw.rstrip(os.sep)
        #     if not os.path.isdir(module_path):
        #         sys.stderr.write("WARNING: Path %s from module_path does not exist. Skipping...\n" % module_path)
        #=======================================================================
        bad_paths = filter(lambda x: not os.path.isdir(x) , param_data["Global"]["module_path"])
        good_paths = filter(lambda x: os.path.isdir(x) , param_data["Global"]["module_path"])
        if bad_paths:
            sys.stderr.write("WARNING: The following module paths do not exist and will be removed from search path: {badpaths}\n".format(badpaths=", ".join(bad_paths)))
            param_data["Global"]["module_path"] = good_paths
        
    # Converting single Qsub_nodes into single element list
    if "Qsub_nodes" in param_data["Global"]:
        if isinstance(param_data["Global"]["Qsub_nodes"],str):
            # Convert to list by splitting by comma.
            # Remove extra spaces from around node names, if these exist (e.g. 'node1 , node2')
            param_data["Global"]["Qsub_nodes"] = [node.strip() for node in param_data["Global"]["Qsub_nodes"].split(",")]
        elif isinstance(param_data["Global"]["Qsub_nodes"],list):
            pass # OK
        else:
            raise Exception("Unrecognised 'Qsub_nodes' format. 'Qsub_nodes' in 'Global_params' must be a single path or a list. \n", "parameters")
    # Checking conda params are sensible:
    if "conda" in param_data["Global"]:
        if "path" not in param_data["Global"]["conda"] or "env" not in param_data["Global"]["conda"]:
            raise Exception("When using 'conda', you must supply a 'path' with the dir in which 'activate' is located and an 'env'.","parameters")
        if param_data["Global"]["conda"]["path"] == None:  # Path is empty, take from $CONDA_PREFIX
            if "CONDA_PREFIX" in os.environ:
                # CONDA_PREFIX is: conda_path/'envs'/env_name
                # First split gets the env name
                # Second split gets the conda_path and adds 'bin'
                (t1,env) = os.path.split(os.environ["CONDA_PREFIX"])
                param_data["Global"]["conda"]["path"] = os.path.join(os.path.split(t1)[0],"bin")
                if  param_data["Global"]["conda"]["env"]==None:
                    param_data["Global"]["conda"]["env"] = env

            else:
                raise Exception("'conda' 'path' is empty, but no CONDA_PREFIX is defined. Make sure you are in an active conda environment.")
        
        
    # Extract step-wise parameter dict from lines:
    param_data["Step"] = convert_param_format(yaml_params["Step_params"])
    # Returning original step order. Will be stored in pipe_data and used to sort scripts in 00.main script
    param_data["step_order"] = step_order
    
    param_data_testing(param_data)
      

    return param_data


    

def get_param_data(filelines):
    """
    Get sample data from filelines
    """
    # Prepare param_data to store parameters:
    param_data = dict()

    # Extract global parameter dict from lines:
    param_data["Global"] = parse_global_param_data_lines(filelines)
    
    # Extract step-wise parameter dict from lines:
    param_data["Step"] = parse_step_param_data_lines(filelines)
    

    
    param_data_testing(param_data)

    # pp(param_data)
    # sys.exit()
    return param_data

def get_global_param_data_lines(filelines):
    """ Get global params from parameter lines
        Is recognized by the words "Sample","Forward","Reverse","Single" as line prefixes
    """
    filelines = remove_comments(filelines)
    # Retain lines that match GLOBAL parameter format
    # possible_g_params_list = ['Default_wait','Main','Qsub_opts','Qsub_q','Qsub_nodes','slow_release']   # Included 'Title'. This is a sample data line... Removed...
    # return [line for line in filelines if re.split("\s", line, maxsplit=1)[0] in possible_g_params_list]
    return [line for line in filelines if re.split("\s", line, maxsplit=1)[0] in GLOBAL_PARAMS_LIST]
    
    
    
def parse_global_param_data_lines(g_filelines):
    """
    Given lines for one sample, return a dictionary holding the data for that sample:
    """

    # Extract global parameter lines from filelines:
    g_filelines = get_global_param_data_lines(g_filelines)
    # Create dict with lists of values for each possible parameter
    # Also splitting values by comma, to enable multiple values per line
    # OLd:
    # g_params = {params:[parm_val.split(",") for (spec_param,parm_val) in \
                    # [re.split("\s+", line, maxsplit=1) for line in g_filelines] \
            # if spec_param==params] for params in GLOBAL_PARAMS_LIST}   
    # New:
    g_params = {params:["" if len(spec_param_val)==1 else spec_param_val[1] for spec_param_val in \
                    [re.split("\s+", line, maxsplit=1) for line in g_filelines] \
            if spec_param_val[0] == params] for params in GLOBAL_PARAMS_LIST}   

    # Convert comma separated character strings into lists
    for param in g_params.keys():
        # First convert lists into space delimited character strings
        if isinstance(g_params[param],list):
            g_params[param] = " ".join(g_params[param])
        # Then split final string by space-padded comma or space
        try:
            # g_params[param] = g_params[param].split(",")
            g_params[param] = re.split("\s*[\,\s]\s*", g_params[param])
        except ValueError:
            g_params[param] = ""
        except AttributeError:
            pass

    # Flatten lists of lists and remove empty lists.
    # g_params = {param:val for param,val in g_params.iteritems() if val!=[]}
    # pp(g_params)
    g_params = {param:(reduce(lambda x,y: " ".join([x,y]), val) if param in GLOBAL_PARAMS_MULTIPLE_V else val[0]) for param,val in g_params.iteritems() if val != ['']}

            
    # Convert single value lists into strings
    # g_params = {param:(val[0] if (len(val) == 1 and param not in GLOBAL_PARAMS_MULTIPLE_V) else val) 
    g_params = {param:(val[0] if (len(val) == 1) else val) 
                    for param,val in g_params.iteritems()}


    # Check that Default_wait is integer. if passed:
    if "Default_wait" in g_params.keys():
        if isinstance(g_params["Default_wait"], (list)): # More than one values was passed
            sys.exit("It seems like you passed two values for 'Default_wait'\n")
        try:
            g_params["Default_wait"] = int(g_params["Default_wait"])
        except ValueError:
            sys.exit("Default_wait value must be an integer")
    else:
        g_params["Default_wait"] = 10

    # pp(g_params)
    # sys.exit("Stoppping in parse_param_data")
            
    return g_params
    
    
def get_step_param_data_lines(filelines):
    """ Get sample data from "Classic" sample data file, i.e. pipeline format
        Is recognized by the words "Sample","Forward","Reverse","Single" as line prefixes
    """
    
    
    filelines = remove_comments(filelines)
    # Retain lines that have a ":" in the first part o the line (before the first whitespace)
    return [line for line in filelines if re.split("\s", line, maxsplit=1)[0].partition(":")[1] == ":"]

def parse_step_param_data_lines(sw_filelines):
    """
    Given lines for one sample, return a dictionary holding the data for that sample:
    """
    # Extract step-wise parameter lines from filelines:
    sw_filelines = get_step_param_data_lines(sw_filelines)

    # Change approach:
    # Comprehend sw_params_lines in 3 levels: step, name and vaues

    sw_lines_steps = [re.split("\:", line, maxsplit=1) for line in sw_filelines]
    # A set of all step types (i.e. first part of line till first ":")
    all_steps = {step_n[0] for step_n in sw_lines_steps}
    
    # For each step type, run parse_step_parameters() on the lines belonging to that step type
    #    and create {"step_type":"param_dict"} pairs
    return {step_n:parse_step_parameters(step_n,[lines for step_n2,lines in sw_lines_steps if step_n2==step_n]) for step_n in all_steps}
    
    

def parse_step_parameters(step_name,step_lines):
    """ Get a list of all step lines. May include more than one name. 
        Returns a dict with names as keys and parameter dicts as values.
    """
    # Split all lines into keys (left of the first space) and values (right of the 1st space):
    sw_step_lines = [re.split("\s+", line, maxsplit=1) for line in step_lines]

    # Find positions of lines containing name definitions:
    names_inds = [ind for (ind,param_l) in list(enumerate(sw_step_lines)) if param_l[0] == "name"]
    # Make sure instance names are unique: (i.e. length of name list is same as length of name set)

    if (len([sw_step_lines[ind][1] for ind in names_inds]) != len({sw_step_lines[ind][1] for ind in names_inds})):
        # get step names
        names = [sw_step_lines[ind][1] for ind in names_inds]
        # get names with more than on definition
        name_nums = [name for name in set(names) if len(filter(lambda x: x == name, names)) > 1]
        sys.exit("There seem to be two instances of %s with the same name: %s\n" % (step_name, ", ".join(name_nums)))
    # Create dict with name as key and parameter dict as value: 
    return {sw_step_lines[i][1]:parse_name_parameters(sw_step_lines[(i+1):j]) for (i,j) in zip(names_inds,[ind for ind in names_inds[1:]+[len(sw_step_lines)]])}

    
def parse_name_parameters(sw_name_lines):
    """ Get parameter lines for a single step name and return a dict with the parameters.
        Special attention is given to redir parameters and to qsub parameters
    """
    
    # Get only redir_params (begin with "_")
    try:
        redir_params = {param_n:[(param_pair[1] if len(param_pair)==2 else None) for param_pair in sw_name_lines if param_pair[0]==param_n] \
                            for param_n in {param_nv[0] for param_nv in sw_name_lines}\
                        if param_n[0]=="_"}
    except IndexError:
        raise Exception("Check that all lines have a step name and a param name!\n", "parameters")
        
        
    # Remove singleton lists and empty lists (shouldnt exist)
    redir_params = {param[1:]:(val[0] if len(val) == 1 else val) for param,val in redir_params.iteritems() if val != []}
    
    
    # Get step-wise qsub_opts parameters
    qsub_params = {param_n:[(param_pair[1] if len(param_pair)==2 else None) for param_pair in sw_name_lines if param_pair[0]==param_n]\
                        for param_n in {param_nv[0] for param_nv in sw_name_lines}\
                    if re.match("^qsub_opts_",param_n)}
    # Remove singleton lists and empty lists (shouldnt exist)
    qsub_params = {re.sub("^qsub_opts_","",param):(val[0] if len(val) == 1 else val) for param,val in qsub_params.iteritems() if val != []}

    other_params = {param_n:[(param_pair[1] if len(param_pair)==2 else None) for param_pair in sw_name_lines if param_pair[0]==param_n] for param_n in {param_nv[0] for param_nv in sw_name_lines} if (param_n[0]!="_" and not re.match("^qsub_opts_",param_n))}
    other_params = {param:(val[0] if len(val) == 1 else val) for param,val in other_params.iteritems() if val != []}
    other_params["redir_params"] = redir_params
    other_params["qsub_params"] = qsub_params

    # Convert "base" parameter into a list by splitting by comma. 
    # At the same time, make sure a "base" exists.
    if "base" in other_params.keys():
        other_params["base"] = other_params["base"].split(",")


    # pp(other_params)
    return other_params
    
    
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
            
    # No default queue is defined:
    if "Qsub_q" not in param_data.keys():
        issue_warning += "You must supply a default queue name with 'Qsub_q'\n"

    if "Qsub_q" in param_data.keys() and isinstance(param_data["Qsub_q"],list):
        issue_warning += "Duplicate values for 'Qsub_q'\n"

        
    if issue_warning=="":
        return True
    else:
        sys.stderr.write("Issues in Global parameters:\n%s\n" % issue_warning)
        return False
        
        
def param_data_testing_step_wise(param_data):

    issue_warning = ""
    issue_count = 0
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
        
        
        