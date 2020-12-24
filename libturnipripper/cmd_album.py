#a Imports
import json

from .database import Database
from .db_album import Album, AlbumSet, AlbumFilter
from .command import Command, CommandArgs

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast
from argparse import ArgumentParser
from .config import Config

#a Command subclasses
#c AlbumArgs
class AlbumArgs(CommandArgs):
    id:str
    title:str
    order_by:str
    def create_filter(self) -> AlbumFilter:
        filter = AlbumFilter()
        if self.order_by!="":    filter.order_by(self.order_by)
        if self.id!="":    filter.add_filter("id", self.id)
        if self.title!="": filter.add_filter("title", self.title)
        return filter
    pass
    
#c AlbumShowCommand
class AlbumShowCommand(Command):
    #v Properties
    args_class = AlbumArgs
    args       : AlbumArgs
    #f do_command
    def do_command(self) -> None:
        db = Database.from_config(self.config.database)
        albums = AlbumSet()
        filter = self.args.create_filter()
        for (uid,album) in db.iter_albums():
            albums.add_if(filter, uid, album)
            pass
        self.show(albums)
        pass
    #f show
    def show(self, albums:AlbumSet) -> None:
        raise Exception("Must override in subclass")
    #f All done
    pass

#c AlbumJsonCommand
class AlbumJsonCommand(AlbumShowCommand):
    #v Properties
    name = "json"
    #f show
    def show(self, albums:AlbumSet) -> None:
        json_data = []
        for album in albums.iter_ordered():
            album = cast(Album,album)
            json_data.append((str(album.uniq_id),album.as_json()))
            pass
        print(json.dumps(json_data,indent=1))
        pass
    #f All done
    pass

#c AlbumListCommand
class AlbumListCommand(AlbumShowCommand):
    #v Properties
    name = "list"
    #f show
    def show(self, albums:AlbumSet) -> None:
        for album in albums.iter_ordered():
            album = cast(Album,album)
            print(album.uniq_id,album.as_json())
            pass
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
        ("--order_by",):{"type":str, "default":"", "help":"How to order the output"},
        }
    args_class = AlbumArgs
    args       : AlbumArgs
    subcommands = [AlbumListCommand, AlbumJsonCommand]
    #f all done
    pass

