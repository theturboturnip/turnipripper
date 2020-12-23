#a Imports
import re

from .database import Database
from .command import Command, CommandArgs

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast
from argparse import ArgumentParser
from .config import Config

#a Command subclasses
class AlbumArgs(CommandArgs):
    id:str
    title:str
    pass
    
class AlbumListCommand(Command):
    #v Properties
    name = "list"
    #f do_command
    def do_command(self, parser:ArgumentParser, config:Config, args:CommandArgs) -> None:
        album_args = cast(AlbumArgs, args)
        print("Do command!")
        pass
    #f All done
    pass

#c AlbumCommand
class AlbumCommand(Command):
    #v Properties
    name = "album"
    parser_args = {
        ("--id",):{"type":str, "default":"", "help":"Regular expression to match id with"},
        ("--title",):{"type":str, "default":"", "help":"Regular expression to match title with"},
        }
    subcommands = [AlbumListCommand]
    #f do_command
    def do_command(self, parser:ArgumentParser, config:Config, args:CommandArgs) -> None:
        album_args = cast(AlbumArgs, args)
        id_re = re.compile(album_args.id)
        title_re = re.compile(album_args.title)
        db = Database.from_config(config.database)
        albums = set()
        for (k,v) in db.iter_albums():
            if id_re.search(str(k)): albums.add(k)
            if title_re.search(v.title): albums.add(k)
            pass
        for k in albums:
            print(db.albums[k].as_json())
            pass
        pass
    #f all done
    pass

