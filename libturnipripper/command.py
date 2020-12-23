#a Imports
import typing
from typing import Protocol, Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast
from argparse import ArgumentParser, Namespace
from .config import Config

#a Command class
class CommandCallback(Protocol):
    def __call__(self, toplevel_parser:ArgumentParser, config:Config, args:"CommandArgs") -> None:
        pass

class CommandArgs:
    func : CommandCallback
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
    parser_args: ClassVar[Dict[Union[Tuple[str],Tuple[str,str]],Dict[str,Any]]] = {}
    subcommands : ClassVar[List[Type["Command"]]] = []
    parser : ArgumentParser
    args_class : ClassVar[Type[CommandArgs]] = CommandArgs

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
        self.args = self.args_class(self.parser.parse_args(**kwargs))
        pass
    #f invoke
    def invoke(self, config:Config) -> None:
        self.args.func(self.parser, config, self.args)
        pass
    #f invoke_command
    def invoke_command(self, toplevel_parser:ArgumentParser, config:Config, args:CommandArgs) -> None:
        self.toplevel_parser = toplevel_parser
        self.config = config
        self.args = args
        self.do_command()
        pass
    #f do_command
    def do_command(self) -> None:
        self.parser.print_help()
        pass
    #f All done
    pass

