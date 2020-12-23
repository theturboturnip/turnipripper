#a Imports
import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast
from argparse import ArgumentParser
from .config import Config

#a Command class
class CommandArgs:
    config_file:str
    verbose:int
    debug:int
    
class Command:
    """
    Base command class, from which all commands are subclassed.

    This provides a basic subcommand of a parser, and parser for
    the subcommand.
    """
    #v properties
    name : ClassVar[str] = "subcommand_name"
    parser_args: ClassVar[Dict[Union[Tuple[str],Tuple[str,str]],Dict[str,Any]]] = {}
    subcommands : ClassVar[List[Type["Command"]]] = []
    #v __init__
    def __init__(self, parser:ArgumentParser) -> None:
        self.parser = parser
        self.parser.set_defaults(func=self.do_command)
        for (k,kwargs) in self.parser_args.items():
            self.parser.add_argument(*k, **kwargs)
            pass
        if self.subcommands!=[]:
            subparser_action = self.parser.add_subparsers(help=f"Subcommand of {self.name}")
            self.subs = []
            for sub in self.subcommands:
                subparser = subparser_action.add_parser(sub.name)
                self.subs.append(sub(parser=subparser))
                pass
            pass
        pass
    #f do_command
    def do_command(self, parser:ArgumentParser, config:Config, args:CommandArgs) -> None:
        parser.print_help()
        pass
    #f All done
    pass

