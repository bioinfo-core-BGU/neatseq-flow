""" Helper functions for parsing and interpolating variables in parameter file
"""

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"



import re, sys, collections
from pprint import pprint as pp

# A closure:
# Function make_interpol_func returns a function with a local copy of variables_bunch
# The local copy is loc_variables_bunch, and is set as global so that eval will recognise it.
def make_interpol_func(variables_bunch):
    # Define a regular expression for variables (any contiguous alphanumeric or period between {})
    var_re = re.compile("\{(Vars\.[\w\.\-]+?)\}")
    global loc_variables_bunch
    loc_variables_bunch = variables_bunch
    
    # Define function to return:
    def interpol_atom(atom):

        if isinstance(atom, str):

            m = var_re.search(atom)

            # While a match exists:
            while (m):
                # print "in here: %s\n" % atom
                # print "loc_variables_bunch.%s\n" % m.group(1)
                # print "Atom: " + atom
                try:
                    # Replace the matched variable with something from variables_bunch
                    # Also converting to str, in case value is int or float
                    repl_str = str(eval("loc_variables_bunch.%s" % m.group(1)))
                    if repl_str==None:
                        repl_str = ""

                    atom = var_re.sub(repl_str,atom,count=1)
                except AttributeError:
                    # If not found, raise exception
                    raise Exception("Unrecognised variable '%s'" % m.group(1), "Variables")
                except TypeError:
                    raise Exception("A 'TypeError' exception has occured. This may happen when variables are left "
                                    "empty. Make sure all your variables have values. ", "Variables")
                m = var_re.search(atom)

        return atom

    return interpol_atom

def walk(node, variables_bunch, callback):
        
    if isinstance(node,dict):
        # Special case: The dict is actually a variable wrongly interpreted by the YAML parser as a dict!
        if len(node.keys()) == 1 and node.values()==[None] and re.match("Vars\.([\w\.]+?)",node.keys()[0]):
            node = callback("{%s}" % node.keys()[0])
        else:
            for key, item in node.items():
                if isinstance(item, collections.Iterable):
                    node[key] = walk(item, variables_bunch, callback)
                elif isinstance(item, str):
                    # node[key] = interpol_atom(item, variables_bunch)
                    node[key] = callback(item)
                else:
                    # node[key] = item
                    pass
    elif isinstance(node,list):
        # print "in 2\n"
        for i in range(0,len(node)):
            if isinstance(node[i], collections.Iterable):
                node[i] = walk(node[i], variables_bunch, callback)
            elif isinstance(node[i], str):
                # node[i] = interpol_atom(node[i], variables_bunch)
                node[i] = callback(node[i])
            else:
                pass
    else:
        # print "in 3\n"
        if isinstance(node, str):
            # print "Node: \n\n'%s'\n\n" % node

            # node = interpol_atom(node, variables_bunch)
            node = callback(node)
        else:
            pass
#        raise Exception("walk() works on dicts and lists only")
    return node

    
def test_vars(node):

    if isinstance(node,dict):
        for key in node.keys():
            if re.search("[^a-zA-Z0-9_]",key):
                raise Exception("Please use only alphanumeric symbols and underscore in variables (%s)" % key, "Variables")
            if re.search("^[0-9]",key):
                raise Exception("Variables must begin with a alphabetic symbol or underscore (%s)" % key, "Variables")
            if node[key] == None:
                # sys.stderr.write("It seems you have an empty variable! (%s)" % key)
                sys.stderr.write("ATTENTION: It seems you have an empty variable! (%s)\n" % key)
            test_vars(node[key])
    elif isinstance(node,list):
        raise Exception("ERROR: Please don't use lists in variables section!", "Variables")
    elif type(node) in [str,int,float]:
        pass
    elif node==None:
        # raise Exception("It seems you have an empty variable!" % key, "Variables")
        # sys.stderr.write("ATTENTION: It seems you have an empty variable!\n")
        pass
    else:
        raise Exception("ERROR: Unrecognised variable type (%s)" % node, "Variables")
