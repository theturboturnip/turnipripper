#a Imports
import re
import json

from .database import Database
from .db_disc import Disc, DiscSet, DiscFilter
from .command import Command, CommandArgs
from .encode import Encoder
from .edit   import Editor

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast
from argparse import ArgumentParser
from .config import Config

#a Command subclasses
#c DiscArgs
class DiscArgs(CommandArgs):
    id:str
    artist:str
    title:str
    cddb:str
    musicbrainz:str
    order_by:str
    include_tracks:bool
    max_discs:int
    def create_filter(self) -> DiscFilter:
        filter = DiscFilter()
        if self.order_by!="":    filter.order_by(self.order_by)
        if self.id!="":    filter.add_filter("id", self.id)
        if self.title!="": filter.add_filter("title", self.title)
        if self.artist!="": filter.add_filter("artist", self.artist)
        if self.musicbrainz!="": filter.add_filter("musicbrainz", self.musicbrainz)
        if self.cddb!="":        filter.add_filter("cddb", self.cddb)
        return filter
    pass
    
#c DiscEncodeArgs
class DiscEncodeArgs(DiscArgs):
    force:bool
    source:str
    pass
    
#c DiscShowCommand
class DiscShowCommand(Command):
    """
    Parent of JSON, List and edit commands
    """
    #v Properties
    args_class = DiscArgs
    args       : DiscArgs
    #f do_command
    def do_command(self) -> None:
        db = Database.from_config(self.config.database)
        discs = DiscSet()
        filter = self.args.create_filter()
        for (uid,disc) in db.iter_discs():
            discs.add_if(filter, uid, disc)
            pass
        self.show(db, discs)
        pass
    #f show
    def show(self, db:Database, discs:DiscSet) -> None:
        raise Exception("Must override in subclass")
    #f All done
    pass

#c DiscJsonCommand
class DiscJsonCommand(DiscShowCommand):
    #v Properties
    name = "json"
    #f show
    def show(self, db:Database, discs:DiscSet) -> None:
        json_data = []
        for disc in discs.iter_ordered():
            disc = cast(Disc,disc)
            disc_json = disc.as_json()
            if not self.args.include_tracks: del disc_json["tracks"]
            json_data.append((str(disc.uniq_id),disc_json))
            pass
        print(json.dumps(json_data,indent=1))
        pass
    #f All done
    pass

#c DiscEditCommand
class DiscEditCommand(DiscShowCommand):
    #v Properties
    name = "edit"
    #f show
    def show(self, db:Database, discs:DiscSet) -> None:
        if len(discs)>self.args.max_discs:
            raise Exception(f"Selected {len(discs)} but max_discs was {self.args.max_discs} - increase max_discs, or filter discs down")
        editor = Editor()
        property_edit_type = "user"
        if not self.args.include_tracks: property_edit_type="user_no_tracks"
        modified = False
        for disc in discs.iter_ordered():
            disc = cast(Disc,disc)
            modified = modified or disc.edit_json(editor, property_edit_type)
            pass
        if modified: db.write()
        pass
    #f All done
    pass

#c DiscListCommand
class DiscListCommand(DiscShowCommand):
    #v Properties
    name = "list"
    #f show
    def show(self, db:Database, discs:DiscSet) -> None:
        for disc in discs.iter_ordered():
            disc = cast(Disc,disc)
            disc.display(self.args.include_tracks,"")
            pass
        pass
    #f All done
    pass

#c DiscEncodeCommand
class DiscEncodeCommand(Command):
    #v Properties
    args_class = DiscEncodeArgs
    args       : DiscEncodeArgs
    name = "encode"
    parser_args = {
        ("--force",):{"default":False, "action":"store_true", "help":"Encode even if output files are newer than old"},
        ("--source",):{"type":str, "default":"", "help":"Prefix to use instead of db config source for files to encode"},
        }
    #f do_command
    def do_command(self) -> None:
        db = Database.from_config(self.config.database)
        discs = DiscSet()
        filter = self.args.create_filter()
        for (uid,disc) in db.iter_discs():
            discs.add_if(filter, uid, disc)
            pass
        if len(discs)>self.args.max_discs:
            raise Exception(f"Selected {len(discs)} but max_discs was {self.args.max_discs} - increase max_discs, or filter discs down")
        e = Encoder(db, self.config, self.args.source)
        for d in discs.iter_ordered():
            print(f"Encoding {d.ui_str()}")
            e.encode(d, force_if_newer=self.args.force)
            pass
        pass
    #f All done
    pass

#c DiscCommand
class DiscCommand(Command):
    #v Properties
    name = "disc"
    parser_args = {
        ("--id",):{"type":str, "default":"", "help":"Regular expression to match id with"},
        ("--cddb",):{"type":str, "default":"", "help":"Regular expression to match cddb_id with"},
        ("--musicbrainz",):{"type":str, "default":"", "help":"Regular expression to match musicbrainz id with"},
        ("--title",):{"type":str, "default":"", "help":"Regular expression to match title with"},
        ("--artist",):{"type":str, "default":"", "help":"Regular expression to match artist with"},
        ("--order_by",):{"type":str, "default":"", "help":"How to order the output"},
        ("--include_tracks",):{"action":"store_true", "default":False, "help":"Include tracks in output"},
        ("--max_discs",):{"type":int, "default":1, "help":"Maximum number of discs to encode"},
        }
    args_class = DiscArgs
    args       : DiscArgs
    subcommands = [DiscListCommand, DiscJsonCommand, DiscEditCommand, DiscEncodeCommand]
    #f all done
    pass

