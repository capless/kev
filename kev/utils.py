import os
import sys
import importlib


def import_mod(imp):
    '''
    Lazily imports a module from a string
    @param imp:
    '''
    __import__(imp,globals(),locals())
    return sys.modules[imp]
    
def import_util(imp):
    '''
    Lazily imports a utils (class,
    function,or variable) from a module) from
    a string.
    @param imp:
    '''

    mod_name,obj_name = imp.rsplit('.',1)
    mod = importlib.import_module(mod_name)
    return getattr(mod,obj_name)

def env(key, default=None):
    """Retrieves env vars and makes Python boolean replacements"""
    val = os.getenv(key, default)
 
    if val == 'True':
        val = True
    elif val == 'False':
        val = False
    return val

def get_doc_type(klass):
    if hasattr(klass.Meta,'doc_type'):
        if klass.Meta.doc_type is not None:
            return klass.Meta.doc_type
    return klass.__name__