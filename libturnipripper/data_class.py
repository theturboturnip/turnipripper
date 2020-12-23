#a Imports
from sqlite3 import Cursor

from .db_types import *
import typing
from typing import Optional, ClassVar, TypeVar, Type, Iterable, Union, Tuple, List, Dict, Set, Any, cast

#f str_add_to_set
def str_add_to_set(set_str:str, s:str, separator:str="###") -> str:
    if s=="": return set_str
    l = set_str.split(separator)
    if set_str=="": l=[]
    if s in l: return set_str
    l.append(s)
    return separator.join(l)

#f str_set_as_list
def str_set_as_list(set_str:str, separator:str="###") -> List[str]:
    return set_str.split(separator)

#c DataClass
class DataClass(object):
    #f Class variable properties
    json_prop_types : ClassVar[Dict[str,Optional[type]]] = {}
    sql_columns     : ClassVar[List[Tuple[str,type]]] = []
    data_class_type : ClassVar[str] = "DataClass"
    sql_table_name  : ClassVar[str] = "sqltable"
    inited_classes  : ClassVar[Set[Type["DataClass"]]] = set()

    # Created at first initialization
    json_prop_types_list : ClassVar[List[Tuple[str,Optional[type]]]]
    #f ensure_inited
    @classmethod
    def ensure_inited(cls) -> None:
        if cls in cls.inited_classes: return
        cls.inited_classes.add(cls)
        cls.json_prop_types_list = [(k,v) for (k,v) in cls.json_prop_types.items()]
        cls.json_prop_types_list.sort(key=lambda kv:kv[0])
        pass
    #f __init__
    def __init__(self) -> None:
        self.ensure_inited()
        pass
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
            if prop_type == None:
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
        for (k,v) in self.json_prop_types_list:
            if hasattr(self, k): data = getattr(self, k)
            if v==None: data=getattr(self,"as_json_"+k)(data)
            result[k] = data
            pass
        return result
    #f sql3_create_table
    @classmethod
    def sql3_create_table(cls, sql3_cursor:Cursor) -> None:
        sql_column_name_types = []
        keys = []
        for (name,value_type) in cls.sql_columns:
            if name[0]=='!':
                keys.append(name[1:])
                name = name[1:]
                pass
            if value_type==str:
                sql_column_name_types.append( (name,f"text") )
                pass
            elif value_type==int:
                sql_column_name_types.append( (name,f"integer") )
                pass
            else:
                raise Exception("Bad column type")
            pass
        sql_columns = ",".join([f"{n} {t}" for (n,t) in sql_column_name_types])
        sql_keys = ",".join(keys)
        sql3_cursor.execute(f"""CREATE TABLE {cls.sql_table_name} ({sql_columns}, PRIMARY KEY({sql_keys}))""")
        pass
    #f sql3_insert_entry
    def sql3_insert_entry(self, sql3_cursor:Cursor) -> None:
        sql_columns = []
        for (name,value_type) in self.sql_columns:
            if name[0]=='!': name = name[1:]
            value = getattr(self, name)
            if value_type==int:
                sql_columns.append( (name,f"{value}") )
                pass
            else:
                sql_columns.append( (name,f'"{str(value)}"') )
                pass
            pass
        sql_column_names  = ",".join(x[0] for x in sql_columns)
        sql_column_values = ",".join(x[1] for x in sql_columns)
        sql3_cursor.execute(f"""REPLACE INTO {self.sql_table_name} ({sql_column_names}) VALUES ({sql_column_values})""")
        pass
    #f sql3_iter_entries
    @classmethod
    def sql3_iter_entries(cls, sql3_cursor:Cursor) -> Iterable[Dict[str,Any]]:
        sql_columns = []
        for (name,value_type) in cls.sql_columns:
            if name[0]=='!': name = name[1:]
            value = 0
            if value_type==int:
                sql_columns.append( (name,f"{value}") )
                pass
            else:
                sql_columns.append( (name,f'"{str(value)}"') )
                pass
            pass
        sql_column_names  = ",".join(x[0] for x in sql_columns)
        sql_column_values = ",".join(x[1] for x in sql_columns)
        print(f"""SELECT {sql_column_names} FROM {cls.sql_table_name}""")
        for row in sql3_cursor.execute(f"""SELECT {sql_column_names} FROM {cls.sql_table_name}"""):
            result_dict = {}
            for i in range(len(row)):
                result_dict[sql_columns[i][0]] = row[i]
                pass
            yield(result_dict)
            pass
        pass
    #f All done
    pass

