#!/usr/bin/env python3

"""
Toplevel command for turnipripperdb

"""

#a Imports
from .command      import Command, CommandArgs
from .cmd_rip      import RipCommand
from .cmd_album    import AlbumCommand
from .cmd_disc     import DiscCommand
from .cmd_database import DatabaseCommand

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast

#a Toplevel command and args
class ToplevelArgs(CommandArgs):
    config_file:str
    pass
class ToplevelCommand(Command):
    name = "turnipripperdb"
    parser_args = Command.parser_args
    parser_args.update({
        ("-c", "--config_file"):{
            "dest":"config_file",
            "help":"Specify config file",
            "metavar":"FILE",
        },
    })
    args_class = ToplevelArgs
    args : ToplevelArgs
    subcommands = [
        RipCommand,
        AlbumCommand,
        DiscCommand,
        DatabaseCommand,
    ]
    pass

