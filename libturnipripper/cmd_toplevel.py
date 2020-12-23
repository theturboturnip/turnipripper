#!/usr/bin/env python3

"""
Toplevel command for turnipripperdb

"""

#a Imports
from libturnipripper.command     import Command, CommandArgs
from libturnipripper.cmd_rip     import RipCommand
from libturnipripper.cmd_album   import AlbumCommand

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast

#a Toplevel command and args
class ToplevelArgs(CommandArgs):
    config_file:str
    verbose:int
    debug:int
    verbose_levels : ClassVar[Dict[str,int]] = {
        "info":1,
        "note":2,
        "warning":3,
        "error":4,
        }
    debug_levels : ClassVar[Dict[str,int]] = {
        "any":1,
        }
    def verbose_out(self, level:str, message:str) -> None:
        if self.verbose_levels[level] <= self.verbose:
            print(message)
            pass
        pass
    pass
    def debug_test(self, reason:str) -> bool:
        return self.debug_levels[reason] <= self.debug
    pass
class ToplevelCommand(Command):
    name = "turnipripperdb"
    parser_args = {
        ("-c", "--config_file"):{
            "dest":"config_file",
            "help":"Specify config file",
            "metavar":"FILE",
        },
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
    }
    args_class = ToplevelArgs
    args : ToplevelArgs
    subcommands = [
        RipCommand,
        AlbumCommand,
    ]
    pass

