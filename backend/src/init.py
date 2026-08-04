import ctypes
import os
from parser import *

path = os.path.abspath(os.path.dirname(__file__))

libtrie = ctypes.CDLL(os.path.join(path, "libtrie.so"))

libtrie.getNumChar.restype = ctypes.c_int
NUM_CHAR = libtrie.getNumChar()

class TrieNode(ctypes.Structure):
    pass

TrieNode._fields_ = [("children", ctypes.POINTER(TrieNode) * NUM_CHAR),
                ("terminal", ctypes.c_bool),
                ("original", ctypes.c_char_p)]

class WordList(ctypes.Structure):
    _fields_ = [("entries", ctypes.POINTER(ctypes.c_char_p)),
                ("count", ctypes.c_int)]

ctypes_map = {
            "int": ctypes.c_int,
            "unsigned int": ctypes.c_uint,
            "long": ctypes.c_long,
            "unsigned long": ctypes.c_ulong,
            "char": ctypes.c_char,
            "char*": ctypes.c_char_p,
            "unsigned char": ctypes.c_ubyte,
            "float": ctypes.c_float,
            "double": ctypes.c_double,
            "bool": ctypes.c_bool,
            "void": None
        }

def init_pointer_type(type, pointer_level: int):
    if pointer_level == 0:  
        return type
    else:
        return ctypes.POINTER(init_pointer_type(type, pointer_level - 1))
    

def init_type(type: str):
    pointer_level = type.count("*")
    base_type = type.replace("*", "").strip()
    if base_type in ctypes_map:
        return ctypes_map[base_type]
    else:
        return init_pointer_type(globals()[base_type], pointer_level)
        
def init_function(name, argtypes: list, restype):
    func = getattr(libtrie, name)
    func.argtypes = argtypes
    func.restype = restype
    return func

def create_trie_root():
    return ctypes.POINTER(TrieNode)()

def init_trie():
    functions = parse_header(os.path.join(path, "../include/trie.h"))

    i = 0
    for func_name, func_param, return_val in functions:
        if func_param is None:
            func_param = []
        functions[i] = (func_name, [init_type(param) for param in func_param], init_type(return_val))
        print(functions[i])
        i += 1

    func_dict = {}
    for func_name, argtypes, restype in functions:
        func_dict[func_name] = init_function(func_name, argtypes, restype)

    return create_trie_root(), func_dict

if __name__ == "__main__":
    init_trie()