#a Imports
import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast
# if python3.X?
if False:
    from typing import Protocol
else:
    Protocol = object
    pass

from argparse import ArgumentParser, Namespace
from .config import Config

#a Command class
class CommandCallback(Protocol):
    def __call__(self, toplevel_parser:ArgumentParser, config:Config, args:"CommandArgs") -> None:
        pass

class CommandArgs(Namespace):
    func : CommandCallback
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
    def debug_test(self, reason:str) -> bool:
        return self.debug_levels[reason] <= self.debug
    def __init__(self, args:Namespace) -> None:
        for (k,v) in vars(args).items():
            setattr(self, k, v)
            pass
        pass
    pass
    
class Command:
    """
    Base command class, from which all commands are subclassed.

    This provides a basic subcommand of a parser, and parser for
    the subcommand.
    """
    #v properties
    name : ClassVar[str] = "subcommand_name"
    subcommands : ClassVar[List[Type["Command"]]] = []
    parser : ArgumentParser
    args_class : ClassVar[Type[CommandArgs]] = CommandArgs
    parser_args: ClassVar[Dict[Union[Tuple[str],Tuple[str,str]],Dict[str,Any]]] = {
    }

    #v properties set on invocation
    toplevel_parser : ArgumentParser
    args : CommandArgs
    #v __init__
    def __init__(self, parser:ArgumentParser) -> None:
        self.parser = parser
        self.parser.set_defaults(func=self.invoke_command)
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
    #f parse_args
    def parse_args(self, **kwargs:Any) -> None:
        parsed_args = self.parser.parse_args(**kwargs)
        self.args = self.args_class(parsed_args)
        pass
    #f invoke
    def invoke(self, config:Config) -> None:
        self.args.func(self.parser, config, self.args)
        pass
    #f invoke_command
    def invoke_command(self, toplevel_parser:ArgumentParser, config:Config, args:CommandArgs) -> None:
        self.toplevel_parser = toplevel_parser
        self.config = config
        self.args = self.args_class(args)
        self.do_command()
        pass
    #f do_command
    def do_command(self) -> None:
        self.parser.print_help()
        pass
    #f All done
    pass

