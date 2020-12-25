#a Imports
import re
import json

from .database import Database
from .db_disc import Disc, DiscSet, DiscFilter
from .command import Command, CommandArgs

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast
from argparse import ArgumentParser
from .config import Config

#a Command subclasses
#c DiscArgs
class DiscArgs(CommandArgs):
    id:str
    title:str
    order_by:str
    include_tracks:bool
    def create_filter(self) -> DiscFilter:
        filter = DiscFilter()
        if self.order_by!="":    filter.order_by(self.order_by)
        if self.id!="":    filter.add_filter("id", self.id)
        if self.title!="": filter.add_filter("title", self.title)
        return filter
    pass
    
#c DiscShowCommand
class DiscShowCommand(Command):
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
        self.show(discs)
        pass
    #f show
    def show(self, discs:DiscSet) -> None:
        raise Exception("Must override in subclass")
    #f All done
    pass

#c DiscJsonCommand
class DiscJsonCommand(DiscShowCommand):
    #v Properties
    name = "json"
    #f show
    def show(self, discs:DiscSet) -> None:
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

#c DiscListCommand
class DiscListCommand(DiscShowCommand):
    #v Properties
    name = "list"
    #f show
    def show(self, discs:DiscSet) -> None:
        for disc in discs.iter_ordered():
            disc = cast(Disc,disc)
            disc_json = disc.as_json()
            if not self.args.include_tracks: del disc_json["tracks"]
            print(disc.uniq_id,disc_json)
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
        ("--title",):{"type":str, "default":"", "help":"Regular expression to match title with"},
        ("--order_by",):{"type":str, "default":"", "help":"How to order the output"},
        ("--include_tracks",):{"action":"store_true", "default":False, "help":"Include tracks in output"},
        }
    args_class = DiscArgs
    args       : DiscArgs
    subcommands = [DiscListCommand, DiscJsonCommand]
    #f all done
    pass

