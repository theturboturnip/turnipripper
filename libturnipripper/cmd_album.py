#a Imports
import json

from .database import Database
from .db_album import Album, AlbumSet, AlbumFilter
from .command import Command, CommandArgs
from .edit   import Editor

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast
from argparse import ArgumentParser
from .config import Config

#a Command subclasses
#c AlbumArgs
class AlbumArgs(CommandArgs):
    id:str
    title:str
    musicbrainz:str
    order_by:str
    max_albums:int
    def create_filter(self) -> AlbumFilter:
        filter = AlbumFilter()
        if self.order_by!="":    filter.order_by(self.order_by)
        if self.id!="":    filter.add_filter("id", self.id)
        if self.title!="": filter.add_filter("title", self.title)
        if self.musicbrainz!="": filter.add_filter("musicbrainz", self.musicbrainz)
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
        self.show(db, albums)
        pass
    #f show
    def show(self, db:Database, albums:AlbumSet) -> None:
        raise Exception("Must override in subclass")
    #f All done
    pass

#c AlbumJsonCommand
class AlbumJsonCommand(AlbumShowCommand):
    #v Properties
    name = "json"
    #f show
    def show(self, db:Database, albums:AlbumSet) -> None:
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
    def show(self, db:Database, albums:AlbumSet) -> None:
        for album in albums.iter_ordered():
            album = cast(Album,album)
            print(album.uniq_id,album.as_json())
            pass
        pass
    #f All done
    pass

#c AlbumEditCommand
class AlbumEditCommand(AlbumShowCommand):
    #v Properties
    name = "edit"
    #f show
    def show(self, db:Database, albums:AlbumSet) -> None:
        if len(albums)>self.args.max_albums:
            raise Exception(f"Selected {len(albums)} but max_albums was {self.args.max_albums} - increase max_albums, or filter albums down")
        editor = Editor()
        property_edit_type = "user"
        modified = False
        for album in albums.iter_ordered():
            album = cast(Album,album)
            modified = modified or album.edit_json(editor, property_edit_type)
            pass
        if modified: db.write()
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
        ("--musicbrainz",):{"type":str, "default":"", "help":"Regular expression to match musicbrainz release id with"},
        ("--order_by",):{"type":str, "default":"", "help":"How to order the output"},
        ("--max_albums",):{"type":int, "default":1, "help":"Maximum number of albums"},
        }
    args_class = AlbumArgs
    args       : AlbumArgs
    subcommands = [AlbumListCommand, AlbumJsonCommand, AlbumEditCommand]
    #f all done
    pass

