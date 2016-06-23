import os
import sys

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
    try:
        mod_name,sep,obj_name = imp.rpartition('.')
    except AttributeError:
        return None
    __import__(mod_name,globals(),locals())
    imp_mod = sys.modules[mod_name]
    imp_obj = imp_mod.__dict__[obj_name]
    return imp_obj


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