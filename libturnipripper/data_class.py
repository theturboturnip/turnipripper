#a Imports
import os.path
import hashlib
import base64
import json
from libturnipripper import musicbrainz

import typing
from typing import Optional, ClassVar, TypeVar, Type, Union, List, Dict, Set, Any, cast
Json = Union[List[Any], Dict[str,Any], str, int]

#f str_add_to_set
def str_add_to_set(set_str:str, s:str, separator:str="###") -> str:
    if s=="": return set_str
    l = set_str.split(separator)
    if set_str=="": l=[]
    if s in l: return set_str
    l.append(s)
    return separator.join(l)

#c DataClass
class DataClass(object):
    json_prop_types : ClassVar[Dict[str,type]] = {}
    data_class_type : ClassVar[str] = "DataClass"
    #f set
    def set(self, **kwargs:Dict[str,Any]) -> None:
        callbacks:Set[Any] = set()
        for (k,v) in kwargs.items():
            if not hasattr(self, k): raise Exception(f"Cannot set property {k}, it does not exist yet")
            if hasattr(self, "set_{k}"):
                f = getattr(self, "set_{k}")
                f(v)
                pass
            else:
                setattr(self, k, v)
                pass
            if hasattr(self, "postset_"+k):
                callbacks.add(getattr(self, "postset_"+k))
                pass
            pass
        for c in callbacks:
            c()
            pass
        pass
    #f from_json
    def from_json(self, json:Json) -> None:
        assert type(json)==dict
        json_dict = cast(Dict[str,Any], json)
        set_dict = {}
        for (k,v) in json_dict.items():
            if k not in self.json_prop_types: raise Exception(f"Failed to read json as key {k} is not an allowed property of type {self.data_class_type}")
            prop_type = self.json_prop_types[k]
            if prop_type == type(lambda y:y):
                getattr(self,"from_json_"+k)(v)
                pass
            else:
                if type(v) != prop_type: raise Exception(f"Failed to read json as key {k} requires type {prop_type} but got {type(v)}")
                set_dict[k] = v
                pass
            pass
        self.set(**set_dict)
        pass
    #f as_json
    def as_json(self) -> Json:
        result = {}
        for (k,v) in self.json_prop_types.items():
            if hasattr(self, k): result[k] = getattr(self, k)
            pass
        return result
    #f All done
    pass

