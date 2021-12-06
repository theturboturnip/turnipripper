#a Imports
import re
import json

from .database import Database
from .db_disc import Disc, DiscSet, DiscFilter
from .command import Command, CommandArgs
from .musicbrainz import MusicbrainzRecordings

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast
from argparse import ArgumentParser
from .config import Config

#a Command subclasses
#c MusicbrainzArgs
class MusicbrainzArgs(CommandArgs):
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
    
#c MusicbrainzUpdateCommand
class MusicbrainzUpdateCommand(Command):
    #v Properties
    name = "update"
    args_class = MusicbrainzArgs
    args       : MusicbrainzArgs
    parser_args = {
        ("--update",):{"default":False, "action":"store_true", "help":"Update the disc downloaded data"},
        }
    #f do_command
    def do_command(self) -> None:
        db = Database.from_config(self.config.database)
        discs = DiscSet()
        filter = self.args.create_filter()
        for (uid,disc) in db.iter_discs():
            discs.add_if(filter, uid, disc)
            pass
        if len(discs)!=1:
            raise Exception(f"Must have precisely one disc selected but selected {len(discs)}")
        for disc in discs.iter_ordered():
            disc = cast(Disc,disc)
            disc.display(True,"")
            pass
        mb_id = "k1e8Jo9pHIUsOyZKWWdZMfmDMnA-"
        for d in discs.iter_ordered():
            db.fetch_mb_disc_data(d, mb_id=mb_id)
            pass
        for disc in discs.iter_ordered():
            disc = cast(Disc,disc)
            disc.display(True,"")
            pass
        # id = "8ea8fdc7-02a8-40ae-861b-57890862b216"
        if self.args.update:
            db.write()
            pass
        pass
    #f show
    def show(self, db:Database, discs:DiscSet) -> None:
        raise Exception("Must override in subclass")
    #f All done
    pass

#c MusicbrainzCommand
class MusicbrainzCommand(Command):
    #v Properties
    name = "musicbrainz"
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
    args_class = MusicbrainzArgs
    args       : MusicbrainzArgs
    subcommands = [MusicbrainzUpdateCommand]
    #f all done
    pass

