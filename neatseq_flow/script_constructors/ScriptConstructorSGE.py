import os, shutil, sys, re
import traceback
import datetime


from copy import *
from pprint import pprint as pp

__author__ = "Menachem Sklarz"
__version__ = "1.2.0"


class ScriptConstructorSGE(ScriptConstructor):

    def __init__(self, name, path):
        """ Create a script constructor with name(i.e. 'qsub_name') and script path
        """
        
        pass
        
    
    
#### Methods for adding lines:
    def add_header(self):
        """
        """
        pass
        
    def add_trap_line(self):
        """
        """
        pass
        
        
    def add_log_line(self):
        """
        """
        pass
        
        
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
        
        
    
class HighScriptConstructor(ScriptConstructor):
    """
    """
    
    pass
    
class LowScriptConstructor(ScriptConstructor):
    """
    """
    
    pass
    
    
