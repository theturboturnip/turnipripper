#!/usr/bin/env python3

"""
The config file specifies:

[database]
root=<path to all library files>
dbfile=<file.db for sqlite3 - inside root>
json_paths=<glob path>,<glob path>... - all inside root
primary=[sqlite|json]

[rip]
source_root=<path to where flacs are stored>
default_dir=[cddb|musicbrainz]

[encode]
output_format=mp3
output_root=<path to where encoded files are stored>

"""
import configparser
from pathlib import Path

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast

#a Config
class ConfigSection:
    #v Properties
    elements : ClassVar[Dict[str,Tuple[str,Any]]] = {}
    #f __init__
    def __init__(self) -> None:
        for (k,v) in self.elements.items():
            f = getattr(self,"init_"+v[0])
            setattr(self,k,f(v))
            pass
        pass
    #f from_dict
    def from_dict(self, d:Dict[str,Any]) -> None:
        for (k,v) in d.items():
            if k not in self.elements: raise Exception(f"Bad key {k} in configuration section ")
            f = getattr(self,"set_"+self.elements[k][0])
            f(k,v)
            pass
        pass
    #f as_dict
    def as_dict(self) -> Dict[str,Any]:
        r = {}
        for k in self.elements:
            r[k] = getattr(self,k)
            pass
        return r
    #f init_str
    @staticmethod
    def init_str(t:Tuple[str,str]) -> str: return ""
    #f set_str
    def set_str(self, k:str, s:str) -> None:
        setattr(self, k, s)
        pass
    #f init_path
    @staticmethod
    def init_path(t:Tuple[str,str]) -> Path: return Path()
    #f set_path
    def set_path(self, k:str, s:str) -> None:
        setattr(self, k, Path(s).expanduser())
        pass
    #f init_list_path
    @staticmethod
    def init_list_path(t:Tuple[str,str]) -> List[Path]: return []
    #f set_list_path
    def set_list_path(self, k:str, s:str) -> None:
        v = getattr(self, k)
        for l in s.split(","):
            v.append(Path(l))
            pass
        pass
    #f init_list_glob
    @staticmethod
    def init_list_glob(t:Tuple[str,str]) -> List[Path]: return []
    #f set_list_glob
    def set_list_glob(self, k:str, s:str) -> None:
        v = getattr(self, k)
        for l in s.split(","):
            v.append(l)
            pass
        pass
    #f init_opt_path
    @staticmethod
    def init_opt_path(t:Tuple[str,str]) -> Optional[Path]: return None
    #f set_opt_path
    def set_opt_path(self, k:str, s:str) -> None:
        if s=="":
            setattr(self, k, None)
            pass
        else:
            setattr(self, k, Path(s))
            pass
        pass
    #f init_option
    @staticmethod
    def init_option(t:Tuple[str,str]) -> Optional[str]: return t[1].split(",")[0]
    #f set_option
    def set_option(self, k:str, s:str) -> None:
        options = self.elements[k][1].split(",")
        if s not in options: raise Exception(f"Bad config option value {s} - permitted are {options}")
        setattr(self, k, s)
        pass
    #f All done
    pass

#a Configurations for database, rip, encode - and the whole file
#c DatabaseConfig
class DatabaseConfig(ConfigSection):
    elements = {
        "root":("path",""),
        "dbfile":("opt_path",""),
        "json_root":("path","library.json"),
        "json_paths":("list_glob",""),
        "json_disc":("str",""),
        "primary":("option","json,sqlite"),
    }
    root: Path
    dbfile : Optional[Path]
    json_root: Path
    json_disc: str
    json_paths: List[str]
    primary : str
    def primary_is_json(self):
        return self.primary=="json"
    def discs_in_own_json(self):
        return self.json_disc!=""
    pass
                                          
#c RipConfig
class RipConfig(ConfigSection):
    elements = {
        "source_root":("path",""),
        "default_dir":("str",("option","musicbrainz,cddb")),
    }
    source_root: Path
    default_dir : str
    def joinpath(self, *paths:Any) -> Path:
        return self.source_root.joinpath(*paths)
    #f relative_path
    def relative_path(self, path:Path) -> Path:
        return path.relative_to(self.source_root)
    pass

#c EncodeConfig
class EncodeConfig(ConfigSection):
    elements = {
        "output_format":("str",""),
        "output_root":("path",""),
        "encode_options":("str",""),
    }
    output_root: Path
    output_format: str
    encode_options: str
    def get_encode_options(self) -> List[Tuple[str,str]]:
        if self.encode_options=="": return []
        r = []
        encode_options_list = self.encode_options.split(",")
        if (len(encode_options_list)&1)==1: raise Exception("Encode options must be even length list")
        for i in range(len(encode_options_list)//2):
            k = encode_options_list[i*2]
            v = encode_options_list[i*2+1]
            if k[0]!="-": raise Exception(f"Encode options must be -arg,value list - got {k} as an arg")
            r.append((k,v))
            pass
        return r
    pass
                                          
#c Config
class Config:
    section_types : ClassVar[Dict[str,Type[ConfigSection]]] = {
        "database":DatabaseConfig,
        "rip":RipConfig,
        "encode":EncodeConfig,
        }
    sections : Dict[str,ConfigSection] = {}
    database : DatabaseConfig
    rip      : RipConfig
    encode   : EncodeConfig
    #f __init__
    def __init__(self) -> None:
        for (k,t) in self.section_types.items():
            self.sections[k] = t()
            setattr(self, k, self.sections[k])
            pass
        pass
    #f read_config_files
    def read_config_files(self, config_files:List[Tuple[bool,Path]]) -> None:
        config = configparser.SafeConfigParser()
        for (required, path) in config_files:
            read_paths = config.read([path.expanduser()])
            if required and read_paths==[]:
                raise Exception(f"Failed to read configuration file {path}")
            pass
        for k in config.sections():
            if k not in self.sections: raise Exception(f"Bad section f{k} in configuration")
            self.sections[k].from_dict(dict(config.items(section=k)))
            pass
        pass
    #f __str__
    def __str__(self) -> str:
        r = "["
        for (k,s) in self.sections.items():
            r+=f"{k}:{s.as_dict()}, "
            pass
        r+="]"
        return r
    #f All done
    pass

