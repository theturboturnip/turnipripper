#!/usr/bin/env python3

"""
Toplevel command for turnipripperdb

"""

#a Imports
from .command      import Command, CommandArgs
from .cmd_config   import ConfigCommand
from .cmd_database import DatabaseCommand
from .cmd_rip      import RipCommand
from .cmd_album    import AlbumCommand
from .cmd_disc     import DiscCommand

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast

#a Toplevel command and args
class ToplevelArgs(CommandArgs):
    config_file:str
    pass
class ToplevelCommand(Command):
    name = "turnipripperdb"
    parser_args = {
        ("-v", "--verbose"):{
            "dest":"verbose",
            "default":0,
            "type":int,
            "help":"Enable verbosity",
        },
        ("--debug",):{
            "dest":"debug",
            "default":0,
            "type":int,
            "help":"Specify debug level",
        },
        ("-c", "--config_file"):{
            "dest":"config_file",
            "help":"Specify config file",
            "metavar":"FILE",
        },
    }
    args_class = ToplevelArgs
    args : ToplevelArgs
    subcommands = [
        ConfigCommand,
        DatabaseCommand,
        RipCommand,
        AlbumCommand,
        DiscCommand,
    ]
    pass

