#a Imports
import json

from .config import Config
from .command import Command, CommandArgs

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast
from argparse import ArgumentParser

#a Command subclasses
#c ConfigArgs
class ConfigArgs(CommandArgs):
    pass
    
#c ConfigShowCommand
class ConfigShowCommand(Command):
    #v Properties
    name="show"
    args_class = ConfigArgs
    args       : ConfigArgs
    parser_args = {}
    #f do_command
    def do_command(self) -> None:
        print(self.config)
        pass
    #f All done
    pass

#c ConfigCommand
class ConfigCommand(Command):
    #v Properties
    name = "config"
    parser_args = {
        }
    args_class = ConfigArgs
    args       : ConfigArgs
    subcommands = [ConfigShowCommand]
    #f all done
    pass

